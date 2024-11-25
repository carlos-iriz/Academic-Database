# app.py (Flask Backend)

from flask import Flask, jsonify, request, session, render_template, redirect, url_for, json
import psycopg2
from psycopg2.extras import RealDictCursor
import webbrowser
from datetime import datetime


from Database_Backend import (
    DatabaseOperations, Students, staff_add_course, staff_remove_course, staff_modify_course, staff_add_instructor,
    staff_remove_instructor, staff_modify_instructor, staff_add_student, staff_remove_student, staff_modify_student, 
    staff_modify_department, advisor_add_student, advisor_drop_student
)

import secrets

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(
        host="academic-database-main.chs4cey0uprk.us-east-2.rds.amazonaws.com",
        database="Academic_Database",
        user="postgres",
        password="pops1234"
    )
    return conn

conn = get_db_connection()

def user_info_check(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Use %s for both placeholders in the SQL query (username is a string, not an integer)
    cursor.execute("""
    SELECT * 
    FROM UserInfo
    WHERE username = %s AND password = %s;
    """, (username, password))

    result = cursor.fetchone()
    print(f"Query result: {result}")  # Debugging the query result

    cursor.close()
    conn.close()

    return result

@app.route('/')
def home():
    return render_template('index.html')  # Ensure this template exists


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials
        user_info = user_info_check(username, password)

        if user_info:
            session['username'] = user_info[0]  # username is at index 1
            #session['username'] = user_info[1]  # username is at index 1
            session['user_role'] = user_info[3]  # role is at index 3
            session['role_id'] = user_info[4]  # role_id is at index 4
            # Redirect based on the user's role
            if session['user_role'] == 'Student':
                return redirect(url_for('student_menu'))
            elif session['user_role'] == 'Advisor':
                return redirect(url_for('advisor_menu'))
            elif session['user_role'] == 'Instructor':
                return redirect(url_for('instructor_menu'))
            elif session['user_role'] == 'Admin':
                return redirect(url_for('admin_menu'))
            elif session['user_role'] == 'Staff':
                return redirect(url_for('staff_menu'))
            else:
                error = 'Unknown user role. Please contact the administrator.'       
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

# Advisor Menu Route
@app.route('/stats_menu')
def stats_menu():
    return render_template('stats_menu.html')


@app.route('/course_summary')
def course_summary():
    # Check if user is logged in
    if 'user_role' not in session:
        return redirect(url_for('login'))  # Redirect to login if no role is set in session

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query for fetching all course details
    base_query = """
        SELECT
            c.course_name,
            c.course_code,
            i.instructor_id,
            d.name AS department_name,
            c.credits
        FROM Courses c
        JOIN Instructors i ON c.dept_id = i.dept_id
        JOIN Departments d ON c.dept_id = d.dept_id
        LEFT JOIN StudentCourse sc ON c.course_code = sc.course_code
        GROUP BY c.course_code, c.course_name, i.instructor_id, d.name, c.credits
        ORDER BY c.course_name;
    """

    # Execute the query to fetch all courses
    cursor.execute(base_query)

    # Fetch all results
    courses = cursor.fetchall()
    
    query2 = """
        SELECT COUNT(*)
        FROM Log
    """

    cursor.execute(query2)
    entry = cursor.fetchone()[0] + 1

    # log the view
    log_data = {
        'entry': entry,
        'timestamp': datetime.now(),  # Current timestamp
        'user_id': session['username'], # User performing the operation
        'operationtype': "VIEW", # Type of operation
        'old_data': "Course Viewing",
        'new_data': None # New data (if any)
    }

    db_ops = DatabaseOperations(conn)

    db_ops.add_entry("Log", log_data)

    # Close the database connection
    cursor.close()
    conn.close()

    # Render the course summary template with the fetched data
    return render_template('course_summary.html', courses=courses)



@app.route('/create_user')
def create_user():
    # You can fetch course details here (e.g., list of courses)
    # courses = get_courses(session['username'])
    return render_template('create_user.html')  # Assuming you have a course summary template

@app.route('/department_summary')
def department_summary():
    # Ensure the user is logged in
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if no role or username is set

    user_role = session['user_role']
    user_id = session['username']  # The username stored in session

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch the department ID for the logged-in user based on their role
        if user_role == 'Instructor':
            table = "Instructors"
            cursor.execute("SELECT dept_id FROM Instructors WHERE instructor_id = %s", (user_id,))
        elif user_role == 'Advisor':
            table = "Advisors"
            cursor.execute("SELECT dept_id FROM Advisors WHERE adv_id = %s", (user_id,))
        elif user_role == 'Staff':
            table = "Staff"
            cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (user_id,))
        else:
            return redirect(url_for('login'))  # Unauthorized role access

        # Get the department ID from the query result
        dept_result = cursor.fetchone()
        if not dept_result:
            return "Department not found for user.", 404
        dept_id = dept_result[0]

        # Fetch all users (excluding students) in the user's department
        query = """
            SELECT u.user_id, u.username, u.role, i.instructor_id, s.staff_id, a.adv_id
            FROM UserInfo u
            LEFT JOIN Instructors i ON u.user_id = i.instructor_id
            LEFT JOIN Staff s ON u.user_id = s.staff_id
            LEFT JOIN Advisors a ON u.user_id = a.adv_id
            WHERE u.role != 'Student' AND (i.dept_id = %s OR s.dept_id = %s OR a.dept_id = %s)
            ORDER BY u.username
        """
        cursor.execute(query, (dept_id, dept_id, dept_id))
        department_summary_data = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching department summary: {e}")
        department_summary_data = []
    finally:
        query2 = """
        SELECT COUNT(*)
        FROM Log
    """

        cursor.execute(query2)
        entry = cursor.fetchone()[0] + 1

        # log the view
        log_data = {
            'entry': entry,
            'timestamp': datetime.now(),  # Current timestamp
            'user_id': session['username'], # User performing the operation
            'operationtype': "VIEW", # Type of operation
            'old_data': table + " Department Viewing",
            'new_data': None # New data (if any)
        }

        db_ops = DatabaseOperations(conn)

        db_ops.add_entry("Log", log_data)
        cursor.close()
        conn.close()

    # Pass the data to the template
    return render_template('department_summary.html', department_summary=department_summary_data)


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
    
    return render_template('gpa_calculator.html')  # Assuming you have a GPA calculator template

# Instructor Menu Route
@app.route('/instructor_menu')
def instructor_menu():
    return render_template('instructor_menu.html')


