import reflex as rx
from typing import TypedDict, Optional, Any
import logging


class NavItem(TypedDict):
    label: str
    icon: str
    href: str


class Record(TypedDict):
    id: str
    patient_id: str
    doctor_id: str
    file_url: str
    file_hash: str
    tx_hash: Optional[str]
    notarization_status: str
    qr_url: Optional[str]
    title: str
    notes: Optional[str]
    created_at: str


class DashboardState(rx.State):
    """State for the dashboard page."""

    is_mobile_menu_open: bool = False

    @rx.var
    def nav_items(self) -> list[NavItem]:
        base_items = [
            {"label": "Dashboard", "icon": "layout-dashboard", "href": "/dashboard"},
            {"label": "My Records", "icon": "files", "href": "/records"},
            {"label": "Verify", "icon": "shield-check", "href": "/verify"},
        ]
        if self.current_user_role == "doctor":
            base_items.insert(
                1, {"label": "Upload Record", "icon": "upload", "href": "/upload"}
            )
        if self.current_user_role == "patient":
            base_items.append(
                {"label": "My Notes", "icon": "notebook-pen", "href": "/notes"}
            )
        return base_items

    active_page: str = "Dashboard"
    records: list[Record] = []
    is_loading: bool = False

    @rx.var
    def total_records(self) -> int:
        return len(self.records)

    @rx.var
    def verified_records(self) -> int:
        return sum(
            (1 for r in self.records if r.get("notarization_status") == "success")
        )

    @rx.var
    def pending_records(self) -> int:
        return self.total_records - self.verified_records

    error_message: str = ""
    current_user_role: str = ""
    current_user_email: str = ""
    current_user_id: str = ""

    @rx.event
    def toggle_mobile_menu(self):
        self.is_mobile_menu_open = not self.is_mobile_menu_open

    @rx.event(background=True)
    async def handle_new_record_notification(self, payload: dict):
        """Handles the realtime payload and shows a toast notification."""
        async with self:
            yield rx.toast.info(
                "A new medical record has been uploaded.",
                description="Click the button to see the latest updates.",
                action=rx.el.button(
                    "Refresh", on_click=DashboardState.fetch_records, size="1"
                ),
                duration=10000,
            )

    @rx.event(background=True)
    async def setup_realtime_subscription(self):
        """Sets up the Supabase realtime subscription for new records."""
        async with self:
            if self.current_user_role != "patient" or not self.current_user_id:
                return
        try:
            from app.backend.database import get_supabase_client
            import asyncio

            client = get_supabase_client()
            channel = client.channel("record-changes")

            @rx.event
            async def on_new_record_sync(payload):
                await self.handle_new_record_notification(payload)

            channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="records",
                filter=f"patient_id=eq.{self.current_user_id}",
                callback=on_new_record_sync,
            )
            channel.subscribe()
            logging.info(
                f"Subscribed to record updates for patient_id: {self.current_user_id}"
            )
            while True:
                await asyncio.sleep(60)
        except Exception as e:
            logging.exception(
                f"Could not set up realtime subscription. This might be because the 'records' table is not enabled for realtime. SQL to enable: ALTER PUBLICATION supabase_realtime ADD TABLE records; Error: {e}"
            )

    @rx.event
    def set_active_page(self, page: str):
        self.active_page = page

    @rx.event
    def logout(self):
        """Logs the user out and redirects to the login page."""
        return rx.redirect("/")

    @rx.event(background=True)
    async def fetch_records(self):
        async with self:
            self.is_loading = True
            self.error_message = ""
        try:
            from app.states.state import AuthState
            import httpx

            token = None
            async with self:
                auth_state = await self.get_state(AuthState)
                token = auth_state.token
            if not token:
                async with self:
                    self.error_message = (
                        "Authentication token not found. Please log in."
                    )
                    self.is_loading = False
                return
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/records", headers=headers
                )
            response.raise_for_status()
            records_data = response.json()
            from app.backend.database import get_supabase_client
            from app.backend.auth import get_current_user_data

            supabase = get_supabase_client()
            current_user = get_current_user_data(token, supabase)
            async with self:
                self.records = records_data if records_data else []
                self.current_user_role = current_user.get("role", "")
                self.current_user_email = current_user.get("email", "")
                self.current_user_id = current_user.get("id", "")
        except httpx.HTTPStatusError as e:
            logging.exception(f"Error fetching records: {e}")
            async with self:
                self.error_message = (
                    f"Failed to fetch records: {e.response.status_code}"
                )
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred while fetching records: {e}"
            )
            async with self:
                self.error_message = "An unexpected error occurred."
        finally:
            async with self:
                self.is_loading = False