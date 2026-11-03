import importlib

st = importlib.import_module("streamlit")
from frontend.services.api import create_task, show_api_error


def render_create_task():
    st.markdown(
        '<div class="section-title">✨ Create a New Task</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="color:#6b7280; margin-bottom:20px;">
            Add a task to your workspace and keep your work organized.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("create_task_form", clear_on_submit=True):

        title = st.text_input(
            "Task Title *",
            placeholder="e.g. Complete my Python project",
            max_chars=200,
        )

        description = st.text_area(
            "Description",
            placeholder="Add more details about your task...",
            max_chars=2000,
            height=150,
        )

        submitted = st.form_submit_button(
            "➕ Create Task",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not title.strip():
                st.warning("Please enter a task title.")

            else:
                try:
                    result = create_task(
                        title.strip(),
                        description.strip(),
                    )

                    st.success(
                        f"Task #{result['id']} created successfully!"
                    )

                    st.rerun()

                except Exception as exc:
                    show_api_error(exc)