@app.route('/instructor_summary')
def instructor_summary():
    # Ensure the user is logged in and has admin or appropriate access
    # if 'user_role' not in session or 'username' not in session:
    #     return redirect(url_for('login'))  # Redirect to login if no role or username is set

    user_role = session['user_role']
    # Admin or another role can access the instructor summary page
    if user_role not in ['Admin', 'Instructor', 'Advisor']:  
        return redirect(url_for('login'))  # Redirect if user role is not allowed

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    instructors = []
    try:
        # Fetch all instructors from the Instructors table
        query = """
            SELECT instructor_id, dept_id
            FROM Instructors
        """
        cursor.execute(query)
        instructors = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching instructors: {e}")
    finally:
        query2 = """
        SELECT COUNT(*)
        FROM Log
    """

        cursor.execute(query2)
        entry = cursor.fetchone()[0] + 1

        # log the view
        log_data = {
            'entry': entry,
            'timestamp': datetime.now(),  # Current timestamp
            'user_id': session['username'], # User performing the operation
            'operationtype': "VIEW", # Type of operation
            'old_data': "Instructor Viewing",
            'new_data': None # New data (if any)
        }

        db_ops = DatabaseOperations(conn)

        db_ops.add_entry("Log", log_data)
        cursor.close()
        conn.close()

    # Pass the instructor data to the template
    return render_template('instructor_summary.html', instructors=instructors)

from flask import render_template, session
from datetime import datetime

from flask import render_template

@app.route('/log')
def log():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch log entries from the database
    query = "SELECT * FROM Log ORDER BY timestamp DESC"
    cursor.execute(query)
    logs = cursor.fetchall()

    # Pass logs to the template
    return render_template('log.html', logs=logs)



# Log operation (to be called after any INSERT, UPDATE, DELETE operation)
def log_operation(user_id, operation_type, affected_table, old_data=None, new_data=None):
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prepare the log entry
    try:
        cursor.execute("""
            INSERT INTO Log (user_id, operationtype, old_data, new_data)
            VALUES (%s, %s, %s, %s)
        """, (
            user_id, 
            operation_type, 
            json.dumps(old_data, default=str) if old_data else None,  # Store old data as JSON string
            json.dumps(new_data, default=str) if new_data else None   # Store new data as JSON string
        ))

        # Commit the transaction
        conn.commit()

    except Exception as e:
        print(f"Error logging operation: {e}")
    finally:
        cursor.close()
        conn.close()

# Example usage of the log function:

def log_addition(user_id, table, new_data):
    log_operation(user_id, "INSERT", table, new_data=new_data)

def log_modification(user_id, table, old_data, new_data):
    log_operation(user_id, "UPDATE", table, old_data=old_data, new_data=new_data)

def log_deletion(user_id, table, old_data):
    log_operation(user_id, "DELETE", table, old_data=old_data)

# Logout Route
@app.route('/logout')
def logout():
    # Clear session data (or any other logout logic)
    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect back to the login page


@app.route('/my_courses')
def my_courses():
    # Ensure the user is logged in
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_role = session['user_role']
    user_id = session['username']  # `username` stores the instructor's ID or student's ID

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    courses = []
    courses1 = []  # Initialize courses1 for students' courses

    try:
        if user_role == 'Instructor':
            # Fetch courses taught by the instructor
            cursor.execute("""
                SELECT
                    c.course_name,
                    c.course_code,
                    i.instructor_id,
                    d.name AS department_name,
                    c.credits,
                    AVG(
                        CASE
                            WHEN sc.grade = 'A' THEN 4.0
                            WHEN sc.grade = 'B' THEN 3.0
                            WHEN sc.grade = 'C' THEN 2.0
                            WHEN sc.grade = 'D' THEN 1.0
                            WHEN sc.grade = 'F' THEN 0.0
                            ELSE NULL
                        END
                    ) AS average_grade
                FROM Courses c
                JOIN Instructors i ON c.dept_id = i.dept_id
                JOIN Departments d ON c.dept_id = d.dept_id
                LEFT JOIN StudentCourse sc ON c.course_code = sc.course_code
                WHERE i.instructor_id = %s
                GROUP BY c.course_code, c.course_name, i.instructor_id, d.name, c.credits
                ORDER BY c.course_name;
            """, (user_id,))
            courses = cursor.fetchall()

        elif user_role == 'Student':
            # Fetch courses the student is enrolled in
            cursor.execute("""
                SELECT
                    c.course_name,
                    c.course_code,
                    c.credits,
                    sc.grade,
                    sc.semester,
                    sc.year_taken
                FROM StudentCourse sc
                JOIN Courses c ON sc.course_code = c.course_code
                WHERE sc.stud_id = %s
                ORDER BY c.course_name;
            """, (user_id,))
            courses1 = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching courses: {e}")
        return "An error occurred while fetching courses.", 500
    finally:
        cursor.close()
        conn.close()

    # Render the appropriate template with the fetched courses
    return render_template('my_courses.html', courses=courses, courses1=courses1, user_role=user_role)

@app.route('/my_grades')
def my_grades():
    # Ensure the user is logged in and has the correct role
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if no role or user_id is set

    user_role = session['user_role']
    user_id = session['username']  # Assuming `user_id` is the logged-in student's ID

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    grades = []
    try:
        # Fetch grades if the logged-in user is a student
        if user_role == 'Student':
            query = """
                SELECT c.course_name, c.course_code, sc.grade, c.credits
                FROM StudentCourse sc
                JOIN Courses c ON sc.course_code = c.course_code
                WHERE sc.stud_id = %s
                ORDER BY c.course_name
            """
            cursor.execute(query, (user_id,))
            grades = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching grades: {e}")
    finally:
        cursor.close()
        conn.close()

    # Render the grades page with the fetched data
    return render_template('my_grades.html', grades=grades)


# @app.route('/my_info')
# def my_info():
#     # Ensure the user is logged in
#     if 'user_role' not in session or 'username' not in session:
#         return redirect(url_for('login'))  # Redirect to login if not logged in

#     user_id = session['username']  # Assume `username` maps to `user_id` in UserInfo
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     user_info = None

#     try:
#         # Fetch user-specific data from UserInfo table
#         cursor.execute("SELECT * FROM UserInfo WHERE user_id = %s", (user_id,))
#         user_info = cursor.fetchone()

#         if not user_info:
#             return redirect(url_for('login'))  # If no user info found, redirect to login

#     except Exception as e:
#         print(f"Error: {e}")
#         return "An error occurred.", 500
#     finally:
#         cursor.close()
#         conn.close()

#     # Render the user information page
#     return render_template('my_info.html', user_info=user_info if user_info else {})

@app.route('/my_info')
def my_info():
    # Ensure the user is logged in
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['username']  # Assume `username` maps to `user_id` in UserInfo
    conn = get_db_connection()
    cursor = conn.cursor()

    user_info = None
    gpa = None

    try:
        # Fetch user-specific data from UserInfo table
        cursor.execute("SELECT * FROM UserInfo WHERE user_id = %s", (user_id,))
        user_info = cursor.fetchone()

        if not user_info:
            return redirect(url_for('login'))  # If no user info found, redirect to login

        if user_info[3] == 'Student': 
            # Assuming you have a Student object and the calculate_gpa method
            student = Students(conn, stud_id=user_info[0])  # Create the student object (adjust this as needed)
            gpa = student.calculate_gpa(conn)  # Call the calculate_gpa method

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred.", 500
    finally:
        cursor.close()
        conn.close()

    # Render the user information page, passing user_info and gpa
    return render_template('my_info.html', user_info=user_info if user_info else {}, gpa=gpa)



# Log Route (Admin access)
@app.route('/staff_menu')
def staff_menu():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('staff_menu.html')  # Assuming you have a log template


from flask import request, render_template, redirect, url_for, session

