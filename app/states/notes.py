import reflex as rx
from typing import TypedDict, Optional
import httpx
import logging


class Note(TypedDict):
    id: str
    title: str
    content: str
    created_at: str
    updated_at: str


class Alternative(TypedDict):
    name: str
    price_range: str


class MedicineInfo(TypedDict):
    medicine_name: str
    generic_alternatives: list[Alternative]
    notes: str


class NotesState(rx.State):
    notes: list[Note] = []
    is_loading: bool = False
    error_message: str = ""
    show_note_modal: bool = False
    current_note_id: Optional[str] = None
    current_title: str = ""
    current_content: str = ""
    medicine_input: str = ""
    alternatives_result: Optional[MedicineInfo] = None
    is_fetching_alternatives: bool = False
    alternatives_error: str = ""

    @rx.event(background=True)
    async def fetch_notes(self):
        async with self:
            self.is_loading = True
            self.error_message = ""
        try:
            from app.states.state import AuthState

            async with self:
                auth_state = await self.get_state(AuthState)
                token = auth_state.token
            if not token:
                async with self:
                    self.error_message = "Authentication token not found."
                    self.is_loading = False
                return
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/notes", headers=headers
                )
                response.raise_for_status()
                notes_data = response.json()
                async with self:
                    self.notes = notes_data
        except httpx.HTTPStatusError as e:
            logging.exception(f"HTTP error fetching notes: {e}")
            async with self:
                self.error_message = f"Failed to fetch notes: {e.response.status_code}"
        except Exception as e:
            logging.exception(f"Error fetching notes: {e}")
            async with self:
                self.error_message = "An unexpected error occurred."
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def get_alternatives(self):
        if not self.medicine_input.strip():
            async with self:
                self.alternatives_error = "Please enter a medicine name."
            yield rx.toast.warning("Please enter a medicine name.")
            return
        async with self:
            self.is_fetching_alternatives = True
            self.alternatives_error = ""
            self.alternatives_result = None
        try:
            from app.states.state import AuthState

            async with self:
                auth_state = await self.get_state(AuthState)
                token = auth_state.token
            if not token:
                raise Exception("Not authenticated")
            headers = {"Authorization": f"Bearer {token}"}
            request_body = {"medicine_name": self.medicine_input}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/ai/medicine-alternatives",
                    json=request_body,
                    headers=headers,
                    timeout=60,
                )
            response.raise_for_status()
            result = response.json()
            async with self:
                self.alternatives_result = result
        except httpx.HTTPStatusError as e:
            error_detail = "AI service failed to process the request."
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except Exception as json_error:
                logging.exception(f"Could not parse error response: {json_error}")
            logging.exception(f"HTTP error fetching alternatives: {e} - {error_detail}")
            async with self:
                self.alternatives_error = error_detail
            yield rx.toast.error(error_detail)
        except Exception as e:
            logging.exception(f"Error fetching alternatives: {e}")
            async with self:
                self.alternatives_error = "An unexpected error occurred."
            yield rx.toast.error("An unexpected error occurred.")
        finally:
            async with self:
                self.is_fetching_alternatives = False

    @rx.event
    def open_note_modal(self, note: Optional[Note] = None):
        if note:
            self.current_note_id = note["id"]
            self.current_title = note["title"]
            self.current_content = note["content"]
        else:
            self.current_note_id = None
            self.current_title = ""
            self.current_content = ""
        self.show_note_modal = True

    @rx.event
    def close_note_modal(self):
        self.show_note_modal = False
        self.current_note_id = None
        self.current_title = ""
        self.current_content = ""

    @rx.event(background=True)
    async def save_note(self, form_data: dict):
        async with self:
            self.is_loading = True
        try:
            from app.states.state import AuthState

            async with self:
                auth_state = await self.get_state(AuthState)
                token = auth_state.token
                note_id = self.current_note_id
            if not token:
                raise Exception("Not authenticated")
            headers = {"Authorization": f"Bearer {token}"}
            note_data = {"title": form_data["title"], "content": form_data["content"]}
            async with httpx.AsyncClient() as client:
                if note_id:
                    url = f"http://localhost:8000/api/notes/{note_id}"
                    response = await client.put(url, json=note_data, headers=headers)
                else:
                    url = "http://localhost:8000/api/notes"
                    response = await client.post(url, json=note_data, headers=headers)
                response.raise_for_status()
            yield NotesState.fetch_notes
            yield NotesState.close_note_modal
            yield rx.toast.success("Note saved successfully!")
        except Exception as e:
            logging.exception(f"Error saving note: {e}")
            yield rx.toast.error(f"Failed to save note: {e}")
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def delete_note(self, note_id: str):
        async with self:
            self.is_loading = True
        try:
            from app.states.state import AuthState

            async with self:
                auth_state = await self.get_state(AuthState)
                token = auth_state.token
            if not token:
                raise Exception("Not authenticated")
            headers = {"Authorization": f"Bearer {token}"}
            url = f"http://localhost:8000/api/notes/{note_id}"
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)
            response.raise_for_status()
            yield NotesState.fetch_notes
            yield rx.toast.info("Note deleted.")
        except Exception as e:
            logging.exception(f"Error deleting note: {e}")
            yield rx.toast.error("Failed to delete note.")
        finally:
            async with self:
                self.is_loading = False