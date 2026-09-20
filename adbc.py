import json
from abc import ABC, abstractmethod
from pathlib import Path
 
import pandas as pd
import streamlit as st
 
DB = Path("school_data.json")
 
# ---------------------------------------------------------------- data layer
def load():
    data = {"Students": [], "Teachers": []}
    if DB.exists() and DB.read_text().strip():
        try:
            data.update(json.loads(DB.read_text()))
        except json.JSONDecodeError:
            DB.replace(DB.with_suffix(".broken.json"))
            st.warning("school_data.json was damaged. It was saved as school_data.broken.json and a fresh file was started.")

    # fill in any missing fields so older or hand-edited records don't crash the app
    for s in data["Students"]:
        s.setdefault("name", "Unknown")
        s.setdefault("age", "–")
        s.setdefault("roll_number", "")
        s.setdefault("email", "–")
        s.setdefault("grades", {})
    for t in data["Teachers"]:
        t.setdefault("name", "Unknown")
        t.setdefault("age", "–")
        t.setdefault("emp_id", "")
        t.setdefault("subject", "–")
        t.setdefault("email", "–")
    return data
 
 
def save(data):
    DB.write_text(json.dumps(data, indent=4))
 
 
# ------------------------------------------------------------- domain classes
class Person(ABC):
    key = ""      # top-level key in the JSON file
    id_field = "" # unique field
 
    @abstractmethod
    def get_role(self): ...
 
    @abstractmethod
    def register(self, data, **fields): ...
 
    @staticmethod
    def validate_email(email):
        return "@" in email and "." in email
 
    def find(self, data, ident):
        return next((p for p in data[self.key] if p[self.id_field] == ident), None)
 
    def _check(self, data, fields):
        if not fields["name"].strip():
            return "Enter a name."
        if not self.validate_email(fields["email"]):
            return "Enter a valid email address, like name@school.edu."
        if not fields[self.id_field].strip():
            return f"Enter a {self.id_field.replace('_', ' ')}."
        if self.find(data, fields[self.id_field]):
            return f"A {self.get_role()} with this {self.id_field.replace('_', ' ')} already exists."
        return None
 
 
class Student(Person):
    key, id_field = "Students", "roll_number"
 
    def get_role(self):
        return "student"
 
    def register(self, data, **f):
        if err := self._check(data, f):
            return False, err
        data[self.key].append({**f, "grades": {}})
        save(data)
        return True, f"{f['name']} is registered."
 
    def add_grade(self, data, roll_number, subject, marks):
        s = self.find(data, roll_number)
        if not s:
            return False, "Student not found."
        s["grades"][subject.strip()] = marks
        save(data)
        return True, f"Saved {subject} grade for {s['name']}."
 
    @staticmethod
    def average(student):
        g = student["grades"]
        return sum(g.values()) / len(g) if g else 0.0
 
 
class Teacher(Person):
    key, id_field = "Teachers", "emp_id"
 
    def get_role(self):
        return "teacher"
 
    def register(self, data, **f):
        if err := self._check(data, f):
            return False, err
        data[self.key].append(f)
        save(data)
        return True, f"{f['name']} is registered."
 
 
student, teacher = Student(), Teacher()
 
# ------------------------------------------------------------------- styling
st.set_page_config(page_title="Schoolroom", page_icon="🏫", layout="wide", initial_sidebar_state="expanded")

 
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&family=Source+Sans+3:wght@400;600&display=swap');
 
