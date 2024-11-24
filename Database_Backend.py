import psycopg2

# Database credentials
hostname = 'academic-database-main.chs4cey0uprk.us-east-2.rds.amazonaws.com'
database = 'Academic_Database'
username = 'postgres'
pwd = 'pops1234'
port_id = 5432

conn = None
cursor = None

#CURRENT PROGRAM!!!!
# This is carlos's branch updated

########################################################################################################################
########################################################################################################################
# Classes to hold database information from user classes (Student, Instructor, Staff, Advisor)
# Has User as parent class and then specific types as children
# IMPORTANT AT LOG IN WE MAKE A USER OBJ AND AN OBJ THAT CORRESPONDS TO THAT SPECIFC USER IN THE TABLE IF ITS A USER TYPE IN A TABLE

class User:
    def __init__(self, conn, user_id):
        """Initialize a User object by querying the database with the user_id."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, role, password 
            FROM UserInfo 
            WHERE user_id = %s
            """,
            (user_id,)
        )
        result = cursor.fetchone()

        if result:
            self.user_id, self.username, self.email, self.role, self.password = result
        else:
            raise ValueError(f"No record found in UserInfo for user_id {user_id}")

    @classmethod
    def from_database(cls, conn, user_id):
        """Factory method to create a User object from the database."""
        return cls(conn, user_id)

# Students class
class Students:
    def __init__(self, conn, stud_id):
        cursor = conn.cursor()
        cursor.execute("SELECT stud_id, gender, major, dept_id FROM Students WHERE stud_id = %s", (stud_id,))
        result = cursor.fetchone()

        if result:
            self.stud_id, self.gender, self.major, self.dept_id = result
            self.courses = []  # Initialize an empty list to store courses
        else:
            raise ValueError(f"No record found in Students for stud_id {stud_id}")

    @classmethod
    def from_database(cls, conn, stud_id):
        return cls(conn, stud_id)

    def load_courses(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT course_code 
            FROM StudentCourse 
            WHERE stud_id = %s
            """, 
            (self.stud_id,)
        )
        results = cursor.fetchall()
        self.courses = [course_code for (course_code,) in results]

    def calculate_gpa(self, conn):

        grade_mapping = {
            'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
        }

        try:
            cursor = conn.cursor()
            # Query to fetch grades for the student
            cursor.execute(
                """
                SELECT grade 
                FROM studentcourse 
                WHERE stud_id = %s
                """,
                (self.stud_id,)
            )

            grades = cursor.fetchall()

            if not grades:
                print(f"No grades found for student ID: {self.stud_id}")
                return None

            # Convert grades to numeric values using grade_mapping
            numeric_grades = [grade_mapping[grade[0]] for grade in grades if grade[0] in grade_mapping]
            
            if not numeric_grades:
                print(f"No valid grades found for student ID: {self.stud_id}")
                return None

            # Calculate GPA by averaging the numeric grades
            gpa = round(sum(numeric_grades) / len(numeric_grades), 2)

            return gpa

        except Exception as e:
            print(f"Error calculating GPA for student {self.stud_id}: {e}")
            return None

        finally:
            # Ensure cursor is closed even if an error occurs
            cursor.close()


# Instructors class
class Instructors:
    def __init__(self, conn, instructor_id):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT instructor_id, dept_id, hired_sem, instructor_phone FROM Instructors WHERE instructor_id = %s", (instructor_id,)
        )
        result = cursor.fetchone()

        if result:
            self.instructor_id, self.dept_id, self.hired_sem, self.instructor_phone = result
            self.courses = []  # Initialize an empty list to store courses
        else:
            raise ValueError(f"No record found in Instructors for instructor_id {instructor_id}")

    @classmethod
    def from_database(cls, conn, instructor_id):
        return cls(conn, instructor_id)

    def load_courses(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT course_code 
            FROM InstructorCourse 
            WHERE instructor_id = %s
            """, 
            (self.instructor_id,)
        )
        results = cursor.fetchall()
        self.courses = [course_code for (course_code,) in results]


# Staff class
class Staff:
    def __init__(self, conn, staff_id):
        cursor = conn.cursor()
        cursor.execute("SELECT staff_id, dept_id, phone FROM Staff WHERE staff_id = %s", (staff_id,))
        result = cursor.fetchone()

        if result:
            self.staff_id, self.dept_id, self.phone = result
        else:
            raise ValueError(f"No record found in Staff for staff_id {staff_id}")

    @classmethod
    def from_database(cls, conn, staff_id):
        return cls(conn, staff_id)


# Advisors class
class Advisors:
    def __init__(self, conn, adv_id):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT adv_id, total_hours_reg, major_offered, dept_id, advisor_phone, building, office 
            FROM Advisors WHERE adv_id = %s
            """,
            (adv_id,)
        )
        result = cursor.fetchone()

        if result:
            (self.adv_id, self.total_hours_reg, self.major_offered, self.dept_id,
             self.advisor_phone, self.building, self.office) = result
        else:
            raise ValueError(f"No record found in Advisors for adv_id {adv_id}")

    @classmethod
    def from_database(cls, conn, adv_id):
        return cls(conn, adv_id)

########################################################################################################################
########################################################################################################################
# Remaining Tables

class Courses:
    def __init__(self, conn, course_code):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Courses WHERE course_code = %s", (course_code,))
        result = cursor.fetchone()

        if result:
            (self.course_code, self.course_name, self.dept_id, self.credits) = result
        else:
            raise ValueError(f"No course found with prefix {course_code}")

    @classmethod
    def load_all_courses(cls, conn):
        """Load all courses from the Courses table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Courses")
        courses = [cls(conn, row[0]) for row in cursor.fetchall()]
        return courses #Returns list of all courses in table