@app.route('/student_info', methods=['GET', 'POST'])
def student_info():
    # Ensure the user is an admin
    if 'user_role' not in session or session['user_role'] != 'Admin':
        return redirect(url_for('login'))  # Redirect to login if not an admin
    
    student_info = None
    stud_id = None  # Store student ID for the search query

    # Handle POST request for searching
    if request.method == 'POST':
        stud_id = request.form.get('stud_id')
        
        if stud_id:
            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to get student information based on stud_id
            try:
                # Fetch student details from Students table
                cursor.execute("""
                    SELECT s.student_id, u.name, u.email, s.major, s.year
                    FROM Students s
                    JOIN Users u ON s.student_id = u.user_id
                    WHERE s.student_id = %s
                """, (stud_id,))
                
                student_info = cursor.fetchone()  # Fetch student information

                # Fetch student's course schedule
                cursor.execute("""
                    SELECT c.course_name, c.course_code, sc.grade, c.credits
                    FROM StudentCourse sc
                    JOIN Courses c ON sc.course_code = c.course_code
                    WHERE sc.student_id = %s
                """, (stud_id,))
                
                student_courses = cursor.fetchall()  # Fetch courses related to student

            except Exception as e:
                print(f"Error fetching student info: {e}")
                student_info = None  # Ensure no data is shown if there's an error

            finally:
                cursor.close()
                conn.close()
                
            # Pass course schedule as part of the student info if data exists
            if student_info:
                student_info['courses'] = student_courses

    return render_template('student_info.html', student_info=student_info, stud_id=stud_id)


# Student Menu Route
@app.route('/student_menu')
def student_menu():
    return render_template('student_menu.html')


@app.route('/student_summary')
def student_summary():
    # Ensure the user is logged in
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if no role or username is set

    user_role = session['user_role']
    user_id = session['username']  # Assuming `username` is stored in session

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prepare data for student summary
    student_summary_data = []

    try:
        # Fetch the department ID for the logged-in user based on their role
        if user_role == 'Instructor':
            cursor.execute("SELECT dept_id FROM Instructors WHERE instructor_id = %s", (user_id,))
        elif user_role == 'Advisor':
            cursor.execute("SELECT dept_id FROM Advisors WHERE adv_id = %s", (user_id,))
        elif user_role == 'Staff':
            cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (user_id,))
        else:
            return redirect(url_for('login'))  # Unauthorized role access

        # Get the department ID from the query result
        dept_result = cursor.fetchone()
        if not dept_result:
            return "Department not found for user.", 404
        dept_id = dept_result[0]
        print(f"Fetched dept_id {dept_id} for {user_role} with user_id {user_id}")


        # Fetch all students in the user's department 
        query = """
            SELECT s.stud_id, u.username AS name, s.major
            FROM Students s
            JOIN UserInfo u ON s.stud_id = u.user_id
            WHERE s.dept_id = %s
            ORDER BY s.stud_id
        """
        cursor.execute(query, (dept_id,))
        student_summary_data = cursor.fetchall()
        print(f"Fetched students: {student_summary_data}")

    except Exception as e:
        print(f"Error fetching student summary: {e}")
        student_summary_data = []
    finally:
        cursor.close()
        conn.close()

    # Render the template with student summary data
    return render_template('student_summary.html', student_summary=student_summary_data)


@app.route('/what_if_analysis', methods=['GET', 'POST'])
def what_if_analysis():
    # create student object with user ID or whatever to call calculateGPA from databast_backend.py
    #currGPA = studentObj.calculate_gpa(x, y, z)
    conn = get_db_connection()
    cursor = conn.cursor()

    stud_id = session['username']
    currGPA = Students(conn, stud_id).calculate_gpa(conn)

    query = """
        SELECT SUM(credits)
        FROM StudentCourse
        WHERE stud_id = %s
    """

    cursor.execute(query, (stud_id,))
    result = cursor.fetchone()
    currCredits = result[0]
    
    query2 = """
        SELECT COUNT(*)
        FROM Log
    """

    cursor.execute(query2)
    entry = cursor.fetchone()[0] + 1

    # log the view
    log_data = {
        'entry': entry,
        'timestamp': datetime.now(),  # Current timestamp
        'user_id': session['username'], # User performing the operation
        'operationtype': "VIEW", # Type of operation
        'old_data': "Grade Viewing",
        'new_data': None # New data (if any)
    }

    db_ops = DatabaseOperations(conn)

    db_ops.add_entry("Log", log_data)

    cursor.close()
    conn.close()

    if request.method == 'POST':
    # Process What-If analysis calculations here
        # Scenario 1: Calculate effect on GPA with N additional courses and grades

        numerical_grade_mapping = {
                'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
            }
        

        # fetch N courses and grades from the HTML side using flask
        grade_input = request.form.get("grade_input")
        grades = grade_input.split()

        # take credit inputs too and typecast em into ints
        credits_input = request.form.get("credit_input")
        credits = credits_input.split()

        if not grade_input or not credits_input:
            return "Please enter both grades and credits."
        
        try:
            credits = [int(credit) for credit in credits]
        except ValueError:
            return "Invalid credit values entered. Please enter numeric values only."
        
        if len(grades) != len(credits):
            return "The number of grades and credits must match."

        # remap all grades that are inputted
        numeric_grades = [numerical_grade_mapping[grade[0]] for grade in grades if grade[0] in numerical_grade_mapping]

        # calculate new mini GPA 
        newGradePts = 0
        newCreds = 0
        for n in range(len(numeric_grades)):
            newGradePts += credits[n] * numeric_grades[n]
            newCreds += credits[n]

        # redo calculate GPA but include new courses added
        newGPA = ((currGPA * currCredits) + newGradePts) / (currCredits + newCreds) 

        calculated_data = "{0:.2f}".format(newGPA)


        return render_template('what_if_results.html', prev_gpa=currGPA, results=calculated_data)
    return render_template('what_if_analysis.html', gpa = currGPA, creds = currCredits)

