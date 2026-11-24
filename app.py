"""Role-based entry point for the database recommendation system."""
import streamlit as st
import pandas as pd
from pandas.io.formats.style import Styler

# Streamlit's dataframe grid is canvas-rendered, so ordinary CSS cannot recolour
# its cells. Apply Pandas Styler cell styles before every st.dataframe call.
# This wrapper is installed before either role-specific page is imported.
_original_st_dataframe = st.dataframe


def _light_theme_dataframe(data=None, *args, **kwargs):
    # "theme" is not accepted by older Streamlit releases; never pass it through.
    kwargs.pop("theme", None)

    if isinstance(data, pd.DataFrame):
        styled = data.style
    elif isinstance(data, Styler):
        styled = data
    else:
        styled = None

    if styled is not None:
        styled = styled.set_properties(
            **{
                "color": "#26344B",
                "border-color": "#BED3C4",
            }
        )
        # Pandas Styler cell backgrounds are carried into Streamlit's grid
        # renderer; unlike CSS selectors, these styles affect the canvas cells.
        styled = styled.apply(
            lambda row: [
                "background-color: #F7F8F4" if row.name % 2 else "background-color: #FFFFFF"
                for _ in row
            ],
            axis=1,
        )
        styled = styled.set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#EBADA2"),
                        ("color", "#26344B"),
                        ("border-color", "#BED3C4"),
                        ("font-weight", "700"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("color", "#26344B"),
                        ("border-color", "#BED3C4"),
                    ],
                },
            ],
            overwrite=False,
        )
        data = styled

    return _original_st_dataframe(data, *args, **kwargs)


st.dataframe = _light_theme_dataframe

