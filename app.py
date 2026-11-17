import sqlite3
import pandas as pd
import streamlit as st

DB = "students.db"
COURSES = ["B.Tech", "BCA", "BSc", "MCA", "MBA"]

st.set_page_config(page_title="Student Records", page_icon="🎓", layout="wide")

# ---------- STYLES ----------
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1100px;}

    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        padding: 1.6rem 2rem; border-radius: 16px; color: white; margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.25);
    }
    .hero h1 {margin: 0; font-size: 1.9rem; font-weight: 700; color: white;}
    .hero p {margin: .3rem 0 0; opacity: .85;}

    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,.15);
        padding: 1rem 1.2rem; border-radius: 12px;
    }
    [data-testid="stMetricLabel"] p {font-size: .85rem; opacity: .7;}

    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
    }
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px; font-weight: 600; padding: .5rem 1.4rem;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    }
    section[data-testid="stSidebar"] * {color: #e0e7ff !important;}
    .section-title {font-size: 1.25rem; font-weight: 650; margin: .5rem 0 1rem;}
</style>
""", unsafe_allow_html=True)

# ---------- DB ----------
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            course TEXT,
            age INTEGER
        )
    """)
    return conn

conn = get_conn()

def fetch_df():
    return pd.read_sql_query("SELECT * FROM students ORDER BY id", conn)

def fetch_one(student_id):
    return conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()

# Show any message queued before a rerun
if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"), icon="✅")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("## 🎓 Student Hub")
    st.caption("Manage student records")
    st.divider()
    menu = st.radio(
        "Navigate",
        ["📋 View Students", "➕ Add Student", "✏️ Update Student", "🗑️ Delete Student"],
        label_visibility="collapsed",
    )

# ---------- HEADER ----------
st.markdown("""
<div class="hero">
    <h1>Student Record Management</h1>
    <p>Add, browse, edit and remove student records in one place.</p>
</div>
""", unsafe_allow_html=True)

df = fetch_df()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Students", len(df))
c2.metric("Courses", df["course"].nunique() if not df.empty else 0)
c3.metric("Average Age", f"{df['age'].mean():.1f}" if not df.empty else "—")
c4.metric("Top Course", df["course"].mode()[0] if not df.empty else "—")
st.write("")

# ---------- READ ----------
if menu == "📋 View Students":
    st.markdown('<div class="section-title">All Students</div>', unsafe_allow_html=True)

    f1, f2 = st.columns([3, 1])
    search = f1.text_input("Search", placeholder="🔍  Search by name or roll no",
                           label_visibility="collapsed")
    course_filter = f2.selectbox("Course", ["All courses"] + COURSES,
                                 label_visibility="collapsed")

    view = df.copy()
    if search:
        s = search.lower()
        view = view[view["name"].str.lower().str.contains(s) |
                    view["roll_no"].str.lower().str.contains(s)]
    if course_filter != "All courses":
        view = view[view["course"] == course_filter]

    if view.empty:
        st.info("No records found.")
    else:
        st.dataframe(
            view,
            hide_index=True,
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "roll_no": "Roll No",
                "name": "Name",
                "email": st.column_config.TextColumn("Email"),
                "course": "Course",
                "age": st.column_config.NumberColumn("Age", width="small"),
            },
        )
        st.caption(f"Showing {len(view)} of {len(df)} student(s)")

# ---------- CREATE ----------
elif menu == "➕ Add Student":
    st.markdown('<div class="section-title">Add New Student</div>', unsafe_allow_html=True)
    with st.form("add_form", clear_on_submit=True):
        a, b = st.columns(2)
        roll_no = a.text_input("Roll No *", placeholder="e.g. 21CS042")
        name = b.text_input("Full Name *", placeholder="e.g. Priya Sharma")
        email = a.text_input("Email", placeholder="name@example.com")
        course = b.selectbox("Course", COURSES)
        age = a.number_input("Age", min_value=15, max_value=60, value=18)
        st.write("")
        submitted = st.form_submit_button("Add Student", type="primary", use_container_width=True)

    if submitted:
        if not roll_no.strip() or not name.strip():
            st.error("Roll No and Name are required.")
        else:
            try:
                conn.execute(
                    "INSERT INTO students (roll_no, name, email, course, age) VALUES (?, ?, ?, ?, ?)",
                    (roll_no.strip(), name.strip(), email.strip(), course, age),
                )
                conn.commit()
                st.session_state.flash = f"Student '{name}' added!"
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("That Roll No already exists.")

# ---------- UPDATE ----------
elif menu == "✏️ Update Student":
    st.markdown('<div class="section-title">Update Student</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No students to update.")
    else:
        options = {f"{r.roll_no} — {r.name}": r.id for r in df.itertuples()}
        selected = st.selectbox("Select student", list(options.keys()))
        s = fetch_one(options[selected])

        with st.form("update_form"):
            a, b = st.columns(2)
            roll_no = a.text_input("Roll No", s[1])
            name = b.text_input("Full Name", s[2])
            email = a.text_input("Email", s[3] or "")
            course = b.selectbox("Course", COURSES,
                                 index=COURSES.index(s[4]) if s[4] in COURSES else 0)
            age = a.number_input("Age", min_value=15, max_value=60, value=s[5] or 18)
            st.write("")
            updated = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

        if updated:
            try:
                conn.execute(
                    "UPDATE students SET roll_no=?, name=?, email=?, course=?, age=? WHERE id=?",
                    (roll_no.strip(), name.strip(), email.strip(), course, age, s[0]),
                )
                conn.commit()
                st.session_state.flash = "Student updated!"
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("That Roll No already exists.")

# ---------- DELETE ----------
elif menu == "🗑️ Delete Student":
    st.markdown('<div class="section-title">Delete Student</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No students to delete.")
    else:
        options = {f"{r.roll_no} — {r.name}": r.id for r in df.itertuples()}
        with st.container(border=True):
            selected = st.selectbox("Select student", list(options.keys()))
            s = fetch_one(options[selected])
            st.markdown(f"**{s[2]}** · {s[4]} · {s[3] or 'no email'} · Age {s[5]}")
            st.warning("This action can't be undone.", icon="⚠️")
            confirm = st.checkbox("I confirm I want to delete this student")
            if st.button("Delete Student", type="primary", disabled=not confirm):
                conn.execute("DELETE FROM students WHERE id = ?", (options[selected],))
                conn.commit()
                st.session_state.flash = f"Deleted '{selected}'"
                st.rerun()