@app.route('/what_if_analysis_advisor', methods=['GET', 'POST'])
def what_if_analysis_advisor():

    if request.method == 'POST':
    # Process What-If analysis calculations here
        # Scenario 1: Calculate effect on GPA with N additional courses and grades

        numerical_grade_mapping = {
                'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
            }
        
        # get the student's id
        id = request.form.get("id_input")

        # fetch N courses and grades from the HTML side using flask
        grade_input = request.form.get("grade_input")
        grades = grade_input.split()

        # take credit inputs too and typecast em into ints
        credits_input = request.form.get("credit_input")
        credits = credits_input.split()



        conn = get_db_connection()
        cursor = conn.cursor()

        currGPA = Students(conn, id).calculate_gpa(conn)

        query = """
            SELECT SUM(credits)
            FROM StudentCourse
            WHERE stud_id = %s
        """

        cursor.execute(query, (id,))
        result = cursor.fetchone()
        currCredits = result[0]
        
        query2 = """
        SELECT COUNT(*)
        FROM Log
    """

        cursor.execute(query2)
        entry = cursor.fetchone()[0] + 1

        # log the view
        log_data = {
            'entry': entry,
            'timestamp': datetime.now(),  # Current timestamp
            'user_id': session['username'], # User performing the operation
            'operationtype': "VIEW", # Type of operation
            'old_data': "Grade Viewing",
            'new_data': None # New data (if any)
        }

        db_ops = DatabaseOperations(conn)

        db_ops.add_entry("Log", log_data)


        cursor.close()
        conn.close()


        if not grade_input or not credits_input:
            return "Please enter both grades and credits."
        
        try:
            credits = [int(credit) for credit in credits]
        except ValueError:
            return "Invalid credit values entered. Please enter numeric values only."
        
        if len(grades) != len(credits):
            return "The number of grades and credits must match."

        # remap all grades that are inputted
        numeric_grades = [numerical_grade_mapping[grade[0]] for grade in grades if grade[0] in numerical_grade_mapping]

        # calculate new mini GPA 
        newGradePts = 0
        newCreds = 0
        for n in range(len(numeric_grades)):
            newGradePts += credits[n] * numeric_grades[n]
            newCreds += credits[n]

        # redo calculate GPA but include new courses added
        newGPA = ((currGPA * currCredits) + newGradePts) / (currCredits + newCreds) 

        calculated_data = "{0:.2f}".format(newGPA)


        return render_template('what_if_results_advisor.html', s_id=id, prev_gpa=currGPA, results=calculated_data)
    return render_template('what_if_analysis_advisor.html')



#/////////////////////////////////////////////////////////////////////////////
# Req 1

# @app.route('/staff_add_drop_modify')
# def staff_add_drop_modify():
#     return render_template('staff_add_drop_modify.html')  # Replace with the correct HTML template

# @app.route('/staff_manage_courses', methods=['GET', 'POST'])
# def staff_manage_courses():
#     conn = get_db_connection()
#     database_operations_instance = DatabaseOperations(conn)

#     if request.method == 'GET':
#         return render_template('staff_manage_courses.html')  # Replace with your courses page template
    
#     if request.method == 'POST':
#         action = request.form.get('action')  # Determine the action: 'add', 'remove', or 'modify'
#         staff_id = request.form.get('staff_id')  # Assuming staff_id is submitted in the form
        
#         if action == 'add':
#             # Retrieve form data for adding a course
#             course_code = request.form.get('course_code')
#             course_name = request.form.get('course_name')
#             credits = request.form.get('credits')
            
#             DatabaseOperations.staff_add_course(database_operations_instance, course_code, course_name, credits, staff_id)
#             conn.close
#             print('Course added successfully!', 'success')
        
#         elif action == 'remove':
#             # Retrieve form data for removing a course
#             course_code = request.form.get('course_code')
            
#             staff_remove_course(database_operations_instance, course_code, staff_id)
#             conn.close
#             print('Course removed successfully!', 'success')
        
#         elif action == 'modify':
#             # Retrieve form data for modifying a course
#             attribute = request.form.get('attribute')  # Example: 'course_name', 'credits'
#             modification = request.form.get('modification')  # New value for the attribute
#             course_code = request.form.get('course_code')
            
#             staff_modify_course(database_operations_instance, attribute, modification, course_code, staff_id)
#             conn.close
#             print('Course modified successfully!', 'success')
        
#         conn.close
        
#         return redirect(url_for('staff_manage_courses'))


# @app.route('/staff_manage_departments', methods=['GET', 'POST'])
# def staff_manage_departments():
#     conn = get_db_connection()
#     database_operations_instance = DatabaseOperations(conn)
#     if request.method == 'GET':
#         # Fetch department data to display in the dropdown and table
#         departments = database_operations_instance.get_all_entries('Departments')  # Fetch all departments
#         return render_template('staff_manage_departments.html', departments=departments)
    
#     if request.method == 'POST':
#         action = request.form.get('action')
#         staff_id = request.form.get('staff_id')  # Assuming staff_id is submitted in the form

#         if action == 'modify':
#             # Retrieve form data for modifying a department
#             dept_id = request.form.get('dept_id')
#             attribute = request.form.get('attribute')  # Example: 'name'
#             modification = request.form.get('modification')  # New value for the attribute
            
#             staff_modify_department(database_operations_instance, attribute, modification, dept_id, staff_id)
#             conn.close
            
#             print('Department modified successfully!', 'success')
#         conn.close
#         return redirect(url_for('staff_manage_departments'))

# # Route to manage instructors
# @app.route('/staff_manage_instructors', methods=['GET', 'POST'])
# def staff_manage_instructors():
#     try:
#         conn = get_db_connection()
#         # Simulated database instance
#         db = DatabaseOperations(conn)
        
#         # Simulated logged-in staff ID (Replace this with your session's user ID logic)
#         staff_id =  session['username']

#         # If POST request is received, handle form actions
#         if request.method == 'POST':
#             action = request.form.get('action')
            
#             if action == 'add':
#                 # Extract form data
#                 instructor_id = request.form.get('instructor_id', type=int)
#                 username = request.form.get('username')
#                 email = request.form.get('email')
#                 password = request.form.get('password')
#                 hired_sem = request.form.get('hired_sem')
#                 instructor_phone = request.form.get('instructor_phone')
                
#                 # Call function to add instructor
#                 staff_add_instructor(
#                     db, 
#                     instructor_id, username, email, password, 
#                     hired_sem, instructor_phone, staff_id
#                 )
#                 conn.close
#                 print("Instructor added successfully!", "success")
            
#             elif action == 'remove':
#                 # Extract form data
#                 instructor_id = request.form.get('instructor_id', type=int)
                
#                 # Call function to remove instructor
#                 staff_remove_instructor(db, instructor_id, staff_id)
#                 conn.close
                
#                 print("Instructor removed successfully!", "success")
            
#             elif action == 'modify':
#                 # Extract form data
#                 instructor_id = request.form.get('instructor_id', type=int)
#                 attribute = request.form.get('attribute')
#                 modification = request.form.get('modification')
                
#                 # Call function to modify instructor
#                 staff_modify_instructor(
#                     db, 
#                     attribute, modification, instructor_id, staff_id
#                 )
                
#                 conn.close
#                 print("Instructor modified successfully!", "success")
#             conn.close
#             return redirect(url_for('staff_manage_instructors'))

#         # # For GET request, fetch instructors data to render on the page
#         # instructors = db.fetch_all('Instructors')  # Adjust to match your database method
        
#         # return render_template(
#         #     'staff_manage_instructors.html', 
#         #     instructors=instructors
#         # )
#         conn.close
#         return redirect(url_for('staff_manage_instructors'))

    
#     except Exception as e:
#         print(f"An error occurred: {e}", "danger")
#         return redirect(url_for('staff_add_drop_modify'))

# # Route to manage students
# @app.route('/staff_manage_students', methods=['GET', 'POST'])
# def staff_manage_students():
#     try:
#         conn = get_db_connection()
#         # Simulated database instance
#         db = DatabaseOperations(conn)
        
#         # Simulated logged-in staff ID (Replace with your session's user ID logic)
#         staff_id =  session['username']

#         # Handle form submission
#         if request.method == 'POST':
#             action = request.form.get('action')
            