st.set_page_config(
    page_title="Database Selection System",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Temporary demonstration credentials. Change these before deployment.
CREDENTIALS = {
    "User": {"username": "user", "password": "user123"},
    "Administrator": {"username": "admin", "password": "admin123"},
}

THEME = """
<style>
:root {
  --sw-rose: #CE6A6C;
  --sw-peach: #EBADA2;
  --sw-sage: #BED3C4;
  --sw-teal: #49919D;
  --sw-slate: #8D94A5;
  --sw-ink: #26344B;
}
.stApp { background: linear-gradient(180deg, #fffaf7 0%, #f7f8f4 100%); color: var(--sw-ink); }
[data-testid="stHeader"] { background: rgba(255,250,247,.88); }
h1, h2, h3 { color: #26344B !important; }
.stApp label, .stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stMarkdownContainer"] p {
  color: #26344B !important;
}
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] {
  color: #26344B !important;
}
.stApp input::placeholder { color: #8D94A5 !important; opacity: 1; }
/* Keep text legible inside Streamlit widgets, including dark-themed nested controls. */
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] *,
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] *,
.stApp .stRadio label,
.stApp .stCheckbox label,
.stApp [data-testid="stExpander"] summary,
.stApp [data-testid="stExpander"] summary *,
.stApp [data-baseweb="select"] *,
.stApp [data-baseweb="input"] *,
.stApp [data-baseweb="textarea"] *,
.stApp [data-testid="stAlert"] *,
.stApp [data-testid="stMetric"] * {
  color: #26344B !important;
}
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] {
  background-color: #ffffff !important;
}
.stApp [data-testid="stPopover"] *,
.stApp [role="listbox"] *,
.stApp [role="option"] {
  color: #26344B !important;
}
/* Streamlit form labels were inheriting a very light theme colour. */
.stApp label, .stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stMarkdownContainer"] p {
  color: #26344B !important;
}
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] {
  color: #26344B !important;
}
.stApp input::placeholder { color: #8D94A5 !important; opacity: 1; }
.stButton > button[kind="primary"], .stFormSubmitButton > button {
  background: #49919D; color: white; border: 0; border-radius: 10px;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
  background: #397984; color: white; border: 0;
}
.stButton > button { border-radius: 10px; border-color: #BED3C4; }
[data-testid="stMetric"] { background: #ffffffb8; border: 1px solid #BED3C4; padding: 14px; border-radius: 12px; }
[data-testid="stExpander"] { border-color: #BED3C4; border-radius: 10px; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border: 1px solid #BED3C4; border-radius: 10px; }
.stProgress > div > div > div > div { background-color: #49919D; }
hr { border-color: #BED3C4; }
.login-panel { padding: 1.4rem; background: rgba(255,255,255,.8); border: 1px solid #BED3C4; border-radius: 16px; }

/* Sidebar: dark background with consistently readable light text */
[data-testid="stSidebar"],
[data-testid="stSidebar"] *:not(input):not(textarea) {
    color: #F7F8F4 !important;
}
[data-testid="stSidebar"] {
    background-color: #26344B !important;
}

/* Sidebar headings and markdown content */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {
    color: #F7F8F4 !important;
}

/* Sidebar input fields: dark surface + light text */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #26344B !important;
    color: #FFFFFF !important;
    border-color: #BED3C4 !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] button * {
    color: #FFFFFF !important;
}

/* Make every button readable, including secondary and form buttons. */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
  background: #49919D !important;
  color: #FFFFFF !important;
  border: 1px solid #397984 !important;
  border-radius: 10px;
}
.stButton > button *,
.stFormSubmitButton > button *,
.stDownloadButton > button * {
  color: #FFFFFF !important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover {
  background: #397984 !important;
  color: #FFFFFF !important;
}

/* Keep expanders and tables aligned with the application's light page theme. */
[data-testid="stExpander"] details,
[data-testid="stExpander"] summary {
  background: #FFFFFF !important;
  color: #26344B !important;
}
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
  color: #26344B !important;
}
[data-testid="stTable"] table {
  background: #FFFFFF !important;
  color: #26344B !important;
  border-collapse: collapse !important;
}
[data-testid="stTable"] th {
  background: #EBADA2 !important;
  color: #26344B !important;
}
[data-testid="stTable"] td {
  background: #FFFFFF !important;
  color: #26344B !important;
  border-color: #BED3C4 !important;
}


/* Explicitly force Streamlit's canvas-based dataframe grid to use the light palette.
   Variables are set on the app and the grid host because the grid paints cells to canvas. */
.stApp,
.stApp [data-testid="stDataFrame"],
.stApp [data-testid="stDataFrame"] > div,
.stApp [data-testid="stDataFrame"] [role="grid"],
.stApp [data-testid="stDataFrame"] canvas {
  color-scheme: light !important;
  --gdg-bg-cell: #FFFFFF !important;
  --gdg-bg-cell-medium: #F7F8F4 !important;
  --gdg-bg-header: #EBADA2 !important;
  --gdg-bg-header-has-focus: #E6A096 !important;
  --gdg-bg-header-hovered: #E6A096 !important;
  --gdg-text-dark: #26344B !important;
  --gdg-text-medium: #26344B !important;
  --gdg-text-light: #526078 !important;
  --gdg-text-header: #26344B !important;
  --gdg-border-color: #BED3C4 !important;
  --gdg-horizontal-border-color: #BED3C4 !important;
  --gdg-drilldown-border: #BED3C4 !important;
  --gdg-accent-color: #49919D !important;
  --gdg-link-color: #397984 !important;
}
.stApp [data-testid="stDataFrame"] *,
.stApp [data-testid="stDataFrame"] [class*="glide"],
.stApp [data-testid="stDataFrame"] [class*="dvn"],
.stApp [data-testid="stDataFrame"] [class*="scroller"] {
  color-scheme: light !important;
  --gdg-bg-cell: #FFFFFF !important;
  --gdg-bg-cell-medium: #F7F8F4 !important;
  --gdg-bg-header: #EBADA2 !important;
  --gdg-text-dark: #26344B !important;
  --gdg-text-medium: #26344B !important;
  --gdg-text-light: #526078 !important;
  --gdg-text-header: #26344B !important;
  --gdg-border-color: #BED3C4 !important;
  --gdg-horizontal-border-color: #BED3C4 !important;
  --gdg-accent-color: #49919D !important;
}
/* Native Streamlit static tables */
.stApp [data-testid="stTable"] table,
.stApp [data-testid="stTable"] thead,
.stApp [data-testid="stTable"] tbody,
.stApp [data-testid="stTable"] tr,
.stApp [data-testid="stTable"] th,
.stApp [data-testid="stTable"] td {
  color: #26344B !important;
  border-color: #BED3C4 !important;
}
.stApp [data-testid="stTable"] th {
  background: #EBADA2 !important;
  font-weight: 700 !important;
}
.stApp [data-testid="stTable"] td {
  background: #FFFFFF !important;
}
.stApp [data-testid="stTable"] tbody tr:nth-child(even) td {
  background: #F7F8F4 !important;
}
</style>
"""
st.markdown(THEME, unsafe_allow_html=True)


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


if not st.session_state.get("authenticated"):
    st.title("Database Selection & Recommendation System")
    st.caption("Sign in to access the system. This is a prototype login, not a sign-up page.")

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.subheader("Sign in")
        role = st.radio(
            "Choose account type",
            ["User", "Administrator"],
            horizontal=True,
            key="login_role",
        )
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                help="Use the temporary prototype credentials provided in README.md.",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            expected = CREDENTIALS[role]
            if username.strip() == expected["username"] and password == expected["password"]:
                st.session_state["authenticated"] = True
                st.session_state["role"] = role
                st.session_state["user_step"] = 1
                st.rerun()
            else:
                st.error("Incorrect username or password. Please check your account type and try again.")

    st.caption("Prototype accounts only: User: user / user123 · Administrator: admin / admin123")

else:
    role = st.session_state.get("role")
    st.sidebar.markdown("### Database System")
    st.sidebar.write(f"Signed in as **{role}**")
    if st.sidebar.button("Log out"):
        logout()

    if role == "Administrator":
        st.sidebar.info("Administrator access: database catalogue, application details and scores.")
        import admin_app
        admin_app.render_admin_page()  # Existing full management view retained for administrators.
    elif role == "User":
        import user_app
        user_app.render_user_page()
    else:
        logout()