class Departments:
    def __init__(self, conn, dept_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Departments WHERE dept_id = %s", (dept_id,))
        result = cursor.fetchone()

        if result:
            (self.dept_id, self.name) = result
        else:
            raise ValueError(f"No department found with ID {dept_id}")

    @classmethod
    def load_all_departments(cls, conn):
        """Load all departments from the Departments table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Departments")
        departments = [cls(conn, row[0]) for row in cursor.fetchall()]
        return departments #Returns list of all courses in table


class Log:
    def __init__(self, conn, entry):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Log WHERE entry = %s", (entry,))
        result = cursor.fetchone()

        if result:
            (self.entry, self.timestamp, self.username, self.operationtype, self.old_data, self.new_data) = result
        else:
            raise ValueError(f"No log entry found with entry ID {entry}")

    @classmethod
    def load_all(cls, conn):
        """Load all logs from the Log table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Log")
        logs = [cls(conn, row[0]) for row in cursor.fetchall()]
        return logs  # Returns a list of all Log objects

class StudentCourse:
    def __init__(self, conn, stud_id, course_code, semester, year_taken):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM StudentCourse 
            WHERE stud_id = %s AND course_code = %s AND semester = %s AND year_taken = %s
        """, (stud_id, course_code, semester, year_taken))
        result = cursor.fetchone()

        if result:
            (self.stud_id, self.course_code, self.semester, self.year_taken, self.grade, self.credits) = result
        else:
            raise ValueError(f"No record found for student {stud_id} in course {course_code}")

    @classmethod
    def load_all(cls, conn):
        """Load all student-course records from the StudentCourse table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM StudentCourse")
        records = [cls(conn, *row[:5]) for row in cursor.fetchall()]
        return records  # Returns a list of all StudentCourse objects

class InstructorCourse:
    def __init__(self, conn, instructor_id, course_code, semester, year_taught):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM InstructorCourse 
            WHERE instructor_id = %s AND course_code = %s AND semester = %s AND year_taught = %s
        """, (instructor_id, course_code, semester, year_taught))
        result = cursor.fetchone()

        if result:
            (self.instructor_id, self.course_code, self.semester, self.year_taught, self.credits) = result
        else:
            raise ValueError(f"No record found for instructor {instructor_id} teaching course {course_code}")

    @classmethod
    def load_all(cls, conn):
        """Load all instructor-course records from the InstructorCourse table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM InstructorCourse")
        records = [cls(conn, *row[:5]) for row in cursor.fetchall()]
        return records  # Returns a list of all InstructorCourse objects

########################################################################################################################
########################################################################################################################

# Database operations class
# Specific checks and conditions to complete database operations will be done by utilizing views when a specific operation needs to be
# completed. For example if an instructor wants to drop a student: We create a view and display only the courses the instructor is
# part of. When the operation is done we feed the VIEW into the method instead of the entire table.

class DatabaseOperations:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def add_entry(self, table, data):
        # Construct query for checking existing entry
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query_check = f"SELECT * FROM {table} WHERE {list(data.keys())[0]} = %s"
        check_value = (list(data.values())[0],)

        query_insert = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())

        try:
            # Check if entry already exists
            self.cursor.execute(query_check, check_value)
            existing_entry = self.cursor.fetchone()
            
            if existing_entry:
                print(f"Entry already exists in {table} table.")
            else:
                self.cursor.execute(query_insert, values)
                self.conn.commit()
                print(f"Entry added to {table} table.")
        except psycopg2.Error as err:
            print(f"Error adding entry: {err}")

    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def add_user(self, user_data):
        """
        Adds a user by calling the `add_user_with_details` procedure.

        Args:
            user_data (dict): A dictionary containing keys matching the stored procedure's parameters.
        """
        # Prepare the stored procedure call
        procedure_call = """
        CALL add_user_with_details(
            %(user_id)s, %(username)s, %(email)s, %(role)s, %(password)s,
            %(gender)s, %(major)s, %(dept_id)s, %(hired_sem)s,
            %(phone)s, %(building)s, %(office)s
        )
        """

        # Fill missing optional fields with None if they are not present
        required_keys = [
            'user_id', 'username', 'email', 'role', 'password',
            'gender', 'major', 'dept_id', 'hired_sem', 'phone', 'building', 'office'
        ]
        user_data = {key: user_data.get(key) for key in required_keys}

        try:
            self.cursor.execute(procedure_call, user_data)
            self.conn.commit()
            print("User added successfully using the procedure.")
        except psycopg2.Error as err:
            print(f"Error adding user: {err}")

    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////


    def remove_entry(self, table, condition):
        condition_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        query = f"DELETE FROM {table} WHERE {condition_clause}"
        values = tuple(condition.values())

        try:
            self.cursor.execute(query, values)
            if self.cursor.rowcount > 0:
                self.conn.commit()
                print(f"Entry removed from {table} table.")
            else:
                print(f"No matching entry found to delete from {table} table.")
        except psycopg2.Error as err:
            print(f"Error removing entry: {err}")

    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def modify_entry(self, table, updates, condition):
        update_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        condition_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        query = f"UPDATE {table} SET {update_clause} WHERE {condition_clause}"
        values = tuple(updates.values()) + tuple(condition.values())

        try:
            self.cursor.execute(query, values)
            if self.cursor.rowcount > 0:
                self.conn.commit()
                print(f"Entry in {table} table modified.")
            else:
                print(f"No matching entry found to modify in {table} table.")
        except psycopg2.Error as err:
            print(f"Error modifying entry: {err}")

    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    def view_entry(self, table, condition):
        condition_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        query = f"SELECT * FROM {table} WHERE {condition_clause}"
        values = tuple(condition.values())

        try:
            self.cursor.execute(query, values)
            results = self.cursor.fetchall()  # Fetch all matching rows
            if results:
                print(f"Entries found in {table} table:")
                for row in results:
                    print(row)  
            else:
                print(f"No matching entries found in {table} table.")
        except psycopg2.Error as err:
            print(f"Error retrieving entries: {err}")

    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////

    ############## REQUIREMENT 7 IS 4 FUNCTIONS BELOW ###############
    # def gpa_stats(self, conn):
    #     grade_mapping = {
    #         'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    #         'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
    #     }

    #     try:
    #         cursor = conn.cursor()

    #         # Query to fetch all grades along with majors and departments
    #         cursor.execute(
    #             """
    #             SELECT s.major, d.name, sc.grade 
    #             FROM studentcourse sc
    #             JOIN students s ON sc.stud_id = s.stud_id
    #             JOIN departments d ON s.major = d.name
    #             """
    #         )

    #         rows = cursor.fetchall()

    #         if not rows:
    #             print("No data found.")

    #         # Create dictionaries to group grades by major and department
    #         major_grades = {}
    #         department_grades = {}
    #         for major, department, grade in rows:
    #             if grade in grade_mapping:
    #                 major_grades.setdefault(major, []).append(grade_mapping[grade])
    #                 department_grades.setdefault(department, []).append(grade_mapping[grade])

    #         # Calculate highest, lowest, and average GPA for each major
    #         major_results = {}
    #         for major, grades in major_grades.items():
    #             highest_gpa = max(grades)
    #             lowest_gpa = min(grades)
    #             average_gpa = round(sum(grades) / len(grades), 2)
    #             major_results[major] = {
    #                 'Highest GPA': highest_gpa,
    #                 'Lowest GPA': lowest_gpa,
    #                 'Average GPA': average_gpa
    #             }

    #         # Calculate average GPA for each department
    #         department_results = {}
    #         for department, grades in department_grades.items():
    #             average_gpa = round(sum(grades) / len(grades), 2)
    #             department_results[department] = average_gpa

    #         # Find department with highest and lowest average GPA
    #         highest_dept = max(department_results, key=department_results.get)
    #         lowest_dept = min(department_results, key=department_results.get)

    #         return {
    #         "major_results": major_results,
    #         "department_results": department_results,
    #         "highest_dept": (highest_dept, department_results[highest_dept]),
    #         "lowest_dept": (lowest_dept, department_results[lowest_dept])
    #         }


    #         # # Beautify the output
    #         # print("\n--- GPA Breakdown by Major ---")
    #         # for major, stats in major_results.items():
    #         #     print(f"Major: {major}")
    #         #     for key, value in stats.items():
    #         #         print(f"  {key}: {value}")
    #         #     print()

    #         # print("\n--- GPA Breakdown by Department ---")
    #         # for department, avg_gpa in sorted(department_results.items(), key=lambda x: x[1], reverse=True):
    #         #     print(f"Department: {department}, Average GPA: {avg_gpa}")

    #         # print(f"\nDepartment with Highest Average GPA: {highest_dept}, {department_results[highest_dept]}")
    #         # print(f"Department with Lowest Average GPA: {lowest_dept}, {department_results[lowest_dept]}")

    #     except Exception as e:
    #         print(f"Error: {e}")
    #         return None
    
    
    def gpa_stats(self, conn):
        grade_mapping = {
        'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
    }

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.major, d.name, sc.grade 
                FROM studentcourse sc
                JOIN students s ON sc.stud_id = s.stud_id
                JOIN departments d ON s.major = d.name
                """
            )
            rows = cursor.fetchall()
            if not rows:
                return [], [], {}, {}

            major_grades = {}
            department_grades = {}

            for major, department, grade in rows:
                if grade in grade_mapping:
                    major_grades.setdefault(major, []).append(grade_mapping[grade])
                    department_grades.setdefault(department, []).append(grade_mapping[grade])

            # Prepare the results
            major_results = [
                {
                    "major": major,
                    "highest_gpa": max(grades),
                    "lowest_gpa": min(grades),
                    "average_gpa": round(sum(grades) / len(grades), 2)
                }
                for major, grades in major_grades.items()
            ]

            department_results = [
                {
                    "department": department,
                    "average_gpa": round(sum(grades) / len(grades), 2)
                }
                for department, grades in department_grades.items()
            ]

            # Determine the highest and lowest GPA departments
            highest_dept = max(department_results, key=lambda x: x["average_gpa"])
            lowest_dept = min(department_results, key=lambda x: x["average_gpa"])

            return major_results, department_results, highest_dept, lowest_dept

        except Exception as e:
            return [], [], {"error": str(e)}, {}
    ###############################################################################

    def course_stats(self, conn):
        # Grade-to-point mapping, including +/- grades
        grade_mapping = {
            'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 
            'F': 0.0, 'S': 4.0, 'U': 0.0, 'I': 0.0
        }

        try:
            cursor = conn.cursor()

            # Query to fetch course enrollments, grades, and semesters
            cursor.execute(
                """
                SELECT sc.course_code, sc.semester, sc.grade
                FROM studentcourse sc
                """
            )
            rows = cursor.fetchall()

            if not rows:
                print("No data found.")
                return []

            # Dictionary to store enrollments and grades by course and semester
            course_stats = {}

            for course_code, semester, grade in rows:
                course_stats.setdefault((course_code, semester), {'enrollments': 0, 'grades': []})
                course_stats[(course_code, semester)]['enrollments'] += 1
                if grade in grade_mapping:
                    course_stats[(course_code, semester)]['grades'].append(grade_mapping[grade])

            # Calculate average grades for each course and semester
            results = {}
            for (course_code, semester), data in course_stats.items():
                enrollments = data['enrollments']
                average_grade = (
                    round(sum(data['grades']) / len(data['grades']), 2)
                    if data['grades'] else 0
                )
                # Handle case where there are no grades for a course
                if enrollments == 0:
                    average_grade = 0

                results.setdefault(semester, []).append({
                    'course_code': course_code,
                    'enrollments': enrollments,
                    'average_grade': average_grade
                })
            
            return results

            # # Beautify and display the output
            # print("\n--- Course Statistics by Semester ---")
            # for semester, stats in sorted(results.items()):
            #     print(f"\n{'='*50}")
            #     print(f"Semester: {semester}")
            #     print(f"{'='*50}")
            #     for course in stats:
            #         print(f"\n    Course:               {course['course_code']}")
            #         print(f"    Total Enrollments:    {course['enrollments']}")
            #         print(f"    Average Grade:        {course['average_grade']}")
            #         print(f"{'-'*50}")

        except Exception as e:
            print(f"Error: {e}")
            return []

    ######################################################################################################
    def instructor_stats(self, conn):
        try:
            cursor = conn.cursor()

            # Query to get total students by major for each instructor and course, regardless of semester
            query = """
            SELECT i.instructor_id, c.course_code, c.course_name AS course, s.major AS major, 
            COUNT(DISTINCT s.stud_id) AS total_students
            FROM instructors i
            JOIN instructorcourse ic ON i.instructor_id = ic.instructor_id
            JOIN courses c ON ic.course_code = c.course_code  
            JOIN studentcourse sc ON ic.course_code = sc.course_code
            JOIN students s ON sc.stud_id = s.stud_id
            GROUP BY i.instructor_id, c.course_code, s.major, c.course_name, c.dept_id
            ORDER BY i.instructor_id, c.course_code, s.major;
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                print("No data found.")
                return []

            # Group results by instructor and then by course
            instructor_courses = {}
            for row in rows:
                instructor_id, course_code, course_name, major_name, total_students = row
                if instructor_id not in instructor_courses:
                    instructor_courses[instructor_id] = {
                        'instructor_id': instructor_id,
                        'courses': []
                    }
                instructor_courses[instructor_id]['courses'].append({
                    'course_code': course_code,
                    'course_name': course_name,
                    'major_name': major_name,
                    'total_students': total_students
                })

            # # Beautify and display the output
            # print("\n--- Instructor Student Count by Major for Each Course ---")
            # for instructor_id, data in instructor_courses.items():
            #     print(f"\nInstructor ID: {instructor_id}")
            #     print("=" * 50)
            #     for course in data['courses']:
            #         print(f"\n  Course: {course['course_code']} - {course['course_name']}")
            #         print(f"  Major: {course['major_name']}")
            #         print(f"  Total Students: {course['total_students']}")
            #         print("-" * 50)

            return instructor_courses

        except Exception as e:
            print(f"Error: {e}")
            return []
    ############################################################################################################
    def student_stats(self, conn):
        try:
            cursor = conn.cursor()

            # Query to get students by major and their total credits, sorted by credits in descending order
            query = """
            SELECT s.major, s.stud_id, s.gender, SUM(sc.credits) AS total_credits
            FROM students s
            JOIN studentcourse sc ON s.stud_id = sc.stud_id
            JOIN courses c ON sc.course_code = c.course_code
            GROUP BY s.major, s.stud_id, s.gender
            ORDER BY s.major, total_credits DESC;
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                print("No data found.")
                return []

            # Group results by major
            major_students = {}
            for row in rows:
                major, stud_id, gender, total_credits = row
                if major not in major_students:
                    major_students[major] = {
                        'major': major,
                        'students': []
                    }
                major_students[major]['students'].append({
                    'stud_id': stud_id,
                    'gender': gender,
                    'total_credits': total_credits
                })

            # Beautify and display the output
            print("\n--- Student Statistics by Major ---")
            for major, data in major_students.items():
                print(f"\nMajor: {major}")
                print("=" * 50)
                for student in data['students']:
                    print(f"\n  Student ID: {student['stud_id']}")
                    print(f"  Gender: {student['gender']}")
                    print(f"  Total Credits: {student['total_credits']}")
                    print("-" * 50)
            
            # return major_students

        except Exception as e:
            print(f"Error: {e}")
            return []


    #/////////////////////////////////////////////////////////////////////////////////////////////////////////////


# Main function to initialize and perform database operations
def main():
    global conn, cursor

    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id
        )

        cursor = conn.cursor()

        #/////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # Creates tables in database only if the tables are not already in database

        create_tables = '''
        
            CREATE TABLE IF NOT EXISTS Departments (
                dept_id VARCHAR(9) PRIMARY KEY,
                name VARCHAR(50)
            );

            CREATE TABLE IF NOT EXISTS UserInfo (
                user_id INTEGER PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role VARCHAR(30) NOT NULL,
                password VARCHAR(20) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Students (
                stud_id INTEGER PRIMARY KEY,
                gender VARCHAR(10),
                major VARCHAR(100),
                dept_id VARCHAR(9),
                FOREIGN KEY (dept_id) REFERENCES Departments(dept_id),
                FOREIGN KEY (stud_id) REFERENCES UserInfo(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Courses (
                course_code CHAR(7) PRIMARY KEY,
                course_name VARCHAR(30),
                dept_id VARCHAR(9),
                credits INTEGER,
                FOREIGN KEY (dept_id) REFERENCES Departments(dept_id)
            );

            CREATE TABLE IF NOT EXISTS Instructors (
                instructor_id INTEGER PRIMARY KEY,
                dept_id VARCHAR(9),
                hired_sem VARCHAR(50),
                instructor_phone VARCHAR(20),
                FOREIGN KEY (dept_id) REFERENCES Departments(dept_id),
                FOREIGN KEY (instructor_id) REFERENCES UserInfo(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Staff (
                staff_id INTEGER PRIMARY KEY,
                dept_id VARCHAR(9),
                phone VARCHAR(20),
                FOREIGN KEY (dept_id) REFERENCES Departments(dept_id),
                FOREIGN KEY (staff_id) REFERENCES UserInfo(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Advisors (
                adv_id INTEGER PRIMARY KEY,
                total_hours_reg INT,
                major_offered VARCHAR(100),
                dept_id VARCHAR(9),
                advisor_phone VARCHAR(20),
                building VARCHAR(50),
                office VARCHAR(50),
                FOREIGN KEY (dept_id) REFERENCES Departments(dept_id),
                FOREIGN KEY (adv_id) REFERENCES UserInfo(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Log (
                entry INTEGER PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                user_id INTEGER NOT NULL REFERENCES UserInfo(user_id),
                operationtype VARCHAR(50) NOT NULL,
                old_data TEXT,
                new_data TEXT
            );

            CREATE TABLE IF NOT EXISTS StudentCourse (
                stud_id INTEGER,
                course_code CHAR(7),
                semester CHAR(1),
                year_taken CHAR(4),
                grade VARCHAR(10),
                credits INT,
                PRIMARY KEY (stud_id, course_code, semester, year_taken),
                FOREIGN KEY (stud_id) REFERENCES Students(stud_id),
                FOREIGN KEY (course_code) REFERENCES Courses(course_code)
            );

            CREATE TABLE IF NOT EXISTS InstructorCourse (
                instructor_id INTEGER,
                course_code CHAR(7),
                semester CHAR(1),
                year_taught CHAR(4),
                credits INT,
                PRIMARY KEY (instructor_id, course_code, semester, year_taught),
                FOREIGN KEY (instructor_id) REFERENCES Instructors(instructor_id),
                FOREIGN KEY (course_code) REFERENCES Courses(course_code)
            );
        '''

        # Executes creation statements in database
        cursor = conn.cursor()
        cursor.execute(create_tables)
        conn.commit()
        #/////////////////////////////////////////////////////////////////////////////////////////////////////////////

        print('Finished making tables')

        # Initialize StaffDatabaseOperations with connection
        operations = DatabaseOperations(conn)

    except psycopg2.Error as error:
        print(f"Error: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

##########################################################################################################################
##########################################################################################################################

# Requirement 1:
# Staff users have permissons to add, remove, and modify entries in course, instructor, student, and (Their)department
# CANNOT Register or widthdraw students from course (Cannot add or remove student from courses)
# Add overall check to make sure we are only giving them entires to alter in their department

def staff_add_remove_modify():
    """
    Contains functions to allow staff to add, remove, and modify courses, instructors, students, 
    and department entries within their department. Staff can only manage entries within their department.
    Args are staff user object and list containing all info you want to add to table
    """

    #
    #REMEMEBR TO CALL LOG FUNCTION after every operation in here
    #

    def staff_add_course(database_operations_instance, course_code, course_name, credits, staff_id):

        staff_user = Staff(staff_id)

        course_data = {
            'course_code' : course_code,
            'course_name' : course_name,
            'dept_id': staff_user.dept_id,
            'credits' : credits
        }

        database_operations_instance.add_entry('Courses', course_data)

        log_operation(database_operations_instance, staff_id, 'INSERT', new_data= course_data)


    def staff_remove_course(database_operations_instance, course_code, staff_id):
        staff_user = Staff(staff_id)
        condition = {'course_code': course_code, 'dept_id': staff_user.dept_id}
        database_operations_instance.remove_entry('Courses', condition)

        log_operation(database_operations_instance, staff_id, 'DELETE', old_data=course_code)


    #NEEDS SPECIAL UI INPUT
    #Show attributes for course table
    #Allow for them to select an attribute from drop down which is saved in "attribute"
    #Input field to enter desired change which is stored in "modification"
    def staff_modify_course(database_operations_instance, attribute, modification, course_code, staff_id):

        staff_user = Staff(staff_id)

        update = {attribute:modification}
        condition = {'course_code': course_code, 'dept_id':staff_user.dept_id} #MAY BE AN ERROR HERE BC OF SYNTAX!!!!!!! maybe comma
        database_operations_instance.modify_entry('Courses', update, condition)

        log_operation(database_operations_instance, staff_id, 'UPDATE', old_data= course_code, new_data=update) #Wrong tehe


    # ADD / REMOVE ENTRY IN USERS AND THEN ADD / REMOVE FROM INSTRUCTOR / STUDENT

    def staff_add_instructor(database_operations_instance, instructor_id, username, email, password, hired_sem, instructor_phone, staff_id):
        """
        Adds an instructor using the `add_user_with_details` procedure.
        
        Args:
            database_operations_instance: Instance of the DatabaseOperations class.
            instructor_id (int): Unique ID for the instructor.
            username (str): Username for the instructor.
            email (str): Email address of the instructor.
            password (str): Password for the instructor.
            hired_sem (str): Semester the instructor was hired.
            instructor_phone (str): Phone number of the instructor.
            staff_id (int): ID of the staff adding the instructor.
        """
        # Retrieve department ID based on the staff ID
        staff_user = Staff(staff_id)

        # Construct the data dictionary for the stored procedure
        instructor_data = {
            'user_id': instructor_id,
            'username': username,
            'email': email,
            'role': 'Instructor',
            'password': password,
            'gender': None,          # Not applicable for instructors
            'major': None,           # Not applicable for instructors
            'dept_id': staff_user.dept_id,
            'hired_sem': hired_sem,
            'phone': instructor_phone,
            'building': None,        # Not applicable for instructors
            'office': None           # Not applicable for instructors
        }

        # Call the add_user method with the instructor data
        database_operations_instance.add_user(instructor_data)
        log_operation(database_operations_instance, staff_id, 'INSERT', new_data= instructor_id)

    # Given on delete cascade in database should delete corresponding user
    def staff_remove_instructor(database_operations_instance, instructor_id, staff_id):

        staff_user = Staff(staff_id)

        condition = {'instructor_id': instructor_id, 'dept_id': staff_user.dept_id}
        database_operations_instance.remove_entry('Instructors', condition)
        log_operation(database_operations_instance, staff_id, 'DELETE', old_data=instructor_id)


    def staff_modify_instructor(database_operations_instance, attribute, modification, instructor_id, staff_id):

        staff_user = Staff(staff_id)

        update = {attribute: modification}
        condition = {'instructor_id': instructor_id, 'dept_id': staff_user.dept_id}
        database_operations_instance.modify_entry('Instructors', update, condition)
        log_operation(database_operations_instance, staff_id, 'UPDATE', old_data= instructor_id, new_data=update) #Wrong tehe


    def staff_add_student(database_operations_instance, user_id, username, email, password, gender, major, dept_id, staff_id):
        staff_user = Staff(staff_id)
        user_data = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'role': 'Student',
            'password': password,
            'gender': gender,
            'major': major,
            'dept_id': dept_id,
            'hired_sem': None,
            'phone': None,
            'building': None,
            'office': None
        }
        database_operations_instance.add_user(user_data)
        log_operation(database_operations_instance, staff_id, 'INSERT', new_data= user_id)



    # Given on delete cascade in database should delete corresponding user
    def staff_remove_student(database_operations_instance, stud_id, staff_id):

        staff_user = Staff(staff_id)

        condition = {'stud_id': stud_id, 'dept_id': staff_user.dept_id}
        database_operations_instance.remove_entry('Students', condition)
        log_operation(database_operations_instance, staff_id, 'DELETE', old_data=stud_id)



    def staff_modify_student(database_operations_instance, attribute, modification, stud_id, staff_id):

        staff_user = Staff(staff_id)

        update = {attribute: modification}
        condition = {'stud_id': stud_id, 'dept_id': staff_user.dept_id}
        database_operations_instance.modify_entry('Students', update, condition)

    # Staff can modify department that they belong to
    def staff_modify_department(database_operations_instance, attribute, modification, dept_id, staff_id):

        staff_user = Staff(staff_id)

        update = {attribute: modification}
        condition = {'dept_id': staff_user.dept_id}
        database_operations_instance.modify_entry('Departments', update, condition)
        log_operation(database_operations_instance, staff_id, 'UPDATE', old_data= dept_id, new_data=update) #Wrong tehe


    #Double check this function please
    def staff_assign_course_to_instructor(database_operations_instance, instructor_id, course_id, staff_id):

        staff_user = Staff(staff_id)

        instructor_condition = {'instructor_id': instructor_id, 'dept_id': staff_user.dept_id}
        course_condition = {'course_id': course_id, 'dept_id': staff_user.dept_id}
        try:
            instructor_valid = database_operations_instance.view_entry('Instructors', instructor_condition)
            course_valid = database_operations_instance.view_entry('Courses', course_condition)
            
            if instructor_valid and course_valid:
                updates = {'course_id': course_id}
                database_operations_instance.modify_entry('Instructors', updates, instructor_condition)
                print(f"Course {course_id} assigned to Instructor {instructor_id}.")
            else:
                print("Instructor and/or course do not belong to the staff user's department.")
        except psycopg2.Error as err:
            print(f"Error assigning course to instructor: {err}")

        log_operation(database_operations_instance, staff_id, 'INSERT', new_data= instructor_id)

    # Staff not allowed to touch "StudentCourse" table (Can't add or remove student from a course)

##########################################################################################################################
##########################################################################################################################
# Requirement 2:
# Advisors are allowed to add and drop students form courses as long as they are in the same department
# Student selection and course selections will appear in UI displaying infomration that matches:
# Student and user object match 

def advisor_add_drop_student():

    # Requires UI element that only allows for advisors to view students that are in their dept then select
    # Will be stored in student_id, function will pull student info from there
    # Same thing for course, show courses in their dept and then 
    # Will fulfill req that advisor can only add or drop those in dept
    def advisor_add_student(database_operations_instance, student_id, course_code, semester, year_taken, grade, advisor_id):
        """
        Adds a student to a course in the 'StudentCourse' table.
        
        Parameters:
        - database_operations_instance: An instance with methods to interact with the database.
        - student_id: Used to pull student entry from database
        - course_code: Used to pull course entry from database
        """

        student = Students(student_id)
        course = Courses(course_code)

        # Constructing the data to insert directly
        data = {
            'stud_id': student.stud_id,
            'course_code': course.course_code,
            'semester': semester,
            'year_taken': year_taken,
            'grade': grade,
            'credits' : course.credits
            }
        
        # Inserting into 'RegisteredFor' table
        database_operations_instance.add_entry('StudentCourse', data)
        log_operation(database_operations_instance, advisor_id, 'INSERT', new_data= student.stud_id)


    # Requires UI element that only allows for advisors to view students that are in their dept then select
    # Will be stored in student_id, function will pull student info from there
    # Same thing for course, show courses in their dept and then
    def advisor_drop_student(database_operations_instance, student_id, course_code, semester, year_taken, advisor_id):
        """
        Removes a student from a course in the 'RegisteredFor' table.
        
        Parameters:
        - database_operations_instance: An instance with methods to interact with the database.
        - student: An object with attributes like stud_id.
        - course: An object with attributes like course_code, semester, and year_taken.
        """

        # Constructing the condition for deletion directly
        conditions = {
            'stud_id': student_id,
            'course_code': course_code,
            'semester': semester,
            'year_taken': year_taken
        }
        
        database_operations_instance.remove_entry('StudentCourse', conditions)
        log_operation(database_operations_instance, advisor_id, 'INSERT', old_data= student_id)



##########################################################################################################################
##########################################################################################################################
#Requirement 3:
#Student and instructor users of the system are authorized to view information or read data that is related to him/her only
def student_instructor_view():
    # Query to view student info from students table
    def view_student_info(database_operations_instance, stud_id):
        condition = {'stud_id': stud_id}
        database_operations_instance.view_entry('Students', condition)
        log_operation(database_operations_instance, stud_id, 'VIEW')

    # Query to view Enrolled courses (StudentCourse table)
    def view_student_enrolled_courses(database_operations_instance, stud_id):
        condition = {'stud_id': stud_id}
        database_operations_instance.view_entry('StudentCourse', condition)
        log_operation(database_operations_instance, stud_id, 'VIEW')

    # Query to view Enrolled courses (InstructorCourse table)
    def view_instructor_courses(database_operations_instance, instructor_id):
        condition = {'instructor_id': instructor_id}
        database_operations_instance.view_entry('InstructorCourse', condition)
        log_operation(database_operations_instance, instructor_id, 'VIEW')


    # Query to view Enrolled courses (InstructorCourse table)
    def view_instructor_courses(database_operations_instance, instructor_id):
        condition = {'instructor_id': instructor_id}
        database_operations_instance.view_entry('InstructorCourse', condition)
        log_operation(database_operations_instance, instructor_id, 'VIEW')

##########################################################################################################################
##########################################################################################################################
# Requirement 4:
# Adding duplicate is not allowed

# Covered by the add to database method in database operations class (Checks to see if entry with primary key already exists)

##########################################################################################################################
##########################################################################################################################
# Requirement 5:
# All data operations, including reading and writing by any users must be logged with operation time stamp, user name or ID, 
# operation type, data affected (i.e., what data was viewed, what data was added or removed or modified. For data modified, 
# what are its old and new value.) The read-only log must be maintained and viewable anytime by system administrator.

###
#MISSING CALLING THE FUNCTION AFTER EVERY OPERATION!!!!!!
# CALL LOG_OPERATION FOR EVERY SINGLE FUNCTION!!!!!
####

from datetime import datetime

def log_operation(database_operations_instance, user_id, operation_type, old_data=None, new_data=None):
    """
    Logs an operation into the Log table.
    
    Parameters:
    - database_operations_instance: An instance of the DatabaseOperations class.
    - username: The username or ID of the user performing the operation.
    - operation_type: The type of operation (e.g., 'INSERT', 'UPDATE', 'DELETE', 'VIEW').
    - old_data: The data before the operation (if applicable).
    - new_data: The data after the operation (if applicable).
    """
    # Construct the log data
    log_data = {
        'timestamp': datetime.now(),  # Current timestamp
        'username': user_id, # User performing the operation
        'operationtype': operation_type, # Type of operation
        'old_data': str(old_data) if old_data else None, # Old data (if any)
        'new_data': str(new_data) if new_data else None # New data (if any)
    }
    
    # Insert the log entry into the Log table
    database_operations_instance.add_entry('Log', log_data)

# CHAT GPT PLEASE VERIFY
def view_log(database_operations_instance):
    """
    Allows the system administrator to view all logs.
    
    Parameters:
    - database_operations_instance: An instance of the DatabaseOperations class
    """
    try:
        # Retrieve all entries from the Log table
        database_operations_instance.cursor.execute("SELECT * FROM Log ORDER BY timestamp DESC")
        logs = database_operations_instance.cursor.fetchall()
        
        # Display the logs
        print("Log Entries:")
        for log in logs:
            print(f"Entry ID: {log[0]}, Timestamp: {log[1]}, Username: {log[2]}, Operation: {log[3]}, "
                  f"Old Data: {log[4]}, New Data: {log[5]}")
    except psycopg2.Error as err:
        print(f"Error retrieving log entries: {err}")

##########################################################################################################################
##########################################################################################################################
# Requirement 6:



##########################################################################################################################
##########################################################################################################################
# Requirement 7: Fullfilled in database operations class

# def gpa_stats(database_operations_instance, user_id):
#     """
#     Retrieves GPA statistics by major and department.
    