:root { --ink:#1E2A3A; --chalk:#F6F7F4; --bus:#F2B705; --sage:#4F7A6A; --slate:#5E6B7A; }
 
html, body, [class*="css"], .stMarkdown, label { font-family:'Source Sans 3', sans-serif; }
h1, h2, h3, .brand { font-family:'Bricolage Grotesque', sans-serif !important; color:var(--ink); letter-spacing:-0.01em; }
h1 { font-weight:800 !important; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; height:0; }
.block-container { padding-top:2rem; max-width:1150px; }
 
/* sidebar */
section[data-testid="stSidebar"] { background:var(--ink); }
section[data-testid="stSidebar"] * { color:#E9EDF2 !important; }
section[data-testid="stSidebar"] .brand { font-size:1.7rem; font-weight:800; margin:0.2rem 0 0.1rem; }
section[data-testid="stSidebar"] .tag { color:#9FB0C3 !important; font-size:0.9rem; margin-bottom:1.5rem; }
section[data-testid="stSidebar"] [role="radiogroup"] { gap:0.25rem; }
section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding:0.55rem 0.8rem; border-radius:8px; width:100%;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background:var(--bus); }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * { color:var(--ink) !important; font-weight:600; }
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display:none; }
 
/* metrics */
div[data-testid="stMetric"] {
    background:white; border:1px solid #E1E5EA; border-left:5px solid var(--bus);
    border-radius:10px; padding:1rem 1.2rem;
}
div[data-testid="stMetricValue"] { font-family:'Bricolage Grotesque'; font-weight:800; color:var(--ink); }
div[data-testid="stMetricLabel"] p { color:var(--slate); }
 
/* forms + buttons */
div[data-testid="stForm"] { background:white; border:1px solid #E1E5EA; border-radius:12px; padding:1.5rem; }
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background:var(--ink); color:white; border:none; border-radius:8px; padding:0.55rem 1.4rem; font-weight:600;
}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { background:var(--sage); color:white; }
button:focus-visible { outline:3px solid var(--bus) !important; outline-offset:2px; }
 
.profile { background:white; border:1px solid #E1E5EA; border-radius:12px; padding:1.4rem 1.6rem; }
.profile h3 { margin:0 0 0.2rem; }
.profile .meta { color:var(--slate); }
.grade-badge { display:inline-block; background:var(--sage); color:white; font-family:'Bricolage Grotesque';
    font-weight:800; font-size:1.6rem; border-radius:10px; padding:0.2rem 0.9rem; }
.empty { border:2px dashed #C9D0D8; border-radius:12px; padding:1.6rem; color:var(--slate); text-align:center; }
</style>
""",
    unsafe_allow_html=True,
)
 
data = load()
 
 
def flash():
    if msg := st.session_state.pop("flash", None):
        (st.success if msg[0] else st.error)(msg[1])
 
 
def done(result):
    """Show the outcome. On success, rerun so lists and counts refresh."""
    ok, message = result
    st.session_state["flash"] = (ok, message)
    if ok:
        st.rerun()
    else:
        flash()
 
 
def empty(text):
    st.markdown(f'<div class="empty">{text}</div>', unsafe_allow_html=True)
 
 
def letter(avg):
    return "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "D" if avg >= 60 else "F"
 
 
def student_label(s):
    return f"{s['roll_number']} · {s['name']}"
 
 
# ------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="brand">Schoolroom</div><div class="tag">Students, teachers and grades</div>',
                unsafe_allow_html=True)
    page = st.radio("Navigate", ["Overview", "Students", "Teachers", "Grades"], label_visibility="collapsed")
 
# ------------------------------------------------------------------ overview
if page == "Overview":
    st.title("Overview")
    students, teachers = data["Students"], data["Teachers"]
    avgs = [Student.average(s) for s in students if s["grades"]]
 
    c1, c2, c3 = st.columns(3)
    c1.metric("Students", len(students))
    c2.metric("Teachers", len(teachers))
    c3.metric("School average", f"{sum(avgs) / len(avgs):.1f}" if avgs else "–")
 
    st.subheader("Top students")
    ranked = sorted((s for s in students if s["grades"]), key=Student.average, reverse=True)[:5]
    if ranked:
        st.dataframe(
            pd.DataFrame(
                {"Roll number": s["roll_number"], "Name": s["name"], "Average": round(Student.average(s), 1),
                 "Grade": letter(Student.average(s))} for s in ranked),
            hide_index=True, use_container_width=True)
    else:
        empty("No grades yet. Add one on the Grades page to see rankings here.")
 
# ------------------------------------------------------------------ students
elif page == "Students":
    st.title("Students")
    flash()
    tab_list, tab_new, tab_profile = st.tabs(["Directory", "Register student", "Student profile"])
 
    with tab_list:
        if data["Students"]:
            q = st.text_input("Search by name or roll number", placeholder="Type to filter")
            rows = [
                {"Roll number": s["roll_number"], "Name": s["name"], "Age": s["age"], "Email": s.get("email", "–"),
                 "Average": round(Student.average(s), 1)}
                for s in data["Students"]
                if q.lower() in s["name"].lower() or q.lower() in s["roll_number"].lower()
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            empty("No students yet. Use Register student to add the first one.")
 
    with tab_new:
        with st.form("student_form", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Full name")
            roll = b.text_input("Roll number")
            age = a.number_input("Age", 3, 100, 15)
            email = b.text_input("Email")
            if st.form_submit_button("Register student"):
                done(student.register(data, name=name.strip(), age=int(age), roll_number=roll.strip(),
                                      email=email.strip()))
 
    with tab_profile:
        if not data["Students"]:
            empty("Register a student to see their profile.")
        else:
            pick = st.selectbox("Choose a student", data["Students"], format_func=student_label)
            avg = Student.average(pick)
            left, right = st.columns([3, 1])
            left.markdown(
                f'<div class="profile"><h3>{pick["name"]}</h3>'
                f'<div class="meta">Roll {pick["roll_number"]} · Age {pick["age"]} · {pick["email"]}</div></div>',
                unsafe_allow_html=True)
            right.markdown(
                f'<div class="profile"><div class="meta">Average {avg:.1f}</div>'
                f'<span class="grade-badge">{letter(avg) if pick["grades"] else "–"}</span></div>',
                unsafe_allow_html=True)
            st.write("")
            if pick["grades"]:
                st.bar_chart(pd.Series(pick["grades"], name="Marks"), color="#4F7A6A")
            else:
                empty("No grades recorded for this student yet.")
 
# ------------------------------------------------------------------ teachers
elif page == "Teachers":
    st.title("Teachers")
    flash()
    tab_list, tab_new = st.tabs(["Directory", "Register teacher"])
 
    with tab_list:
        if data["Teachers"]:
            st.dataframe(
                pd.DataFrame(
                    {"Employee ID": t["emp_id"], "Name": t["name"], "Subject": t["subject"],
                     "Age": t["age"], "Email": t["email"]} for t in data["Teachers"]),
                hide_index=True, use_container_width=True)
        else:
            empty("No teachers yet. Use Register teacher to add the first one.")
 
    with tab_new:
        with st.form("teacher_form", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Full name")
            emp = b.text_input("Employee ID")
            subject = a.text_input("Subject")
            age = b.number_input("Age", 18, 100, 30)
            email = a.text_input("Email")
            if st.form_submit_button("Register teacher"):
                done(teacher.register(data, name=name.strip(), age=int(age), emp_id=emp.strip(),
                                      subject=subject.strip(), email=email.strip()))
 
# -------------------------------------------------------------------- grades
else:
    st.title("Grades")
    flash()
    if not data["Students"]:
        empty("Register a student first, then come back to add grades.")
    else:
        with st.form("grade_form", clear_on_submit=True):
            pick = st.selectbox("Student", data["Students"], format_func=student_label)
            a, b = st.columns(2)
            subject = a.text_input("Subject")
            marks = b.number_input("Marks (out of 100)", 0.0, 100.0, 0.0, step=0.5)
            if st.form_submit_button("Save grade"):
                if not subject.strip():
                    done((False, "Enter a subject."))
                else:
                    done(student.add_grade(data, pick["roll_number"], subject, marks))
 
