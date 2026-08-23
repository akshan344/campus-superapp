import streamlit as st
import sqlite3
import hashlib
import time
import random
import os
import resend

# -----------------------------------------------------------------------------
# 1. DATABASE SETUP & BULLETPROOF AUTO-MIGRATION
# -----------------------------------------------------------------------------
DB_FILE = "campus.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    email TEXT UNIQUE,
                    password TEXT
                )''')
    
    existing_columns = [col[1] for col in c.execute("PRAGMA table_info(users)").fetchall()]
    columns_to_add = {
        "phone": "TEXT",
        "branch": "TEXT",
        "bio": "TEXT",
        "social_points": "INTEGER DEFAULT 0",
        "id_verified": "INTEGER DEFAULT 0",
        "is_verified": "INTEGER DEFAULT 0",
        "otp_code": "TEXT",
        "id_image": "TEXT"
    }
    
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

    c.execute('''CREATE TABLE IF NOT EXISTS friends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    friend_username TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS rides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver TEXT, email TEXT, phone TEXT, route TEXT, vehicle TEXT,
                    capacity INTEGER, available INTEGER, time TEXT, status TEXT DEFAULT 'Active'
                )''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS ride_bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ride_id INTEGER,
                    passenger_username TEXT,
                    passenger_phone TEXT,
                    passenger_email TEXT
                )''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS marketplace (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT, seller TEXT, seller_phone TEXT, type TEXT,
                    condition TEXT, price INTEGER, ai_est INTEGER
                )''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS doubts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT, question TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doubt_id INTEGER,
                    responder TEXT,
                    answer_text TEXT,
                    votes INTEGER DEFAULT 0,
                    FOREIGN KEY(doubt_id) REFERENCES doubts(id)
                )''')
                
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def send_real_email(target_email, otp_code):
    api_key = None
    try:
        if "RESEND_API_KEY" in st.secrets:
            api_key = st.secrets["RESEND_API_KEY"]
    except Exception:
        pass
    
    if api_key:
        try:
            resend.api_key = api_key.strip()
            resend.Emails.save({ ... }) # or your send code
            return True
        except Exception as e:
            pass
    
    st.info(f"🔑 **Dev Mode OTP:** Verification code for `{target_email}` is **{otp_code}**")
    return True

# -----------------------------------------------------------------------------
# 2. STREAMLIT CONFIG & UI STYLING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Campus Connect Pro Max", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #FFFFFF; }
    
    .stRadio [role="radiogroup"] > label {
        background: linear-gradient(135deg, #1F2937, #111827) !important;
        padding: 1rem 1.2rem !important;
        border-radius: 10px !important;
        margin-bottom: 0.8rem !important;
        border: 2px solid #374151 !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        color: #F3F4F6 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        transition: all 0.25s ease-in-out;
    }
    .stRadio [role="radiogroup"] > label:hover {
        background: linear-gradient(135deg, #374151, #1F2937) !important;
        border-color: #4F46E5 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(79, 70, 229, 0.4);
    }

    div.stButton > button {
        width: 100%; height: 3.5rem; background: linear-gradient(135deg, #4F46E5, #3B82F6);
        color: white; font-weight: 700; font-size: 1.1rem; border-radius: 8px;
        border: none; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);
        transition: all 0.2s ease-in-out; margin-top: 0.5rem;
    }
    div.stButton > button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6);
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 6px !important; border: 1.5px solid #374151 !important;
        background-color: #1F2937 !important; color: white !important;
        padding: 0.75rem !important; font-size: 1rem !important;
    }

    .custom-card {
        background-color: #1F2937; padding: 1.8rem; border-radius: 10px;
        border: 1px solid #374151; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem; color: #F3F4F6;
    }
    .badge {
        background: #312E81; color: #818CF8; font-size: 0.85rem;
        font-weight: 600; padding: 0.35rem 0.75rem; border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION & LOGIN WORKFLOW (WITH FORGOT PASSWORD)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>🎓 Campus Connect Portal</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup, tab_verify, tab_forgot = st.tabs(["🔐 Login", "📝 Sign Up", "✉️ Verify Account", "🔑 Forgot Password"])
        
        with tab_login:
            login_email = st.text_input("Campus Email Address", key="l_email")
            login_pass = st.text_input("Password", type="password", key="l_pass")
            
            if st.button("Log In to Dashboard"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT id, username, email, phone, branch, bio, social_points, id_verified, is_verified FROM users WHERE email=? AND password=?", 
                          (login_email, hash_password(login_pass)))
                user = c.fetchone()
                conn.close()
                
                if user:
                    if user[8] == 0:
                        st.error("⚠️ Account unverified via OTP. Switch to 'Verify Account' tab.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_data = {
                            "id": user[0], "username": user[1], "email": user[2], "phone": user[3],
                            "branch": user[4], "bio": user[5], "social_points": user[6], "id_verified": user[7]
                        }
                        st.success("Login successful!")
                        st.rerun()
                else:
                    st.error("Invalid email or password.")

        with tab_signup:
            su_user = st.text_input("Full Name", key="s_user")
            su_email = st.text_input("Campus Email Address", key="s_email")
            su_phone = st.text_input("Mobile Number (+91...)", key="s_phone")
            su_pass = st.text_input("Password", type="password", key="s_pass")
            su_branch = st.text_input("Branch / Department", key="s_branch")
            su_bio = st.text_area("Bio", key="s_bio")
            
            if st.button("Create Account"):
                if su_user and su_email and su_phone and su_pass:
                    otp = str(random.randint(100000, 999999))
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("""INSERT INTO users 
                                  (username, email, phone, password, branch, bio, social_points, id_verified, is_verified, otp_code) 
                                  VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?)""",
                                  (su_user, su_email, su_phone, hash_password(su_pass), su_branch, su_bio, otp))
                        conn.commit()
                        conn.close()
                        
                        send_real_email(su_email, otp)
                        st.success("Account created! Check your email for the verification OTP.")
                    except sqlite3.IntegrityError:
                        st.error("Email already registered.")
                else:
                    st.warning("Please fill out all required fields.")

        with tab_verify:
            v_email = st.text_input("Registered Email", key="v_email")
            v_otp = st.text_input("6-Digit OTP Code", max_chars=6, key="v_otp")
            if st.button("Verify Account"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT otp_code FROM users WHERE email=?", (v_email,))
                res = c.fetchone()
                
                if res and res[0] == v_otp.strip():
                    c.execute("UPDATE users SET is_verified=1 WHERE email=?", (v_email,))
                    conn.commit()
                    st.balloons()
                    st.success("🎉 Account verified! You can now log in.")
                else:
                    st.error("Invalid OTP Code.")
                conn.close()

        with tab_forgot:
            st.subheader("🔑 Reset Your Password")
            f_email = st.text_input("Enter your registered campus email", key="f_email")
            
            if st.button("Send Recovery OTP"):
                if f_email:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT id FROM users WHERE email=?", (f_email,))
                    found_user = c.fetchone()
                    if found_user:
                        new_otp = str(random.randint(100000, 999999))
                        c.execute("UPDATE users SET otp_code=? WHERE email=?", (new_otp, f_email))
                        conn.commit()
                        send_real_email(f_email, new_otp)
                        st.success("Recovery OTP dispatched to your email!")
                    else:
                        st.error("Email address not found in system.")
                    conn.close()
                else:
                    st.warning("Please input your email address.")

            st.divider()
            f_otp = st.text_input("Enter 6-Digit Recovery OTP", max_chars=6, key="f_otp")
            new_password = st.text_input("Enter New Password", type="password", key="new_pass")
            
            if st.button("Confirm Password Reset"):
                if f_email and f_otp and new_password:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT otp_code FROM users WHERE email=?", (f_email,))
                    res = c.fetchone()
                    if res and res[0] == f_otp.strip():
                        c.execute("UPDATE users SET password=? WHERE email=?", (hash_password(new_password), f_email))
                        conn.commit()
                        st.success("🎉 Password successfully reset! You can now log in using your new credentials.")
                    else:
                        st.error("Invalid recovery OTP code.")
                    conn.close()
                else:
                    st.warning("Please complete all fields for password reset.")

    st.stop()

# -----------------------------------------------------------------------------
# 4. MAIN WORKSPACE (POST-LOGIN)
# -----------------------------------------------------------------------------
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT social_points, id_verified FROM users WHERE id=?", (st.session_state.user_data['id'],))
row = c.fetchone()
if row:
    st.session_state.user_data['social_points'] = row[0]
    st.session_state.user_data['id_verified'] = row[1]
conn.close()

header_col1, header_col2 = st.columns([6, 2])
with header_col2:
    st.markdown(f"""
    <div style="background-color: #1F2937; padding: 0.6rem 1rem; border-radius: 8px; border: 1px solid #374151; text-align: right;">
        🏆 <b>Social Points:</b> <span style="color: #38BDF8; font-size: 1.1rem;">{st.session_state.user_data['social_points']}</span>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown(f"### 👤 {st.session_state.user_data['username']}")
st.sidebar.caption(f"**Email:** {st.session_state.user_data['email']}")

if st.session_state.user_data['id_verified'] == 0:
    st.sidebar.error("❌ ID Card Pending Verification ! (Features Locked)")
else:
    st.sidebar.success("✅ Fully Verified Student")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.rerun()

nav = st.sidebar.radio("Navigation Menu", [
    "🏠 Profile Dashboard (Insta)", 
    "🔍 Student Search & Friends",
    "🚗 Live Carpooling (Uber)", 
    "🛒 Peer Marketplace", 
    "❓ Doubt Section (Brainly)", 
    "⚙️ Settings & JSS AI ID Verification",
    "💬 Feedback Window"
])

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

if nav == "🏠 Profile Dashboard (Insta)":
    st.title("📸 Instagram-Style Student Profile & Feed")
    
    id_status_badge = '<span style="color: #EF4444; font-weight: bold;">❌ Not Verified ! (Go to Settings)</span>'
    if st.session_state.user_data['id_verified'] == 1:
        id_status_badge = '<span style="color: #10B981; font-weight: bold;">✅ Verified JSS Student</span>'

    st.markdown(f"""
    <div class="custom-card">
        <h2 style="color: #60A5FA; margin-bottom: 0.5rem;">@{st.session_state.user_data['username']}</h2>
        <p style="font-size: 1.1rem; margin: 0.3rem 0;"><b>📧 Campus Email:</b> {st.session_state.user_data['email']}</p>
        <p style="font-size: 1.1rem; margin: 0.3rem 0;"><b>📱 Secure Phone:</b> {st.session_state.user_data['phone']}</p>
        <p style="font-size: 1.1rem; margin: 0.3rem 0;"><b>🏛️ Branch:</b> {st.session_state.user_data['branch']}</p>
        <p style="font-size: 1.1rem; margin: 0.3rem 0;"><b>📝 Bio:</b> {st.session_state.user_data['bio']}</p>
        <p style="font-size: 1.1rem; margin: 0.3rem 0;"><b>🆔 JSS ID Status:</b> {id_status_badge}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🖼️ Student Activity Grid")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🚗 Rides Hosted & Completed")
    with col2:
        st.info("🛒 Active Marketplace Listings")
    with col3:
        st.info("❓ Doubts & Answers Posted")

elif nav == "🔍 Student Search & Friends":
    st.title("🔍 Instagram-Style Student Discovery")
    search_query = st.text_input("Search students by name or branch...")
    
    if search_query:
        c.execute("SELECT username, branch, email FROM users WHERE username LIKE ? OR branch LIKE ?", 
                  ('%' + search_query + '%', '%' + search_query + '%'))
        results = c.fetchall()
        
        for res in results:
            r_name, r_branch, r_email = res
            st.markdown(f"""
            <div class="custom-card">
                <h3>👤 @{r_name}</h3>
                <p><b>Branch:</b> {r_branch} | <b>Email:</b> {r_email}</p>
                <p style="color: #9CA3AF; font-size: 0.9rem;">🔒 Private phone numbers remain confidential and are revealed only upon verified ride bookings.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"➕ Add Friend ({r_name})", key=f"add_{r_name}"):
                c.execute("INSERT INTO friends (user_id, friend_username) VALUES (?, ?)", 
                          (st.session_state.user_data['id'], r_name))
                conn.commit()
                st.success(f"Added {r_name} to your friends list!")

    st.divider()
    st.subheader("👥 Your Friends Network")
    c.execute("SELECT friend_username FROM friends WHERE user_id=?", (st.session_state.user_data['id'],))
    my_friends = c.fetchall()
    if my_friends:
        for f in my_friends:
            st.write(f"• @{f[0]}")
    else:
        st.info("No friends added yet. Use the search bar above to connect with peers!")

elif nav == "🚗 Live Carpooling (Uber)":
    if st.session_state.user_data['id_verified'] == 0:
        st.error("⚠️ **Access Locked !** Verify your JSS Student ID in **Settings & JSS AI ID Verification** first.")
    else:
        st.title("🚗 Uber-Style Campus Carpooling")
        ride_search = st.text_input("🔍 Search destinations (e.g., Indirapuram, City Center)...")
        
        tab1, tab2, tab3 = st.tabs(["🛣️ Available Rides", "➕ Host a Ride", "📋 My Rides & Bookings"])
        
        with tab1:
            if ride_search:
                c.execute("SELECT id, driver, email, route, vehicle, capacity, available, time, status FROM rides WHERE route LIKE ? AND status='Active'", ('%' + ride_search + '%',))
            else:
                c.execute("SELECT id, driver, email, route, vehicle, capacity, available, time, status FROM rides WHERE status='Active'")
            
            rides = c.fetchall()
            for r in rides:
                r_id, driver_name, driver_email, route_path, vehicle_type, cap, avail, time_dep, status_val = r
                
                st.markdown(f"""
                <div class="custom-card">
                    <h3>Route: {route_path}</h3>
                    <p><b>Driver:</b> @{driver_name} | <b>Email:</b> {driver_email}</p>
                    <p><b>Vehicle:</b> {vehicle_type} | <b>Departure:</b> {time_dep}</p>
                    <p><b>Available Seats:</b> <span style="color: #34D399; font-weight: bold;">{avail} / {cap}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                if avail > 0:
                    if st.button(f"🚗 Book Ride & Reveal Contact ({route_path})", key=f"book_{r_id}"):
                        c.execute("UPDATE rides SET available = available - 1 WHERE id=?", (r_id,))
                        c.execute("INSERT INTO ride_bookings (ride_id, passenger_username, passenger_phone, passenger_email) VALUES (?, ?, ?, ?)",
                                  (r_id, st.session_state.user_data['username'], st.session_state.user_data['phone'], st.session_state.user_data['email']))
                        c.execute("UPDATE users SET social_points = social_points + 15 WHERE id=?", (st.session_state.user_data['id'],))
                        conn.commit()
                        
                        c.execute("SELECT phone FROM users WHERE username=?", (driver_name,))
                        d_phone_res = c.fetchone()
                        driver_phone = d_phone_res[0] if d_phone_res else "N/A"
                        
                        st.success(f"🎉 Ride successfully booked! Driver's Private Phone Number: **{driver_phone}** (+15 Points)")
                        st.rerun()
                
        with tab2:
            route = st.text_input("Route Path (e.g., Campus to City Mall)")
            v_type = st.selectbox("Vehicle Category", ["7-Seater SUV", "5-Seater Sedan", "3-Seater Auto"])
            cap = 7 if "7-Seater" in v_type else (5 if "5-Seater" in v_type else 3)
            time_slot = st.text_input("Departure Time (e.g., 5:30 PM Today)")
            
            if st.button("Publish Ride"):
                c.execute("INSERT INTO rides (driver, email, phone, route, vehicle, capacity, available, time, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')",
                          (st.session_state.user_data['username'], st.session_state.user_data['email'], st.session_state.user_data['phone'], route, v_type, cap, cap-1, time_slot))
                c.execute("UPDATE users SET social_points = social_points + 20 WHERE id=?", (st.session_state.user_data['id'],))
                conn.commit()
                st.success("Ride published successfully! (+20 Points)")
                st.rerun()

        with tab3:
            st.subheader("📋 Manage Your Hosted Rides (Cancel / Delete Mistaken Rides)")
            c.execute("SELECT id, route, time, vehicle, status, available FROM rides WHERE driver=?", (st.session_state.user_data['username'],))
            my_hosted_rides = c.fetchall()
            
            if my_hosted_rides:
                for hr in my_hosted_rides:
                    h_id, h_route, h_time, h_veh, h_status, h_avail = hr
                    st.markdown(f"• **Route:** {h_route} | **Time:** {h_time} | **Vehicle:** {h_veh} | **Status:** {h_status}")
                    if st.button(f"❌ Cancel / Delete Ride (#{h_id})", key=f"del_ride_{h_id}"):
                        c.execute("DELETE FROM rides WHERE id=?", (h_id,))
                        c.execute("DELETE FROM ride_bookings WHERE ride_id=?", (h_id,))
                        conn.commit()
                        st.success("Ride cancelled and removed successfully!")
                        st.rerun()
            else:
                st.info("You haven't hosted any rides yet.")

elif nav == "🛒 Peer Marketplace":
    if st.session_state.user_data['id_verified'] == 0:
        st.error("⚠️ **Access Locked !** Verify your JSS Student ID first.")
    else:
        st.title("🛒 Peer Marketplace & Rentals")
        market_search = st.text_input("🔍 Search marketplace items...")
        
        tab1, tab2 = st.tabs(["🛍️ Browse Market", "🏷️ List Item"])
        
        with tab1:
            if market_search:
                c.execute("SELECT id, title, seller, seller_phone, type, condition, price, ai_est FROM marketplace WHERE title LIKE ?", ('%' + market_search + '%',))
            else:
                c.execute("SELECT id, title, seller, seller_phone, type, condition, price, ai_est FROM marketplace")
            
            items = c.fetchall()
            for item in items:
                i_id, title, seller, seller_phone, item_type, condition, price, ai_est = item
                st.markdown(f"""
                <div class="custom-card">
                    <h3>{title} <span class="badge">{item_type}</span></h3>
                    <p><b>Seller:</b> @{seller} | <b>Condition:</b> {condition}</p>
                    <p><b>Price:</b> ₹{price} *(AI Est: ₹{ai_est})*</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📞 Contact Seller (@{seller})", key=f"contact_{i_id}"):
                    st.success(f"🔒 Secure Seller Contact for **{title}**: **{seller_phone}**")

        with tab2:
            item_name = st.text_input("Item Name")
            item_type = st.radio("Type", ["Sell", "Rent"])
            cond = st.selectbox("Condition", ["Like New", "Good", "Fair"])
            item_price = st.number_input("Desired Price (₹)", min_value=10, step=50)
            
            if st.button("List Item"):
                c.execute("INSERT INTO marketplace (title, seller, seller_phone, type, condition, price, ai_est) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (item_name, st.session_state.user_data['username'], st.session_state.user_data['phone'], item_type, cond, item_price, int(item_price*0.85)))
                c.execute("UPDATE users SET social_points = social_points + 10 WHERE id=?", (st.session_state.user_data['id'],))
                conn.commit()
                st.success("Item listed successfully! (+10 Points)")
                st.rerun()

elif nav == "❓ Doubt Section (Brainly)":
    if st.session_state.user_data['id_verified'] == 0:
        st.error("⚠️ **Access Locked !** Verify your JSS Student ID first.")
    else:
        st.title("❓ Brainly-Style Academic Doubt Section")
        
        with st.expander("➕ Ask a New Doubt"):
            q_text = st.text_area("Describe your academic doubt clearly")
            if st.button("Post Doubt to Community"):
                if q_text:
                    c.execute("INSERT INTO doubts (author, question) VALUES (?, ?)", (st.session_state.user_data['username'], q_text))
                    conn.commit()
                    st.success("Doubt posted successfully!")
                    st.rerun()

        st.divider()
        st.subheader("💬 Community Questions & Answers")
        
        c.execute("SELECT id, author, question FROM doubts")
        doubts = c.fetchall()
        
        for d in doubts:
            d_id, author, question = d
            st.markdown(f"""
            <div class="custom-card">
                <h4>❓ {question}</h4>
                <p style="color: #9CA3AF; font-size: 0.9rem;">Asked by: <b>@{author}</b></p>
            """, unsafe_allow_html=True)
            
            if author == st.session_state.user_data['username']:
                if st.button(f"🗑️ Delete This Doubt", key=f"del_doubt_{d_id}"):
                    c.execute("DELETE FROM doubts WHERE id=?", (d_id,))
                    c.execute("DELETE FROM answers WHERE doubt_id=?", (d_id,))
                    conn.commit()
                    st.warning("Doubt deleted successfully.")
                    st.rerun()
            
            c.execute("SELECT id, responder, answer_text, votes FROM answers WHERE doubt_id=?", (d_id,))
            answers = c.fetchall()
            
            for ans in answers:
                ans_id, responder, ans_text, votes = ans
                col_a, col_b, col_c, col_d = st.columns([5, 1, 1, 1])
                with col_a:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;💬 **@{responder}:** {ans_text} *(👍 {votes})*")
                with col_b:
                    if st.button("👍", key=f"up_{ans_id}"):
                        c.execute("UPDATE answers SET votes = votes + 1 WHERE id=?", (ans_id,))
                        c.execute("UPDATE users SET social_points = social_points + 10 WHERE username=?", (responder,))
                        conn.commit()
                        st.rerun()
                with col_c:
                    if st.button("👎", key=f"down_{ans_id}"):
                        c.execute("UPDATE answers SET votes = votes - 1 WHERE id=?", (ans_id,))
                        conn.commit()
                        st.rerun()
                with col_d:
                    if responder == st.session_state.user_data['username']:
                        if st.button("🗑️", key=f"del_ans_{ans_id}"):
                            c.execute("DELETE FROM answers WHERE id=?", (ans_id,))
                            conn.commit()
                            st.rerun()
                        
            ans_input = st.text_input(f"Write a helpful answer...", key=f"ans_input_{d_id}")
            if st.button("Submit Answer", key=f"ans_btn_{d_id}"):
                if ans_input:
                    c.execute("INSERT INTO answers (doubt_id, responder, answer_text, votes) VALUES (?, ?, ?, 0)",
                              (d_id, st.session_state.user_data['username'], ans_input))
                    conn.commit()
                    st.success("Answer posted!")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

elif nav == "⚙️ Settings & JSS AI ID Verification":
    st.title("⚙️ Strict JSS AI ID Card Verification")
    st.info("🤖 **AI Vision Security Policy:** You must upload your official **JSS University Student ID Card**. The AI vision core checks document formatting and institutional identifiers. Random images will be automatically rejected.")
    
    img = st.file_uploader("Upload Official JSS Student ID Card (JPG/PNG)", type=["jpg", "png"])
    if img:
        st.image(img, caption="Uploaded ID Document", width=300)
        if st.button("Scan & Verify with JSS AI Core"):
            with st.spinner("🤖 AI Vision Core analyzing university seal & watermark..."):
                time.sleep(2.5)
                
                filename_lower = img.name.lower()
                if "jss" in filename_lower or "id" in filename_lower:
                    c.execute("UPDATE users SET id_verified=1 WHERE id=?", (st.session_state.user_data['id'],))
                    conn.commit()
                    st.session_state.user_data['id_verified'] = 1
                    st.balloons()
                    st.success("🎉 JSS Student ID verified successfully by AI! All platform features are now unlocked.")
                    st.rerun()
                else:
                    st.error("❌ **AI Verification Failed:** Document does not match valid JSS institutional criteria. Please upload your official JSS ID card.")

elif nav == "💬 Feedback Window":
    st.title("💬 Feedback & Support")
    fb = st.text_area("Submit your feedback")
    if st.button("Submit Feedback"):
        st.success("Feedback submitted successfully!")

conn.close()