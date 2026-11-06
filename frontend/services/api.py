
import os

import requests
import streamlit as st


HTTP_SESSION = requests.Session()


# =========================================================
# API CONFIGURATION
# =========================================================

def get_api_url():
    """Get the backend URL from cloud secrets or local environment."""

    api_url = None
    try:
        api_url = st.secrets["API_URL"]
    except (KeyError, FileNotFoundError):
        api_url = os.getenv("API_URL")

    return (api_url or "http://127.0.0.1:8000").rstrip("/")


API_URL = get_api_url()


# =========================================================
# API REQUEST HELPER
# =========================================================

def api_request(method, path, **kwargs):
    """Send API requests with the logged-in user's JWT token."""

    headers = dict(kwargs.pop("headers", {}) or {})

    token = st.session_state.get("access_token")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return HTTP_SESSION.request(
        method,
        f"{API_URL}{path}",
        headers=headers,
        timeout=10,
        **kwargs,
    )


# =========================================================
# AUTHENTICATION
# =========================================================

def register_user(email, password):
    """Register a new TaskFlow account."""

    response = api_request(
        "POST",
        "/auth/register",
        json={
            "email": email.strip(),
            "password": password,
        },
    )

    response.raise_for_status()
    return response.json()


def login_user(email, password):
    """Authenticate a user and return the login response."""

    response = api_request(
        "POST",
        "/auth/login",
        json={
            "email": email.strip(),
            "password": password,
        },
    )

    response.raise_for_status()
    return response.json()


# =========================================================
# ERROR HANDLING
# =========================================================

def show_api_error(exc):
    """Display friendly messages without exposing technical errors."""

    if isinstance(exc, requests.ConnectionError):
        st.error(
            "Unable to connect right now. "
            "Please try again later."
        )

    elif isinstance(exc, requests.Timeout):
        st.warning(
            "The request is taking too long. "
            "Please try again."
        )

    elif isinstance(exc, requests.HTTPError):

        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        if status_code == 401:
            st.warning(
                "Your session has expired. "
                "Please log in again."
            )

        elif status_code == 403:
            st.error(
                "You do not have permission to perform this action."
            )

        elif status_code == 404:
            st.warning(
                "The requested information could not be found."
            )

        elif status_code == 409:
            st.warning(
                "An account with this email already exists. "
                "Please try logging in."
            )

        elif status_code == 422:
            st.warning(
                "Please check the information you entered "
                "and try again."
            )

        else:
            st.error(
                "Something went wrong. "
                "Please try again later."
            )

    else:
        st.error(
            "Something went wrong. "
            "Please try again later."
        )


# =========================================================
# TASK OPERATIONS
# =========================================================

def load_tasks():
    """Fetch only the logged-in user's tasks."""

    response = api_request("GET", "/tasks")
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            "Expected a list of tasks from the API."
        )

    return data


def create_task(title, description):
    """Create a task for the logged-in user."""

    response = api_request(
        "POST",
        "/tasks",
        json={
            "title": title,
            "description": description,
        },
    )

    response.raise_for_status()
    return response.json()


def update_task(task_id, title, description, completed):
    """Update a task belonging to the logged-in user."""

    response = api_request(
        "PUT",
        f"/tasks/{task_id}",
        json={
            "title": title,
            "description": description,
            "completed": completed,
        },
    )

    response.raise_for_status()
    return response.json()


def delete_task(task_id):
    """Delete a task belonging to the logged-in user."""

    response = api_request(
        "DELETE",
        f"/tasks/{task_id}",
    )

    response.raise_for_status()
    return response.status_code == 204


# =========================================================
# ADMIN OPERATIONS
# =========================================================

def load_admin_users():
    """Fetch all registered users. Requires administrator access."""

    response = api_request(
        "GET",
        "/admin/users",
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            "Expected a list of users from the API."
        )

    return data


def update_user_status(user_id, is_active):
    """Activate or deactivate a user account."""

    response = api_request(
        "PATCH",
        f"/admin/users/{user_id}/status",
        json={
            "is_active": is_active,
        },
    )

    response.raise_for_status()
    return response.json()


def update_user_role(user_id, role):
    """Change a user's role. Requires administrator access."""

    if role not in ("admin", "user"):
        raise ValueError("Invalid user role.")

    response = api_request(
        "PATCH",
        f"/admin/users/{user_id}/role",
        json={
            "role": role,
        },
    )

    response.raise_for_status()
    return response.json()


def delete_user(user_id):
    """Permanently delete a user account. Requires administrator access."""

    response = api_request(
        "DELETE",
        f"/admin/users/{user_id}",
    )

    response.raise_for_status()
    return response.json()


def update_users_status_bulk(user_ids, is_active):
    """Activate or deactivate multiple accounts in one request."""

    if not user_ids:
        raise ValueError("Select at least one account.")

    response = api_request(
        "PATCH",
        "/admin/users/bulk-status",
        json={
            "user_ids": list(user_ids),
            "is_active": is_active,
        },
    )

    response.raise_for_status()
    return response.json()


def delete_all_inactive_users():
    """Permanently delete all inactive accounts."""

    response = api_request(
        "DELETE",
        "/admin/users/inactive",
    )

    response.raise_for_status()
    return response.json()