#     Parameters:
#     - database_operations_instance: An instance of DatabaseOperations class for querying.
#     - user_id: The user performing the action, used for logging.
#     """
#     try:
#         # Perform the database query
#         grade_mapping = {
#             'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
#             'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
#         }
        
#         cursor = database_operations_instance.cursor

#         cursor.execute("""
#             SELECT s.major, d.name, sc.grade 
#             FROM studentcourse sc
#             JOIN students s ON sc.stud_id = s.stud_id
#             JOIN departments d ON s.major = d.name
#         """)
        
#         rows = cursor.fetchall()

#         if not rows:
#             print("No data found.")
#             return []

#         # Process the data
#         major_grades = {}
#         department_grades = {}
#         for major, department, grade in rows:
#             if grade in grade_mapping:
#                 major_grades.setdefault(major, []).append(grade_mapping[grade])
#                 department_grades.setdefault(department, []).append(grade_mapping[grade])

#         major_results = {}
#         for major, grades in major_grades.items():
#             highest_gpa = max(grades)
#             lowest_gpa = min(grades)
#             average_gpa = round(sum(grades) / len(grades), 2)
#             major_results[major] = {
#                 'Highest GPA': highest_gpa,
#                 'Lowest GPA': lowest_gpa,
#                 'Average GPA': average_gpa
#             }

