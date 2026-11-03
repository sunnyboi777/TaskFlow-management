import streamlit as st  # type: ignore[import-not-found]
from frontend.services.api import update_task, delete_task, show_api_error


def render_all_tasks(tasks):
    st.markdown(
        '<div class="section-title">📋 Manage All Tasks</div>',
        unsafe_allow_html=True,
    )

    search_col, filter_col = st.columns([2, 1])

    with search_col:
        search = st.text_input(
            "🔍 Search tasks",
            placeholder="Search by title or description...",
        )

    with filter_col:
        status_filter = st.selectbox(
            "🔽 Filter tasks",
            [
                "All Tasks",
                "Pending",
                "Completed",
            ],
            key="all_tasks_status_filter",
            help="Show all tasks, pending tasks, or completed tasks.",
        )

    # Sort tasks by their actual database ID.
    # Display numbers are assigned separately from database IDs.
    filtered_tasks = sorted(
        tasks,
        key=lambda item: item["id"],
    )

    if search.strip():
        query = search.strip().casefold()

        filtered_tasks = [
            task for task in filtered_tasks
            if query in task["title"].casefold()
            or query in task["description"].casefold()
        ]

    if status_filter == "Pending":
        filtered_tasks = [
            task for task in filtered_tasks
            if not task["completed"]
        ]

    elif status_filter == "Completed":
        filtered_tasks = [
            task for task in filtered_tasks
            if task["completed"]
        ]

    st.caption(f"Showing {len(filtered_tasks)} task(s)")

    if not filtered_tasks:
        st.info("No matching tasks found.")

    # Assign sequential display numbers after sorting and filtering.
    for task_number, task in enumerate(filtered_tasks, start=1):

        task_id = task["id"]

        with st.container(border=True):

            title_col, status_col = st.columns([3, 1])

            with title_col:
                st.markdown(
                    f"### #{task_number} · {task['title']}"
                )

            with status_col:
                if task["completed"]:
                    st.success("✓ Completed")
                else:
                    st.warning("◷ Pending")

            st.write(
                task["description"] or "No description provided."
            )

            action1, action2, action3 = st.columns(3)

            # UPDATE COMPLETION STATUS

            with action1:

                button_label = (
                    "↩️ Reopen Task"
                    if task["completed"]
                    else "✅ Complete Task"
                )

                if st.button(
                    button_label,
                    key=f"toggle_{task_id}",
                    use_container_width=True,
                ):

                    try:
                        update_task(
                            task_id,
                            task["title"],
                            task["description"],
                            not task["completed"],
                        )

                        st.success("Task status updated!")
                        st.rerun()

                    except Exception as exc:
                        show_api_error(exc)

            # EDIT TASK

            with action2:

                if st.button(
                    "✏️ Edit Task",
                    key=f"edit_{task_id}",
                    use_container_width=True,
                ):
                    st.session_state[f"editing_{task_id}"] = (
                        not st.session_state.get(
                            f"editing_{task_id}",
                            False,
                        )
                    )

            # DELETE TASK

            with action3:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{task_id}",
                    use_container_width=True,
                ):
                    st.session_state[f"confirm_delete_{task_id}"] = True

            # EDIT FORM

            if st.session_state.get(f"editing_{task_id}", False):

                st.markdown("#### ✏️ Edit Task Details")

                with st.form(f"edit_form_{task_id}"):

                    edited_title = st.text_input(
                        "Title",
                        value=task["title"],
                        max_chars=200,
                        key=f"title_input_{task_id}",
                    )

                    edited_description = st.text_area(
                        "Description",
                        value=task["description"],
                        max_chars=2000,
                        key=f"description_input_{task_id}",
                    )

                    edited_completed = st.checkbox(
                        "Task completed",
                        value=task["completed"],
                        key=f"completed_input_{task_id}",
                    )

                    save_col, cancel_col = st.columns(2)

                    with save_col:
                        save = st.form_submit_button(
                            "💾 Save Changes",
                            type="primary",
                            use_container_width=True,
                        )

                    with cancel_col:
                        cancel = st.form_submit_button(
                            "Cancel",
                            use_container_width=True,
                        )

                    if save:

                        if not edited_title.strip():
                            st.warning("Title cannot be empty.")

                        else:
                            try:
                                update_task(
                                    task_id,
                                    edited_title.strip(),
                                    edited_description.strip(),
                                    edited_completed,
                                )

                                st.session_state[
                                    f"editing_{task_id}"
                                ] = False

                                st.success(
                                    f"Task #{task_id} updated successfully!"
                                )

                                st.rerun()

                            except Exception as exc:
                                show_api_error(exc)

                    if cancel:
                        st.session_state[
                            f"editing_{task_id}"
                        ] = False

                        st.rerun()

            # DELETE CONFIRMATION

            if st.session_state.get(
                f"confirm_delete_{task_id}",
                False,
            ):

                st.warning(
                    f"Are you sure you want to delete "
                    f"task #{task_id}?"
                )

                yes_col, no_col = st.columns(2)

                with yes_col:

                    if st.button(
                        "Yes, Delete",
                        key=f"confirm_yes_{task_id}",
                        type="primary",
                        use_container_width=True,
                    ):

                        try:
                            delete_task(task_id)

                            st.session_state[
                                f"confirm_delete_{task_id}"
                            ] = False

                            st.success(
                                f"Task #{task_id} deleted successfully!"
                            )

                            st.rerun()

                        except Exception as exc:
                            show_api_error(exc)

                with no_col:

                    if st.button(
                        "Cancel",
                        key=f"confirm_no_{task_id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"confirm_delete_{task_id}"
                        ] = False

                        st.rerun()
