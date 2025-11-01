import reflex as rx
from typing import Optional, TypedDict
import httpx
import logging


class VerificationDetails(TypedDict):
    is_verified: bool
    details: dict


class RecordDetails(TypedDict):
    id: str
    title: str
    created_at: str
    tx_hash: str


class VerificationResult(TypedDict):
    record: RecordDetails
    verification: VerificationDetails


class VerifyState(rx.State):
    """State for the record verification page."""

    record_id_input: str = ""
    verification_result: Optional[VerificationResult] = None
    is_verifying: bool = False
    error_message: str = ""

    @rx.event
    def on_load(self):
        """Handle page load, checking for a record ID in the URL."""
        splat = self.router.page.params.get("splat", [])
        if splat:
            self.record_id_input = splat[0]
            return VerifyState.verify_record

    @rx.event(background=True)
    async def verify_record(self):
        async with self:
            record_id_to_verify = self.record_id_input.strip()
            if not record_id_to_verify:
                self.error_message = "Please enter a Record ID."
                yield
                return
            self.is_verifying = True
            self.error_message = ""
            self.verification_result = None
            yield
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8000/api/verify/{record_id_to_verify}"
                )
            response.raise_for_status()
            result = response.json()
            async with self:
                self.verification_result = result
        except httpx.HTTPStatusError as e:
            error_detail = f"Verification failed: {e.response.status_code}"
            try:
                error_detail = e.response.json().get("detail", error_detail)
            except Exception as json_e:
                logging.exception(f"Error parsing error response: {json_e}")
                pass
            async with self:
                self.error_message = error_detail
            logging.exception(
                f"Verification HTTP error for {record_id_to_verify}: {e} - {error_detail}"
            )
        except Exception as e:
            async with self:
                self.error_message = f"An unexpected error occurred."
            logging.exception(f"Verification failed for {record_id_to_verify}: {e}")
        finally:
            async with self:
                self.is_verifying = False