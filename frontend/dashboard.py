
"""TaskFlow Streamlit entry point with role-based navigation."""

from importlib import import_module

try:
    st = import_module("streamlit")
except ModuleNotFoundError as exc:
    if exc.name == "streamlit":
        raise RuntimeError(
            "Streamlit is required to run TaskFlow. "
            "Install it with: pip install streamlit"
        ) from exc
    raise

from frontend.components.styles import load_styles
from frontend.components.layout import render_hero
from frontend.services.api import (
    api_request,
    show_api_error,
    load_tasks,
)
from frontend.pages.home import render_dashboard
from frontend.pages.create_task import render_create_task
from frontend.pages.all_tasks import render_all_tasks
from frontend.pages.auth import render_auth_page
from frontend.pages.admin import render_admin_dashboard


st.set_page_config(
    page_title="TaskFlow | Task Manager",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_styles()


# =========================================================
# AUTHENTICATION STATE
# =========================================================

def is_authenticated():
    """Check whether a user has a valid local login session."""

    return bool(
        st.session_state.get("authenticated")
        and st.session_state.get("access_token")
        and st.session_state.get("current_user")
    )


def logout():
    """Remove the current user's authentication session."""

    st.session_state.pop("access_token", None)
    st.session_state.pop("current_user", None)
    st.session_state.pop("authenticated", None)

    st.rerun()


# =========================================================
# DASHBOARD DATA
# =========================================================

def get_tasks_and_stats():
    """Fetch tasks and calculate dashboard statistics."""

    tasks = load_tasks()

    total_tasks = len(tasks)

    completed_tasks = sum(
        1 for task in tasks if task["completed"]
    )

    pending_tasks = total_tasks - completed_tasks

    completion_rate = (
        round(completed_tasks / total_tasks * 100)
        if total_tasks
        else 0
    )

    return (
        tasks,
        total_tasks,
        completed_tasks,
        pending_tasks,
        completion_rate,
    )


# =========================================================
# SIDEBAR
# =========================================================

def check_backend():
    """Display navigation and backend status."""

    with st.sidebar:

        st.markdown(
            """
            <div style="padding:10px 0 18px 0;">
                <div style="font-size:30px;">✅</div>
                <div style="font-size:23px;font-weight:800;color:#312e81;">
                    TaskFlow
                </div>
                <div style="color:#9ca3af;font-size:12px;">
                    YOUR PRODUCTIVITY SPACE
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_user = st.session_state.get(
            "current_user",
            {},
        )

        st.caption(
            f"Logged in: {current_user.get('email', '')}"
        )

        if current_user.get("role") == "admin":
            st.success("Administrator")

        else:
            st.info("Standard User")

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            logout()

        st.divider()

        st.markdown("### Navigation")

        st.page_link(
            dashboard_route,
            label="📊 Dashboard",
        )

        st.page_link(
            create_task_route,
            label="➕ Create Task",
        )

        st.page_link(
            all_tasks_route,
            label="📋 All Tasks",
        )

        if current_user.get("role") == "admin":
            st.page_link(
                admin_route,
                label="🛡️ Admin Dashboard",
            )

        st.divider()

        st.markdown("### System Status")

        if st.button(
            "🔌 Check Backend",
            use_container_width=True,
        ):
            try:
                response = api_request("GET", "/")
                response.raise_for_status()

                st.success("FastAPI is online!")

            except Exception as exc:
                show_api_error(exc)


# =========================================================
# APPLICATION PAGES
# =========================================================

def dashboard_page():

    try:
        tasks, total, completed, pending, rate = (
            get_tasks_and_stats()
        )

    except Exception as exc:
        show_api_error(exc)
        return

    render_hero()

    render_dashboard(
        tasks,
        total,
        completed,
        pending,
        rate,
    )


def create_task_page():
    render_create_task()


def all_tasks_page():

    try:
        tasks, *_ = get_tasks_and_stats()

    except Exception as exc:
        show_api_error(exc)
        return

    render_all_tasks(tasks)


def admin_page():
    render_admin_dashboard()


# =========================================================
# EXISTING URL ROUTES - PRESERVED
# =========================================================

dashboard_route = st.Page(
    dashboard_page,
    title="Dashboard",
    url_path="",
    default=True,
)

create_task_route = st.Page(
    create_task_page,
    title="Create Task",
    url_path="create-task",
)

all_tasks_route = st.Page(
    all_tasks_page,
    title="All Tasks",
    url_path="all-tasks",
)

admin_route = st.Page(
    admin_page,
    title="Admin Dashboard",
    url_path="admin",
)


# =========================================================
# APPLICATION NAVIGATION
# =========================================================

current_user = st.session_state.get("current_user", {})

pages = [
    dashboard_route,
    create_task_route,
    all_tasks_route,
]

if current_user.get("role") == "admin":
    pages.append(admin_route)


current_page = st.navigation(
    pages,
    position="hidden",
)


# =========================================================
# AUTHENTICATION GATE
# =========================================================

if not is_authenticated():

    render_auth_page()

else:

    check_backend()

    current_page.run()

    st.markdown(
        """
        <div class="footer">
            Built with ❤️ using Streamlit, FastAPI, SQLAlchemy & PostgreSQL
            <br><br>
            TaskFlow · Your productivity, simplified.
        </div>
        """,
        unsafe_allow_html=True,
    )
