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
        conn.close()

    except Exception as e:
        print("Error init_db:", e)


init_db()


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