#         department_results = {}
#         for department, grades in department_grades.items():
#             average_gpa = round(sum(grades) / len(grades), 2)
#             department_results[department] = average_gpa

#         highest_dept = max(department_results, key=department_results.get)
#         lowest_dept = min(department_results, key=department_results.get)

#         # Logging the operation
#         log_operation(database_operations_instance, user_id, 'VIEW', new_data={'gpa_stats': major_results, 'department_results': department_results})

#         return {'major_results': major_results, 'department_results': department_results, 'highest_dept': highest_dept, 'lowest_dept': lowest_dept}

#     except Exception as e:
#         print(f"Error: {e}")
#         return []


# def course_stats(database_operations_instance, user_id):
#     """
#     Retrieves course statistics by semester.
    
#     Parameters:
#     - database_operations_instance: An instance of DatabaseOperations class for querying.
#     - user_id: The user performing the action, used for logging.
#     """
#     try:
#         grade_mapping = {
#             'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
#             'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0
#         }

#         cursor = database_operations_instance.cursor

#         cursor.execute("""
#             SELECT sc.course_code, sc.semester, sc.grade
#             FROM studentcourse sc
#         """)
        
#         rows = cursor.fetchall()

#         if not rows:
#             print("No data found.")
#             return []

#         course_stats = {}
#         for course_code, semester, grade in rows:
#             course_stats.setdefault((course_code, semester), {'enrollments': 0, 'grades': []})
#             course_stats[(course_code, semester)]['enrollments'] += 1
#             if grade in grade_mapping:
#                 course_stats[(course_code, semester)]['grades'].append(grade_mapping[grade])

