import os
import re
import sqlite3
import hashlib
import secrets
import uuid
from datetime import datetime

import streamlit as st


# ============================================================
# CAMPUS CONNECT
# ============================================================

st.set_page_config(
    page_title="Campus Connect",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIG
# ============================================================

DB_PATH = "campus.db"
UPLOAD_DIR = "uploads"
ID_DIR = os.path.join(UPLOAD_DIR, "student_ids")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ID_DIR, exist_ok=True)


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0f172a;
        color: #f8fafc;
    }

    [data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #334155;
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
    }

    p, label, span, div {
        color: inherit;
    }

    .card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .green-card {
        background: #052e24;
        border: 1px solid #059669;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .danger-card {
        background: #3b1010;
        border: 1px solid #ef4444;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .badge {
        display: inline-block;
        padding: 5px 11px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        margin: 3px;
    }

    .badge-green {
        background: #064e3b;
        color: #6ee7b7 !important;
    }

    .badge-blue {
        background: #172554;
        color: #93c5fd !important;
    }

    .badge-yellow {
        background: #422006;
        color: #fde68a !important;
    }

    .badge-red {
        background: #450a0a;
        color: #fca5a5 !important;
    }

    .metric-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
    }

    .metric-number {
        color: #34d399 !important;
        font-size: 28px;
        font-weight: 800;
    }

    .metric-label {
        color: #94a3b8 !important;
        font-size: 13px;
    }

    .chat-me {
        background: #065f46;
        border-radius: 14px 14px 3px 14px;
        padding: 10px 14px;
        margin: 7px 0;
        margin-left: 20%;
    }

    .chat-them {
        background: #334155;
        border-radius: 14px 14px 14px 3px;
        padding: 10px 14px;
        margin: 7px 20% 7px 0;
    }

    .small-muted {
        color: #94a3b8 !important;
        font-size: 13px;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #f8fafc !important;
    }

    div[data-baseweb="select"] * {
        color: #f8fafc !important;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background: #111827 !important;
        border-color: #475569 !important;
    }

    .stButton button {
        border-radius: 10px;
        font-weight: 700;
    }

    .stButton button:hover {
        border-color: #10b981 !important;
        color: #10b981 !important;
    }

    [data-testid="stFileUploader"] {
        background: #1e293b;
        border-radius: 14px;
        padding: 8px;
    }

    hr {
        border-color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT DEFAULT '',
            branch TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            social_points INTEGER DEFAULT 0,
            id_verified INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 0,
            otp_code TEXT DEFAULT '',
            id_image TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            UNIQUE(sender, receiver)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            route TEXT NOT NULL,
            vehicle TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            available INTEGER NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ride_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER NOT NULL,
            passenger_username TEXT NOT NULL,
            passenger_phone TEXT DEFAULT '',
            passenger_email TEXT DEFAULT '',
            UNIQUE(ride_id, passenger_username)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS doubts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doubt_id INTEGER NOT NULL,
            responder TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS answer_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answer_id INTEGER NOT NULL,
            voter TEXT NOT NULL,
            UNIQUE(answer_id, voter)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS marketplace (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT DEFAULT '',
            contact_info TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# HELPERS
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def get_user(username):
    conn = get_db()
    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()
    conn.close()
    return row


def add_points(username, amount):
    conn = get_db()
    conn.execute(
        """
        UPDATE users
        SET social_points = social_points + ?
        WHERE username = ?
        """,
        (amount, username),
    )
    conn.commit()
    conn.close()


def refresh_session_user():
    username = st.session_state.get("username")

    if not username:
        return

    user = get_user(username)

    if user:
        st.session_state["id_verified"] = int(
            user["id_verified"] or 0
        )
        st.session_state["is_verified"] = int(
            user["is_verified"] or 0
        )
        st.session_state["social_points"] = int(
            user["social_points"] or 0
        )


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# ============================================================
# STUDENT ID VERIFICATION
# ============================================================

def verify_student_id(username, uploaded_file):
    """
    Current verification mode:

    A valid uploaded PNG/JPG/JPEG student-ID image
    immediately verifies the account.

    The image remains private and is never displayed
    publicly.
    """

    if uploaded_file is None:
        return False, "Please upload your Student ID."

    try:
        allowed = {
            "image/png",
            "image/jpeg",
            "image/jpg",
        }

        if uploaded_file.type not in allowed:
            return False, "Only PNG, JPG or JPEG images are allowed."

        image_bytes = uploaded_file.getvalue()

        if not image_bytes:
            return False, "The uploaded image is empty."

        if len(image_bytes) > 10 * 1024 * 1024:
            return False, "Maximum image size is 10 MB."

        safe_username = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            username,
        )

        extension = ".png"

        if uploaded_file.type in {
            "image/jpeg",
            "image/jpg",
        }:
            extension = ".jpg"

        filename = (
            f"{safe_username}_"
            f"{uuid.uuid4().hex[:12]}"
            f"{extension}"
        )

        image_path = os.path.join(
            ID_DIR,
            filename,
        )

        with open(image_path, "wb") as file:
            file.write(image_bytes)

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET
                id_verified = 1,
                id_image = ?
            WHERE username = ?
            """,
            (
                image_path,
                username,
            ),
        )

        if cursor.rowcount != 1:
            conn.rollback()
            conn.close()

            return False, "User account was not found."

        # THIS IS THE IMPORTANT FIX.
        conn.commit()

        check = conn.execute(
            """
            SELECT id_verified
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        conn.close()

        if not check:
            return False, "Could not confirm verification."

        if int(check["id_verified"]) != 1:
            return False, "Verification was not saved."

        # Immediately update Streamlit state.
        st.session_state["id_verified"] = 1

        return True, "Student ID verified successfully! 🎉"

    except sqlite3.Error as e:
        return False, f"Database error: {e}"

    except Exception as e:
        return False, f"Verification error: {e}"


# ============================================================
# AUTHENTICATION
# ============================================================

def signup_page():
    st.title("🎓 Create your Campus Connect account")
    st.caption("Connect. Learn. Ride. Trade.")

    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Campus Email")
        phone = st.text_input("Phone")
        branch = st.text_input("Branch / Department")
        bio = st.text_area("Short Bio")
        password = st.text_input(
            "Password",
            type="password",
        )
        confirm = st.text_input(
            "Confirm Password",
            type="password",
        )

        submit = st.form_submit_button(
            "Create Account",
            use_container_width=True,
        )

    if submit:

        username = username.strip()
        email = email.strip().lower()

        if not username or not email or not password:
            st.error("Please fill all required fields.")
            return

        if password != confirm:
            st.error("Passwords do not match.")
            return

        if len(password) < 6:
            st.error("Password must contain at least 6 characters.")
            return

        otp = generate_otp()

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password,
                    phone,
                    branch,
                    bio,
                    otp_code
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    hash_password(password),
                    phone,
                    branch,
                    bio,
                    otp,
                ),
            )

            conn.commit()

            st.success(
                "Account created! Verify your account using the OTP below."
            )

            st.info(
                f"Developer OTP: **{otp}**"
            )

        except sqlite3.IntegrityError:
            st.error(
                "Username or email already exists."
            )

        finally:
            conn.close()


