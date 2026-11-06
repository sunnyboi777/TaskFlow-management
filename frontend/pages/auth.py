
import requests
import streamlit as st

from frontend.services.api import (
    login_user,
    register_user,
)


def render_auth_page():
    """Display TaskFlow Login and Sign Up screens."""

    theme = st.session_state.get("theme", "light")
    if st.button(
        "☀️ Light theme" if theme == "dark" else "🌙 Dark theme",
        key="auth_theme_toggle",
    ):
        selected_theme = (
            "light" if theme == "dark" else "dark"
        )
        st.session_state["theme"] = selected_theme
        st.query_params["theme"] = selected_theme
        st.rerun()

    st.markdown(
        """
        <div class="auth-header">
            <div class="auth-logo">✓</div>
            <div class="auth-kicker">TASKFLOW WORKSPACE</div>
            <h1 class="auth-title">Welcome to TaskFlow</h1>
            <p class="auth-subtitle">
                Plan clearly, work confidently, and keep every task moving forward.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 2, 1])

    with center:

        login_tab, signup_tab = st.tabs(
            ["Login", "Sign Up"]
        )

        # -----------------------------------------
        # LOGIN
        # -----------------------------------------

        with login_tab:

            st.markdown(
                '<div class="auth-form-title">Welcome back</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                "Log in securely to continue to your tasks."
            )

            with st.form("taskflow_login_form"):

                email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email",
                    key="login_email",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password",
                )

                login_submitted = st.form_submit_button(
                    "Login",
                    type="primary",
                    use_container_width=True,
                )

            if login_submitted:

                if not email.strip() or not password:

                    st.warning(
                        "Please enter your email and password."
                    )

                else:

                    try:

                        result = login_user(
                            email,
                            password,
                        )

                        st.session_state["access_token"] = (
                            result["access_token"]
                        )

                        st.session_state["current_user"] = (
                            result["user"]
                        )

                        st.session_state["authenticated"] = True

                        st.success("Login successful!")

                        st.rerun()

                    except requests.HTTPError as exc:

                        status_code = (
                            exc.response.status_code
                            if exc.response is not None
                            else None
                        )

                        if status_code == 401:

                            st.warning(
                                "We couldn't log you in. "
                                "Please check your email and password. "
                                "If you don't have an account yet, "
                                "please go to Sign Up and create one."
                            )

                        elif status_code == 403:

                            st.error(
                                "Your account is currently inactive. "
                                "Please contact support."
                            )

                        else:

                            st.error(
                                "Login could not be completed. "
                                "Please try again later."
                            )

                    except requests.ConnectionError:

                        st.error(
                            "Unable to connect right now. "
                            "Please try again in a moment."
                        )

                    except requests.Timeout:

                        st.error(
                            "The request took too long. "
                            "Please try again."
                        )

                    except requests.RequestException:

                        st.error(
                            "Something went wrong while logging in. "
                            "Please try again."
                        )

                    except (KeyError, ValueError, TypeError):

                        st.error(
                            "Unable to complete login. "
                            "Please try again."
                        )

        # -----------------------------------------
        # SIGN UP
        # -----------------------------------------

        with signup_tab:

            st.markdown(
                '<div class="auth-form-title">Create your account</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                "Sign up to start managing your personal tasks."
            )

            with st.form("taskflow_signup_form"):

                new_email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email",
                    key="signup_email",
                )

                new_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a password (minimum 8 characters)",
                    key="signup_password",
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Enter your password again",
                    key="signup_confirm_password",
                )

                signup_submitted = st.form_submit_button(
                    "Create Account",
                    type="primary",
                    use_container_width=True,
                )

            if signup_submitted:

                if not new_email.strip():

                    st.warning(
                        "Please enter your email address."
                    )

                elif len(new_password) < 8:

                    st.warning(
                        "Password must contain at least 8 characters."
                    )

                elif new_password != confirm_password:

                    st.warning(
                        "Passwords do not match. Please try again."
                    )

                else:

                    try:

                        register_user(
                            new_email,
                            new_password,
                        )

                        st.success(
                            "Account created successfully! "
                            "Please open the Login tab to sign in."
                        )

                    except requests.HTTPError as exc:

                        status_code = (
                            exc.response.status_code
                            if exc.response is not None
                            else None
                        )

                        if status_code == 409:

                            st.warning(
                                "An account with this email already "
                                "exists. Please go to Login instead."
                            )

                        elif status_code == 422:

                            st.error(
                                "Please enter valid details and a "
                                "password containing at least "
                                "8 characters."
                            )

                        else:

                            st.error(
                                "We couldn't create your account. "
                                "Please try again."
                            )

                    except requests.ConnectionError:

                        st.error(
                            "Unable to connect right now. "
                            "Please try again later."
                        )

                    except requests.Timeout:

                        st.error(
                            "The request took too long. "
                            "Please try again."
                        )

                    except requests.RequestException:

                        st.error(
                            "Something went wrong during registration. "
                            "Please try again."
                        )