#             if action == 'add':
#                 # Extract form data
#                 user_id = request.form.get('user_id', type=int)
#                 username = request.form.get('username')
#                 email = request.form.get('email')
#                 password = request.form.get('password')
#                 gender = request.form.get('gender')
#                 major = request.form.get('major')
#                 dept_id = request.form.get('dept_id', type=int)
                
#                 # Call function to add student
#                 staff_add_student(
#                     db,
#                     user_id, username, email, password,
#                     gender, major, dept_id, staff_id
#                 )
                
#                 conn.close
#                 print("Student added successfully!", "success")
            
#             elif action == 'remove':
#                 # Extract form data
#                 stud_id = request.form.get('stud_id', type=int)
                
#                 # Call function to remove student
#                 staff_remove_student(db, stud_id, staff_id)
#                 conn.close
#                 print("Student removed successfully!", "success")
            
#             elif action == 'modify':
#                 # Extract form data
#                 stud_id = request.form.get('stud_id', type=int)
#                 attribute = request.form.get('attribute')
#                 modification = request.form.get('modification')
                
#                 # Call function to modify student
#                 staff_modify_student(
#                     db,
#                     attribute, modification, stud_id, staff_id
#                 )
#                 conn.close
#                 print("Student modified successfully!", "success")
#             conn.close
#             return redirect(url_for('staff_manage_students'))

#         # For GET request, fetch students data to render on the page
        
#         conn.close
#         return redirect(url_for('staff_manage_students'))

    
#     except Exception as e:
#         print(f"An error occurred: {e}", "danger")
#         return redirect(url_for('staff_manage_students'))

@app.route('/staff_add_drop_modify')
def staff_add_drop_modify():
    return render_template('staff_add_drop_modify.html')  # Replace with the correct HTML template


# @app.route('/staff_manage_courses', methods=['GET', 'POST'])
# def staff_manage_courses():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         staff_id = session.get('username')  # Assuming 'username' holds the staff ID

#         if request.method == 'GET':
#             # Query to get the department ID for the current staff member
#             cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
#             department = cursor.fetchone()  # Get department data as a tuple
            
#             if department:
#                 department_id = department[0]  # Access dept_id by index, assuming it's the first column
#                 # Query to fetch courses for the staff member's department
#                 cursor.execute("SELECT course_code, course_name FROM Courses WHERE dept_id = %s", (department_id,))
#                 courses = cursor.fetchall()  # Get courses data as a list of tuples
#             else:
#                 courses = []

#             conn.close()
#             return render_template('staff_manage_courses.html', courses=courses)
        
#         # Handle POST request actions: 'add', 'remove', 'modify'
#         action = request.form.get('action')
        
#         if action == 'add':
#             course_code = request.form.get('course_code')
#             course_name = request.form.get('course_name')
#             credits = request.form.get('credits')
#             cursor.execute(
#                 "INSERT INTO Courses (course_code, course_name, credits, dept_id) VALUES (%s, %s, %s, %s)",
#                 (course_code, course_name, credits, department_id)
#             )
#             conn.commit()
#             print('Course added successfully!', 'success')
        
#         elif action == 'remove':
#             course_code = request.form.get('course_code')
#             cursor.execute("DELETE FROM Courses WHERE course_code = %s AND dept_id = %s", (course_code, department_id))
#             conn.commit()
#             print('Course removed successfully!', 'success')
        
#         elif action == 'modify':
#             attribute = request.form.get('attribute')
#             modification = request.form.get('modification')
#             course_code = request.form.get('course_code')
#             # Execute an UPDATE query based on the attribute to modify
#             cursor.execute(f"UPDATE Courses SET {attribute} = %s WHERE course_code = %s AND dept_id = %s",
#                            (modification, course_code, department_id))
#             conn.commit()
#             print('Course modified successfully!', 'success')
        
#         conn.close()
#         return redirect(url_for('staff_manage_courses'))
    
#     except Exception as e:
#         print(f"An error occurred: {e}", "danger")
#         return redirect(url_for('staff_manage_courses'))

@app.route('/staff_manage_courses', methods=['GET', 'POST'])
def staff_manage_courses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        operations = DatabaseOperations(conn)
        
        staff_id = session.get('username')  # Assuming 'username' holds the staff ID

        if request.method == 'GET':
            # Query to get the department ID for the current staff member
            cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
            department = cursor.fetchone()  # Get department data as a tuple
            
            if department:
                department_id = department[0]  # Access dept_id by index, assuming it's the first column
                # Query to fetch courses for the staff member's department
                cursor.execute("SELECT course_code, course_name FROM Courses WHERE dept_id = %s", (department_id,))
                courses = cursor.fetchall()  # Get courses data as a list of tuples
            else:
                courses = []

            conn.close()
            return render_template('staff_manage_courses.html', courses=courses)
        
        # Handle POST request actions: 'add', 'remove', 'modify'
        action = request.form.get('action')
        
        if action == 'add':
            course_code = request.form.get('course_code')
            course_name = request.form.get('course_name')
            credits = request.form.get('credits')
            
            cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
            dept_result = cursor.fetchone()
            if not dept_result:
                return "Department not found for user.", 404
            dept_id = dept_result[0]
            
            staff_add_course(operations, course_code, course_name, credits, staff_id, dept_id)
            print('Course added successfully!', 'success')
        
        elif action == 'remove':
            cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
            dept_result = cursor.fetchone()
            if not dept_result:
                return "Department not found for user.", 404
            dept_id = dept_result[0]
            
            course_code = request.form.get('course_code')
            staff_remove_course(operations, course_code, dept_id)
            print('Course removed successfully!', 'success')
        
        elif action == 'modify':
            #staff_id = session.get('username') 
            attribute = request.form.get('attribute')
            modification = request.form.get('modification')
            course_code = request.form.get('course_code')
            staff_modify_course(operations, attribute, modification, course_code)
            print('Course modified successfully!', 'success')
        
        conn.close()
        return redirect(url_for('staff_manage_courses'))
    
    except Exception as e:
        print(f"An error occurred: {e}", "danger")
        return redirect(url_for('staff_manage_courses'))

# @app.route('/staff_manage_courses', methods=['GET', 'POST'])
# def staff_manage_courses():
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     staff_id = request.form.get('staff_id')  # Assuming staff_id is submitted in the form

#     if request.method == 'GET':
#         # Query to get the department ID for the current staff member
#         cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
#         department = cursor.fetchone()  # Get department data as a tuple
        
#         if department:
#             department_id = department[0]  # Access dept_id by index, assuming it's the first column
#             # Query to fetch courses for the staff member's department
#             cursor.execute("SELECT course_code, course_name FROM Courses WHERE dept_id = %s", (department_id,))
#             courses = cursor.fetchall()  # Get courses data as a list of tuples
#         else:
#             courses = []

#         conn.close()
#         return render_template('staff_manage_courses.html', courses=courses)

#     if request.method == 'POST':
#         action = request.form.get('action')  # Determine action: 'add', 'remove', 'modify'
#         staff_id = request.form.get('staff_id')  # Assuming staff_id is submitted in the form
        
