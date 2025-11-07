from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"


class RecordCreate(BaseModel):
    patient_email: EmailStr
    title: str
    notes: Optional[str] = None


class RecordResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    file_url: str
    file_hash: str
    tx_hash: Optional[str] = None
    notarization_status: str
    qr_url: Optional[str] = None
    title: str
    notes: Optional[str] = None
    created_at: str


class NoteBase(BaseModel):
    title: str
    content: str


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteResponse(NoteBase):
    id: str
    patient_id: str
    created_at: str
    updated_at: str


class MedicineInput(BaseModel):
    medicine_name: str