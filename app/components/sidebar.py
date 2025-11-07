import reflex as rx
from app.states.dashboard import DashboardState, NavItem


def nav_item(item: NavItem) -> rx.Component:
    """Renders a single navigation item in the sidebar."""
    return rx.el.a(
        rx.icon(item["icon"], class_name="h-5 w-5"),
        rx.el.span(item["label"]),
        href=item["href"],
        on_click=lambda: DashboardState.set_active_page(item["label"]),
        class_name=rx.cond(
            DashboardState.active_page == item["label"],
            "flex items-center gap-3 rounded-lg bg-gray-100 px-3 py-2 text-gray-900 transition-all hover:text-gray-900",
            "flex items-center gap-3 rounded-lg px-3 py-2 text-gray-500 transition-all hover:text-gray-900",
        ),
    )


def sidebar() -> rx.Component:
    """The sidebar component for the dashboard layout."""
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.icon("activity", class_name="h-6 w-6 text-blue-600"),
                    rx.el.span("ArogyaChain", class_name="font-bold"),
                    href="/dashboard",
                    class_name="flex items-center gap-2 font-semibold",
                ),
                class_name="flex h-[60px] items-center border-b px-6",
            ),
            rx.el.div(
                rx.el.nav(
                    rx.foreach(DashboardState.nav_items, nav_item),
                    class_name="flex flex-col gap-1 px-4 text-sm font-medium",
                ),
                class_name="flex-1 overflow-auto py-4",
            ),
            class_name="flex h-full flex-col",
        ),
        class_name="fixed inset-y-0 left-0 z-30 w-64 -translate-x-full border-r bg-white transition-transform lg:translate-x-0 lg:static",
        transform=rx.cond(DashboardState.is_mobile_menu_open, "translateX(0)", ""),
    )