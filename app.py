from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

DATABASE_URL = os.environ.get("DATABASE_URL")


# -------------------------
# DB
# -------------------------
def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL NO CONFIGURADA")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# -------------------------
# TABLAS
# -------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS comments")
    cur.execute("DROP TABLE IF EXISTS messages")
    cur.execute("DROP TABLE IF EXISTS posts")
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_name TEXT,
            content TEXT,
            image TEXT,
            likes INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER,
            user_name TEXT,
            comment TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE messages (
            id SERIAL PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


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
# POST
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
# LIKE
# -------------------------
@app.route("/like/<int:post_id>")
def like(post_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE posts
        SET likes = COALESCE(likes,0) + 1
        WHERE id=%s
    """, (post_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# DELETE
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
# COMMENTS
# -------------------------
@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    if "user" not in session:
        return redirect("/login")

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
# USERS LIST
# -------------------------
@app.route("/users")
def users():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name FROM users WHERE name != %s", (session["user"],))
    users = cur.fetchall()

    conn.close()

    return render_template("users.html", users=users)


# -------------------------
# CHAT PRIVADO
# -------------------------
@app.route("/chat/<name>", methods=["GET", "POST"])
def chat(name):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO messages(sender,receiver,message)
            VALUES(%s,%s,%s)
        """, (session["user"], name, request.form["message"]))

        conn.commit()

    cur.execute("""
        SELECT sender,message
        FROM messages
        WHERE (sender=%s AND receiver=%s)
        OR (sender=%s AND receiver=%s)
        ORDER BY id ASC
    """, (session["user"], name, name, session["user"]))

    messages = cur.fetchall()
    conn.close()

    return render_template("chat.html", messages=messages, chat_with=name)


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run()
