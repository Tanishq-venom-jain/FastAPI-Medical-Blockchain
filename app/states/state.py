import reflex as rx
import os
from supabase import create_client, Client
from typing import Optional
import logging


class State(rx.State):
    """The base state for the app."""


class AuthState(rx.State):
    """Handles authentication and user state."""

    email: str = ""
    password: str = ""
    error_message: str = ""
    is_loading: bool = False
    is_signup: bool = False
    selected_role: str = "patient"
    token: str = rx.Cookie(name="sb-localhost-auth-token", same_site="strict")

    def _get_supabase_client(self) -> Client:
        return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

    @rx.event
    def on_submit(self):
        """Handles the login/signup form submission."""
        self.is_loading = True
        self.error_message = ""
        if not self.email or not self.password:
            self.error_message = "Email and password cannot be empty."
            self.is_loading = False
            return
        try:
            supabase = self._get_supabase_client()
            if self.is_signup:
                try:
                    response = supabase.auth.sign_up(
                        {"email": self.email, "password": self.password}
                    )
                    user = response.user
                    if user:
                        logging.info(f"Sign up initiated for {user.email}")
                        user_data = {
                            "id": str(user.id),
                            "email": self.email,
                            "role": self.selected_role,
                        }
                        supabase.table("users").insert(user_data).execute()
                        self.error_message = "Signup successful! Please check your email to confirm before logging in."
                        self.is_signup = False
                        self.email = ""
                        self.password = ""
                    else:
                        self.error_message = (
                            "Could not sign up user. Check password strength or logs."
                        )
                except Exception as sign_up_error:
                    logging.exception(f"Error during sign up: {sign_up_error}")
                    if (
                        "already registered" in str(sign_up_error).lower()
                        or "user already registered" in str(sign_up_error).lower()
                    ):
                        self.error_message = (
                            "This email is already registered. Please log in."
                        )
                    else:
                        self.error_message = f"An error occurred during sign up."
            else:
                try:
                    response = supabase.auth.sign_in_with_password(
                        {"email": self.email, "password": self.password}
                    )
                    if response.user and response.session:
                        logging.info(f"Login successful for {response.user.email}")
                        self.token = response.session.access_token
                        user_role_res = (
                            supabase.table("users")
                            .select("role")
                            .eq("id", str(response.user.id))
                            .single()
                            .execute()
                        )
                        if user_role_res.data:
                            role = user_role_res.data.get("role")
                            if role == "doctor":
                                yield rx.redirect("/upload")
                            elif role == "patient":
                                yield rx.redirect("/records")
                            else:
                                yield rx.redirect("/dashboard")
                        else:
                            yield rx.redirect("/dashboard")
                except Exception as e:
                    logging.exception(f"Error during login: {e}")
                    self.error_message = "Invalid login credentials."
        except Exception as e:
            logging.exception(f"Error during authentication: {e}")
            self.error_message = f"An unexpected error occurred: {e}"
        self.is_loading = False
        yield

    @rx.event
    def toggle_mode(self):
        self.is_signup = not self.is_signup
        self.error_message = ""
        self.email = ""
        self.password = ""

    @rx.event
    def on_load(self) -> rx.event.EventSpec | None:
        """Check if the user is authenticated on page load."""
        logging.info(f"on_load triggered for path: {self.router.page.path}")
        is_public_page = (
            self.router.page.path == "/" or self.router.page.path.startswith("/verify")
        )
        if is_public_page:
            logging.info(f"Allowing access to public page: {self.router.page.path}")
            return None
        if not self.token:
            logging.warning(
                f"No token found. Redirecting to login page from: {self.router.page.path}"
            )
            return rx.redirect("/")
        logging.info(
            f"User is authenticated on {self.router.page.path}, fetching records."
        )
        from .dashboard import DashboardState

        return DashboardState.fetch_records

    @rx.event
    def logout(self):
        """Logs the user out and redirects to the login page."""
        self.email = ""
        self.password = ""
        self.is_signup = False
        self.token = ""
        yield rx.remove_cookie("sb-localhost-auth-token")
        return rx.redirect("/")