from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
import hashlib
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_change_me")

DATABASE_URL = os.environ.get("DATABASE_URL")

logging.basicConfig(level=logging.INFO)


# -------------------------
# DB CONNECTION
# -------------------------
def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL NO CONFIGURADA EN RENDER")

    return psycopg2.connect(DATABASE_URL, sslmode="require")


# -------------------------
# INIT DB
# -------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_name TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_name, content FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    conn.close()

    return render_template("home.html", user=session["user"], posts=posts)


# -------------------------
# REGISTER (ARREGLADO + DEBUG REAL)
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = None
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = hashlib.sha256(request.form["password"].encode()).hexdigest()

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                (name, email, password)
            )

            conn.commit()
            return redirect("/login")

        except Exception as e:
            logging.error(f"REGISTER ERROR: {e}")
            return f"Error en registro: {e}"

        finally:
            if conn:
                conn.close()

    return render_template("register.html")


# -------------------------
# LOGIN (ARREGLADO + DEBUG REAL)
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = None
        try:
            email = request.form["email"]
            password = hashlib.sha256(request.form["password"].encode()).hexdigest()

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "SELECT name FROM users WHERE email=%s AND password=%s",
                (email, password)
            )

            user = cur.fetchone()

            if user:
                session["user"] = user[0]
                return redirect("/")

            return "Login incorrecto"

        except Exception as e:
            logging.error(f"LOGIN ERROR: {e}")
            return f"Error en login: {e}"

        finally:
            if conn:
                conn.close()

    return render_template("login.html")


# -------------------------
# POST
# -------------------------
@app.route("/post", methods=["POST"])
def post():
    if "user" not in session:
        return redirect("/login")

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO posts(user_name,content) VALUES(%s,%s)",
            (session["user"], request.form["content"])
        )

        conn.commit()
        return redirect("/")

    except Exception as e:
        logging.error(f"POST ERROR: {e}")
        return f"Error al publicar: {e}"

    finally:
        if conn:
            conn.close()


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
