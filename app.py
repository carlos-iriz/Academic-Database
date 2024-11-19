# app.py (Flask Backend)

from flask import Flask, request, session, render_template, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import webbrowser
import time

import secrets



app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

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

# Login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check user credentials
        user_info = user_info_check(username, password)
        
        if user_info:
            session['username'] = username
            session['user_role'] = user_info[1]  # Assuming user role is stored in column index 1
            session['dept_id'] = user_info[2]  # Assuming department ID is stored in column index 2
            return redirect(url_for('index')) 
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/admin_menu')
def admin_menu():
    # Assuming this is an admin menu, you can add more logic if needed
    return render_template('admin_menu.html')

# Advisor Menu Route
@app.route('/advisor_menu')
def advisor_menu():
    return render_template('advisor_menu.html')

# Course Summary Route
@app.route('/course_summary')
def course_summary():
    # You can fetch course details here (e.g., list of courses)
    # courses = get_courses(session['username'])
    return render_template('course_summary.html')  # Assuming you have a course summary template

@app.route('/create_user')
def create_user():
    # You can fetch course details here (e.g., list of courses)
    # courses = get_courses(session['username'])
    return render_template('create_user.html')  # Assuming you have a course summary template

@app.route('/department_summary')
def department_summary():
    # You can fetch course details here (e.g., list of courses)
    # courses = get_courses(session['username'])
    return render_template('department_summary.html')  # Assuming you have a course summary template

@app.route('/edit_instructor_info')
def edit_instructor_info():
    # You can fetch course details here (e.g., list of courses)
    # courses = get_courses(session['username'])
    return render_template('edit_instructor_info.html')  # Assuming you have a course summary template

@app.route('/edit_user')
def edit_user():
    # You can fetch course details here (e.g., list of courses)
    # courses = get_courses(session['username'])
    return render_template('edit_user.html')  # Assuming you have a course summary template


# GPA Calculator Route
@app.route('/gpa_calculator')
def gpa_calculator():
    # You may implement GPA calculation logic here
    # gpa = calculate_gpa(student_courses)
    return render_template('gpa_calculator.html')  # Assuming you have a GPA calculator template

# Instructor Menu Route
@app.route('/instructor_menu')
def instructor_menu():
    return render_template('instructor_menu.html')

# Instructor Menu Route
@app.route('/instructor_summary')
def instructor_summary():
    return render_template('instructor_summary.html')

# Log Route (Admin access)
@app.route('/log')
def log():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('log.html')  # Assuming you have a log template

# Logout Route
@app.route('/logout')
def logout():
    # Clear session data (or any other logout logic)
    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect back to the login page

# Log Route (Admin access)
@app.route('/my_courses')
def my_courses():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('my_courses.html')  # Assuming you have a log template

# Log Route (Admin access)
@app.route('/my_grades')
def my_grades():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('my_grades.html')  # Assuming you have a log template

# My Information Route
@app.route('/my_info')
def my_info():
    # Here you might want to fetch user-specific data from a database
    # user_info = get_user_info_from_db(session['username'])
    return render_template('my_info.html')  # Assuming you have a template for "my_info"

# Log Route (Admin access)
@app.route('/staff_menu')
def staff_menu():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('staff_menu.html')  # Assuming you have a log template

# Log Route (Admin access)
@app.route('/student_info')
def student_info():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('student_info.html')  # Assuming you have a log template

# Student Menu Route
@app.route('/student_menu')
def student_menu():
    return render_template('student_menu.html')

# Student Summary Route
@app.route('/student_summary')
def student_summary():
    # Here you can fetch the student summary (grades, courses, etc.) from a database
    # student_info = get_student_summary(session['username'])
    return render_template('student_summary.html')  # Assuming you have a student summary template

# Student Summary Route
@app.route('/student_summary_advisor')
def student_summary_advisor():
    # Here you can fetch the student summary (grades, courses, etc.) from a database
    # student_info = get_student_summary(session['username'])
    return render_template('student_summary_advisor.html')  # Assuming you have a student summary template

# def get_student_info(student_id):
#     conn = get_db_connection()
#     cursor = conn.cursor(cursor_factory=RealDictCursor)
#     cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
#     student_info = cursor.fetchone()
#     conn.close()
#     return student_info


# # @app.route('/student_summary_advisor', methods=['GET'])
# def student_summary_advisor():
#     student_id = request.args.get('student_id')  # for query parameter in URL
#     # or use request.form.get('student_id') if it is posted via form
#     student_info = get_student_info(student_id)
#     return render_template('student_summary_advisor.html', student_info=student_info)


# User Info Route (Admin/Instructor access)
@app.route('/user_info')
def user_info():
    # Example of dummy data (if you're testing and not connected to a database)
    user_info = {
        'user_id': '12345',
        'full_name': 'John Doe',
        'email': 'john.doe@example.com'
    }
    return render_template('user_info.html', user_info=user_info)
 # Assuming you have a user info template
 
#  @app.route('/what_if_analysis', methods=['GET', 'POST'])
# def what_if_analysis():
#     if request.method == 'POST':
#         # Process What-If analysis calculations here
#         # Scenario 1: Calculate effect on GPA with N additional courses and grades
#         # Scenario 2: Calculate courses/grades needed to achieve desired GPA
#         return render_template('what_if_results.html', results=calculated_data)
#     return render_template('what_if_analysis.html')


# @app.route('/gpa_summary')
# def gpa_summary():
#     # Fetch highest, lowest, and average GPA for each major from the database
#     return render_template('gpa_summary.html', gpa_data=gpa_summary_data)


# @app.route('/department_gpa_ranking')
# def department_gpa_ranking():
#     # Logic to fetch and rank departments by GPA
#     return render_template('department_gpa_ranking.html', ranking=department_ranking_data)


# @app.route('/semester_report')
# def semester_report():
#     # Fetch semester data for enrollments and average grades
#     return render_template('semester_report.html', semester_data=semester_report_data)


# @app.route('/student_credit_ranking')
# def student_credit_ranking():
#     # Fetch and sort student data by major and total credits
#     return render_template('student_credit_ranking.html', student_data=student_ranking_data)



# Function to open all routes in the default web browser when the app starts
def visit_all_routes():
    base_url = "http://127.0.0.1:5000"  # Adjust this if your app runs on a different host/port
    routes = [
        '/login',
        '/admin_menu',
        '/advisor_menu',
        '/course_summary',
        '/create_user',
        '/department_summary',
        '/edit_instructor_info',
        '/edit_user',
        '/gpa_calculator',
        '/instructor_menu',
        '/instructor_summary',
        '/log',
        '/logout',
        '/my_courses',
        '/my_grades',
        '/my_info',
        '/staff_menu',
        '/student_info',
        '/student_menu',
        '/student_summary',
        '/student_summary_advisor',
        '/user_info'
    ]

    for route in routes:
        full_url = base_url + route
        #response = client.get(route)
        #print(f"Visiting {route} - Status Code: {response.status_code}")
        print(f"Opening {full_url}")
        webbrowser.open(full_url)
        time.sleep(1)  # Delay to prevent opening all pages at once

# Call this function once your app is running


# if __name__ == "__main__":
#     # Automatically open the browser to the Flask app URL
#     webbrowser.open('http://127.0.0.1:5000/staff_menu')
    
#     # Start the Flask app in debug mode
#     app.run(debug=True)

if __name__ == "__main__":
    # Automatically open the browser to the Flask app URL
    webbrowser.open('http://127.0.0.1:5000/login')

    visit_all_routes()
    # Start the Flask app in debug mode
    app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent the test client from running twice
    
    # Call the function to visit all routes after the app starts