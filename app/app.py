import reflex as rx
from app.states.state import AuthState
from app.states.dashboard import DashboardState
from app.states.upload import UploadState


def login_input(
    placeholder: str, type: str, icon: str, on_change: rx.event.EventHandler
) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-5 w-5 text-gray-400"),
        rx.el.input(
            placeholder=placeholder,
            type=type,
            on_change=on_change,
            class_name="flex-1 bg-transparent outline-none text-gray-800 placeholder-gray-400",
        ),
        class_name="flex items-center w-full gap-3 px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all",
    )


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.icon("activity", class_name="h-8 w-8 text-blue-600"),
                rx.el.h1("ArogyaChain", class_name="text-2xl font-bold text-gray-900"),
                class_name="flex items-center gap-2 mb-8",
            ),
            rx.el.div(
                rx.el.h2(
                    rx.cond(AuthState.is_signup, "Create an Account", "Welcome Back"),
                    class_name="text-3xl font-bold text-gray-900 mb-2",
                ),
                rx.el.p(
                    rx.cond(
                        AuthState.is_signup,
                        "Create an account to get started.",
                        "Enter your credentials to access your account.",
                    ),
                    class_name="text-gray-600 font-medium mb-8",
                ),
                rx.el.div(
                    login_input("Email Address", "email", "mail", AuthState.set_email),
                    login_input("Password", "password", "lock", AuthState.set_password),
                    rx.cond(
                        AuthState.is_signup,
                        rx.el.div(
                            rx.el.label(
                                "I am a:", class_name="font-medium text-gray-700"
                            ),
                            rx.el.select(
                                rx.el.option("Patient", value="patient"),
                                rx.el.option("Doctor", value="doctor"),
                                value=AuthState.selected_role,
                                on_change=AuthState.set_selected_role,
                                class_name="w-full px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all",
                            ),
                            class_name="flex flex-col gap-2 text-left w-full",
                        ),
                        None,
                    ),
                    rx.el.button(
                        rx.cond(
                            AuthState.is_loading,
                            rx.el.p(
                                rx.cond(
                                    AuthState.is_signup,
                                    "Signing up...",
                                    "Logging in...",
                                )
                            ),
                            rx.el.p(
                                rx.cond(AuthState.is_signup, "Create Account", "Login")
                            ),
                        ),
                        on_click=AuthState.on_submit,
                        disabled=AuthState.is_loading,
                        class_name="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50",
                    ),
                    class_name="flex flex-col gap-4",
                ),
                rx.cond(
                    AuthState.error_message != "",
                    rx.el.div(
                        rx.icon(
                            "flag_triangle_right", class_name="h-5 w-5 text-red-600"
                        ),
                        rx.el.p(
                            AuthState.error_message,
                            class_name="text-red-600 font-medium text-sm",
                        ),
                        class_name="flex items-center gap-2 p-3 mt-4 bg-red-50 border border-red-200 rounded-lg text-left",
                    ),
                ),
                rx.el.div(
                    rx.el.p(
                        rx.cond(
                            AuthState.is_signup,
                            "Already have an account?",
                            "Don't have an account?",
                        ),
                        class_name="text-sm text-gray-600",
                    ),
                    rx.el.button(
                        rx.cond(AuthState.is_signup, "Log In", "Sign Up"),
                        on_click=AuthState.toggle_mode,
                        class_name="text-sm font-semibold text-blue-600 hover:underline",
                    ),
                    class_name="mt-6 flex items-center justify-center gap-2",
                ),
                class_name="w-full max-w-md",
            ),
            class_name="flex flex-col items-center justify-center min-h-screen p-4 text-center bg-white",
        ),
        class_name="font-['Inter'] bg-white",
    )


from app.components.sidebar import sidebar


def dashboard_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.p("Welcome,", class_name="text-sm text-gray-500"),
                rx.el.h1(
                    AuthState.email, class_name="text-lg font-semibold text-gray-800"
                ),
                class_name="flex flex-col",
            ),
            class_name="flex items-center gap-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    AuthState.selected_role.capitalize(),
                    class_name="text-sm font-medium",
                ),
                class_name=rx.cond(
                    AuthState.selected_role == "doctor",
                    "px-3 py-1 text-blue-800 bg-blue-100 rounded-full w-fit",
                    "px-3 py-1 text-green-800 bg-green-100 rounded-full w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("log-out", class_name="h-4 w-4 mr-2"),
                "Logout",
                on_click=AuthState.logout,
                class_name="flex items-center text-sm font-medium text-gray-600 hover:text-red-600 transition-colors",
            ),
            class_name="flex items-center gap-4",
        ),
        class_name="flex items-center justify-between p-4 border-b bg-white",
    )


