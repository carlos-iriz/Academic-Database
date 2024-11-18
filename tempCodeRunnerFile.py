# app.py (Flask Backend)

from flask import Flask, request, session, render_template, redirect, url_for
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


# check that the info inputted is valid and correct within the user table
def user_info_check(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * 
    FROM event_scheduling.users 
    WHERE user_id = %s AND password = %s;
    """, (username, password))
    
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result


# Root route
@app.route('/')
def hello_world():
    return "Hello, World!"

#login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # get user info
        user_info = user_info_check(username, password)
        
        if user_info:
            session['username'] = username
            session['admin_id'] = username
            return redirect(url_for('index')) 
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)



if __name__ == "__main__":
    # Automatically open the browser to the Flask app URL
    webbrowser.open('http://127.0.0.1:5000/')
    
    # Start the Flask app in debug mode
    app.run(debug=True)