#         if action == 'add':
#             course_code = request.form.get('course_code')
#             course_name = request.form.get('course_name')
#             credits = request.form.get('credits')
#             staff_add_course(course_code, course_name, credits, staff_id)
#             print('Course added successfully!', 'success')
        
#         elif action == 'remove':
#             course_code = request.form.get('course_code')
#             staff_remove_course(course_code, staff_id)
#             print('Course removed successfully!', 'success')
        
#         elif action == 'modify':
#             attribute = request.form.get('attribute')
#             modification = request.form.get('modification')
#             course_code = request.form.get('course_code')
#             staff_modify_course(attribute, modification, course_code, staff_id)
#             print('Course modified successfully!', 'success')
        
#         conn.close()  # Make sure connection is properly closed
#         return redirect(url_for('staff_manage_courses'))



# @app.route('/staff_manage_courses', methods=['GET', 'POST'])
# def staff_manage_courses():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     database_operations_instance = DatabaseOperations(conn)
#     staff_id = request.form.get('staff_id')  # Assuming staff_id is submitted in the form


#     if request.method == 'GET':
#             # Query to get the department ID for the current staff member
#             cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
#             department = cursor.fetchone()  # Get department data as a tuple
            
#             if department:
#                 department_id = department[0]  # Access dept_id by index, assuming it's the first column
#                 # Query to fetch courses for the staff member's department
#                 cursor.execute("SELECT course_code, course_name FROM Courses WHERE dept_id = %s", (department_id,))
#                 courses = cursor.fetchall()  # Get courses data as a list of tuples
#             else:
#                 courses = []

#             conn.close()
#             return render_template('staff_manage_courses.html', courses=courses)
        
#     if request.method == 'POST':
#         action = request.form.get('action')  # Determine action: 'add', 'remove', 'modify'
#         staff_id = request.form.get('staff_id')  # Assuming staff_id is submitted in the form
        
#         if action == 'add':
#             course_code = request.form.get('course_code')
#             course_name = request.form.get('course_name')
#             credits = request.form.get('credits')
#             staff_add_course(course_code, course_name, credits, staff_id)
#             print('Course added successfully!', 'success')
        
#         elif action == 'remove':
#             course_code = request.form.get('course_code')
#             staff_remove_course(course_code, staff_id)
#             print('Course removed successfully!', 'success')
        
#         elif action == 'modify':
#             attribute = request.form.get('attribute')
#             modification = request.form.get('modification')
#             course_code = request.form.get('course_code')
#             staff_modify_course(attribute, modification, course_code, staff_id)
#             print('Course modified successfully!', 'success')
        
#         conn.close()  # Make sure connection is properly closed
#         return redirect(url_for('staff_manage_courses'))

@app.route('/staff_manage_departments', methods=['GET', 'POST'])
def staff_manage_departments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        database_operations_instance = DatabaseOperations(conn)
        
        staff_id = session.get('username')  # Ensure 'username' is in session
        cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
        dept_result = cursor.fetchone()
        
        if not dept_result:
            return "Department not found for user.", 404
        dept_id = dept_result[0]

        if request.method == 'POST':
            action = request.form.get('action')
            staff_id = request.form.get('staff_id')
            
            if action == 'modify':
            
                attribute = request.form.get('attribute')
                modification = request.form.get('modification')
                
                # Call the function to modify the department
                staff_modify_department(database_operations_instance,attribute, modification, dept_id)
                print('Department modified successfully!', 'success')
            
            # Close the connection after modifying
            conn.close()
            return redirect(url_for('staff_manage_departments'))
        
        # For GET requests, render the page template for managing departments
        conn.close()
        return render_template('staff_manage_departments.html')
    
    except Exception as e:
        print(f"An error occurred: {e}", "danger")
        return redirect(url_for('staff_manage_departments'))




@app.route('/staff_manage_instructors', methods=['GET', 'POST'])
def staff_manage_instructors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db = DatabaseOperations(conn)
        
        staff_id = session.get('username')  # Ensure 'username' is in session
        cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
        dept_result = cursor.fetchone()
        
        if not dept_result:
            return "Department not found for user.", 404
        dept_id = dept_result[0]
        
        if request.method == 'GET':
            # Fetch instructor IDs for the department
            cursor.execute("""
                SELECT instructor_id 
                FROM instructors 
                WHERE dept_id = %s
            """, (dept_id,))
            instructors = cursor.fetchall()  # Get list of instructor IDs

            # Fetch course IDs for the department
            cursor.execute("""
                SELECT course_code 
                FROM courses 
                WHERE dept_id = %s
            """, (dept_id,))
            courses_instructor = cursor.fetchall()  # Get list of course IDs
            
            
            
            # Fetch course IDs for the department
            cursor.execute("""
                SELECT * 
                FROM courses 
                WHERE dept_id = %s
            """, (dept_id,))
            data = cursor.fetchall()  # Get list of course IDs
            
            conn.close()

            # Pass both instructors and courses_instructor to the template
            return render_template('staff_manage_instructors.html', instructors=instructors, courses_instructor=courses_instructor)

        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':            
                instructor_id = request.form.get('instructor_id', type=int)
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                hired_sem = request.form.get('hired_sem')
                instructor_phone = request.form.get('instructor_phone')
                staff_add_instructor(db, instructor_id, username, email, password, hired_sem, instructor_phone, dept_id)
                print("Instructor added successfully!", "success")
            
            elif action == 'remove':
                instructor_id = request.form.get('instructor_id', type=int)
                staff_remove_instructor(db, instructor_id, dept_id)
                print("Instructor removed successfully!", "success")
            
            elif action == 'modify':
                instructor_id = request.form.get('instructor_id', type=int)
                attribute = request.form.get('attribute')
                modification = request.form.get('modification')
                staff_modify_instructor(db, attribute, modification, instructor_id, dept_id)
                print("Instructor modified successfully!", "success")
                
            elif action == 'assign':
                # Fetch course IDs for the department
                cursor.execute("""
                    SELECT * 
                    FROM courses 
                    WHERE dept_id = %s
                    """, (dept_id,))
                data = cursor.fetchall()  # Get list of course IDs
                
                cursor.close()
                
                # Fetch instructor_id, course_code, and dept_id from form
                instructor_id = request.form.get('instructor_id', type=int)
                course_code = request.form.get('course_code')
                semester = 'F'
                year_taught =  '2024'
                 # Find the credits value for the selected course_code
                credits = next((course[3] for course in data if course[0] == course_code), None)
                
                data2 = {
                    'instructor_id' : instructor_id,
                    'course_code' : course_code,
                    'semester': semester,
                    'year_taught' : year_taught,
                    'credits' : credits
                }
                db.add_entry('InstructorCourse', data2)
                
                print(data2)
                
                # Assign the course to the instructor (implement this logic as needed)
                # cursor.execute("""
                #     INSERT INTO instructorcourse (instructor_id, course_code, dept_id, semester)
                #     VALUES (%s, %s, %s, %s, %s)
                # """, (instructor_id, course_code, dept_id, semester, year_taught, credits))
                
                # conn.commit()
                print("Course assigned to instructor successfully!", "success")
            
            conn.close()
            return redirect(url_for('staff_manage_instructors'))
        
    except Exception as e:
        print(f"An error occurred: {e}", "danger")
        return redirect(url_for('staff_manage_instructors'))



