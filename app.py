import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import uuid
import re



#page layout #


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

}

.sub-title {
    font-size: 20px;
    color: #555;
    margin-bottom: 20px;
}

.login-box {
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0px 0px 15px rgba(0,0,0,0.1);
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

.sidebar .sidebar-content {
    background-color: #1f3c88;
    color: white;
}

.footer {
    text-align: center;
    color: gray;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)



#-----data from--------#



SHEET_NAME = "USER_DATA"

from google.oauth2.service_account import Credentials
import streamlit as st
import gspread

def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )

    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def load_data():
    sheet = connect_sheet()
    return pd.DataFrame(sheet.get_all_records())

def add_user(data):
    sheet = connect_sheet()
    sheet.append_row(data)

# ---------------- Session ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "login"

st.set_page_config(page_title="Running Staff Care Fund", layout="wide")

st.markdown('<div class="page-title"> 🚆Running Staff Care Fund🚆</div>', unsafe_allow_html=True)


df = load_data()

@st.cache_data(ttl=300)
def get_contribution_by_cms(cmsid):
    df = load_data()

    # safety: string match
    df["cmsid"] = df["cmsid"].astype(str)

    row = df[df["cmsid"] == str(cmsid)]

    if row.empty:
        return 0

    return row.iloc[0].get("contribution", 0)

# ---------------- Signup ----------------
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
        margin-top: 40px;
        box-shadow: 0px -2px 8px rgba(0,0,0,0.2);
    ">
        "Design & Developed by RSCF © 2026 #BSR1419//BSR1402//BSR1400# | All Rights Reserved"
    </div>
    """, unsafe_allow_html=True)



def signup_page():
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.image("handshake.png", width=420)

    with col2:
        
        st.markdown("### 📝 Create Account")

        name = st.text_input("Name *").strip()
        hq = st.text_input("Headquarter *").strip()
        cmsid = st.text_input("CMSID *").strip()
        email = st.text_input("Email *").strip()
        password = st.text_input("Password *", type="password").strip()
        mobile = st.text_input("Mobile (10 digits) *").strip()

        if st.button("Register"):

            if not all([name, hq, cmsid, email, password, mobile]):
                st.error("❌ All fields required")
                return

            if not re.fullmatch(r"\d{10}", mobile):
                st.error("❌ Mobile must be 10 digits")
                return

            if email in df["email"].values:
                st.error("❌ Email already registered")
                return

            user_id = str(uuid.uuid4())[:8]

            add_user([user_id, name, hq, cmsid, email, password, mobile, "PENDING"])

            st.success("✅ Registered. Wait for admin approval.")
            st.session_state.page = "login"
            st.rerun()

        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# ---------------- Login ----------------
def login_page():
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.image("handshake.png", width=420)

    with col2:
        

        st.markdown('<div class="main-title">🔐only signed up group members can login 🔐</div>', unsafe_allow_html=True)
        

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
                    st.success("Login successful ✅")
                    st.rerun()

        st.markdown("----")
        if st.button("Create new account"):
            st.session_state.page = "signup"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        app_footer()


# ---------------- Dashboard ----------------
def dashboard_page():
    user = st.session_state.user_data

    # ===== MOBILE SAFE MENU (ONLY HERE) =====
    with st.expander("☰ Menu", expanded=False):
        st.link_button("📜 Group Rules", "https://docs.google.com/document/d/1UmwVVb2q8azpaN4nrN22489r9zBH_tJKzXJPZtivyxM/edit?tab=t.0")
        st.link_button("ℹ️ Group Members", "https://docs.google.com/document/d/1YymXCoUaKSVT9I8O-4JrPcAAHTnsmNagHRoZV9Q7quM/edit?tab=t.0")
       
        st.link_button("💰 Fund Status Coming Soon", "Coming Soon...")
        st.link_button("ℹ️FAQ", "https://sites.google.com/view/runningstaffcarefund/faq?authuser=0")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.rerun()

    
    # ================= DASHBOARD BODY =================
    st.markdown("## 📊 User Dashboard")


    # ================= BRIEF HISTORY =================
    st.markdown("### 📝 A Brief History")

    st.markdown("""
    यह **“रनिंग स्टाफ सहायता ग्रुप”** पूर्णतः **गैर-लाभकारी (Non-Profit)** एवं **आपसी सहयोग** के आधार पर  
    **Jan 2026** में गठित किया गया है, जिसका उद्देश्य रनिंग स्टाफ के सदस्यों को  
    **असामान्य, आपातकालीन, आर्थिक एवं कठिन परिस्थितियों** में सहायता प्रदान करना है।
    """)

    st.markdown("""
    The **“Running Staff Care Fund”** is a completely **non-profit group** formed in **Jan 2026**  
    on the basis of **mutual cooperation**.

    The objective of this group is to provide **financial and necessary assistance**  
    to running staff members during **abnormal, emergency, financial, and difficult situations**,  
    subject to the **rules of the group**.
    """)

    contribution = get_contribution_by_cms(user["cmsid"])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💰 Your Contribution", f"₹ {contribution}")

    with col2:
        st.metric("🆔 CMS ID", user["cmsid"])

    with col3:
        st.metric("✅ Status", user["status"])

    st.markdown("---")

    st.write("👤 **Name:**", user["name"])
    st.write("🏢 **HQ:**", user["hq"])
    st.write("📧 **Email:**", user["email"])
    st.write("📱 **Mobile:**", user["mobile"])
    
    
    
    app_footer()



# ---------------- Router ----------------
if st.session_state.logged_in:
    dashboard_page()
else:
    if st.session_state.page == "login":
        login_page()
    else:

        signup_page()








