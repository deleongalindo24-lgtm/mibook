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
# DB
# -------------------------
def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL NO CONFIGURADA")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# -------------------------
# INIT DB COMPLETO
# -------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            avatar TEXT DEFAULT 'default.png'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_name TEXT,
            content TEXT,
            image TEXT,
            likes INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER,
            user_name TEXT,
            comment TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_name TEXT,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, user_name, content, image, likes
        FROM posts
        ORDER BY id DESC
    """)

    posts = cur.fetchall()
    conn.close()

    return render_template("home.html", user=session["user"], posts=posts)


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

        cur.execute("""
            INSERT INTO users(name,email,password)
            VALUES(%s,%s,%s)
        """, (name, email, password))

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

        cur.execute("""
            SELECT name FROM users
            WHERE email=%s AND password=%s
        """, (email, password))

        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[0]
            return redirect("/")

        return "Login incorrecto"

    return render_template("login.html")


# -------------------------
# POST CREATE (TEXT + IMAGE)
# -------------------------
@app.route("/post", methods=["POST"])
def post():
    if "user" not in session:
        return redirect("/login")

    image_file = request.files.get("image")
    image_name = None

    if image_file:
        image_name = image_file.filename
        image_file.save("static/" + image_name)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO posts(user_name,content,image)
        VALUES(%s,%s,%s)
    """, (session["user"], request.form["content"], image_name))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# EDIT POST
# -------------------------
@app.route("/edit/<int:post_id>", methods=["POST"])
def edit(post_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE posts
        SET content=%s
        WHERE id=%s AND user_name=%s
    """, (request.form["content"], post_id, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# DELETE POST
# -------------------------
@app.route("/delete/<int:post_id>")
def delete(post_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM posts
        WHERE id=%s AND user_name=%s
    """, (post_id, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# LIKE
# -------------------------
@app.route("/like/<int:post_id>")
def like(post_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE posts
        SET likes = likes + 1
        WHERE id=%s
    """, (post_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# COMMENT
# -------------------------
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO comments(post_id,user_name,comment)
        VALUES(%s,%s,%s)
    """, (post_id, session["user"], request.form["comment"]))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# PROFILE
# -------------------------
@app.route("/profile/<name>")
def profile(name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name,email FROM users WHERE name=%s", (name,))
    user = cur.fetchone()

    cur.execute("SELECT content FROM posts WHERE user_name=%s", (name,))
    posts = cur.fetchall()

    conn.close()

    return render_template("profile.html", user=user, posts=posts)


# -------------------------
# CHAT (BÁSICO)
# -------------------------
@app.route("/chat", methods=["GET", "POST"])
def chat():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO messages(user_name,message)
            VALUES(%s,%s)
        """, (session["user"], request.form["message"]))

        conn.commit()

    cur.execute("SELECT user_name,message FROM messages")
    messages = cur.fetchall()

    conn.close()

    return render_template("chat.html", messages=messages)


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run()
