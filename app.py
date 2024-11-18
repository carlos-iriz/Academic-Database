# app.py (Flask Backend)

from flask import Flask, request
import psycopg2
from psycopg2.extras import RealDictCursor
import webbrowser

app = Flask(__name__)

# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(
        host="",
        database="Academic_Database",
        user="postgres",
        password=""
    )
    return conn


# Root route
@app.route('/')
def hello_world():
    return "Hello, World!"


if __name__ == "__main__":
    # Automatically open the browser to the Flask app URL
    webbrowser.open('http://127.0.0.1:5000/')
    
    # Start the Flask app in debug mode
    app.run(debug=True)