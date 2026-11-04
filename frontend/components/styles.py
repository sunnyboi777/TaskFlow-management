import streamlit as st  # type: ignore[import-not-found]


def load_styles():
    # =========================================================
    # CUSTOM CSS
    # =========================================================

    st.markdown(
        """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        html {
            color-scheme: light;
        }

        .stApp {
            background: linear-gradient(
                135deg,
                #f5f7ff 0%,
                #eef2ff 50%,
                #f8faff 100%
            );
            color: #1f2937;
        }

        div[data-testid="stAppViewContainer"],
        div[data-testid="stAppViewContainer"] label,
        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2,
        div[data-testid="stAppViewContainer"] h3,
        div[data-testid="stAppViewContainer"] p {
            color: #1f2937;
        }

        div[data-testid="stAppViewContainer"] input,
        div[data-testid="stAppViewContainer"] textarea {
            color: #1f2937;
            background-color: #ffffff;
        }

        div[data-testid="stSidebar"],
        div[data-testid="stSidebar"] * {
            color: #1f2937;
        }

        div[data-testid="stSidebar"] {
            background: #ffffff;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            background: linear-gradient(
                120deg,
                #312e81 0%,
                #4f46e5 55%,
                #7c3aed 100%
            );
            padding: 35px;
            border-radius: 24px;
            color: white;
            margin-bottom: 28px;
            box-shadow: 0 12px 35px rgba(79, 70, 229, 0.20);
        }

        .hero h1 {
            font-size: 38px;
            font-weight: 800;
            color: white;
            margin: 0 0 10px 0;
            letter-spacing: -1px;
        }

        .hero p {
            color: #e0e7ff;
            font-size: 15px;
            margin-bottom: 0;
        }

        .hero,
        .hero h1,
        .hero p,
        .hero .hero-badge {
            color: white;
        }

        div[data-testid="stAppViewContainer"] .hero h1,
        div[data-testid="stAppViewContainer"] .hero p,
        div[data-testid="stAppViewContainer"] .hero .hero-badge {
            color: white;
        }

        .hero-badge {
            display: inline-block;
            padding: 7px 13px;
            border-radius: 30px;
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.20);
            font-size: 12px;
            margin-bottom: 15px;
        }

        .section-title {
            color: #1e1b4b;
            font-size: 23px;
            font-weight: 800;
            margin-top: 12px;
            margin-bottom: 18px;
        }

        .metric-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 22px;
            min-height: 135px;
            box-shadow: 0 5px 18px rgba(31, 41, 55, 0.04);
        }

        .metric-icon {
            font-size: 25px;
            margin-bottom: 12px;
        }

        .metric-label {
            color: #6b7280;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #111827;
            font-size: 32px;
            font-weight: 800;
        }

        .task-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 12px;
            box-shadow: 0 5px 18px rgba(31, 41, 55, 0.035);
        }

        .task-title {
            font-size: 17px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 8px;
            overflow-wrap: anywhere;
        }

        .task-description {
            color: #6b7280;
            font-size: 14px;
            line-height: 1.7;
            overflow-wrap: anywhere;
        }

        .status-done {
            display: inline-block;
            background: #dcfce7;
            color: #166534;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }

        .status-open {
            display: inline-block;
            background: #fef3c7;
            color: #92400e;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }

        .panel {
            background: white;
            padding: 24px;
            border-radius: 20px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 5px 18px rgba(31, 41, 55, 0.04);
            margin-bottom: 20px;
        }

        .small-muted {
            color: #6b7280;
            font-size: 13px;
        }

        div.stButton > button {
            border-radius: 10px;
            font-weight: 600;
            min-height: 42px;
            transition: all 0.2s ease;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(120deg, #4f46e5, #7c3aed);
            border: none;
            color: white;
        }

        div.stButton > button:hover {
            border-color: #818cf8;
            transform: translateY(-1px);
        }

        div[data-testid="stForm"] {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 20px;
        }

        div[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e5e7eb;
        }

        .footer {
            text-align: center;
            color: #9ca3af;
            font-size: 12px;
            padding-top: 35px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