@app.route('/staff_manage_students', methods=['GET', 'POST'])
def staff_manage_students():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db = DatabaseOperations(conn)
        
        staff_id = session.get('username')  # Ensure session has 'username' set
        cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
        dept_result = cursor.fetchone()
        if not dept_result:
            return "Department not found for user.", 404
        dept_id = dept_result[0]
        
        print(staff_id)
        
        
        if request.method == 'GET':
            # Fetch only instructor_id for the department
            cursor.execute("""
                SELECT stud_id 
                FROM students 
                WHERE dept_id = %s
            """, (dept_id,))
            student = cursor.fetchall()  # Get list of instructor IDs
            
            print(student)
            # Closing the connection after the GET operation
            conn.close()

            return render_template('staff_manage_students.html', student=student)

        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':
                user_id = request.form.get('user_id', type=int)
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                gender = request.form.get('gender')
                major = request.form.get('major')
                # dept_id = request.form.get('dept_id', type=int)
                staff_add_student(db,user_id, username, email, password, gender, major, dept_id)
                print("Student added successfully!", "success")
            
            elif action == 'remove':
                stud_id = request.form.get('stud_id', type=int)
                cursor.execute("SELECT dept_id FROM Staff WHERE staff_id = %s", (staff_id,))
                dept_result = cursor.fetchone()
                if not dept_result:
                    return "Department not found for user.", 404
                dept_id = dept_result[0]
                staff_remove_student(db,stud_id, dept_id)
                print("Student removed successfully!", "success")
            
            elif action == 'modify':
                stud_id = request.form.get('stud_id', type=int)
                attribute = request.form.get('attribute')
                modification = request.form.get('modification')
                staff_modify_student(db,attribute, modification, stud_id)
                print("Student modified successfully!", "success")

            conn.close()
            return redirect(url_for('staff_manage_students'))

        # For GET request, fetch students data to render on the page
        #students = db.get_all_entries('Students')
        conn.close()
        return render_template('staff_manage_students.html')

    except Exception as e:
        print(f"An error occurred: {e}", "danger")
        return redirect(url_for('staff_add_drop_modify'))

#/////////////////////////////////////////////////////////////////////////////
# Req 2
# @app.route('/advisor_add_drop', methods=['GET', 'POST'])
# def advisor_add_drop():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     operations = DatabaseOperations(conn)

#     # Retrieve the advisor's department
#     advisor_id = session['username']  # Assume `username` holds the advisor's user ID
#     advisor_query = "SELECT dept_id FROM Advisors WHERE adv_id = %s"
#     advisor_dept = cursor.execute(advisor_query, (advisor_id,)).fetchone()['dept_id']

#     # Query students and courses for dropdowns
#     student_query = """
#         SELECT stud_id, (SELECT username FROM UserInfo WHERE user_id = stud_id) AS name 
#         FROM Students WHERE dept_id = %s
#     """
#     course_query = """
#         SELECT course_code, course_name FROM Courses WHERE dept_id = %s
#     """
#     students = cursor.execute(student_query, (advisor_dept,)).fetchall()
#     courses = cursor.execute(course_query, (advisor_dept,)).fetchall()
    
#     conn.close()

#     return render_template('advisor_add_drop.html', students=students, courses=courses)

# @app.route('/advisor_add_drop', methods=['GET', 'POST'])
# def advisor_add_drop():
#     # Establish a database connection
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     operations = DatabaseOperations(conn)

#     # Retrieve the advisor's department
#     advisor_id = session.get('username')  # Get advisor_id from session

#     if not advisor_id:
#         # If 'username' (advisor_id) is not in the session, handle it by redirecting or returning an error
#         print("Advisor ID not found in session.")
#         conn.close()
#         return redirect('/login')  # Redirect to login or a relevant page if not logged in

#     # Fetch advisor's department ID by iterating over the cursor
#     advisor_query = "SELECT dept_id FROM Advisors WHERE adv_id = %s"
#     cursor.execute(advisor_query, (advisor_id,))
#     advisor_dept = None

#     for row in cursor:
#         advisor_dept = row[0]  # Assume `dept_id` is in the first column
#         break  # Only need the first result, so we break after fetching it

#     if advisor_dept is None:
#         # Handle the case where no department is found for the advisor
#         print(f"No department found for advisor_id: {advisor_id}")
#         conn.close()
#         return "Department not found for this advisor.", 404

#     # Retrieve students for the advisor's department
#     student_query = """
#         SELECT stud_id, (SELECT username FROM UserInfo WHERE user_id = stud_id) AS name 
#         FROM Students WHERE dept_id = %s
#     """
#     cursor.execute(student_query, (advisor_dept,))
#     students = [(row[0]) for row in cursor]  # Assuming `stud_id` and `name` are in columns 0 and 1

#     # Retrieve courses for the advisor's department
#     course_query = """
#         SELECT course_code FROM Courses WHERE dept_id = %s
#     """
#     cursor.execute(course_query, (advisor_dept,))
#     courses = [(row[0]) for row in cursor]  # Assuming `course_code` and `course_name` are in columns 0 and 1

#     print(courses)
#     print(students)

#     # Close the connection
#     conn.close()

#     # Render the page with students and courses populated in the dropdowns
#     return render_template('advisor_add_drop.html', students=students, courses=courses)
@app.route('/advisor_add_drop', methods=['GET', 'POST'])
def advisor_add_drop():
    # Establish a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve the advisor's department ID from the session
    advisor_id = session.get('username')  # Get advisor_id from session

    if not advisor_id:
        # If 'username' (advisor_id) is not in the session, handle it by redirecting or returning an error
        print("Advisor ID not found in session.")
        conn.close()
        return redirect('/login')  # Redirect to login or a relevant page if not logged in

    # Fetch advisor's department ID
    advisor_query = "SELECT dept_id FROM Advisors WHERE adv_id = %s"
    cursor.execute(advisor_query, (advisor_id,))
    advisor_dept = next(cursor, (None,))[0]

    if advisor_dept is None:
        # Handle the case where no department is found for the advisor
        print(f"No department found for advisor_id: {advisor_id}")
        conn.close()
        return "Department not found for this advisor.", 404

    # Retrieve students for the advisor's department
    student_query = """
        SELECT stud_id, (SELECT user_id FROM UserInfo WHERE user_id = stud_id) AS name 
        FROM Students WHERE dept_id = %s
    """
    cursor.execute(student_query, (advisor_dept,))
    students = [{"stud_id": row[0], "name": row[1]} for row in cursor]

    # Retrieve courses for the advisor's department
    course_query = """
        SELECT course_code, course_name FROM Courses WHERE dept_id = %s
    """
    cursor.execute(course_query, (advisor_dept,))
    courses = [{"course_code": row[0], "course_name": row[1]} for row in cursor]

    # Close the connection
    conn.close()

    # Render the page with students and courses populated in the dropdowns
    return render_template('advisor_add_drop.html', students=students, courses=courses)


