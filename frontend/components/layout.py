import streamlit as st  # type: ignore[reportMissingImports]


def render_app_toolbar(theme):
    """Render theme controls inside the application content area."""

    left, right = st.columns([3, 1])

    with left:
        st.markdown(
            """
            <div class="app-toolbar-brand">
                <span class="app-toolbar-mark">✓</span>
                <span>
                    <strong>TaskFlow</strong>
                    <small>Productivity workspace</small>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        label = "☀️ Light mode" if theme == "dark" else "🌙 Dark mode"
        if st.button(
            label,
            key="app_toolbar_theme_toggle",
            use_container_width=True,
        ):
            selected_theme = "light" if theme == "dark" else "dark"
            st.session_state["theme"] = selected_theme
            st.query_params["theme"] = selected_theme
            st.rerun()


def render_hero():
    # =========================================================

    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">✦ YOUR PERSONAL WORKSPACE</div>
            <h1>Manage your tasks.<br>Make things happen.</h1>
            <p>
                Organize your work, track your progress, and stay productive
                with your personal task management dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