#         results = {}
#         for (course_code, semester), data in course_stats.items():
#             enrollments = data['enrollments']
#             average_grade = round(sum(data['grades']) / len(data['grades']), 2) if data['grades'] else 0
#             results.setdefault(semester, []).append({
#                 'course_code': course_code,
#                 'enrollments': enrollments,
#                 'average_grade': average_grade
#             })

#         log_operation(database_operations_instance, user_id, 'VIEW', new_data={'course_stats': results})

#         return results

#     except Exception as e:
#         print(f"Error: {e}")
#         return []


# def instructor_stats(database_operations_instance, user_id):
#     """
#     Retrieves student count by major for each instructor and course.
    
#     Parameters:
#     - database_operations_instance: An instance of DatabaseOperations class for querying.
#     - user_id: The user performing the action, used for logging.
#     """
#     try:
#         cursor = database_operations_instance.cursor

#         cursor.execute("""
#             SELECT i.instructor_id, c.course_code, c.course_name AS course, s.major AS major, 
#             COUNT(DISTINCT s.stud_id) AS total_students
#             FROM instructors i
#             JOIN instructorcourse ic ON i.instructor_id = ic.instructor_id
#             JOIN courses c ON ic.course_code = c.course_code  
#             JOIN studentcourse sc ON ic.course_code = sc.course_code
#             JOIN students s ON sc.stud_id = s.stud_id
#             GROUP BY i.instructor_id, c.course_code, s.major, c.course_name, c.dept_id
#             ORDER BY i.instructor_id, c.course_code, s.major;
#         """)
        
