import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="TNPSC VetriPathai SaaS Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database Initialization (SQLite for Production Persistence)
def init_db():
    conn = sqlite3.connect("tnpsc_saas.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    # Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit TEXT,
            question_ta TEXT,
            question_en TEXT,
            opt1_ta TEXT, opt2_ta TEXT, opt3_ta TEXT, opt4_ta TEXT,
            opt1_en TEXT, opt2_en TEXT, opt3_en TEXT, opt4_en TEXT,
            answer_idx INTEGER,
            explanation_ta TEXT,
            explanation_en TEXT
        )
    ''')
    
    # Default Admin creation if not exists
    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@tnpsc.com",))
    if not cursor.fetchone():
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                       ("admin@tnpsc.com", hashed_pw, "Admin"))
    
    # Insert default questions if table is empty
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        default_qs = [
            ("Unit 8: Tamil Society", "திருக்குறளில் எத்தனை அதிகாரங்கள் உள்ளன?", "How many chapters in Thirukkural?", 
             "130", "133", "108", "120", "130", "133", "108", "120", 1, 
             "திருக்குறளில் 133 அதிகாரங்கள் உள்ளன.", "Thirukkural has 133 chapters."),
            ("Unit 5: Indian Polity", "இந்திய அரசியலமைப்பின் தந்தை யார்?", "Who is the Father of Indian Constitution?",
             "நேரு", "காந்தி", "அம்பேத்கர்", "ராஜேந்திர பிரசாத்", "Nehru", "Gandhi", "Ambedkar", "Prasad", 2,
             "டாக்டர் பி.ஆர். அம்பேத்கர்.", "Dr. B.R. Ambedkar.")
        ]
        cursor.executemany('''
            INSERT INTO questions (unit, question_ta, question_en, opt1_ta, opt2_ta, opt3_ta, opt4_ta, opt1_en, opt2_en, opt3_en, opt4_en, answer_idx, explanation_ta, explanation_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_qs)
        
    conn.commit()
    conn.close()

init_db()

# Helper DB functions
def get_db_connection():
    return sqlite3.connect("tnpsc_saas.db", check_same_thread=False)

# Session State Setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_role = "Free"

# -------------------------------------------------------------
# AUTHENTICATION GATEWAY (LOGIN / SIGNUP)
# -------------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🛡️ TNPSC VetriPathai SaaS - Secure Portal")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register (Free Tier)"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login to Dashboard")
            
            if submit_login:
                conn = get_db_connection()
                cursor = conn.cursor()
                hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute("SELECT role FROM users WHERE email = ? AND password = ?", (email, hashed_pw))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.user_role = user[0]
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Email or Password. (Demo Admin: admin@tnpsc.com / admin123)")
                    
    with tab2:
        with st.form("reg_form"):
            new_email = st.text_input("New Email")
            new_pass = st.text_input("New Password", type="password")
            submit_reg = st.form_submit_button("Create Free Account")
            
            if submit_reg:
                if new_email and new_pass:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    try:
                        hashed_pw = hashlib.sha256(new_pass.encode()).hexdigest()
                        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", 
                                       (new_email, hashed_pw, "Free"))
                        conn.commit()
                        st.success("Account created successfully! Please switch to Login tab.")
                    except sqlite3.IntegrityError:
                        st.error("Email already exists.")
                    finally:
                        conn.close()
                else:
                    st.warning("Please fill all fields.")
    st.stop()

# -------------------------------------------------------------
# MAIN DASHBOARD & NAVIGATION (AFTER LOGIN)
# -------------------------------------------------------------
st.sidebar.title("🚀 TNPSC SaaS Hub")
st.sidebar.write(f"👤 {st.session_state.user_email}")
st.sidebar.info(f"🛡️ Tier: **{st.session_state.user_role}**")
st.sidebar.markdown("---")

lang_option = st.sidebar.radio("Language", ["தமிழ் (Tamil)", "English"])
is_tamil = "தமிழ்" in lang_option

menu_options = ["🏠 Dashboard", "📝 Mock Test", "📊 Syllabus Tracker", "💎 SaaS Pricing"]
if st.session_state.user_role == "Admin":
    menu_options.append("⚙️ Admin Panel")

