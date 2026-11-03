
"""TaskFlow administrator dashboard and user management."""

import time

import streamlit as st

from frontend.services.api import (
    load_admin_users,
    update_user_status,
    update_user_role,
    update_users_status_bulk,
    delete_user,
    delete_all_inactive_users,
    show_api_error,
)


def _select_all_changed(user_ids):
    """Select or deselect all accounts except the current admin."""
    select_all = st.session_state.get("select_all_accounts", False)

    for user_id in user_ids:
        st.session_state[f"select_user_{user_id}"] = select_all


def _sync_select_all(user_ids):
    """Keep Select All synchronized with individual selections."""
    st.session_state["select_all_accounts"] = bool(user_ids) and all(
        st.session_state.get(f"select_user_{user_id}", False)
        for user_id in user_ids
    )


def _clear_admin_cache(cache_key):
    """Force the next dashboard run to reload users."""
    st.session_state.pop(cache_key, None)
    st.session_state.pop(f"{cache_key}_loaded_at", None)


def _reset_admin_widget_state(admin_id):
    """Schedule account-selection reset before widgets are instantiated."""
    st.session_state[f"reset_admin_widgets_{admin_id}"] = True


@st.fragment(run_every="5s")
def render_admin_dashboard():
    """Render administrator statistics and account management."""

    current_user = st.session_state.get("current_user", {})

    if current_user.get("role") != "admin":
        st.error("Administrator access required.")
        return

    admin_id = current_user.get("id")

    if admin_id is None:
        st.error("Unable to identify the administrator account.")
        return

    cache_key = f"admin_users_cache_{admin_id}"
    cache_loaded_at_key = f"{cache_key}_loaded_at"

    st.title("🛡️ Admin Dashboard")
    st.caption("Manage TaskFlow accounts, permissions and platform access.")

    cache_age = time.monotonic() - st.session_state.get(
        cache_loaded_at_key,
        0,
    )

    # Refresh periodically so accounts created in another session appear.
    if cache_key not in st.session_state or cache_age >= 5:
        try:
            with st.spinner("Loading accounts..."):
                st.session_state[cache_key] = load_admin_users()
                st.session_state[cache_loaded_at_key] = time.monotonic()
        except Exception as exc:
            show_api_error(exc)
            return

    users = st.session_state[cache_key]

    reset_widgets_key = f"reset_admin_widgets_{admin_id}"
    if st.session_state.pop(reset_widgets_key, False):
        st.session_state["select_all_accounts"] = False
        for user in users:
            st.session_state.pop(f"select_user_{user['id']}", None)

    total_users = len(users)
    active_users = sum(1 for user in users if user["is_active"])
    inactive_users = total_users - active_users
    admin_users = sum(1 for user in users if user["role"] == "admin")

    st.markdown("### Platform Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Accounts", total_users)
    col2.metric("Active Accounts", active_users)
    col3.metric("Inactive Accounts", inactive_users)
    col4.metric("Administrators", admin_users)

    st.divider()
    st.markdown("### Account Management")

    if not users:
        st.info("No registered accounts found.")
        return

    # The current administrator cannot be selected for deactivation.
    selectable_ids = [
        user["id"]
        for user in users
        if user["id"] != admin_id
    ]

    # Initialize selection state before rendering the widgets.
    for user_id in selectable_ids:
        st.session_state.setdefault(f"select_user_{user_id}", False)

    st.checkbox(
        "Select All Accounts",
        key="select_all_accounts",
        on_change=_select_all_changed,
        args=(selectable_ids,),
    )

    selected_ids = [
        user_id
        for user_id in selectable_ids
        if st.session_state.get(f"select_user_{user_id}", False)
    ]

    active_selected_ids = [
        user["id"]
        for user in users
        if user["id"] in selected_ids and user["is_active"]
    ]

    st.caption(
        f"{len(selected_ids)} account(s) selected · "
        f"{len(active_selected_ids)} active account(s) ready for deactivation"
    )

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button(
            "🔒 Deactivate Selected",
            disabled=not active_selected_ids,
            use_container_width=True,
        ):
            try:
                with st.spinner("Deactivating selected accounts..."):
                    result = update_users_status_bulk(
                        active_selected_ids,
                        False,
                    )

                _clear_admin_cache(cache_key)
                _reset_admin_widget_state(admin_id)
                st.success(
                    f"Successfully deactivated "
                    f"{result.get('updated_count', len(active_selected_ids))} "
                    f"account(s)."
                )
                st.rerun()

            except Exception as exc:
                show_api_error(exc)

    with action_col2:
        if st.button(
            "🗑️ Clear All Inactive Accounts",
            disabled=inactive_users == 0,
            use_container_width=True,
        ):
            try:
                with st.spinner("Removing inactive accounts..."):
                    result = delete_all_inactive_users()

                _clear_admin_cache(cache_key)
                _reset_admin_widget_state(admin_id)
                st.success(
                    f"Successfully deleted "
                    f"{result.get('deleted_count', 0)} inactive account(s)."
                )
                st.rerun()

            except Exception as exc:
                show_api_error(exc)

    if inactive_users:
        st.caption(
            "Clear All Inactive Accounts permanently deletes inactive "
            "accounts. Your own administrator account is protected. "
            "Tasks belonging to deleted accounts are preserved without an owner."
        )

    st.divider()

    # Search
    search = st.text_input(
        "Search Accounts",
        placeholder="Search by email address...",
    )

    filtered_users = [
        user
        for user in users
        if search.strip().lower() in user["email"].lower()
    ]

    st.caption(f"Showing {len(filtered_users)} account(s)")

    # Individual account management
    for user in filtered_users:
        user_id = user["id"]
        email = user["email"]
        role = user["role"]
        is_active = user["is_active"]
        is_current_admin = user_id == admin_id

        with st.container(border=True):
            header_col, status_col = st.columns([4, 1])

            with header_col:
                if is_current_admin:
                    st.markdown(f"**{email}**  ·  You")
                else:
                    st.markdown(f"**{email}**")

                st.caption(
                    f"User ID: {user_id} · "
                    f"Role: {role.upper()}"
                )

            with status_col:
                if is_active:
                    st.success("Active")
                else:
                    st.error("Inactive")

            # Individual selection
            if is_current_admin:
                st.caption("Your administrator account is protected.")
            else:
                st.checkbox(
                    "Select account",
                    key=f"select_user_{user_id}",
                    on_change=_sync_select_all,
                    args=(selectable_ids,),
                )

            # Individual account actions
            action1, action2 = st.columns(2)

            with action1:
                if not is_active and not is_current_admin:
                    if st.button(
                        "Activate Account",
                        key=f"activate_{user_id}",
                        use_container_width=True,
                    ):
                        try:
                            with st.spinner("Activating account..."):
                                update_user_status(user_id, True)

                            _clear_admin_cache(cache_key)
                            _reset_admin_widget_state(admin_id)
                            st.success("Account activated successfully.")
                            st.rerun()

                        except Exception as exc:
                            show_api_error(exc)

            with action2:
                if not is_current_admin:
                    if st.button(
                        "🗑️ Delete Account",
                        key=f"delete_{user_id}",
                        use_container_width=True,
                    ):
                        try:
                            with st.spinner("Deleting account..."):
                                delete_user(user_id)

                            _clear_admin_cache(cache_key)
                            _reset_admin_widget_state(admin_id)
                            st.success("Account deleted successfully.")
                            st.rerun()

                        except Exception as exc:
                            show_api_error(exc)

            # Role management
            if not is_current_admin:
                role_col1, role_col2 = st.columns([2, 1])

                with role_col1:
                    new_role = st.selectbox(
                        "Account Role",
                        options=["user", "admin"],
                        index=0 if role == "user" else 1,
                        key=f"role_{user_id}",
                    )

                with role_col2:
                    st.write("")
                    st.write("")

                    if st.button(
                        "Update Role",
                        key=f"update_role_{user_id}",
                        use_container_width=True,
                    ):
                        if new_role == role:
                            st.info("This role is already assigned.")
                        else:
                            try:
                                with st.spinner("Updating role..."):
                                    update_user_role(user_id, new_role)

                                _clear_admin_cache(cache_key)
                                _reset_admin_widget_state(admin_id)
                                st.success("Account role updated.")
                                st.rerun()

                            except Exception as exc:
                                show_api_error(exc)

    st.divider()

    if st.button("🔄 Refresh User List"):
        _clear_admin_cache(cache_key)
        st.rerun()