def stat_card(icon: str, title: str, value: str, color_class: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-6 w-6"),
            class_name=f"p-3 rounded-full {color_class}",
        ),
        rx.el.div(
            rx.el.p(title, class_name="text-sm font-medium text-gray-500"),
            rx.el.p(value, class_name="text-2xl font-bold text-gray-900"),
            class_name="flex flex-col",
        ),
        class_name="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg shadow-sm",
    )


def dashboard() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            dashboard_header(),
            rx.el.main(
                rx.el.h2(
                    "Analytics Overview",
                    class_name="text-2xl font-bold mb-6 text-gray-900",
                ),
                rx.el.div(
                    stat_card(
                        "file-text", "Total Records", "0", "bg-blue-100 text-blue-600"
                    ),
                    stat_card(
                        "shield-check",
                        "Verified Records",
                        "0",
                        "bg-green-100 text-green-600",
                    ),
                    stat_card(
                        "clock",
                        "Pending Verification",
                        "0",
                        "bg-yellow-100 text-yellow-600",
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8",
                ),
                rx.el.div(
                    rx.el.h3(
                        "Recent Activity",
                        class_name="text-xl font-semibold mb-4 text-gray-800",
                    ),
                    rx.el.div(
                        rx.el.p("No recent activity.", class_name="text-gray-500"),
                        class_name="p-6 text-center bg-white border border-gray-200 rounded-lg shadow-sm",
                    ),
                    class_name="mt-8",
                ),
                class_name="flex-1 p-6",
            ),
            class_name="flex flex-col flex-1 h-screen overflow-y-auto",
        ),
        class_name="flex min-h-screen w-full bg-gray-50/90 font-['Inter']",
    )


from app.states.dashboard import Record
from app.states.upload import UploadState


def record_card(record: Record) -> rx.Component:
    return rx.el.div(
        rx.el.a(
            rx.image(
                src=record.get("qr_url", "/placeholder.svg"),
                class_name="w-full h-40 object-cover rounded-t-lg",
            ),
            href=f"/verify/{record['id']}",
            class_name="block",
        ),
        rx.el.div(
            rx.el.a(
                rx.el.h3(
                    record["title"],
                    class_name="font-semibold text-gray-800 hover:underline",
                ),
                href=record.get("file_url", "#"),
                is_external=True,
            ),
            rx.el.p(
                f"Created: {record['created_at'][:10]}",
                class_name="text-sm text-gray-500 mt-1",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-4 w-4"),
                rx.el.p(record["notarization_status"].capitalize()),
                class_name=rx.cond(
                    record["notarization_status"] == "success",
                    "flex items-center gap-1 text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full w-fit mt-3",
                    "flex items-center gap-1 text-xs font-medium text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full w-fit mt-3",
                ),
            ),
            class_name="p-4",
        ),
        class_name="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow",
    )


def records() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            dashboard_header(),
            rx.el.main(
                rx.el.h2(
                    "My Medical Records",
                    class_name="text-2xl font-bold mb-6 text-gray-900",
                ),
                rx.cond(
                    DashboardState.is_loading,
                    rx.el.div(
                        rx.el.div(
                            class_name="h-8 w-8 border-t-2 border-blue-600 rounded-full animate-spin"
                        ),
                        class_name="flex justify-center items-center p-12",
                    ),
                    rx.cond(
                        DashboardState.records,
                        rx.el.div(
                            rx.foreach(DashboardState.records, record_card),
                            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                        ),
                        rx.el.div(
                            rx.icon("file-x-2", class_name="h-12 w-12 text-gray-400"),
                            rx.el.p(
                                "No medical records found.",
                                class_name="mt-4 text-gray-600 font-medium",
                            ),
                            class_name="flex flex-col items-center justify-center p-12 bg-white border border-dashed border-gray-300 rounded-lg",
                        ),
                    ),
                ),
                class_name="flex-1 p-6",
            ),
            class_name="flex flex-col flex-1 h-screen overflow-y-auto",
        ),
        class_name="flex min-h-screen w-full bg-gray-50/90 font-['Inter']",
    )


