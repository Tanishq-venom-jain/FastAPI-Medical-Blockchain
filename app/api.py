import reflex as rx
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from typing import Annotated, Optional
from supabase import Client
import logging
from app.backend.database import get_supabase_client
from app.backend.auth import get_current_user_data, role_required
from app.backend.utils import calculate_file_hash, generate_qr_code
from app.backend.blockchain import notarize_hash, verify_hash_on_chain
from app.backend.models import RecordCreate, RecordResponse, UserRole

api = FastAPI(title="ArogyaChain API")


@api.get("/api/health")
async def health_check():
    return {"status": "ok"}


@api.post("/api/records/upload", response_model=RecordResponse)
async def upload_record(
    patient_email: Annotated[str, Form()],
    title: Annotated[str, Form()],
    notes: Annotated[Optional[str], Form()] = None,
    file: UploadFile = File(...),
    current_user=Depends(role_required(UserRole.DOCTOR)),
    supabase: Client = Depends(get_supabase_client),
):
    logging.info(f"Upload request from doctor: {current_user['email']}")
    allowed_mime_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Please upload a PDF, PNG, or JPG.",
        )
    try:
        patient_res = (
            supabase.table("users")
            .select("id, role")
            .eq("email", patient_email)
            .single()
            .execute()
        )
        if not patient_res.data or patient_res.data["role"] != UserRole.PATIENT.value:
            raise HTTPException(status_code=404, detail="Patient not found.")
        patient_id = patient_res.data["id"]
    except Exception as e:
        logging.exception(f"Error validating patient '{patient_email}': {e}")
        raise HTTPException(status_code=500, detail="Error validating patient details.")
    try:
        file_content = await file.read()
        file_hash = calculate_file_hash(file_content)
        file_extension = file.filename.split(".")[-1]
        file_path_in_storage = (
            f"{current_user['id']}/{patient_id}/{file_hash}.{file_extension}"
        )
        supabase.storage.from_("records").upload(
            file_path_in_storage,
            file_content,
            file_options={"content-type": file.content_type},
        )
        file_url = supabase.storage.from_("records").get_public_url(
            file_path_in_storage
        )
    except Exception as e:
        logging.exception(f"Failed to upload file to Supabase: {e}")
        raise HTTPException(
            status_code=500, detail="File upload failed during storage."
        )
    try:
        tx_hash = notarize_hash(file_hash)
        notarization_status = "success" if tx_hash else "pending"
    except Exception as e:
        logging.exception(f"Blockchain notarization failed: {e}")
        tx_hash = None
        notarization_status = "failed"
    try:
        record_data = {
            "patient_id": patient_id,
            "doctor_id": str(current_user["id"]),
            "file_url": file_url,
            "file_hash": file_hash,
            "tx_hash": tx_hash,
            "notarization_status": notarization_status,
            "title": title,
            "notes": notes,
        }
        inserted_record_res = supabase.table("records").insert(record_data).execute()
        if not inserted_record_res.data:
            raise Exception("No data returned from insert operation.")
        new_record = inserted_record_res.data[0]
    except Exception as e:
        logging.exception(f"Failed to save record to database: {e}")
        try:
            supabase.storage.from_("records").remove([file_path_in_storage])
            logging.info(f"Cleaned up orphaned file: {file_path_in_storage}")
        except Exception as remove_e:
            logging.exception(f"Failed to cleanup orphaned storage file: {remove_e}")
        raise HTTPException(status_code=500, detail="Failed to save record metadata.")
    try:
        record_id = new_record["id"]
        frontend_url = "http://localhost:3000"
        qr_code_bytes = generate_qr_code(record_id, tx_hash, frontend_url)
        qr_path = f"{record_id}_qr.png"
        supabase.storage.from_("qrcodes").upload(
            qr_path, qr_code_bytes, file_options={"content-type": "image/png"}
        )
        qr_url = supabase.storage.from_("qrcodes").get_public_url(qr_path)
        updated_record = (
            supabase.table("records")
            .update({"qr_url": qr_url})
            .eq("id", record_id)
            .execute()
            .data[0]
        )
        return RecordResponse(**updated_record)
    except Exception as e:
        logging.exception(f"Failed to upload QR code or finalize record: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate and save QR code."
        )


