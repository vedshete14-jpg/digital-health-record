from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "health-record-secret"


# ============================================================
# DATABASE
# ============================================================

def create_database():
    connection = sqlite3.connect("health.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            native_state TEXT NOT NULL,
            current_location TEXT NOT NULL,
            occupation TEXT,
            blood_group TEXT,
            emergency_contact TEXT,
            address TEXT
        )
    """)
    # Create medical records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id TEXT NOT NULL,
        visit_date TEXT NOT NULL,
        condition TEXT NOT NULL,
        diagnosis TEXT NOT NULL,
        treatment TEXT NOT NULL,
        doctor_name TEXT,
        FOREIGN KEY (worker_id) REFERENCES workers(worker_id)
    )
""")

    connection.commit()
    connection.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# WORKER REGISTRATION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # Get data from form
        worker_id = request.form.get("worker_id", "").strip()
        full_name = request.form.get("full_name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        native_state = request.form.get("native_state", "").strip()
        current_location = request.form.get("current_location", "").strip()
        occupation = request.form.get("occupation", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        emergency_contact = request.form.get("emergency_contact", "").strip()
        address = request.form.get("address", "").strip()

        # Check required fields
        if not worker_id:
            flash("Worker ID is required.", "error")
            return redirect(url_for("register"))

        if not full_name:
            flash("Full name is required.", "error")
            return redirect(url_for("register"))

        if not age:
            flash("Age is required.", "error")
            return redirect(url_for("register"))

        if not gender:
            flash("Gender is required.", "error")
            return redirect(url_for("register"))

        if not phone:
            flash("Phone number is required.", "error")
            return redirect(url_for("register"))

        if not native_state:
            flash("Native state is required.", "error")
            return redirect(url_for("register"))

        if not current_location:
            flash("Current location is required.", "error")
            return redirect(url_for("register"))

        # Convert age to integer
        try:
            age = int(age)

            if age <= 0:
                flash("Age must be greater than 0.", "error")
                return redirect(url_for("register"))

        except ValueError:
            flash("Please enter a valid age.", "error")
            return redirect(url_for("register"))

        # Insert worker into database
        try:

            with sqlite3.connect("health.db", timeout=30) as connection:

                cursor = connection.cursor()

                cursor.execute("""
                    INSERT INTO workers (
                        worker_id,
                        full_name,
                        age,
                        gender,
                        phone,
                        native_state,
                        current_location,
                        occupation,
                        blood_group,
                        emergency_contact,
                        address
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    worker_id,
                    full_name,
                    age,
                    gender,
                    phone,
                    native_state,
                    current_location,
                    occupation,
                    blood_group,
                    emergency_contact,
                    address
                ))

                connection.commit()

        except sqlite3.IntegrityError:
            flash(
                "Worker ID already exists. Please use another Worker ID.",
                "error"
            )

            return redirect(url_for("register"))

        except sqlite3.Error as error:
            print("Database error:", error)

            flash(
                "An error occurred while saving the worker.",
                "error"
            )

            return redirect(url_for("register"))

        # Registration successful
        flash("Worker registered successfully!", "success")

        return redirect(url_for("register"))

    # Show registration page for GET request
    return render_template("register.html")


# ============================================================
# HEALTH RECORD PAGE
# ============================================================

@app.route("/health-record", methods=["GET", "POST"])
def health_record():

    if request.method == "POST":

        worker_id = request.form.get("worker_id", "").strip()
        visit_date = request.form.get("visit_date", "").strip()
        doctor_name = request.form.get("doctor_name", "").strip()
        condition = request.form.get("condition", "").strip()
        diagnosis = request.form.get("diagnosis", "").strip()
        treatment = request.form.get("medicines", "").strip()

        # Check required fields
        if not worker_id or not visit_date or not condition or not diagnosis or not treatment:
            flash("Please fill all required medical details.", "error")
            return redirect(url_for("health_record"))

        try:
            with sqlite3.connect("health.db", timeout=30) as connection:
                cursor = connection.cursor()

                # Check whether worker exists
                cursor.execute(
                    "SELECT worker_id FROM workers WHERE worker_id = ?",
                    (worker_id,)
                )

                worker = cursor.fetchone()

                if worker is None:
                    flash("Worker ID does not exist. Register the worker first.", "error")
                    return redirect(url_for("health_record"))

                # Save health record
                cursor.execute("""
                    INSERT INTO medical_records
                    (worker_id, visit_date, condition, diagnosis,
                     treatment, doctor_name)

                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    worker_id,
                    visit_date,
                    condition,
                    diagnosis,
                    treatment,
                    doctor_name
                ))

                connection.commit()

            flash("Health record added successfully!", "success")
            return redirect(url_for("health_record"))

        except sqlite3.Error as error:
            print("Database error:", error)
            flash("An error occurred while saving the health record.", "error")
            return redirect(url_for("health_record"))

    return render_template("health-record.html")


# ============================================================
# SEARCH PAGE
# ============================================================
@app.route("/search", methods=["GET", "POST"])
def search():

    worker = None
    medical_records = []

    if request.method == "POST":

        worker_id = request.form.get("worker_id", "").strip()

        with sqlite3.connect("health.db") as connection:

            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            # Find worker
            cursor.execute(
                "SELECT * FROM workers WHERE worker_id = ?",
                (worker_id,)
            )

            worker = cursor.fetchone()

            # If worker exists, get medical records
            if worker is not None:

                cursor.execute("""
                    SELECT visit_date, condition, diagnosis,
                           treatment, doctor_name
                    FROM medical_records
                    WHERE worker_id = ?
                    ORDER BY id DESC
                """, (worker_id,))

                medical_records = cursor.fetchall()

        if worker is None:
            flash("Worker not found.", "error")

    return render_template(
        "search.html",
        worker=worker,
        medical_records=medical_records
    )

# ============================================================
# DASHBOARD PAGE
# ============================================================
@app.route("/dashboard")
def dashboard():

    with sqlite3.connect("health.db") as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        # Total workers
        cursor.execute("SELECT COUNT(*) AS total FROM workers")
        total_workers = cursor.fetchone()["total"]

        # Total health records
        cursor.execute("SELECT COUNT(*) AS total FROM medical_records")
        total_records = cursor.fetchone()["total"]
        # Today's visits
        from datetime import date
        today = date.today().isoformat()

        cursor.execute(
    "SELECT COUNT(*) AS total FROM medical_records WHERE visit_date = ?",
    (today,)
)
        today_visits = cursor.fetchone()["total"]

# Locations covered
        cursor.execute(
    "SELECT COUNT(DISTINCT current_location) AS total FROM workers"
)
        locations_covered = cursor.fetchone()["total"]

        # Recent health records
        cursor.execute("""
            SELECT
                medical_records.worker_id,
                workers.full_name,
                medical_records.visit_date,
                medical_records.condition,
                workers.current_location
            FROM medical_records
            JOIN workers
            ON medical_records.worker_id = workers.worker_id
            ORDER BY medical_records.id DESC
            LIMIT 5
        """)

        recent_records = cursor.fetchall()

    return render_template(
        "dashboard.html",
        total_workers=total_workers,
        total_records=total_records,
        today_visits=today_visits,
        locations_covered=locations_covered,
        recent_records=recent_records
    )

# ============================================================
# ABOUT PAGE
# ============================================================

@app.route("/about")
def about():
    return render_template("about.html")


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )