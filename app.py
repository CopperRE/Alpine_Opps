# Import the required Flask modules
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

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

    ('Admin', '1234')
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

        session["email"] = email

        return redirect(url_for("dashboard"))

    return render_template(
        "index.html",
        error="Incorrect email or password."
    )


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

    # Remove the stored username
    session.pop("email", None)

    # Return to login page
    return redirect(url_for("login_page"))


# --------------------------------------------------
# RUN THE APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)