choice = st.sidebar.selectbox("Navigation", menu_options)

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Fetch questions from DB
conn = get_db_connection()
questions_df = pd.read_sql("SELECT * FROM questions", conn)
conn.close()

# 1. DASHBOARD
if "Dashboard" in choice:
    st.title("🎯 TNPSC VetriPathai SaaS Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Question Bank", f"{len(questions_df)} MCQs")
    col2.metric("Account Status", f"{st.session_state.user_role} User")
    col3.metric("Platform Status", "Online & Secure 🟢")
    st.success("Welcome to your production-ready exam portal!")

# 2. MOCK TEST
elif "Mock Test" in choice:
    st.title("📝 Mock Test Engine")
    if len(questions_df) == 0:
        st.warning("No questions available.")
    else:
        with st.form("exam_form"):
            answers = {}
            for idx, row in questions_df.iterrows():
                q_text = row['question_ta'] if is_tamil else row['question_en']
                opts = [row['opt1_ta'], row['opt2_ta'], row['opt3_ta'], row['opt4_ta']] if is_tamil else \
                       [row['opt1_en'], row['opt2_en'], row['opt3_en'], row['opt4_en']]
                
                st.subheader(f"Q{idx+1}. {q_text}")
                ans = st.radio("Select answer:", opts, key=f"q_{row['id']}", index=None)
                answers[row['id']] = ans
                st.markdown("---")
            
            submitted = st.form_submit_button("Submit Test")
            
        if submitted:
            score = 0
            for idx, row in questions_df.iterrows():
                opts = [row['opt1_ta'], row['opt2_ta'], row['opt3_ta'], row['opt4_ta']] if is_tamil else \
                       [row['opt1_en'], row['opt2_en'], row['opt3_en'], row['opt4_en']]
                correct_opt = opts[row['answer_idx']]
                if answers.get(row['id']) == correct_opt:
                    score += 1
            st.balloons()
            st.header(f"🎯 Your Score: {score} / {len(questions_df)}")

# 3. SYLLABUS TRACKER
elif "Syllabus Tracker" in choice:
    st.title("📊 Syllabus Progress Tracker")
    units = [f"Unit {i}" for i in range(1, 11)]
    completed = sum(1 for u in units if st.checkbox(u))
    st.progress(completed / len(units))

# 4. PRICING
elif "SaaS Pricing" in choice:
    st.title("💎 Subscription Plans")
    c1, c2 = st.columns(2)
    c1.subheader("Free Tier")
    c1.write("Basic mock tests & tracker.")
    c2.subheader("Pro Tier (₹199/mo)")
    c2.write("Unlimited tests, AI solutions & PYQs.")
    if c2.button("Upgrade via UPI"):
        st.info("Payment gateway integration ready (Razorpay/PhonePe API hook).")

# 5. ADMIN PANEL (RBAC RESTRICTED)
elif "Admin Panel" in choice:
    st.title("⚙️ Admin Management Panel")
    if st.session_state.user_role == "Admin":
        st.success("Authorized Admin Access")
        with st.form("add_q_form"):
            unit = st.text_input("Unit Name", "Unit 1: General Science")
            q_ta = st.text_input("Question (Tamil)")
            q_en = st.text_input("Question (English)")
            opt1 = st.text_input("Option 1")
            opt2 = st.text_input("Option 2")
            opt3 = st.text_input("Option 3")
            opt4 = st.text_input("Option 4")
            ans_idx = st.number_input("Correct Option Index (0 to 3)", min_value=0, max_value=3, value=0)
            exp_ta = st.text_area("Explanation (Tamil)")
            exp_en = st.text_area("Explanation (English)")
            
            add_btn = st.form_submit_button("Save Question to Database")
            if add_btn:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO questions (unit, question_ta, question_en, opt1_ta, opt2_ta, opt3_ta, opt4_ta, opt1_en, opt2_en, opt3_en, opt4_en, answer_idx, explanation_ta, explanation_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (unit, q_ta, q_en, opt1, opt2, opt3, opt4, opt1, opt2, opt3, opt4, ans_idx, exp_ta, exp_en))
                conn.commit()
                conn.close()
                st.success("Question successfully added to production DB!")
                st.rerun()
    else:
        st.error("Access Denied: Admin privileges required.")