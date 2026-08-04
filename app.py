# Import the required Flask modules
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
import sqlite3
import random
import time
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "alpopp.db"

def initialise_database():

    # Connect to the database
    connection = sqlite3.connect(DATABASE)
    # Access other fields later on
    connection.row_factory = sqlite3.Row
    # Create a cursor
    cursor = connection.cursor()

    # --------------------------------------------------
    # CREATE USERS TABLE
    # --------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (

        UserID INTEGER PRIMARY KEY AUTOINCREMENT,

        Email TEXT UNIQUE NOT NULL,

        Password TEXT NOT NULL,

        Role TEXT NOT NULL DEFAULT 'User'

    )
    """)

    # --------------------------------------------------
    # CREATE FILES TABLE
    # --------------------------------------------------
    # This table stores information about each file.
    # It stores a link to the external file rather than
    # storing the actual PDF or spreadsheet in SQLite.

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Files (

        FileID INTEGER PRIMARY KEY AUTOINCREMENT,

        FileName TEXT NOT NULL,

        FileType TEXT NOT NULL,

        FileURL TEXT NOT NULL,

        FileOwner TEXT NOT NULL,

        LastModified TEXT NOT NULL,

        FileSize TEXT,

        IsPinned INTEGER DEFAULT 0

    )
    """)


    # --------------------------------------------------
    # INSERT ADMINISTRATOR ACCOUNT
    # --------------------------------------------------

    admin_emailX = "26tweco@goodnews.vic.edu.au"
    admin_passwordX = generate_password_hash("1234")

    cursor.execute("""
    SELECT UserID FROM Users WHERE Email = ?
    """, (admin_emailX,)
    )

    existing_admin = cursor.fetchone()

    if existing_admin is None:
        cursor.execute("""
            INSERT INTO Users (Email, Password, Role)
            VALUES (?, ?, ?)
        """, (admin_emailX, admin_passwordX, "Admin"))
   
    # --------------------------------------------------
    # INSERT FILES
    # --------------------------------------------------
    # FileID is included so INSERT OR IGNORE does not
    # create duplicate example files every time the app runs.
    #
    # Replace the example URLs with real Google Drive,
    # OneDrive, Dropbox or other external file links.

    cursor.execute("""
    INSERT OR IGNORE INTO Files
    (
        FileID,
        FileName,
        FileType,
        FileURL,
        FileOwner,
        LastModified,
        FileSize,
        IsPinned
    )

    VALUES
    (
        1,
        'Design Breif.docx',
        'DOCX',
        'https://goodnewslc-my.sharepoint.com/:w:/g/personal/26tweco_goodnews_vic_edu_au/IQB1J7ZWOEj5Qb4F021onoFjAeZWCzHqCG8YRpGyzNDOWZc?e=8pB5cR',
        'Admin',
        '2 May 2026',
        '20 KB',
        1
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO Files
    (
        FileID,
        FileName,
        FileType,
        FileURL,
        FileOwner,
        LastModified,
        FileSize,
        IsPinned
    )

    VALUES
    (
        2,
        'Project Timeline SAT Part 2.xlsx',
        'XLSX',
        'https://goodnewslc-my.sharepoint.com/:x:/g/personal/26tweco_goodnews_vic_edu_au/IQCxNQO5zYi1Toxi9ByximM3AfrZ_wlvRLahMJqsSrz2D3Y?e=ehOtzK',
        'Admin',
        '16 July 2026',
        '26 KB',
        0
    )
    """)


    # Save all database changes.
    connection.commit()

    # Close the database connection.
    connection.close()


# Create the Flask application
app = Flask(__name__)

# Secret key is required for sessions (login system)
# Can be anything
app.secret_key = "SecretKey"

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'verify.alpineopps@gmail.com'
app.config['MAIL_PASSWORD'] = 'gliz tycd xlin pfjs'

mail = Mail(app)

#Generate verification code
def generate_code():
    return str(random.randint(100000, 999999))