def login_page():
    st.title("🔐 Welcome back")

    with st.form("login_form"):
        username = st.text_input("Username or Email")
        password = st.text_input(
            "Password",
            type="password",
        )

        submit = st.form_submit_button(
            "Login",
            use_container_width=True,
        )

    if submit:

        user = None

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
               OR email = ?
            """,
            (
                username.strip(),
                username.strip().lower(),
            ),
        ).fetchone()

        conn.close()

        if not user:
            st.error("Incorrect username/email or password.")
            return

        if user["password"] != hash_password(password):
            st.error("Incorrect username/email or password.")
            return

        if int(user["is_verified"] or 0) != 1:
            st.warning(
                "Your account is not verified yet."
            )
            return

        st.session_state["logged_in"] = True
        st.session_state["username"] = user["username"]

        refresh_session_user()

        st.rerun()


def verify_account_page():
    st.title("✉️ Verify Account")

    email = st.text_input(
        "Campus Email",
        key="verify_email",
    )

    otp = st.text_input(
        "6-digit OTP",
        key="verify_otp",
    )

    if st.button(
        "Verify Account",
        use_container_width=True,
    ):

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email.strip().lower(),),
        ).fetchone()

        if not user:
            conn.close()
            st.error("No account found with that email.")
            return

        if user["otp_code"] != otp.strip():
            conn.close()
            st.error("Incorrect OTP.")
            return

        conn.execute(
            """
            UPDATE users
            SET
                is_verified = 1,
                otp_code = ''
            WHERE email = ?
            """,
            (email.strip().lower(),),
        )

        conn.commit()
        conn.close()

        st.success(
            "Account verified! You can now log in."
        )


def forgot_password_page():
    st.title("🔑 Forgot Password")

    email = st.text_input(
        "Account Email",
        key="forgot_email",
    )

    if st.button(
        "Generate Reset OTP",
        use_container_width=True,
    ):

        conn = get_db()

        user = conn.execute(
            """
            SELECT username
            FROM users
            WHERE email = ?
            """,
            (email.strip().lower(),),
        ).fetchone()

        if not user:
            conn.close()
            st.error("No account found.")
            return

        otp = generate_otp()

        conn.execute(
            """
            UPDATE users
            SET otp_code = ?
            WHERE email = ?
            """,
            (
                otp,
                email.strip().lower(),
            ),
        )

        conn.commit()
        conn.close()

        st.session_state["reset_email"] = email.strip().lower()

        st.info(
            f"Developer reset OTP: **{otp}**"
        )

    st.divider()

    reset_otp = st.text_input(
        "Reset OTP",
        key="reset_otp",
    )

    new_password = st.text_input(
        "New Password",
        type="password",
        key="new_password",
    )

    if st.button(
        "Reset Password",
        use_container_width=True,
    ):

        reset_email = st.session_state.get(
            "reset_email"
        )

        if not reset_email:
            st.error(
                "Generate a reset OTP first."
            )
            return

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (reset_email,),
        ).fetchone()

        if not user:
            conn.close()
            st.error("Account not found.")
            return

        if user["otp_code"] != reset_otp.strip():
            conn.close()
            st.error("Incorrect reset OTP.")
            return

        if len(new_password) < 6:
            conn.close()
            st.error(
                "Password must contain at least 6 characters."
            )
            return

        conn.execute(
            """
            UPDATE users
            SET
                password = ?,
                otp_code = ''
            WHERE email = ?
            """,
            (
                hash_password(new_password),
                reset_email,
            ),
        )

        conn.commit()
        conn.close()

        st.success(
            "Password reset successfully. You can now log in."
        )


def auth_page():
    st.title("🎓 Campus Connect")

    tabs = st.tabs(
        [
            "🔐 Login",
            "📝 Sign Up",
            "✉️ Verify Account",
            "🔑 Forgot Password",
        ]
    )

    with tabs[0]:
        login_page()

    with tabs[1]:
        signup_page()

    with tabs[2]:
        verify_account_page()

    with tabs[3]:
        forgot_password_page()


# ============================================================
# PROFILE
# ============================================================

def profile():
    refresh_session_user()

    user = get_user(
        st.session_state["username"]
    )

    if not user:
        st.error("User account not found.")
        return

    st.title("🏠 Profile Dashboard")

    col1, col2 = st.columns(
        [2, 1]
    )

    with col1:

        st.markdown(
            f"""
            <div class="card">
                <h2>👤 {user["username"]}</h2>
                <p>📧 {user["email"]}</p>
                <p>📱 {user["phone"] or "Not provided"}</p>
                <p>🎓 {user["branch"] or "Not provided"}</p>
                <p>{user["bio"] or "No bio yet."}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:

        verified = int(
            user["id_verified"] or 0
        )

        if verified:
            st.success("✅ Verified Student")
        else:
            st.error("❌ Student ID Not Verified")

        st.metric(
            "🏆 Social Points",
            user["social_points"],
        )