def upload() -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            dashboard_header(),
            rx.el.main(
                rx.el.div(
                    rx.el.h2(
                        "Upload New Record",
                        class_name="text-2xl font-bold text-gray-900",
                    ),
                    rx.el.p(
                        "Fill in the details below to add a new medical record for a patient.",
                        class_name="text-gray-500 mt-1",
                    ),
                    class_name="mb-6",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.label(
                                "Patient Email",
                                class_name="text-sm font-medium text-gray-700 mb-1",
                            ),
                            rx.el.input(
                                placeholder="Enter patient's email address",
                                on_change=UploadState.set_patient_email,
                                class_name="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        rx.el.div(
                            rx.el.label(
                                "Record Title",
                                class_name="text-sm font-medium text-gray-700 mb-1",
                            ),
                            rx.el.input(
                                placeholder="e.g., Annual Check-up Results",
                                on_change=UploadState.set_record_title,
                                class_name="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            ),
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Notes (Optional)",
                            class_name="text-sm font-medium text-gray-700 mb-1",
                        ),
                        rx.el.textarea(
                            placeholder="Add any relevant notes here...",
                            on_change=UploadState.set_notes,
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                            rows=4,
                        ),
                        class_name="mt-6",
                    ),
                    rx.upload.root(
                        rx.el.div(
                            rx.icon(
                                "cloud-upload",
                                class_name="h-10 w-10 text-gray-400 mx-auto",
                            ),
                            rx.el.p(
                                "Click to upload or drag and drop",
                                class_name="mt-2 text-sm font-medium text-gray-600",
                            ),
                            rx.el.p(
                                "PDF, PNG, JPG (max. 10MB)",
                                class_name="text-xs text-gray-500",
                            ),
                            border="2px dashed #d1d5db",
                            class_name="w-full mt-6 flex flex-col items-center justify-center p-6 rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors",
                        ),
                        id="upload1",
                        multiple=False,
                        accept={
                            "application/pdf": [".pdf"],
                            "image/png": [".png"],
                            "image/jpeg": [".jpg", ".jpeg"],
                        },
                    ),
                    rx.el.div(
                        rx.foreach(
                            rx.selected_files("upload1"),
                            lambda file: rx.el.div(
                                rx.el.p(file, class_name="font-medium"),
                                class_name="flex items-center justify-between p-2 mt-2 bg-gray-100 border rounded-md",
                            ),
                        ),
                        rx.cond(
                            UploadState.upload_error != "",
                            rx.el.div(
                                rx.el.p(
                                    UploadState.upload_error,
                                    class_name="text-red-600 text-sm",
                                ),
                                class_name="mt-2 p-2 bg-red-50 border border-red-200 rounded-md",
                            ),
                        ),
                        class_name="mt-4 w-full",
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("upload", class_name="h-4 w-4 mr-2"),
                            "Select File",
                            on_click=UploadState.handle_upload(
                                rx.upload_files(upload_id="upload1")
                            ),
                            class_name="flex items-center justify-center px-4 py-2 border border-transparent font-medium rounded-md shadow-sm text-white bg-gray-600 hover:bg-gray-700 disabled:opacity-50",
                        ),
                        rx.el.button(
                            rx.icon("check", class_name="h-4 w-4 mr-2"),
                            "Submit Record",
                            on_click=UploadState.submit_record,
                            disabled=UploadState.is_uploading,
                            class_name="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50",
                        ),
                        class_name="flex justify-end gap-4 mt-6",
                    ),
                    class_name="p-8 bg-white border border-gray-200 rounded-lg shadow-sm",
                ),
                class_name="flex-1 p-6",
            ),
            class_name="flex flex-col flex-1 h-screen overflow-y-auto",
        ),
        class_name="flex min-h-screen w-full bg-gray-50/90 font-['Inter']",
    )


from app.api import api as fastapi_app

app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
    api_transformer=fastapi_app,
)
from app.states.verify import VerifyState


