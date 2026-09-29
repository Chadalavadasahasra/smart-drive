from flask import Flask, render_template, request, redirect, send_from_directory, session
import os
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document

app = Flask(__name__)

app.secret_key = "smart-drive-secret-key"

STORAGE_FOLDER = "storage"
TRASH_FOLDER = os.path.join(STORAGE_FOLDER, "trash")
RESUME_FOLDER = os.path.join(STORAGE_FOLDER, "resumes")

os.makedirs(STORAGE_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        # For now, any username beginning with cse is allowed
        if username.startswith("cse") and password:

            session["username"] = username
            return redirect("/")

        return render_template(
            "login.html",
            error="Only CSE users can log in. Username must start with 'cse'."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ---------------------------------------------------
# LOGIN CHECK
# ---------------------------------------------------

@app.before_request
def require_login():

    allowed_routes = ["login", "static"]

    if request.endpoint not in allowed_routes:
        if "username" not in session:
            return redirect("/login")


# ---------------------------------------------------
# HOME / MY DRIVE
# ---------------------------------------------------

@app.route("/")
def home():

    files = []

    for filename in os.listdir(STORAGE_FOLDER):

        filepath = os.path.join(STORAGE_FOLDER, filename)

        if os.path.isfile(filepath):

            files.append({
                "name": filename,
                "starred": filename.startswith("STARRED_")
            })

    return render_template(
        "index.html",
        files=files,
        page="My Drive",
        username=session.get("username")
    )


# ---------------------------------------------------
# UPLOAD FILE
# ---------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files.get("file")

    if file and file.filename:

        filename = secure_filename(file.filename)

        file.save(
            os.path.join(STORAGE_FOLDER, filename)
        )

    return redirect("/")


# ---------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------

@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        STORAGE_FOLDER,
        filename,
        as_attachment=True
    )


# ---------------------------------------------------
# MOVE TO TRASH
# ---------------------------------------------------

@app.route("/delete/<filename>")
def delete(filename):

    source = os.path.join(STORAGE_FOLDER, filename)
    destination = os.path.join(TRASH_FOLDER, filename)

    if os.path.exists(source):

        os.rename(source, destination)

    return redirect("/")


# ---------------------------------------------------
# TRASH
# ---------------------------------------------------

@app.route("/trash")
def trash():

    files = os.listdir(TRASH_FOLDER)

    return render_template(
        "index.html",
        files=[
            {
                "name": file,
                "starred": False
            }
            for file in files
        ],
        page="Trash",
        trash=True,
        username=session.get("username")
    )


# ---------------------------------------------------
# RESTORE
# ---------------------------------------------------

@app.route("/restore/<filename>")
def restore(filename):

    source = os.path.join(TRASH_FOLDER, filename)
    destination = os.path.join(STORAGE_FOLDER, filename)

    if os.path.exists(source):

        os.rename(source, destination)

    return redirect("/trash")


# ---------------------------------------------------
# DELETE FOREVER
# ---------------------------------------------------

@app.route("/delete-forever/<filename>")
def delete_forever(filename):

    filepath = os.path.join(TRASH_FOLDER, filename)

    if os.path.exists(filepath):

        os.remove(filepath)

    return redirect("/trash")


# ---------------------------------------------------
# STAR / UNSTAR
# ---------------------------------------------------

@app.route("/star/<filename>")
def star(filename):

    old_path = os.path.join(STORAGE_FOLDER, filename)

    if filename.startswith("STARRED_"):

        new_name = filename.replace("STARRED_", "", 1)

    else:

        new_name = "STARRED_" + filename

    new_path = os.path.join(STORAGE_FOLDER, new_name)

    if os.path.exists(old_path):

        os.rename(old_path, new_path)

    return redirect("/")


# ---------------------------------------------------
# STARRED
# ---------------------------------------------------

@app.route("/starred")
def starred():

    files = []

    for filename in os.listdir(STORAGE_FOLDER):

        if filename.startswith("STARRED_"):

            files.append({
                "name": filename,
                "starred": True
            })

    return render_template(
        "index.html",
        files=files,
        page="Starred",
        username=session.get("username")
    )


# ---------------------------------------------------
# RECENT
# ---------------------------------------------------

@app.route("/recent")
def recent():

    files = []

    for filename in os.listdir(STORAGE_FOLDER):

        filepath = os.path.join(STORAGE_FOLDER, filename)

        if os.path.isfile(filepath):

            modified = os.path.getmtime(filepath)

            files.append({
                "name": filename,
                "starred": filename.startswith("STARRED_"),
                "time": datetime.fromtimestamp(modified)
            })

    files.sort(
        key=lambda x: x["time"],
        reverse=True
    )

    return render_template(
        "index.html",
        files=files,
        page="Recent",
        username=session.get("username")
    )


# ---------------------------------------------------
# DATASET ANALYZER
# ---------------------------------------------------

@app.route("/dataset")
def dataset():

    csv_files = [
        file
        for file in os.listdir(STORAGE_FOLDER)
        if file.lower().endswith(".csv")
    ]

    if not csv_files:

        return render_template(
            "dataset.html",
            error="Upload a CSV file to analyze it."
        )

    filename = csv_files[0]

    filepath = os.path.join(
        STORAGE_FOLDER,
        filename
    )

    try:

        df = pd.read_csv(filepath)

        rows = len(df)

        columns = len(df.columns)

        column_names = list(df.columns)

        numeric = df.select_dtypes(
            include="number"
        )

        averages = numeric.mean().round(2).to_dict()

        preview = df.head(10).to_html(
            classes="data-table",
            index=False
        )

        return render_template(
            "dataset.html",
            filename=filename,
            rows=rows,
            columns=columns,
            column_names=column_names,
            averages=averages,
            preview=preview,
            username=session.get("username")
        )

    except Exception as e:

        return render_template(
            "dataset.html",
            error=str(e)
        )


# ---------------------------------------------------
# STUDENT PERFORMANCE
# ---------------------------------------------------

@app.route("/student")
def student():

    filename = "student_data.csv"

    filepath = os.path.join(
        STORAGE_FOLDER,
        filename
    )

    if not os.path.exists(filepath):

        return render_template(
            "student.html",
            error="Please upload student_data.csv first."
        )

    try:

        df = pd.read_csv(filepath)

        required = [
            "name",
            "attendance",
            "maths",
            "science",
            "english"
        ]

        if not all(
            column in df.columns
            for column in required
        ):

            return render_template(
                "student.html",
                error="This application requires name, attendance, maths, science and english columns."
            )

        students = []

        for _, row in df.iterrows():

            score = round(
                (
                    row["maths"]
                    + row["science"]
                    + row["english"]
                ) / 3,
                2
            )

            if score >= 85:

                status = "Excellent"

            elif score >= 70:

                status = "Good"

            elif score >= 50:

                status = "Average"

            else:

                status = "Needs Improvement"

            students.append({
                "name": row["name"],
                "attendance": row["attendance"],
                "score": score,
                "status": status
            })

        students.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return render_template(
            "student.html",
            students=students,
            filename=filename,
            username=session.get("username")
        )

    except Exception as e:

        return render_template(
            "student.html",
            error=str(e)
        )


# ---------------------------------------------------
# RESUME TEXT EXTRACTION
# ---------------------------------------------------

def extract_resume_text(filepath):

    extension = filepath.lower().split(".")[-1]

    text = ""

    if extension == "pdf":

        reader = PdfReader(filepath)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

    elif extension == "docx":

        document = Document(filepath)

        for paragraph in document.paragraphs:

            text += paragraph.text + "\n"

    return text.lower()


# ---------------------------------------------------
# DATA ANALYST PROFILE
# ---------------------------------------------------

DATA_ANALYST_SKILLS = [
    "python",
    "sql",
    "excel",
    "power bi",
    "pandas",
    "statistics",
    "tableau"
]

DATA_ANALYST_KEYWORDS = [
    "data analysis",
    "data analytics",
    "data visualization",
    "dashboard",
    "reporting",
    "etl"
]

DATA_ANALYST_EDUCATION = [
    "computer science",
    "computer and communication",
    "information technology",
    "data science",
    "b.tech",
    "b.e",
    "engineering"
]


# ---------------------------------------------------
# RESUME SCREENING PAGE
# ---------------------------------------------------

@app.route("/screen")
def screen():

    return render_template(
        "screen.html",
        username=session.get("username")
    )


# ---------------------------------------------------
# RESUME UPLOAD + ANALYSIS
# ---------------------------------------------------

@app.route("/analyze-resume", methods=["POST"])
def analyze_resume():

    file = request.files.get("resume")

    if not file or not file.filename:

        return render_template(
            "screen.html",
            error="Please select a resume.",
            username=session.get("username")
        )

    filename = secure_filename(file.filename)

    allowed_extensions = ["pdf", "docx"]

    extension = filename.lower().split(".")[-1]

    if extension not in allowed_extensions:

        return render_template(
            "screen.html",
            error="Please upload a PDF or DOCX resume.",
            username=session.get("username")
        )

    filepath = os.path.join(
        RESUME_FOLDER,
        filename
    )

    file.save(filepath)

    try:

        resume_text = extract_resume_text(filepath)

        if not resume_text.strip():

            return render_template(
                "screen.html",
                error="Could not extract text from this resume.",
                username=session.get("username")
            )

        # -------------------------------
        # SKILL MATCHING
        # -------------------------------

        matched_skills = []
        missing_skills = []

        for skill in DATA_ANALYST_SKILLS:

            if skill.lower() in resume_text:

                matched_skills.append(skill)

            else:

                missing_skills.append(skill)

        skill_score = round(
            (
                len(matched_skills)
                / len(DATA_ANALYST_SKILLS)
            ) * 100
        )

        # -------------------------------
        # KEYWORD MATCHING
        # -------------------------------

        matched_keywords = []

        for keyword in DATA_ANALYST_KEYWORDS:

            if keyword.lower() in resume_text:

                matched_keywords.append(keyword)

        keyword_score = round(
            (
                len(matched_keywords)
                / len(DATA_ANALYST_KEYWORDS)
            ) * 100
        )

        # -------------------------------
        # EDUCATION MATCHING
        # -------------------------------

        education_matches = []

        for education in DATA_ANALYST_EDUCATION:

            if education.lower() in resume_text:

                education_matches.append(education)

        education_score = 100 if education_matches else 0

        # -------------------------------
        # OVERALL SCORE
        # -------------------------------

        overall_score = round(
            (
                skill_score * 0.60
                + keyword_score * 0.25
                + education_score * 0.15
            )
        )

        # -------------------------------
        # RESULT
        # -------------------------------

        if overall_score >= 80:

            result = "Excellent Match"

        elif overall_score >= 65:

            result = "Good Match"

        elif overall_score >= 50:

            result = "Moderate Match"

        else:

            result = "Low Match"

        return render_template(
            "screen.html",

            username=session.get("username"),

            filename=filename,

            overall_score=overall_score,

            skill_score=skill_score,

            keyword_score=keyword_score,

            education_score=education_score,

            matched_skills=matched_skills,

            missing_skills=missing_skills,

            matched_keywords=matched_keywords,

            result=result
        )

    except Exception as e:

        return render_template(
            "screen.html",
            error="Error processing resume: " + str(e),
            username=session.get("username")
        )


# ---------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)