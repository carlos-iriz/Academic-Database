# app.py (Flask Backend)

from flask import Flask, jsonify, request, session, render_template, redirect, url_for, json
import psycopg2
from psycopg2.extras import RealDictCursor
import webbrowser
import time

# from Database_Backend import (
#     DatabaseOperations, Students, staff_add_course, staff_remove_course, staff_modify_course, 
#     staff_add_instructor, staff_remove_instructor, staff_modify_instructor,
#     staff_add_student, staff_remove_student, staff_modify_student,
#     staff_modify_department, staff_assign_course_to_instructor,
#     advisor_add_student, advisor_drop_student,
#     view_student_info, view_student_enrolled_courses, view_instructor_courses,
#     log_operation, view_log
# )

from Database_Backend import (
    DatabaseOperations, Students
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
        GROUP BY c.course_code, c.course_name, i.instructor_id, d.name, c.credits
        ORDER BY c.course_name;
    """

    # Execute the query to fetch all courses
    cursor.execute(base_query)

    # Fetch all results
    courses = cursor.fetchall()

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

# @app.route('/department_summary')
# def department_summary():
#     # You can fetch course details here (e.g., list of courses)
#     # courses = get_courses(session['username'])
#     return render_template('department_summary.html')  # Assuming you have a course summary template


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
        cursor.close()
        conn.close()

    # Pass the data to the template
    return render_template('department_summary.html', department_summary=department_summary_data)


# @app.route('/department_summary')
# def department_summary():
#     # Ensure the user is logged in
#     if 'user_role' not in session or 'username' not in session:
#         return redirect(url_for('login'))  # Redirect to login if no role or username is set

#     user_role = session['user_role']
#     username = session['username']  # The username stored in session

#     # Connect to the database
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     departments = {}

#     try:
#         # Retrieve user_id based on username
#         cursor.execute("SELECT user_id FROM UserInfo WHERE username = %s", (username,))
#         user_id_record = cursor.fetchone()
#         if not user_id_record:
#             return "User not found.", 404  # Handle missing user case
#         user_id = user_id_record['user_id']

#         if user_role in ['Admin', 'Instructor']:
#             # Admins and Instructors can see all departments
#             query = """
#                 SELECT i.instructor_id, i.name, i.department, i.email
#                 FROM Instructors i
#                 ORDER BY i.department, i.name
#             """
#             cursor.execute(query)
        
#         elif user_role == 'Staff':
#             # Staff can see only their associated department
#             # Get the staff member's department
#             dept_query = "SELECT dept_id FROM Staff WHERE staff_id = %s"
#             cursor.execute(dept_query, (user_id,))
#             staff_dept = cursor.fetchone()
            
#             if staff_dept:
#                 # Fetch instructors only in the staff member's department
#                 query = """
#                     SELECT i.instructor_id, i.name, i.department, i.email
#                     FROM Instructors i
#                     WHERE i.department = %s
#                     ORDER BY i.name
#                 """
#                 cursor.execute(query, (staff_dept['dept_id'],))
#             else:
#                 return "No department found for staff member.", 403

#         else:
#             return redirect(url_for('login'))  # Redirect if user role is not allowed

#         # Process query results
#         instructors = cursor.fetchall()

#         # Group instructors by department
#         for instructor in instructors:
#             department = instructor['department']
#             if department not in departments:
#                 departments[department] = []
#             departments[department].append(instructor)

#     except Exception as e:
#         print(f"Error fetching instructors: {e}")
#     finally:
#         cursor.close()
#         conn.close()

#     # Pass the grouped instructors data to the template
#     return render_template('department_summary.html', departments=departments)


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

# @app.route('/instructor_summary')
# def instructor_summary():

#     return render_template('instructor_summary.html')  # Pass the course data to the template

@app.route('/instructor_summary')
def instructor_summary():
    # Ensure the user is logged in and has admin or appropriate access
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if no role or username is set

    user_role = session['user_role']
    # Admin or another role can access the instructor summary page
    if user_role not in ['Admin', 'Instructor']:  
        return redirect(url_for('login'))  # Redirect if user role is not allowed

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    instructors = []
    try:
        # Fetch all instructors from the Instructors table
        query = """
            SELECT instructor_id, name, department, email
            FROM Instructors
            ORDER BY name
        """
        cursor.execute(query)
        instructors = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching instructors: {e}")
    finally:
        cursor.close()
        conn.close()

    # Pass the instructor data to the template
    return render_template('instructor_summary.html', instructors=instructors)


# # Log Route (Admin access)
# @app.route('/log')
# def log():
#     # Log file or event viewer logic here
#     # logs = fetch_logs_from_db()
#     return render_template('log.html')  # Assuming you have a log template

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


# @app.route('/my_courses')
# def my_courses():
#     # Check if the user is logged in and if they are an instructor
#     if 'user_role' not in session or session['user_role'] != 'Instructor':
#         return redirect(url_for('login'))  # Redirect to login if not an instructor
    
#     instructor_id = session['username']  # Assuming the session stores the instructor's username or ID
#     # Connect to the database and fetch course details for the instructor
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT
#             c.course_name,
#             c.course_code,
#             i.instructor_id,  -- Instructor ID or name if applicable
#             d.name AS department_name,
#             c.credits,
#             AVG(
#                 CASE
#                     WHEN sc.grade = 'A' THEN 4.0
#                     WHEN sc.grade = 'B' THEN 3.0
#                     WHEN sc.grade = 'C' THEN 2.0
#                     WHEN sc.grade = 'D' THEN 1.0
#                     WHEN sc.grade = 'F' THEN 0.0
#                     ELSE NULL
#                 END
#             ) AS average_grade
#         FROM Courses c
#         JOIN Instructors i ON c.dept_id = i.dept_id
#         JOIN Departments d ON c.dept_id = d.dept_id
#         LEFT JOIN StudentCourse sc ON c.course_code = sc.course_code
#         WHERE i.instructor_id = %s
#         GROUP BY c.course_code, c.course_name, i.instructor_id, d.name, c.credits
#         ORDER BY c.course_name;
#     """, (instructor_id,))

#     courses = cursor.fetchall()  # Fetch all the courses for the instructor

#     cursor.close()
#     conn.close()
#     return render_template('my_courses.html', courses=courses)  # Assuming you have a template for my_courses


# # Log Route (Admin access)
# @app.route('/my_grades')
# def my_grades():
#     # Log file or event viewer logic here
#     # logs = fetch_logs_from_db()
#     return render_template('my_grades.html')  # Assuming you have a log template

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



# # My Information Route
# @app.route('/my_info')
# def my_info():
#     # Here you might want to fetch user-specific data from a database
#     # user_info = get_user_info_from_db(session['username'])
#     return render_template('my_info.html')  # Assuming you have a template for "my_info"

@app.route('/my_info')
def my_info():
    # Ensure the user is logged in
    if 'user_role' not in session or 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['username']  # Assume `username` maps to `user_id` in UserInfo
    conn = get_db_connection()
    cursor = conn.cursor()

    user_info = None

    try:
        # Fetch user-specific data from UserInfo table
        cursor.execute("SELECT * FROM UserInfo WHERE user_id = %s", (user_id,))
        user_info = cursor.fetchone()

        if not user_info:
            return redirect(url_for('login'))  # If no user info found, redirect to login

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred.", 500
    finally:
        cursor.close()
        conn.close()

    # Render the user information page
    return render_template('my_info.html', user_info=user_info if user_info else {})




# Log Route (Admin access)
@app.route('/staff_menu')
def staff_menu():
    # Log file or event viewer logic here
    # logs = fetch_logs_from_db()
    return render_template('staff_menu.html')  # Assuming you have a log template

# # Log Route (Admin access)
# @app.route('/student_info')
# def student_info():
#     # Log file or event viewer logic here
#     # logs = fetch_logs_from_db()
#     return render_template('student_info.html')  # Assuming you have a log template

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

# Student Summary Route
# @app.route('/student_summary')
# def student_summary():
#     # Here you can fetch the student summary (grades, courses, etc.) from a database
#     # student_info = get_student_summary(session['username'])
#     return render_template('student_summary.html')  # Assuming you have a student summary template


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

# @app.route('/student_summary')
# def student_summary():
#     # Ensure the user is logged in
#     if 'user_role' not in session or 'username' not in session:
#         return redirect(url_for('login'))  # Redirect to login if no role or username is set

#     user_role = session['user_role']
#     user_id = session['username']  # Assuming `username` is stored in session

#     # Connect to the database
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Prepare data for student summary
#     student_summary_data = []

#     try:
#         if user_role == 'Instructor':
#             # Fetch students in the instructor's courses
#             query = """
#                 SELECT DISTINCT s.stud_id, s.major, c.course_name
#                 FROM Students s
#                 JOIN StudentCourse sc ON s.stud_id = sc.stud_id
#                 JOIN Courses c ON sc.course_code = c.course_code
#                 JOIN Instructors i ON i.dept_id = c.dept_id
#                 JOIN userinfo u ON s.stud_id = u.user_id
#                 WHERE i.instructor_id = %s
#                 ORDER BY s.stud_id
#             """
#             cursor.execute(query, (user_id,))
#             student_summary_data = cursor.fetchall()

#         elif user_role == 'Advisor':
#             # Fetch all students in the advisor's department
#             query = """
#                 SELECT s.stud_id, s.major
#                 FROM Students s
#                 JOIN userinfo u ON s.stud_id = u.user_id
#                 JOIN Advisors a ON s.dept_id = a.dept_id
#                 WHERE a.advisor_id = %s
#                 ORDER BY s.stud_id
#             """
#             cursor.execute(query, (user_id,))
#             student_summary_data = cursor.fetchall()

#         elif user_role == 'Staff':
#             # Fetch all student information
#             query = """
#                 SELECT s.stud_id, s.major
#                 FROM Students s
#                 JOIN userinfo u ON s.stud_id = u.user_id
#                 ORDER BY s.stud_id
#             """
#             cursor.execute(query)
#             student_summary_data = cursor.fetchall()

#     except Exception as e:
#         print(f"Error fetching student summary: {e}")
#         student_summary_data = []

#     finally:
#         cursor.close()
#         conn.close()

#     # Render the template with student summary data
#     return render_template('student_summary.html', student_summary=student_summary_data)



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


        return render_template('what_if_results.html', results=calculated_data)
    return render_template('what_if_analysis.html', gpa = currGPA, creds = currCredits)


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


@app.route('/staff_add_drop_modify', methods=['GET'])
def staff_add_drop_modify():
    return render_template('staff_add_drop_modify.html')

@app.route('/process_staff_action', methods=['POST'])
def process_staff_action():
    action = request.form.get('action')
    attribute = request.form.get('attribute')
    modification = request.form.get('modification')
    course_code = request.form.get('course_code')
    instructor_id = request.form.get('instructor_id')
    student_id = request.form.get('student_id')
    #staff_id = username
    staff_id = session['username'] = user_info[0]


    # Instance of your database_operations class
    conn = get_db_connection()

    db_ops = DatabaseOperations(conn)

    if action == 'add_course':
        staff_add_course(db_ops, course_code, request.form.get('course_name'), request.form.get('credits'), staff_id)
    elif action == 'remove_course':
        staff_remove_course(db_ops, course_code, staff_id)
    elif action == 'modify_course':
        staff_modify_course(db_ops, attribute, modification, course_code, staff_id)
    elif action == 'add_instructor':
        staff_add_instructor(db_ops, instructor_id, request.form.get('username'), request.form.get('email'),
                             request.form.get('password'), request.form.get('hired_sem'),
                             request.form.get('instructor_phone'), staff_id)
    elif action == 'remove_instructor':
        staff_remove_instructor(db_ops, instructor_id, staff_id)
    elif action == 'modify_instructor':
        staff_modify_instructor(db_ops, attribute, modification, instructor_id, staff_id)
    elif action == 'add_student':
        staff_add_student(db_ops, student_id, request.form.get('username'), request.form.get('email'),
                          request.form.get('password'), request.form.get('gender'),
                          request.form.get('major'), request.form.get('dept_id'), staff_id)
    elif action == 'remove_student':
        staff_remove_student(db_ops, student_id, staff_id)
    elif action == 'modify_student':
        staff_modify_student(db_ops, attribute, modification, student_id, staff_id)
    elif action == 'modify_department':
        staff_modify_department(db_ops, attribute, modification, request.form.get('dept_id'), staff_id)
    elif action == 'assign_course':
        staff_assign_course_to_instructor(db_ops, instructor_id, request.form.get('course_id'), staff_id)
    else:
        return "Invalid action", 400

    return redirect(url_for('staff_add_drop_modify'))

#/////////////////////////////////////////////////////////////////////////////
# Req 2
@app.route('/advisor_add_drop', methods=['GET'])
def advisor_add_drop():
    return render_template('advisor_add_drop.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    conn = get_db_connection()
    operations = DatabaseOperations(conn)
    try:
        # Get form data
        student_id = request.form['student_id']
        course_code = request.form['course_code']
        semester = request.form['semester']
        year_taken = int(request.form['year_taken'])
        grade = request.form['grade']
        #advisor_id = username
        advisor_id = session['username'] = user_info[0]

        
        # Call your function
        operations.advisor_add_student(student_id, course_code, semester, year_taken, grade, advisor_id)
        print('Added to Course')
        # Flash success message if needed
    except Exception as e:
        print(f'Error: {str(e)}')
        # Flash error message if needed
    
    return redirect('/advisor_add_drop')

@app.route('/drop_student', methods=['POST'])
def drop_student():
    conn = get_db_connection()
    operations = DatabaseOperations(conn)
    try:
        # Get form data
        student_id = request.form['student_id']
        course_code = request.form['course_code']
        semester = request.form['semester']
        year_taken = int(request.form['year_taken'])
        #advisor_id = username
        advisor_id = session['username'] = user_info[0]

        
        # Call your function
        operations.advisor_drop_student(student_id, course_code, semester, year_taken, advisor_id)
        print('Dropped from Course')
        # Flash success message if needed
    except Exception as e:
        print(f'Error: {str(e)}')
        # Flash error message if needed
    
    return redirect('/advisor_add_drop')

#/////////////////////////////////////////////////////////////////////////////
# Req 3
# Done already in pages attached to student and instructor

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

# @app.route('/gpa_stats', methods=['GET'])
# def gpa_stats():
#     conn = get_db_connection()

#     result = DatabaseOperations.gpa_stats(conn)
#     return jsonify(result)  # Convert result dictionary to JSON

# @app.route('/gpa_stats_page', methods=['GET'])
# def gpa_stats_page():
#     return render_template('gpa_stats.html')  # Render the HTML file

# @app.route('/course_stats', methods=['GET'])
# def course_stats():
#     conn = get_db_connection()
#     result = DatabaseOperations.course_stats(conn)
#     return jsonify(result)  # Convert result dictionary to JSON

# @app.route('/course_stats_page', methods=['GET'])
# def course_stats_page():
#     return render_template('course_stats.html')  # Render the HTML file

# @app.route('/instructor_stats', methods=['GET'])
# def instructor_stats():
#     conn = get_db_connection()
#     result = DatabaseOperations.instructor_stats(conn)
#     return jsonify(result)  # Convert result dictionary to JSON

# @app.route('/instrcutor_stats_page', methods=['GET'])
# def instructor_stats_page():
#     return render_template('instructor_stats.html')  # Render the HTML file


# @app.route('/student_stats', methods=['GET'])
# def student_stats():
#     conn = get_db_connection()
#     result = DatabaseOperations.student_stats(conn)
#     return jsonify(result)  # Convert result dictionary to JSON

# @app.route('/student_stats_page', methods=['GET'])
# def student_stats_page():
#     return render_template('student_stats.html')  # Render the HTML file


# # GPA Stats Routes
# @app.route('/gpa_stats', methods=['GET'])
# def gpa_stats():
#     conn = get_db_connection()
#     db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
#     result = db_ops.gpa_stats(conn)        # Call the gpa_stats method on the instance
#     return jsonify(result)              # Convert result dictionary to JSON

# @app.route('/gpa_stats_page', methods=['GET'])
# def gpa_stats_page():
#     return render_template('gpa_stats.html')  # Render the HTML file

# # Course Stats Routes
# @app.route('/course_stats', methods=['GET'])
# def course_stats():
#     conn = get_db_connection()
#     db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
#     result = db_ops.course_stats(conn)     # Call the course_stats method on the instance
#     return jsonify(result)             # Convert result dictionary to JSON

# @app.route('/course_stats_page', methods=['GET'])
# def course_stats_page():
#     return render_template('course_stats.html')  # Render the HTML file

# # Instructor Stats Routes
# @app.route('/instructor_stats', methods=['GET'])
# def instructor_stats():
#     conn = get_db_connection()
#     db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
#     result = db_ops.instructor_stats(conn) # Call the instructor_stats method on the instance
#     return jsonify(result)             # Convert result dictionary to JSON

# @app.route('/instructor_stats_page', methods=['GET'])
# def instructor_stats_page():
#     return render_template('instructor_stats.html')  # Render the HTML file

# # Student Stats Routes
# @app.route('/student_stats', methods=['GET'])
# def student_stats():
#     conn = get_db_connection()
#     db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
#     result = db_ops.student_stats(conn)    # Call the student_stats method on the instance
#     return jsonify(result)             # Convert result dictionary to JSON

# @app.route('/student_stats_page', methods=['GET'])
# def student_stats_page():
#     return render_template('student_stats.html')  # Render the HTML file


# GPA Stats Routes
@app.route('/gpa_stats', methods=['GET'])
def gpa_stats():
    conn = get_db_connection()
    db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
    result = db_ops.gpa_stats(conn)    # Call the gpa_stats method on the instance
    return render_template('gpa_stats.html', stats=result)  # Render the HTML file with data

@app.route('/gpa_stats_page', methods=['GET'])
def gpa_stats_page():
    return render_template('gpa_stats.html')  # Render the HTML file


# Course Stats Routes
@app.route('/course_stats', methods=['GET'])
def course_stats():
    conn = get_db_connection()
    db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
    result = db_ops.course_stats(conn) # Call the course_stats method on the instance
    return render_template('course_stats.html', stats=result)  # Render the HTML file with data

@app.route('/course_stats_page', methods=['GET'])
def course_stats_page():
    return render_template('course_stats.html')  # Render the HTML file


# Instructor Stats Routes
@app.route('/instructor_stats', methods=['GET'])
def instructor_stats():
    conn = get_db_connection()
    db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
    result = db_ops.instructor_stats(conn) # Call the instructor_stats method on the instance
    return render_template('instructor_stats.html', stats=result)  # Render the HTML file with data

@app.route('/instructor_stats_page', methods=['GET'])
def instructor_stats_page():
    return render_template('instructor_stats.html')  # Render the HTML file


# Student Stats Routes
@app.route('/student_stats', methods=['GET'])
def student_stats():
    conn = get_db_connection()
    db_ops = DatabaseOperations(conn)  # Create an instance of DatabaseOperations
    result = db_ops.student_stats(conn) # Call the student_stats method on the instance
    return render_template('student_stats.html', stats=result)  # Render the HTML file with data

@app.route('/student_stats_page', methods=['GET'])
def student_stats_page():
    return render_template('student_stats.html')  # Render the HTML file



if __name__ == "__main__":
    # Automatically open the browser to the Flask app URL
    webbrowser.open('http://127.0.0.1:5000/login')

    #visit_all_routes()
    # Start the Flask app in debug mode
    app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent the test client from running twice
    
    # Call the function to visit all routes after the app starts