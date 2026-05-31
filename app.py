from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
import hashlib
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

DATABASE_URL = os.environ.get("DATABASE_URL")

logging.basicConfig(level=logging.INFO)


# -------------------------
# CONEXIÓN DB
# -------------------------
def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL NO CONFIGURADA")

    return psycopg2.connect(DATABASE_URL, sslmode="require")


# -------------------------
# INIT DB (AUTO FIX COMPLETO)
# -------------------------
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()

        # USERS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # POSTS (sin likes al inicio)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                user_name TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)

        # COMMENTS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                user_name TEXT,
                comment TEXT
            )
        """)

        # 🔥 AUTO FIX: columna likes
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='posts' AND column_name='likes'
                ) THEN
                    ALTER TABLE posts ADD COLUMN likes INTEGER DEFAULT 0;
                END IF;
            END
            $$;
        """)

        conn.commit()
        conn.close()

        print("TABLAS OK (AUTO FIX ACTIVADO)")

    except Exception as e:
        print("ERROR INIT DB:", e)


# Ejecutar solo si hay DB
if DATABASE_URL:
    init_db()


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, user_name, content, likes
            FROM posts
            ORDER BY id DESC
        """)

        posts = cur.fetchall()
        conn.close()

        return render_template("home.html", user=session["user"], posts=posts)

    except Exception as e:
        logging.error(f"HOME ERROR: {e}")
        return f"Error en home: {e}"


# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[0]
            return redirect("/")

        return "Login incorrecto"

    return render_template("login.html")


# -------------------------
# POST
# -------------------------
@app.route("/post", methods=["POST"])
def post():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO posts(user_name,content) VALUES(%s,%s)",
        (session["user"], request.form["content"])
    )

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# LIKE
# -------------------------
@app.route("/like/<int:post_id>")
def like(post_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE posts SET likes = COALESCE(likes,0) + 1 WHERE id=%s",
        (post_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# COMMENT
# -------------------------
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    if "user" not in session:
        return redirect("/login")

    text = request.form.get("comment")

    if not text:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO comments(post_id,user_name,comment) VALUES(%s,%s,%s)",
        (post_id, session["user"], text)
    )

    conn.commit()
    conn.close()

    return redirect("/")


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
    app.run()
