import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import uuid
import re

# ---------------- PAGE CONFIG (ALWAYS FIRST) ----------------
st.set_page_config(page_title="Running Staff Care Fund", layout="wide")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
body {
    background-color: #f5f7fb;
}

.main-title {
    font-size: 28px;
    font-weight: 700;
    color: white;
    background: linear-gradient(90deg, #0f4c75, #1f3c88, #0f4c75);
    padding: 14px 30px;
    border-radius: 8px;
    text-align: center;
    margin-bottom: 20px;
    letter-spacing: 1px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
}

.page-title {
    font-size: 32px;
    font-weight: 700;
    color: white;
    background: linear-gradient(90deg, #0f4c75, #3282b8, #0f4c75);
    padding: 14px 25px;
    border-radius: 8px;
    text-align: center;
    margin: 10px auto 20px auto;
    width: 100%;
    letter-spacing: 1px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.25);
}

.sub-title {
    font-size: 20px;
    color: #555;
    margin-bottom: 20px;
}

.stButton > button {
    background-color: #0078AA;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    font-size: 16px;
}

.stButton > button:hover {
    background-color: #005f85;
}

.footer {
    text-align: center;
    color: gray;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title"> 🚆Running Staff Care Fund🚆</div>', unsafe_allow_html=True)

# ---------------- GOOGLE SHEET CONNECTION ----------------
SHEET_NAME = "USER_DATA"

def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def load_data():
    sheet = connect_sheet()
    return pd.DataFrame(sheet.get_all_records())

def add_user(data):
    sheet = connect_sheet()
    sheet.append_row(data)

@st.cache_data(ttl=300)
def get_contribution_by_cms(cmsid):
    df = load_data()
    df["cmsid"] = df["cmsid"].astype(str)
    row = df[df["cmsid"] == str(cmsid)]
    if row.empty:
        return 0
    return row.iloc[0].get("contribution", 0)

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "login"

df = load_data()

# ---------------- FOOTER ----------------
def app_footer():
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #0f4c75, #1f3c88, #0f4c75);
        color: white;
        text-align: center;
        padding: 12px;
        font-size: 14px;
        font-weight: 500;
        border-radius: 6px;
        margin-top: 40px;">
        Design & Developed by RSCF © 2026 | All Rights Reserved
    </div>
    """, unsafe_allow_html=True)

# ---------------- LOGIN ----------------
def login_page():
    st.markdown("### 🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = df[(df["email"] == email) & (df["password"] == password)]

        if user.empty:
            st.error("❌ Invalid credentials")
        else:
            user_data = user.iloc[0]
            if user_data["status"] != "ACTIVE":
                st.warning("⏳ Account not activated by admin")
            else:
                st.session_state.logged_in = True
                st.session_state.user_data = user_data.to_dict()
                st.rerun()

# ---------------- DASHBOARD ----------------
def dashboard_page():
    user = st.session_state.user_data

    # Header Row
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## 📊 User Dashboard")
    with col2:
        st.link_button("💰 Fund Status",
                       "https://lookerstudio.google.com/u/0/reporting/94ba324a-1489-432b-8107-a3ace8fddcf1/page/ibGoF")

    st.markdown("---")

    # Brief History
    st.markdown("""
    यह **“रनिंग स्टाफ सहायता ग्रुप”** पूर्णतः **गैर-लाभकारी (Non-Profit)** 
    एवं **आपसी सहयोग** के आधार पर **Jan 2026** में गठित किया गया है।
    """)

    st.markdown("---")

    # Metrics
    contribution = get_contribution_by_cms(user["cmsid"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Your Contribution", f"₹ {contribution}")
    with col2:
        st.metric("🆔 CMS ID", user["cmsid"])
    with col3:
        st.metric("✅ Status", user["status"])

    st.markdown("---")

    # User Info
    st.write("👤 **Name:**", user["name"])
    st.write("🏢 **HQ:**", user["hq"])
    st.write("📧 **Email:**", user["email"])
    st.write("📱 **Mobile:**", user["mobile"])

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

    app_footer()

# ---------------- ROUTER ----------------
if st.session_state.logged_in:
    dashboard_page()
else:
    login_page()