# ============================================================
# ID SETTINGS
# ============================================================

def id_verification():
    refresh_session_user()

    st.title("⚙️ Settings & Student ID")

    if st.session_state.get(
        "id_verified",
        0,
    ):

        st.markdown(
            """
            <div class="green-card">
                <h2>✅ Student ID Verified</h2>
                <p>Your account has access to ID-gated Campus Connect features.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    st.markdown(
        """
        <div class="card">
            <h3>🎓 Verify your Student ID</h3>
            <p>
                Upload a clear PNG or JPG image of your university
                student ID. The uploaded ID remains private.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Student ID Image",
        type=[
            "png",
            "jpg",
            "jpeg",
        ],
        key="student_id",
    )

    if uploaded:

        st.image(
            uploaded,
            caption="Preview",
            width=400,
        )

        if st.button(
            "✅ Verify Student ID",
            use_container_width=True,
        ):

            success, message = verify_student_id(
                st.session_state["username"],
                uploaded,
            )

            if success:
                st.success(message)

                refresh_session_user()

                st.rerun()

            else:
                st.error(message)


# ============================================================
# CARPOOL
# ============================================================

def carpool():
    refresh_session_user()

    st.title("🚗 Campus Carpool")

    if not st.session_state.get(
        "id_verified",
        0,
    ):
        st.warning(
            "🔒 Student ID verification is required to use carpooling."
        )
        st.info(
            "Go to ⚙️ Settings & ID Verification first."
        )
        return

    tabs = st.tabs(
        [
            "🚗 Available Rides",
            "➕ Host a Ride",
            "📋 My Hosted Rides",
        ]
    )

    with tabs[0]:

        search = st.text_input(
            "Search routes",
            placeholder="Example: Campus → City Centre",
        )

        conn = get_db()

        if search.strip():
            rides = conn.execute(
                """
                SELECT *
                FROM rides
                WHERE status = 'Active'
                AND available > 0
                AND route LIKE ?
                ORDER BY id DESC
                """,
                (f"%{search.strip()}%",),
            ).fetchall()
        else:
            rides = conn.execute(
                """
                SELECT *
                FROM rides
                WHERE status = 'Active'
                AND available > 0
                ORDER BY id DESC
                """
            ).fetchall()

        conn.close()

        if not rides:
            st.info("No rides available.")

        for ride in rides:

            st.markdown(
                f"""
                <div class="card">
                    <h3>🚗 {ride["route"]}</h3>
                    <p>👤 Driver: {ride["driver"]}</p>
                    <p>🚘 Vehicle: {ride["vehicle"]}</p>
                    <p>🕐 Departure: {ride["time"]}</p>
                    <span class="badge badge-green">
                        🪑 {ride["available"]} seats
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if ride["driver"] == st.session_state["username"]:
                st.caption(
                    "You cannot book your own ride."
                )
                continue

            if st.button(
                "🎟️ Book Seat",
                key=f"book_{ride['id']}",
            ):

                conn = get_db()

                try:

                    existing = conn.execute(
                        """
                        SELECT id
                        FROM ride_bookings
                        WHERE ride_id = ?
                        AND passenger_username = ?
                        """,
                        (
                            ride["id"],
                            st.session_state["username"],
                        ),
                    ).fetchone()

                    if existing:
                        st.warning(
                            "You already booked this ride."
                        )
                        conn.close()
                        continue

                    current = conn.execute(
                        """
                        SELECT available
                        FROM rides
                        WHERE id = ?
                        AND status = 'Active'
                        """,
                        (ride["id"],),
                    ).fetchone()

                    if not current or current["available"] <= 0:
                        st.error("No seats remaining.")
                        conn.close()
                        continue

                    user = get_user(
                        st.session_state["username"]
                    )

                    conn.execute(
                        """
                        INSERT INTO ride_bookings (
                            ride_id,
                            passenger_username,
                            passenger_phone,
                            passenger_email
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            ride["id"],
                            user["username"],
                            user["phone"],
                            user["email"],
                        ),
                    )

                    conn.execute(
                        """
                        UPDATE rides
                        SET available = available - 1
                        WHERE id = ?
                        AND available > 0
                        """,
                        (ride["id"],),
                    )

                    conn.commit()
                    conn.close()

                    add_points(
                        st.session_state["username"],
                        15,
                    )

                    st.success(
                        "Seat booked! +15 Social Points 🏆"
                    )

                    st.rerun()

                except sqlite3.IntegrityError:
                    conn.rollback()
                    conn.close()

                    st.warning(
                        "You already booked this ride."
                    )

                except Exception as e:
                    conn.rollback()
                    conn.close()
                    st.error(str(e))

    with tabs[1]:

        with st.form("host_ride"):

            route = st.text_input(
                "Route"
            )

            vehicle = st.selectbox(
                "Vehicle",
                [
                    "4-Seater Sedan",
                    "7-Seater SUV",
                    "2-Seater Bike",
                ],
            )

            departure = st.text_input(
                "Departure Time",
                placeholder="6:30 PM",
            )

            seats = st.number_input(
                "Total Seats",
                min_value=1,
                max_value=20,
                value=3,
            )

            submit = st.form_submit_button(
                "Publish Ride",
                use_container_width=True,
            )

        if submit:

            if not route.strip():
                st.error("Enter a route.")
                return

            user = get_user(
                st.session_state["username"]
            )

            conn = get_db()

            conn.execute(
                """
                INSERT INTO rides (
                    driver,
                    email,
                    phone,
                    route,
                    vehicle,
                    capacity,
                    available,
                    time,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')
                """,
                (
                    user["username"],
                    user["email"],
                    user["phone"],
                    route.strip(),
                    vehicle,
                    seats,
                    seats,
                    departure.strip(),
                ),
            )

            conn.commit()
            conn.close()

            add_points(
                st.session_state["username"],
                20,
            )

            st.success(
                "Ride published! +20 Social Points 🏆"
            )

            st.rerun()

    with tabs[2]:

        conn = get_db()

        rides = conn.execute(
            """
            SELECT *
            FROM rides
            WHERE driver = ?
            ORDER BY id DESC
            """,
            (st.session_state["username"],),
        ).fetchall()

        conn.close()

        if not rides:
            st.info("You have not hosted any rides.")

        for ride in rides:

            st.markdown(
                f"""
                <div class="card">
                    <h3>{ride["route"]}</h3>
                    <p>🚘 {ride["vehicle"]}</p>
                    <p>🕐 {ride["time"]}</p>
                    <p>🪑 {ride["available"]}/{ride["capacity"]} seats available</p>
                    <p>Status: {ride["status"]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if ride["status"] == "Active":

                if st.button(
                    "❌ Cancel Ride",
                    key=f"cancel_{ride['id']}",
                ):

                    conn = get_db()

                    conn.execute(
                        """
                        UPDATE rides
                        SET status = 'Cancelled'
                        WHERE id = ?
                        AND driver = ?
                        """,
                        (
                            ride["id"],
                            st.session_state["username"],
                        ),
                    )

                    conn.commit()
                    conn.close()

                    st.success("Ride cancelled.")
                    st.rerun()


# ============================================================
# DOUBTS
# ============================================================

def doubts():
    st.title("❓ Campus Doubts")

    tabs = st.tabs(
        [
            "📚 Browse & Answer",
            "➕ Ask Question",
        ]
    )

    with tabs[0]:

        conn = get_db()

        questions = conn.execute(
            """
            SELECT *
            FROM doubts
            ORDER BY created_at DESC
            """
        ).fetchall()

        conn.close()

        if not questions:
            st.info(
                "No questions yet. Be the first to ask!"
            )

        for doubt in questions:

            st.markdown(
                f"""
                <div class="card">
                    <span class="badge badge-blue">
                        {doubt["subject"]}
                    </span>
                    <h3>{doubt["question"]}</h3>
                    <p class="small-muted">
                        Asked by {doubt["author"]}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if doubt["author"] == st.session_state["username"]:

                if st.button(
                    "🗑️ Delete Question",
                    key=f"delete_doubt_{doubt['id']}",
                ):

                    conn = get_db()

                    conn.execute(
                        """
                        DELETE FROM answers
                        WHERE doubt_id = ?
                        """,
                        (doubt["id"],),
                    )

                    conn.execute(
                        """
                        DELETE FROM doubts
                        WHERE id = ?
                        AND author = ?
                        """,
                        (
                            doubt["id"],
                            st.session_state["username"],
                        ),
                    )

                    conn.commit()
                    conn.close()

                    st.success("Question deleted.")
                    st.rerun()

            with st.expander("💬 Answers"):

                conn = get_db()

                answers = conn.execute(
                    """
                    SELECT *
                    FROM answers
                    WHERE doubt_id = ?
                    ORDER BY votes DESC, id ASC
                    """,
                    (doubt["id"],),
                ).fetchall()

                conn.close()

                for answer in answers:

                    st.markdown(
                        f"""
                        <div class="card">
                            <b>👤 {answer["responder"]}</b>
                            <p>{answer["answer_text"]}</p>
                            <span class="badge badge-green">
                                👍 {answer["votes"]}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "👍 Upvote",
                            key=f"vote_{answer['id']}",
                        ):

                            if (
                                answer["responder"]
                                == st.session_state["username"]
                            ):
                                st.warning(
                                    "You cannot vote for your own answer."
                                )
                                continue

                            conn = get_db()

                            try:

                                conn.execute(
                                    """
                                    INSERT INTO answer_votes (
                                        answer_id,
                                        voter
                                    )
                                    VALUES (?, ?)
                                    """,
                                    (
                                        answer["id"],
                                        st.session_state["username"],
                                    ),
                                )

                                conn.execute(
                                    """
                                    UPDATE answers
                                    SET votes = votes + 1
                                    WHERE id = ?
                                    """,
                                    (answer["id"],),
                                )

                                conn.commit()
                                conn.close()

                                add_points(
                                    answer["responder"],
                                    5,
                                )

                                st.success(
                                    "Upvoted! +5 points to answer author."
                                )

                                st.rerun()

                            except sqlite3.IntegrityError:

                                conn.rollback()
                                conn.close()

                                st.warning(
                                    "You already voted for this answer."
                                )

                    with col2:

                        if answer["responder"] == st.session_state["username"]:

                            if st.button(
                                "🗑️ Delete Answer",
                                key=f"delete_answer_{answer['id']}",
                            ):

                                conn = get_db()

                                conn.execute(
                                    """
                                    DELETE FROM answers
                                    WHERE id = ?
                                    AND responder = ?
                                    """,
                                    (
                                        answer["id"],
                                        st.session_state["username"],
                                    ),
                                )

                                conn.commit()
                                conn.close()

                                st.rerun()

                answer_text = st.text_area(
                    "Write an answer",
                    key=f"answer_box_{doubt['id']}",
                )

                if st.button(
                    "Post Answer",
                    key=f"answer_btn_{doubt['id']}",
                ):

                    if not answer_text.strip():
                        st.warning("Write an answer first.")
                        continue

                    conn = get_db()

                    conn.execute(
                        """
                        INSERT INTO answers (
                            doubt_id,
                            responder,
                            answer_text
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            doubt["id"],
                            st.session_state["username"],
                            answer_text.strip(),
                        ),
                    )

                    conn.commit()
                    conn.close()

                    add_points(
                        st.session_state["username"],
                        10,
                    )

                    st.success(
                        "Answer posted! +10 Social Points 🏆"
                    )

                    st.rerun()

    with tabs[1]:

        with st.form("new_doubt"):

            subject = st.selectbox(
                "Subject",
                [
                    "Computer Science",
                    "Math",
                    "Physics",
                    "Electrical",
                    "General Campus",
                ],
            )

            question = st.text_area(
                "Your Question"
            )

            submit = st.form_submit_button(
                "Ask Question",
                use_container_width=True,
            )

        if submit:

            if not question.strip():
                st.error("Write your question.")
                return

            conn = get_db()

            conn.execute(
                """
                INSERT INTO doubts (
                    author,
                    subject,
                    question
                )
                VALUES (?, ?, ?)
                """,
                (
                    st.session_state["username"],
                    subject,
                    question.strip(),
                ),
            )

            conn.commit()
            conn.close()

            st.success("Question posted.")
            st.rerun()


# ============================================================
# MARKETPLACE
# ============================================================

def marketplace():
    st.title("🛍️ Peer Marketplace")

    tabs = st.tabs(
        [
            "🛒 Browse Listings",
            "➕ Post Item",
        ]
    )

    with tabs[0]:

        search = st.text_input(
            "Search listings",
            placeholder="Textbooks, notes, laptop..."
        )

        conn = get_db()

        if search.strip():

            listings = conn.execute(
                """
                SELECT *
                FROM marketplace
                WHERE title LIKE ?
                   OR description LIKE ?
                   OR category LIKE ?
                ORDER BY created_at DESC
                """,
                (
                    f"%{search.strip()}%",
                    f"%{search.strip()}%",
                    f"%{search.strip()}%",
                ),
            ).fetchall()

        else:

            listings = conn.execute(
                """
                SELECT *
                FROM marketplace
                ORDER BY created_at DESC
                """
            ).fetchall()

        conn.close()

        if not listings:
            st.info("No listings found.")

        for item in listings:

            st.markdown(
                f"""
                <div class="card">
                    <span class="badge badge-yellow">
                        {item["category"]}
                    </span>

                    <h3>{item["title"]}</h3>

                    <h2 style="color:#34d399;">
                        ₹{item["price"]:.2f}
                    </h2>

                    <p>{item["description"]}</p>

                    <p>
                        👤 Seller:
                        <b>{item["seller"]}</b>
                    </p>

                    <p>
                        📞 Contact:
                        {item["contact_info"]}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if item["seller"] == st.session_state["username"]:

                if st.button(
                    "🗑️ Delete Listing",
                    key=f"delete_listing_{item['id']}",
                ):

                    conn = get_db()

                    conn.execute(
                        """
                        DELETE FROM marketplace
                        WHERE id = ?
                        AND seller = ?
                        """,
                        (
                            item["id"],
                            st.session_state["username"],
                        ),
                    )

                    conn.commit()
                    conn.close()

                    st.success("Listing deleted.")
                    st.rerun()

    with tabs[1]:

        with st.form("marketplace_form"):

            title = st.text_input(
                "Title"
            )

            category = st.selectbox(
                "Category",
                [
                    "Textbook",
                    "Study Notes",
                    "Electronics",
                    "Furniture",
                    "Other",
                ],
            )

            price = st.number_input(
                "Price",
                min_value=0.0,
                value=0.0,
                step=50.0,
            )

            description = st.text_area(
                "Description"
            )

            contact = st.text_input(
                "Contact information"
            )

            submit = st.form_submit_button(
                "Publish Listing",
                use_container_width=True,
            )

        if submit:

            if not title.strip():
                st.error("Enter a title.")
                return

            conn = get_db()

            conn.execute(
                """
                INSERT INTO marketplace (
                    seller,
                    title,
                    category,
                    price,
                    description,
                    contact_info
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    st.session_state["username"],
                    title.strip(),
                    category,
                    price,
                    description.strip(),
                    contact.strip(),
                ),
            )

            conn.commit()
            conn.close()

            st.success("Listing published.")
            st.rerun()


# ============================================================
# FRIENDS + MESSAGES
# ============================================================

def friends():
    st.title("💬 Friends & Direct Messaging")

    tabs = st.tabs(
        [
            "💬 Direct Chat",
            "👥 Friend Requests",
        ]
    )

    with tabs[0]:

        conn = get_db()

        friendships = conn.execute(
            """
            SELECT *
            FROM friendships
            WHERE status = 'Accepted'
            AND (
                sender = ?
                OR receiver = ?
            )
            """,
            (
                st.session_state["username"],
                st.session_state["username"],
            ),
        ).fetchall()

        conn.close()

        friend_names = []

        for friendship in friendships:

            if friendship["sender"] == st.session_state["username"]:
                friend_names.append(
                    friendship["receiver"]
                )
            else:
                friend_names.append(
                    friendship["sender"]
                )

        if not friend_names:
            st.info(
                "Add some friends to start chatting."
            )
        else:

            friend = st.selectbox(
                "Choose friend",
                friend_names,
            )

            conn = get_db()

            messages = conn.execute(
                """
                SELECT *
                FROM messages
                WHERE
                    (
                        sender = ?
                        AND receiver = ?
                    )
                    OR
                    (
                        sender = ?
                        AND receiver = ?
                    )
                ORDER BY timestamp ASC
                """,
                (
                    st.session_state["username"],
                    friend,
                    friend,
                    st.session_state["username"],
                ),
            ).fetchall()

            conn.close()

            for message in messages:

                if message["sender"] == st.session_state["username"]:

                    st.markdown(
                        f"""
                        <div class="chat-me">
                            {message["message"]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:

                    st.markdown(
                        f"""
                        <div class="chat-them">
                            {message["message"]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            text = st.text_input(
                "Message",
                key=f"message_{friend}",
            )

            if st.button(
                "Send",
                use_container_width=True,
            ):

                if text.strip():

                    conn = get_db()

                    conn.execute(
                        """
                        INSERT INTO messages (
                            sender,
                            receiver,
                            message
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            st.session_state["username"],
                            friend,
                            text.strip(),
                        ),
                    )

                    conn.commit()
                    conn.close()

                    st.rerun()

    with tabs[1]:

        st.subheader("➕ Send Friend Request")

        target = st.text_input(
            "Username",
            key="friend_target",
        )

        if st.button(
            "Send Request",
            use_container_width=True,
        ):

            target = target.strip()

            if not target:
                st.error("Enter a username.")
            elif target == st.session_state["username"]:
                st.error("You cannot add yourself.")
            elif not get_user(target):
                st.error("User not found.")
            else:

                conn = get_db()

                try:

                    conn.execute(
                        """
                        INSERT INTO friendships (
                            sender,
                            receiver,
                            status
                        )
                        VALUES (?, ?, 'Pending')
                        """,
                        (
                            st.session_state["username"],
                            target,
                        ),
                    )

                    conn.commit()
                    st.success("Friend request sent.")

                except sqlite3.IntegrityError:

                    st.warning(
                        "A relationship already exists."
                    )

                finally:
                    conn.close()

        st.divider()

        st.subheader("📥 Incoming Requests")

        conn = get_db()

        requests = conn.execute(
            """
            SELECT *
            FROM friendships
            WHERE receiver = ?
            AND status = 'Pending'
            """,
            (st.session_state["username"],),
        ).fetchall()

        conn.close()

        for request in requests:

            st.markdown(
                f"""
                <div class="card">
                    👤 <b>{request["sender"]}</b>
                    wants to be your friend.
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "✅ Accept",
                key=f"accept_{request['id']}",
            ):

                conn = get_db()

                conn.execute(
                    """
                    UPDATE friendships
                    SET status = 'Accepted'
                    WHERE id = ?
                    AND receiver = ?
                    """,
                    (
                        request["id"],
                        st.session_state["username"],
                    ),
                )

                conn.commit()
                conn.close()

                st.success("Friend request accepted.")
                st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():
    refresh_session_user()

    user = get_user(
        st.session_state["username"]
    )

    st.sidebar.markdown(
        "# 🎓 Campus Connect"
    )

    st.sidebar.divider()

    st.sidebar.markdown(
        f"### 👤 {user['username']}"
    )

    st.sidebar.caption(
        user["email"]
    )

    if user["id_verified"]:

        st.sidebar.success(
            "✅ Verified Student"
        )

    else:

        st.sidebar.error(
            "❌ Not Verified"
        )

    st.sidebar.metric(
        "🏆 Social Points",
        user["social_points"],
    )

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Profile",
            "🚗 Carpool",
            "❓ Doubts",
            "🛍️ Marketplace",
            "💬 Friends & Chat",
            "⚙️ Settings & ID",
        ],
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True,
    ):
        logout()

    return page


# ============================================================
# MAIN APP
# ============================================================

def run_app():

    if not st.session_state.get(
        "logged_in",
        False,
    ):

        auth_page()
        return

    # Refresh database-backed state on every rerun.
    refresh_session_user()

    page = sidebar()

    st.markdown(
        """
        <div style="
            text-align:right;
            color:#94a3b8;
            margin-bottom:15px;
        ">
            🏆 Social Points:
            <b style="color:#34d399;">
                """
        + str(
            st.session_state.get(
                "social_points",
                0,
            )
        )
        + """
            </b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if page == "🏠 Profile":
        profile()

    elif page == "🚗 Carpool":
        carpool()

    elif page == "❓ Doubts":
        doubts()

    elif page == "🛍️ Marketplace":
        marketplace()

    elif page == "💬 Friends & Chat":
        friends()

    elif page == "⚙️ Settings & ID":
        id_verification()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    run_app()
