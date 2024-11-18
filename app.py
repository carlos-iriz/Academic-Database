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

# instruc route
@app.route('/instructor_menu')
def hello_world():
    return "Hello, World!"


# advise route
@app.route('/advisor_menu')
def hello_world():
    return "Hello, World!"


# staff route
@app.route('/staff_menu')
def hello_world():
    return "Hello, World!"


@app.route('/student_menu')
def hello_world():
    return "Hello, World!"


@app.route('/admin_menu')
def hello_world():
    return "Hello, World!"


@app.route('/course_summary')
def hello_world():
    return "Hello, World!"


@app.route('/my_info')
def hello_world():
    return "Hello, World!"


@app.route('/my_courses')
def hello_world():
    return "Hello, World!"


@app.route('/student_summary')
def hello_world():
    return "Hello, World!"

@app.route('/student_summary_advisor')
def hello_world():
    return "Hello, World!"

@app.route('/student_info')
def hello_world():
    return "Hello, World!"

@app.route('/gpa_calculator')
def hello_world():
    return "Hello, World!"


@app.route('/instructor_summary')
def hello_world():
    return "Hello, World!"

@app.route('/department_summary')
def hello_world():
    return "Hello, World!"

@app.route('pop-15')
def hello_world():
    return "Hello, World!"

@app.route('/user_info')
def hello_world():
    return "Hello, World!"

@app.route('/log')
def hello_world():
    return "Hello, World!"

@app.route('/pop_up_18')
def hello_world():
    return "Hello, World!"

@app.route('/pop_up_19')
def hello_world():
    return "Hello, World!"

@app.route('/my_grades')
def hello_world():
    return "Hello, World!"






if __name__ == "__main__":
    # Automatically open the browser to the Flask app URL
    webbrowser.open('http://127.0.0.1:5000/login')
    
    # Start the Flask app in debug mode
    app.run(debug=True)