import reflex as rx
from typing import Optional
import httpx
import logging


class UploadState(rx.State):
    patient_email: str = ""
    record_title: str = ""
    notes: str = ""
    uploaded_file: Optional[rx.UploadFile] = None
    is_uploading: bool = False
    upload_progress: int = 0
    upload_error: str = ""

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.upload_error = "No file was selected for upload."
            return
        self.uploaded_file = files[0]
        self.upload_error = ""
        yield rx.toast.info(f"Selected file: {self.uploaded_file.filename}")

    @rx.event
    async def submit_record(self):
        if not self.patient_email or not self.record_title or (not self.uploaded_file):
            yield rx.toast.error(
                "Patient Email, Record Title, and a file are required."
            )
            return
        self.is_uploading = True
        yield
        try:
            from app.states.state import AuthState

            auth_state = await self.get_state(AuthState)
            token = auth_state.token
            if not token:
                self.is_uploading = False
                yield rx.toast.error(
                    "Authentication token not found. Please log in again."
                )
                return
            file_content = await self.uploaded_file.read()
            async with httpx.AsyncClient(timeout=60) as client:
                files = {
                    "file": (
                        self.uploaded_file.filename,
                        file_content,
                        self.uploaded_file.content_type,
                    )
                }
                data = {
                    "patient_email": self.patient_email,
                    "title": self.record_title,
                    "notes": self.notes,
                }
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.post(
                    "http://localhost:8000/api/records/upload",
                    files=files,
                    data=data,
                    headers=headers,
                )
            response.raise_for_status()
            self.patient_email = ""
            self.record_title = ""
            self.notes = ""
            self.uploaded_file = None
            self.upload_error = ""
            yield rx.toast.success("Record uploaded successfully!")
            yield rx.redirect("/records")
        except httpx.HTTPStatusError as e:
            error_detail = "An error occurred during upload."
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except Exception as json_error:
                logging.exception(f"Error parsing error response: {json_error}")
            logging.exception(
                f"HTTP error during record submission: {e} - {error_detail}"
            )
            self.upload_error = f"Upload failed: {error_detail}"
            yield rx.toast.error(f"Upload failed: {error_detail}")
        except Exception as e:
            logging.exception(f"Failed to upload record: {e}")
            self.upload_error = f"An unexpected error occurred: {e}"
            yield rx.toast.error(f"An unexpected error occurred: {e}")
        finally:
            self.is_uploading = False