@app.route('/add_student', methods=['POST'])
def add_student():
    conn = get_db_connection()
    cursor = conn.cursor()
    operations = DatabaseOperations(conn)
    
    try:
        student_id = request.form['student_id']
        course_code = request.form['course_code']
        semester = "F"  # You can adjust as necessary or fetch from form
        year_taken = "2024"  # Adjust as necessary or fetch from form
        grade = "A"  # Adjust as necessary or fetch from form
        credits = 3  # Adjust as necessary

        # Check if the student is already enrolled in the course
        query_check = """
            SELECT 1 FROM StudentCourse
            WHERE stud_id = %s AND course_code = %s
        """
        cursor.execute(query_check, (student_id, course_code))
        already_enrolled = cursor.fetchone()

        if already_enrolled:
            # If already enrolled, you can add a message or redirect
            print(f"Student {student_id} is already enrolled in course {course_code}.")
            return redirect('/advisor_add_drop')  # Or show an appropriate message to the user

        # If not enrolled, insert the new student-course association
        query_insert = """
            INSERT INTO StudentCourse (stud_id, course_code, semester, year_taken, grade, credits)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_insert, (student_id, course_code, semester, year_taken, grade, credits))
        conn.commit()  # Don't forget to commit the transaction to save the changes
        
        # # After successful insertion, perform any necessary post-insertion operations
        # advisor_add_student(operations, student_id, course_code, semester, year_taken, grade, credits)
        
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        conn.close()
    
    return redirect('/advisor_add_drop')  # Redirect back to the advisor add/drop page


# @app.route('/add_student', methods=['POST'])
# def add_student():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     operations = DatabaseOperations(conn)
#     try:
#         student_id = request.form['student_id']
#         course_code = request.form['course_code']
#         semester = "F"
#         year_taken = "2024"
#         grade = "A"
#         credits = 3
        
#         query = """FROM stud_id
#                 SELECT """

#         advisor_add_student(operations, student_id, course_code, semester, year_taken, grade, credits)
#     except Exception as e:
#         print(f'Error: {str(e)}')
#     finally:
#         conn.close()
    
#     return redirect('/advisor_add_drop')


@app.route('/drop_student', methods=['POST'])
def drop_student():
    conn = get_db_connection()
    operations = DatabaseOperations(conn)
    try:
        student_id = request.form['student_id']
        course_code = request.form['course_code']
        

        advisor_drop_student(operations, student_id, course_code)
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        conn.close()
    
    return redirect('/advisor_add_drop')


@app.route('/get_student_courses', methods=['POST'])
def get_student_courses():
    conn = get_db_connection()
    student_id = request.form['student_id']

    # Fetch courses the student is registered for
    query = """
        SELECT sc.course_code, c.course_name
        FROM StudentCourse sc
        JOIN Courses c ON sc.course_code = c.course_code
        WHERE sc.stud_id = %s
    """
    student_courses = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return student_courses


#/////////////////////////////////////////////////////////////////////////////
# Req 4
# Covered by database with primary keys

#/////////////////////////////////////////////////////////////////////////////
# Req 5
# Logging is already called within functions to add each log
# Log.html covers already

#/////////////////////////////////////////////////////////////////////////////
# Req 6
# 

#/////////////////////////////////////////////////////////////////////////////
# Req 7



@app.route('/gpa_stats', methods=['GET'])
def gpa_stats():
    operations = DatabaseOperations(get_db_connection()) 

    try:
        # Call the gpa_stats function
        major_results, department_results, highest_dept, lowest_dept = operations.gpa_stats(conn)
        
        # Render the data as plain HTML or send the variables to a template
        return render_template(
            'gpa_stats.html',
            major_results=major_results,
            department_results=department_results,
            highest_dept=highest_dept,
            lowest_dept=lowest_dept
        )
    except Exception as e:
        # Handle unexpected errors
        return f"An error occurred: {str(e)}", 500

@app.route('/course_stats', methods=['GET'])
def course_stats():
    
    operations = DatabaseOperations(get_db_connection()) 

    try:
        # Call the course_stats function
        course_data = operations.course_stats(conn)

        if "error" in course_data:
            return f"Error: {course_data['error']}", 500

        # Render the course data to the HTML template
        return render_template('course_stats.html', course_data=course_data)
    except Exception as e:
        # Handle unexpected errors
        return f"An error occurred: {str(e)}", 500


@app.route('/instructor_stats', methods=['GET'])
def instructor_stats():
    operations = DatabaseOperations(get_db_connection()) 

    try:
        instructor_data = operations.instructor_stats(conn)

        if "error" in instructor_data:
            return f"Error: {instructor_data['error']}", 500

        # Render the course data to the HTML template
        return render_template('instructor_stats.html', instructor_data=instructor_data)
    except Exception as e:
        # Handle unexpected errors
        return f"An error occurred: {str(e)}", 500
    
@app.route('/student_stats', methods=['GET'])
def student_stats():
    operations = DatabaseOperations(get_db_connection()) 

    try:
        student_data = operations.student_stats(conn)

        if "error" in student_data:
            return f"Error: {student_data['error']}", 500

        # Render the course data to the HTML template
        return render_template('student_stats.html', student_data=student_data)
    except Exception as e:
        # Handle unexpected errors
        return f"An error occurred: {str(e)}", 500

# #Function to open all routes in the default web browser when the app starts
# def visit_all_routes():
#     base_url = "http://127.0.0.1:5000"  # Adjust this if your app runs on a different host/port
#     routes = [
#         '/login',
#         '/admin_menu',
#         '/advisor_menu',
#         '/course_summary',
#         '/create_user',
#         '/department_summary',
#         '/edit_instructor_info',
#         '/edit_user',
#         '/gpa_calculator',
#         '/instructor_menu',
#         '/instructor_summary',
#         '/log',
#         '/logout',
#         '/my_courses',
#         '/my_grades',
#         '/my_info',
#         '/staff_menu',
#         '/student_info',
#         '/student_menu',
#         '/student_summary',
#         '/student_summary_advisor',
#         '/user_info'
#         '/advisor_add_drop',
#         '/course_stats',
#         '/gpa_stats',
#         '/instructor_stats',
#         '/staff_add_drop_modify',
#         '/stats_menu',
#         '/student_stats',
#         '/what_if_analysis',
#         '/what_if_results',
#         '/what_if_analysis_advisor',
#         '/what_if_results_advisor',
#     ]

#     for route in routes:
#         full_url = base_url + route
#         #response = client.get(route)
#         #print(f"Visiting {route} - Status Code: {response.status_code}")
#         print(f"Opening {full_url}")
#         webbrowser.open(full_url)
#         time.sleep(1)  # Delay to prevent opening all pages at once

# Call this function once your app is running


# if __name__ == "__main__":
#     # Automatically open the browser to the Flask app URL
#     webbrowser.open('http://127.0.0.1:5000/staff_menu')
    
#     # Start the Flask app in debug mode
#     app.run(debug=True)

if __name__ == "__main__":
    # Automatically open the browser to the Flask app URL
    webbrowser.open('http://127.0.0.1:5000/login')

    # visit_all_routes()
    # Start the Flask app in debug mode
    app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent the test client from running twice
    
    # Call the function to visit all routes after the app starts