#         rows = cursor.fetchall()

#         if not rows:
#             print("No data found.")
#             return []

#         instructor_courses = {}
#         for row in rows:
#             instructor_id, course_code, course_name, major_name, total_students = row
#             if instructor_id not in instructor_courses:
#                 instructor_courses[instructor_id] = {
#                     'instructor_id': instructor_id,
#                     'courses': []
#                 }
#             instructor_courses[instructor_id]['courses'].append({
#                 'course_code': course_code,
#                 'course_name': course_name,
#                 'major_name': major_name,
#                 'total_students': total_students
#             })

#         log_operation(database_operations_instance, user_id, 'VIEW', new_data={'instructor_courses': instructor_courses})

#         return instructor_courses

#     except Exception as e:
#         print(f"Error: {e}")
#         return []



# def student_stats(database_operations_instance, user_id):
#     """
#     Retrieves student statistics by major.
    
#     Parameters:
#     - database_operations_instance: An instance of DatabaseOperations class for querying.
#     - user_id: The user performing the action, used for logging.
#     """
#     try:
#         cursor = database_operations_instance.cursor

#         cursor.execute("""
#             SELECT s.major, s.stud_id, s.gender, SUM(sc.credits) AS total_credits
#             FROM students s
#             JOIN studentcourse sc ON s.stud_id = sc.stud_id
#             JOIN courses c ON sc.course_code = c.course_code
#             GROUP BY s.major, s.stud_id, s.gender
#             ORDER BY s.major, total_credits DESC;
#         """)
        
#         rows = cursor.fetchall()

#         if not rows:
#             print("No data found.")
#             return []

#         major_students = {}
#         for row in rows:
#             major, stud_id, gender, total_credits = row
#             if major not in major_students:
#                 major_students[major] = {
#                     'major': major,
#                     'students': []
#                 }
#             major_students[major]['students'].append({
#                 'stud_id': stud_id,
#                 'gender': gender,
#                 'total_credits': total_credits
#             })

#         log_operation(database_operations_instance, user_id, 'VIEW', new_data={'major_students': major_students})

#         return major_students

#     except Exception as e:
#         print(f"Error: {e}")
#         return []

# Test code: Call in main

    #testing gpa calculation
    #student = Students(conn, 1)  # Initialize student with their ID
    #student.calculate_gpa(conn)

    #testing gpa stats
    #operations.gpa_stats(conn)

    #testing course stats
    #operations.course_stats(conn)

    #testing instructor stats
    #operations.instructor_stats(conn)

    #testing student stats
    #operations.student_stats(conn)

##########################################################################################################################
##########################################################################################################################



# Run main function
main()