# Create the database if required
# --FOR USE IN DEBUGGING ONLY-- #
initialise_database()


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------
# Displays the login page when the website opens.

@app.route("/")
def login_page():
    return render_template("index.html")


# --------------------------------------------------
# LOGIN VALIDATION
# --------------------------------------------------
# This route checks whether the username and password
# entered by the user are correct.

@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email")
    password = request.form.get("password")

    # Connect to the database
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Find a user with the matching username and password
    cursor.execute(
    """
    SELECT * FROM Users
    WHERE Email = ?
    """, (email,)
    )

    user = cursor.fetchone()

    connection.close()

    if user and check_password_hash(user["Password"], password):
        
        session["email"] = user["Email"]
        session["role"] = user["Role"]

        code = generate_code()

        session["2fa_code"] = code
        session["2fa_email"] = email
        session["2fa_expiry"] = time.time() + 300

        msg = Message(
            "Alpine Opps Verification Code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = f"""
        Your Alpine Opps verification code is:

        {code}

        This code expires in 5 minutes.
        """

        mail.send(msg)

        return redirect(url_for("verify"))

    return render_template(
        "index.html",
        error="Incorrect email or password."
    )


# --------------------------------------------------
# VERIFY ACCOUNT
# --------------------------------------------------
# Page for 2FA code entry.

@app.route("/verify", methods=["GET", "POST"])
def verify():

    if request.method == "POST":

        entered = request.form.get("code")

        if time.time() > session.get("2fa_expiry", 0):
            
            # Remove the expired verification information
            session.pop("2fa_code", None)
            session.pop("2fa_email", None)
            session.pop("2fa_expiry", None)
            return render_template("expired.html")

        if entered == session.get("2fa_code"):

            # User is now fully logged in
            session["email"] = session["2fa_email"]

            # Remove temporary 2FA data
            session.pop("2fa_code", None)
            session.pop("2fa_email", None)
            session.pop("2fa_expiry", None)

            return redirect(url_for("dashboard"))

        return render_template(
            "verify.html",
            error="Incorrect verification code."
        )

    return render_template("verify.html")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
# Only users who have logged in can access this page.

@app.route("/dashboard")
def dashboard():

    # If the user is not logged in,
    # send them back to the login page.
    if "email" not in session:
        return redirect(url_for("login_page"))

    # Connect to the database.
    connection = sqlite3.connect(DATABASE)

    # Allow columns to be accessed by their names.
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    # Retrieve every file from the Files table.
    # Pinned files are displayed first.
    cursor.execute("""
        SELECT *
        FROM Files
        ORDER BY IsPinned DESC, FileID DESC
    """)

    files = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Send the files variable to dashboard.html.
    return render_template(
        "dashboard.html",
        files=files
    )


# -----------------------------
# New File Form
# -----------------------------
# This route displays the form for creating a new file.

@app.route("/newfile")
def newfile():

    # Make sure the user is logged in
    if "email" not in session:
        return redirect(url_for("login_page"))

    return render_template("newfile.html")


# --------------------------------------------------
# OPEN EXTERNAL FILE
# --------------------------------------------------
# This route finds the selected file's URL and
# redirects the user to that external file.

@app.route("/open-file/<int:file_id>")
def open_file(file_id):

    # Only logged-in users can open files.
    if "email" not in session:
        return redirect(url_for("login_page"))

    # Connect to the database.
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    # Find the file that has the selected FileID.
    cursor.execute("""
        SELECT FileURL
        FROM Files
        WHERE FileID = ?
    """, (file_id,))

    file = cursor.fetchone()

    connection.close()

    # Display an error if the file cannot be found.
    if file is None:
        return "File not found.", 404

    # Redirect the browser to the external file link.
    return redirect(file["FileURL"])


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
# Removes the user from the session.

@app.route("/logout")
def logout():

    # Remove all session data
    session.clear()

    # Return to login page
    return redirect(url_for("login_page"))


# --------------------------------------------------
# RUN THE APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)