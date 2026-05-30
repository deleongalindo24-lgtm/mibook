from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "mibook_secret"

DATABASE_URL = os.environ.get("DATABASE_URL")


# -------------------------
# CONEXIÓN POSTGRES
# -------------------------
def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# -------------------------
# CREAR TABLAS
# -------------------------
def init_db():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                password TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                content TEXT,
                user_name TEXT
            )
        """)

        conn.commit()

    except Exception as e:
        print("Error init_db:", e)

    finally:
        if conn:
            conn.close()


init_db()


# -------------------------
# HOME (MURO)
# -------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT content, user_name FROM posts ORDER BY id DESC")
        posts = cur.fetchall()

        return render_template("home.html", user=session["user"], posts=posts)

    except Exception as e:
        return f"Error home: {e}"

    finally:
        if conn:
            conn.close()


# -------------------------
# REGISTRO
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                (
                    request.form["name"],
                    request.form["email"],
                    request.form["password"]
                )
            )

            conn.commit()
            return redirect("/login")

        except Exception as e:
            return f"Error register: {e}"

        finally:
            if conn:
                conn.close()

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = None
        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "SELECT name FROM users WHERE email=%s AND password=%s",
                (request.form["email"], request.form["password"])
            )

            user = cur.fetchone()

            if user:
                session["user"] = user[0]
                return redirect("/")

            return "Login incorrecto"

        except Exception as e:
            return f"Error login: {e}"

        finally:
            if conn:
                conn.close()

    return render_template("login.html")


# -------------------------
# POSTS
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
            "INSERT INTO posts(content,user_name) VALUES(%s,%s)",
            (request.form["content"], session["user"])
        )

        conn.commit()
        return redirect("/")

    except Exception as e:
        return f"Error post: {e}"

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


if __name__ == "__main__":
    app.run()
