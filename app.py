from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "mibook_secret"

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    return psycopg2.connect(DATABASE_URL)


@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    conn.close()

    return render_template("home.html", user=session["user"], posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (request.form["name"], request.form["email"], request.form["password"])
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (request.form["email"], request.form["password"])
        )

        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            return redirect("/")

        return "Login incorrecto"

    return render_template("login.html")


@app.route("/post", methods=["POST"])
def post():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO posts(content,user_name) VALUES(%s,%s)",
        (request.form["content"], session["user"])
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