def verification_result_display() -> rx.Component:
    return rx.cond(
        VerifyState.verification_result,
        rx.el.div(
            rx.el.h3(
                "Verification Result",
                class_name="text-xl font-semibold text-gray-800 mb-4",
            ),
            rx.el.div(
                rx.cond(
                    VerifyState.verification_result["verification"]["is_verified"],
                    rx.el.div(
                        rx.icon("shield-check", class_name="h-6 w-6 text-green-600"),
                        rx.el.p(
                            "Record Verified", class_name="font-semibold text-green-700"
                        ),
                        class_name="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg",
                    ),
                    rx.el.div(
                        rx.icon("shield-alert", class_name="h-6 w-6 text-red-600"),
                        rx.el.p(
                            "Verification Failed",
                            class_name="font-semibold text-red-700",
                        ),
                        class_name="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg",
                    ),
                ),
                rx.el.div(
                    rx.el.h4(
                        "Record Details", class_name="font-medium text-gray-600 mb-2"
                    ),
                    rx.el.p(
                        f"Title: {VerifyState.verification_result['record']['title']}"
                    ),
                    rx.el.p(
                        f"Created: {VerifyState.verification_result['record']['created_at']}"
                    ),
                    rx.el.h4(
                        "Blockchain Details",
                        class_name="font-medium text-gray-600 mt-4 mb-2",
                    ),
                    rx.el.p(
                        f"Tx Hash: {VerifyState.verification_result['record']['tx_hash']}"
                    ),
                    class_name="text-sm text-gray-700 space-y-1 p-4 border rounded-lg mt-4 bg-gray-50",
                ),
                class_name="space-y-4",
            ),
            class_name="mt-8 w-full p-8 bg-white border border-gray-200 rounded-lg shadow-sm",
        ),
        None,
    )


def public_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.a(
                rx.icon("activity", class_name="h-8 w-8 text-blue-600"),
                rx.el.h1("ArogyaChain", class_name="text-2xl font-bold text-gray-900"),
                href="/",
                class_name="flex items-center gap-2",
            ),
            class_name="container mx-auto flex items-center justify-between p-4",
        ),
        class_name="w-full bg-white border-b",
    )


def verify() -> rx.Component:
    return rx.el.div(
        public_header(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Verify Medical Record",
                        class_name="text-3xl font-bold text-gray-900",
                    ),
                    rx.el.p(
                        "Check the authenticity of a record by entering its unique ID.",
                        class_name="text-gray-500 mt-2",
                    ),
                    class_name="text-center",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.label(
                            "Record ID",
                            class_name="text-sm font-medium text-gray-700 mb-1 text-left",
                        ),
                        rx.el.input(
                            placeholder="Enter the record ID to verify...",
                            default_value=VerifyState.record_id_input,
                            on_change=VerifyState.set_record_id_input,
                            class_name="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500",
                        ),
                        class_name="flex flex-col",
                    ),
                    rx.el.button(
                        rx.icon("shield-check", class_name="h-5 w-5 mr-2"),
                        "Verify Record",
                        on_click=VerifyState.verify_record,
                        disabled=VerifyState.is_verifying,
                        class_name="mt-6 w-full flex items-center justify-center px-4 py-3 border border-transparent font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors",
                    ),
                    rx.cond(
                        VerifyState.is_verifying,
                        rx.el.div(
                            class_name="h-6 w-6 border-t-2 border-blue-600 rounded-full animate-spin mx-auto mt-4"
                        ),
                    ),
                    rx.cond(
                        VerifyState.error_message != "",
                        rx.el.div(
                            rx.el.p(
                                VerifyState.error_message,
                                class_name="text-sm font-medium text-red-600",
                            ),
                            class_name="mt-4 text-center p-3 bg-red-50 border border-red-200 rounded-lg",
                        ),
                    ),
                    verification_result_display(),
                    class_name="p-8 bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-2xl mx-auto mt-8",
                ),
                class_name="flex-1 p-6 container mx-auto",
            )
        ),
        class_name="min-h-screen w-full bg-gray-50 font-['Inter']",
    )


app.add_page(index)
app.add_page(dashboard, route="/dashboard", on_load=AuthState.on_load)
app.add_page(records, route="/records", on_load=DashboardState.fetch_records)
app.add_page(upload, route="/upload", on_load=AuthState.on_load)
app.add_page(verify, route="/verify/[[...splat]]", on_load=VerifyState.on_load)