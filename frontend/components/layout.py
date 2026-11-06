import streamlit as st  # type: ignore[reportMissingImports]


def render_app_toolbar(theme):
    """Render the application wordmark above the page content."""

    st.markdown(
        """
        <div class="app-toolbar-brand">
            <span>
                <strong>TaskFlow</strong>
                <small>Productivity workspace</small>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