@api.get("/api/records", response_model=list[RecordResponse])
async def get_user_records(
    current_user=Depends(get_current_user_data),
    supabase: Client = Depends(get_supabase_client),
):
    user_id = str(current_user["id"])
    user_role = current_user["role"]
    query_field = "patient_id" if user_role == UserRole.PATIENT else "doctor_id"
    records_res = (
        supabase.table("records")
        .select("*")
        .eq(query_field, user_id)
        .order("created_at", desc=True)
        .execute()
    )
    if not records_res.data:
        return []
    return [RecordResponse(**record) for record in records_res.data]


@api.get("/api/verify/{record_id}")
async def verify_record_endpoint(
    record_id: str, supabase: Client = Depends(get_supabase_client)
):
    record_res = (
        supabase.table("records")
        .select("id, title, created_at, file_hash, tx_hash")
        .eq("id", record_id)
        .single()
        .execute()
    )
    if not record_res.data:
        raise HTTPException(status_code=404, detail="Record not found.")
    record = record_res.data
    file_hash = record["file_hash"]
    verification_details = verify_hash_on_chain(file_hash)
    if not verification_details:
        raise HTTPException(
            status_code=500, detail="Blockchain verification service is unavailable."
        )
    return {
        "record": {
            "id": record["id"],
            "title": record["title"],
            "created_at": record["created_at"],
            "tx_hash": record["tx_hash"],
        },
        "verification": verification_details,
    }


from app.backend.models import NoteCreate, NoteUpdate, NoteResponse, MedicineInput
from app.backend.gemini_service import get_medicine_alternatives, MedicineInfo


@api.post("/api/ai/medicine-alternatives", response_model=Optional[MedicineInfo])
async def medicine_alternatives(
    request: MedicineInput, current_user=Depends(get_current_user_data)
):
    logging.info(
        f"Medicine alternative request for '{request.medicine_name}' from user: {current_user['email']}"
    )
    alternatives = get_medicine_alternatives(request.medicine_name)
    if not alternatives:
        raise HTTPException(
            status_code=503, detail="AI service is currently unavailable."
        )
    return alternatives


@api.post("/api/notes", response_model=NoteResponse)
async def create_note(
    note_in: NoteCreate,
    current_user=Depends(role_required(UserRole.PATIENT)),
    supabase: Client = Depends(get_supabase_client),
):
    try:
        note_data = note_in.dict()
        note_data["patient_id"] = str(current_user["id"])
        inserted_note_res = supabase.table("notes").insert(note_data).execute()
        if not inserted_note_res.data:
            raise HTTPException(status_code=500, detail="Failed to create note.")
        return NoteResponse(**inserted_note_res.data[0])
    except Exception as e:
        logging.exception(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail="Could not create note.")


@api.get("/api/notes", response_model=list[NoteResponse])
async def get_notes(
    current_user=Depends(role_required(UserRole.PATIENT)),
    supabase: Client = Depends(get_supabase_client),
):
    user_id = str(current_user["id"])
    notes_res = (
        supabase.table("notes")
        .select("*")
        .eq("patient_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return [NoteResponse(**note) for note in notes_res.data]


@api.put("/api/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_in: NoteUpdate,
    current_user=Depends(role_required(UserRole.PATIENT)),
    supabase: Client = Depends(get_supabase_client),
):
    user_id = str(current_user["id"])
    existing_note_res = (
        supabase.table("notes")
        .select("id")
        .eq("id", note_id)
        .eq("patient_id", user_id)
        .single()
        .execute()
    )
    if not existing_note_res.data:
        raise HTTPException(status_code=404, detail="Note not found or access denied.")
    updated_note_res = (
        supabase.table("notes").update(note_in.dict()).eq("id", note_id).execute()
    )
    if not updated_note_res.data:
        raise HTTPException(status_code=500, detail="Failed to update note.")
    return NoteResponse(**updated_note_res.data[0])


@api.delete("/api/notes/{note_id}", status_code=204)
async def delete_note(
    note_id: str,
    current_user=Depends(role_required(UserRole.PATIENT)),
    supabase: Client = Depends(get_supabase_client),
):
    user_id = str(current_user["id"])
    delete_res = (
        supabase.table("notes")
        .delete()
        .eq("id", note_id)
        .eq("patient_id", user_id)
        .execute()
    )
    if not delete_res.data:
        raise HTTPException(
            status_code=404, detail="Note not found or could not be deleted."
        )
    return