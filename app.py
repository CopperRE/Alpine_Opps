# Import the required Flask modules
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
import sqlite3
import random
import time


def initialise_database():

    # Connect to the database
    connection = sqlite3.connect("user.db")
    # Access other fields later on
    connection.row_factory = sqlite3.Row
    # Create a cursor
    cursor = connection.cursor()

    # Create the Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (

        UserID INTEGER PRIMARY KEY AUTOINCREMENT,

        Email TEXT UNIQUE NOT NULL,

        Password TEXT NOT NULL

    )
    """)

    # Insert the Administrator account
    cursor.execute("""
    INSERT OR IGNORE INTO Users
    (Email, Password)

    VALUES

    ('26tweco@goodnews.vic.edu.au', '1234')
    """)

    # Save the changes
    connection.commit()

    # Close the database
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
    connection = sqlite3.connect("user.db")

    cursor = connection.cursor()

    # Find a user with the matching username and password
    cursor.execute(
        """
        SELECT UserID
        FROM Users
        WHERE Email = ?
        AND Password = ?
        """, (email, password)
    )

    user = cursor.fetchone()

    connection.close()

    if user:

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
            return "Verification code expired."

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

    if "email" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html")


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