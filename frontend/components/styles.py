import streamlit as st  # type: ignore[import-not-found]


def load_styles(theme="light"):
    dark_theme = theme == "dark"
    theme_variables = """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        :root {
            color-scheme: %s;
            --app-background: %s;
            --app-background-mid: %s;
            --surface: %s;
            --surface-raised: %s;
            --surface-border: %s;
            --text-primary: %s;
            --text-secondary: %s;
            --text-muted: %s;
            --heading: %s;
            --input-background: %s;
            --shadow: %s;
            --toolbar-icon-filter: %s;
        }
    """ % (
        "dark" if dark_theme else "light",
        "#111827" if dark_theme else "#f5f7ff",
        "#172554" if dark_theme else "#eef2ff",
        "#1f2937" if dark_theme else "#ffffff",
        "#273449" if dark_theme else "#ffffff",
        "#374151" if dark_theme else "#e5e7eb",
        "#f9fafb" if dark_theme else "#1f2937",
        "#d1d5db" if dark_theme else "#6b7280",
        "#9ca3af",
        "#c7d2fe" if dark_theme else "#1e1b4b",
        "#111827" if dark_theme else "#ffffff",
        "rgba(0, 0, 0, 0.25)" if dark_theme else "rgba(31, 41, 55, 0.04)",
        "brightness(0) invert(1)" if dark_theme else "none",
    )

    # =========================================================
    # CUSTOM CSS
    # =========================================================

    st.html(
        theme_variables
        + """
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        html, body {
            background: var(--app-background) !important;
        }

        .stApp {
            background: linear-gradient(
                135deg,
                var(--app-background) 0%,
                var(--app-background-mid) 50%,
                var(--app-background) 100%
            );
            color: var(--text-primary);
        }

        div[data-testid="stAppViewContainer"],
        div[data-testid="stAppViewContainer"] label,
        div[data-testid="stAppViewContainer"] h1,
        div[data-testid="stAppViewContainer"] h2,
        div[data-testid="stAppViewContainer"] h3,
        div[data-testid="stAppViewContainer"] p {
            color: var(--text-primary);
        }

        div[data-testid="stAppViewContainer"] > .main,
        div[data-testid="stAppViewContainer"] .main .block-container {
            background: transparent !important;
        }

        div[data-testid="stAppViewContainer"] input,
        div[data-testid="stAppViewContainer"] textarea,
        div[data-testid="stAppViewContainer"] [data-baseweb="select"] > div {
            color: var(--text-primary);
            background-color: var(--input-background) !important;
            border-color: var(--surface-border);
        }

        div[data-testid="stAppViewContainer"] input::placeholder,
        div[data-testid="stAppViewContainer"] textarea::placeholder {
            color: var(--text-muted);
            opacity: 1;
        }

        div[data-testid="stAppViewContainer"] [data-baseweb="select"] * {
            color: var(--text-primary);
        }

        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] * {
            color: var(--text-primary) !important;
        }

        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {
            background: var(--surface) !important;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] a,
        header[data-testid="stHeader"] [role="button"] {
            color: var(--text-primary) !important;
            opacity: 1 !important;
        }

        header[data-testid="stHeader"] button svg,
        header[data-testid="stHeader"] a svg,
        header[data-testid="stHeader"] [role="button"] svg {
            color: var(--text-primary) !important;
            filter: var(--toolbar-icon-filter);
            opacity: 1 !important;
        }

        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="stSidebarNavCollapse"] svg,
        [data-testid="stToolbar"] svg,
        [data-testid="stToolbar"] button svg,
        [data-testid="stToolbar"] a svg {
            filter: var(--toolbar-icon-filter) !important;
            opacity: 1 !important;
        }

        header[data-testid="stHeader"] button:hover,
        header[data-testid="stHeader"] a:hover,
        header[data-testid="stHeader"] [role="button"]:hover {
            color: #818cf8 !important;
            background: rgba(129, 140, 248, 0.14) !important;
        }

        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .app-toolbar-brand {
            display: flex;
            align-items: center;
            min-height: 46px;
            margin-bottom: 18px;
            color: var(--text-primary);
        }

        .app-toolbar-brand strong,
        .app-toolbar-brand small {
            display: block;
        }

        .app-toolbar-brand strong {
            color: var(--text-primary);
            font-size: 24px;
            font-weight: 800;
            line-height: 1.1;
        }

        .app-toolbar-brand small {
            margin-top: 3px;
            color: var(--text-secondary);
            font-size: 11px;
        }

        section[data-testid="stSidebar"] h3 {
            margin-top: 14px;
            color: var(--text-primary) !important;
            font-size: 14px;
            letter-spacing: 0.2px;
        }

        div.stButton > button[kind="secondary"] {
            min-height: 42px;
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            background: var(--surface-raised);
            color: var(--text-primary);
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

        .brand-name {
            color: #312e81;
        }

        .brand-tagline {
            color: #6b7280;
        }

        .auth-header {
            max-width: 680px;
            margin: 18px auto 28px;
            padding: 30px 28px 26px;
            text-align: center;
            border: 1px solid var(--surface-border);
            border-radius: 26px;
            background: linear-gradient(
                145deg,
                var(--surface-raised),
                var(--surface)
            );
            box-shadow: 0 18px 45px var(--shadow);
        }

        .auth-logo {
            width: 52px;
            height: 52px;
            margin: 0 auto 13px;
            display: grid;
            place-items: center;
            border-radius: 16px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            font-size: 30px;
            font-weight: 800;
            box-shadow: 0 10px 24px rgba(79, 70, 229, 0.30);
        }

        .auth-kicker {
            color: #818cf8;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
        }

        .auth-title {
            margin: 8px 0 8px;
            color: var(--text-primary) !important;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.8px;
        }

        .auth-subtitle {
            max-width: 500px;
            margin: 0 auto;
            color: var(--text-secondary) !important;
            font-size: 15px;
            line-height: 1.6;
        }

        .auth-form-title {
            margin: 4px 0 5px;
            color: var(--text-primary);
            font-size: 24px;
            font-weight: 800;
        }

        .auth-form-title + div p {
            color: var(--text-secondary) !important;
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
            color: white !important;
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
            color: var(--heading);
            font-size: 23px;
            font-weight: 800;
            margin-top: 12px;
            margin-bottom: 18px;
        }

        .metric-card {
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 18px;
            padding: 22px;
            min-height: 135px;
            box-shadow: 0 5px 18px var(--shadow);
        }

        .metric-icon {
            font-size: 25px;
            margin-bottom: 12px;
        }

        .metric-label {
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .metric-value {
            color: var(--text-primary);
            font-size: 32px;
            font-weight: 800;
        }

        .task-card {
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 12px;
            box-shadow: 0 5px 18px var(--shadow);
        }

        .task-title {
            font-size: 17px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            overflow-wrap: anywhere;
        }

        .task-description {
            color: var(--text-secondary);
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
            background: var(--surface);
            padding: 24px;
            border-radius: 20px;
            border: 1px solid var(--surface-border);
            box-shadow: 0 5px 18px var(--shadow);
            margin-bottom: 20px;
        }

        .panel h2,
        .panel h3,
        .panel h4,
        .panel p {
            color: var(--text-primary);
        }

        .small-muted {
            color: var(--text-secondary);
            font-size: 13px;
        }

        div.stButton > button {
            border-radius: 10px;
            font-weight: 600;
            min-height: 42px;
            transition: all 0.2s ease;
            border: 1px solid var(--surface-border);
            color: var(--text-primary);
            background: var(--surface-raised);
        }

        section[data-testid="stSidebar"] div.stButton > button {
            color: var(--text-primary) !important;
            background: var(--surface-raised) !important;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(120deg, #4f46e5, #7c3aed);
            border: none;
            color: white;
        }

        div.stButton > button[kind="primary"],
        section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            color: white !important;
        }

        div.stButton > button:hover {
            border-color: #818cf8;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.18);
        }

        div[data-testid="stForm"] {
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 14px 32px var(--shadow);
        }

        div[data-testid="stTabs"] {
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 22px;
            padding: 12px 18px 20px;
            box-shadow: 0 18px 45px var(--shadow);
        }

        div[data-testid="stTabs"] [role="tablist"] {
            gap: 8px;
            border-bottom: 1px solid var(--surface-border);
        }

        div[data-testid="stTabs"] button[role="tab"] {
            min-height: 42px;
            border-radius: 10px 10px 0 0;
            color: var(--text-secondary);
            font-weight: 700;
        }

        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #818cf8 !important;
        }

        div[data-testid="stForm"] label {
            color: var(--text-primary) !important;
            font-weight: 600;
        }

        div[data-testid="stForm"] input {
            min-height: 44px;
            border-radius: 10px;
        }

        div[data-testid="stForm"] button {
            color: var(--text-primary) !important;
        }

        div[data-testid="stForm"] button[kind="primary"],
        div[data-testid="stForm"] button[type="submit"] {
            min-height: 46px;
            border: 0 !important;
            border-radius: 11px;
            background: linear-gradient(120deg, #4f46e5, #7c3aed) !important;
            color: #ffffff !important;
            font-size: 15px;
            font-weight: 800;
            box-shadow: 0 8px 18px rgba(79, 70, 229, 0.28);
        }

        div[data-testid="stForm"] button[type="submit"]:hover {
            background: linear-gradient(120deg, #4338ca, #6d28d9) !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }

        div[data-testid="stForm"] button[aria-label*="password"],
        div[data-testid="stForm"] button[title*="password"],
        div[data-testid="stForm"] button[aria-label*="Show"],
        div[data-testid="stForm"] button[aria-label*="Hide"] {
            min-height: 32px;
            border: 0 !important;
            background: transparent !important;
            color: var(--text-secondary) !important;
            box-shadow: none !important;
            transform: none !important;
        }

        div[data-testid="stForm"] button[aria-label*="password"] svg,
        div[data-testid="stForm"] button[title*="password"] svg,
        div[data-testid="stForm"] button[aria-label*="Show"] svg,
        div[data-testid="stForm"] button[aria-label*="Hide"] svg {
            stroke: var(--text-primary) !important;
            fill: none !important;
            opacity: 1 !important;
        }

        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {
            background: var(--surface);
            border-right: 1px solid var(--surface-border);
        }

        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: var(--text-secondary) !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] a,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: var(--text-primary) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stAlert"] * {
            color: var(--text-primary) !important;
        }

        div[data-testid="stAlert"] {
            border: 1px solid var(--surface-border);
        }

        div[data-testid="stTabs"] button {
            color: var(--text-secondary);
        }

        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #818cf8;
        }

        .footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
            padding-top: 35px;
        }

        [style*="#1f2937"] {
            color: var(--text-primary) !important;
        }

        [style*="#4b5563"],
        [style*="#6b7280"],
        [style*="#9ca3af"] {
            color: var(--text-secondary) !important;
        }

        [style*="#312e81"] {
            color: var(--heading) !important;
        }
        </style>
        """,
    )
