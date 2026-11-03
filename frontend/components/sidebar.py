import importlib

st = importlib.import_module("streamlit")
from frontend.services.api import api_request, show_api_error


def render_sidebar():
    # =========================================================

    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 25px 0;">
                <div style="font-size: 30px;">✅</div>
                <div style="
                    font-size: 23px;
                    font-weight: 800;
                    color: #312e81;
                ">
                    TaskFlow
                </div>
                <div style="color: #9ca3af; font-size: 12px;">
                    YOUR PRODUCTIVITY SPACE
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Navigation")

        page = st.radio(
            "Navigate",
            [
                "📊 Dashboard",
                "➕ Create Task",
                "📋 All Tasks",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        st.markdown("### System Status")

        if st.button("🔌 Check Backend", use_container_width=True):
            try:
                health = api_request("GET", "/")
                health.raise_for_status()
                st.success("FastAPI is online!")
            except Exception as exc:
                show_api_error(exc)

    return page
