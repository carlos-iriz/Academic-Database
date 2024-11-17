import psycopg2

# Database credentials
hostname = '//'
database = 'Academic_Database'
username = 'postgres'
pwd = '//'
port_id = 5432

conn = None
cursor = None

########################################################################################################################
########################################################################################################################
# Classes to hold database information from user classes (Student, Instructor, Staff, Advisor)
# Has User as parent class and then specific types as children

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_type = self.__class__.__name__

    @classmethod
    def from_database(cls, conn, user_id):
        """Creates an instance of the subclass and populates its fields from the database"""
        cursor = conn.cursor()
        query = f"SELECT * FROM {cls.__name__} WHERE {cls.primary_key} = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result:
            return cls(*result)
        else:
            raise ValueError(f"No record found in {cls.__name__} for ID {user_id}")

class Students(User):
    primary_key = 'stud_id'

    def __init__(self, conn, stud_id):
        super().__init__(stud_id)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Students WHERE stud_id = %s", (stud_id,))
        result = cursor.fetchone()

        if result:
            self.stud_id, self.gender, self.major = result
        else:
            raise ValueError(f"No record found in Students for ID {stud_id}")

class Instructors(User):
    primary_key = 'instructor_id'

    def __init__(self, conn, instructor_id):
        super().__init__(instructor_id)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Instructors WHERE instructor_id = %s", (instructor_id,))
        result = cursor.fetchone()

        if result:
            self.instructor_id, self.dept_id, self.hired_sem, self.instructor_phone = result
        else:
            raise ValueError(f"No record found in Instructors for ID {instructor_id}")

class Staff(User):
    primary_key = 'staff_id'

    def __init__(self, conn, staff_id):
        super().__init__(staff_id)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Staff WHERE staff_id = %s", (staff_id,))
        result = cursor.fetchone()

        if result:
            self.staff_id, self.dept_id, self.phone = result
        else:
            raise ValueError(f"No record found in Staff for ID {staff_id}")

class Advisors(User):
    primary_key = 'adv_id'

    def __init__(self, conn, adv_id):
        super().__init__(adv_id)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Advisors WHERE adv_id = %s", (adv_id,))
        result = cursor.fetchone()

        if result:
            (self.adv_id, self.total_hours_reg, self.major_offered, 
             self.dept_id, self.advisor_phone, self.building, self.office) = result
        else:
            raise ValueError(f"No record found in Advisors for ID {adv_id}")

########################################################################################################################
########################################################################################################################
# Remaining Tables

class Courses:
    def __init__(self, conn, course_prefix):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Courses WHERE course_prefix = %s", (course_prefix,))
        result = cursor.fetchone()

        if result:
            self.course_prefix, self.course_number, self.dept_id, self.credits = result
        else:
            raise ValueError(f"No course found with prefix {course_prefix}")

    @classmethod
    def load_all_courses(cls, conn):
        """Load all courses from the Courses table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Courses")
        courses = [cls(conn, row[0]) for row in cursor.fetchall()]
        return courses

class Departments:
    def __init__(self, conn, dept_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Departments WHERE dept_id = %s", (dept_id,))
        result = cursor.fetchone()

        if result:
            self.dept_id, self.name = result
        else:
            raise ValueError(f"No department found with ID {dept_id}")

    @classmethod
    def load_all_departments(cls, conn):
        """Load all departments from the Departments table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Departments")
        departments = [cls(conn, row[0]) for row in cursor.fetchall()]
        return departments

class RegisteredFor:
    def __init__(self, conn, stud_id):
        """Load all registration records for a specific student ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM RegisteredFor WHERE stud_id = %s", (stud_id,))
        records = cursor.fetchall()
        
        self.records = []
        for record in records:
            data = {
                'stud_id': record[0],
                'course_prefix': record[1],
                'course_number': record[2],
                'year_taken': record[3],
                'grade': record[4],
                'semester': record[5]
            }
            self.records.append(data)

class Teaches:
    def __init__(self, conn, instructor_id):
        """Load all teaching records for a specific instructor ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Teaches WHERE instructor_id = %s", (instructor_id,))
        records = cursor.fetchall()
        
        self.records = []
        for record in records:
            data = {
                'instructor_id': record[0],
                'course_prefix': record[1],
                'course_number': record[2],
                'year_taught': record[3],
                'semester': record[4]
            }
            self.records.append(data)

class UserInfo:
    def __init__(self, conn, username):
        """Load user information for a specific username."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if result:
            self.username, self.name, self.privilege = result
        else:
            raise ValueError(f"No user found with username {username}")

    @classmethod
    def load_all_users(cls, conn):
        """Load all users from the UserInfo table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM UserInfo")
        users = [cls(conn, row[0]) for row in cursor.fetchall()]
        return users

class Log:
    def __init__(self, conn, entry=None, username=None):
        cursor = conn.cursor()
        if entry:
            cursor.execute("SELECT * FROM Log WHERE entry = %s", (entry,))
            result = cursor.fetchone()
            if result:
                self.entry, self.timestamp, self.username, self.operationtype, self.old_data, self.new_data = result
            else:
                raise ValueError(f"No log entry found with entry ID {entry}")
        elif username:
            cursor.execute("SELECT * FROM Log WHERE username = %s", (username,))
            self.records = cursor.fetchall()
        else:
            raise ValueError("Either entry ID or username must be provided to load logs")

    @classmethod
    def load_all_logs(cls, conn):
        """Load all logs from the Log table."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Log")
        logs = [cls(conn, row[0]) for row in cursor.fetchall()]
        return logs

# Additional classes for other added tables
class StudentCourse:
    def __init__(self, conn, student_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM StudentCourse WHERE student_id = %s", (student_id,))
        self.records = cursor.fetchall()

class InstructorCourse:
    def __init__(self, conn, instructor_id):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM InstructorCourse WHERE instructor_id = %s", (instructor_id,))
        self.records = cursor.fetchall()

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

        create_students_table = '''
            CREATE TABLE IF NOT EXISTS Students(stud_id VARCHAR(9) PRIMARY KEY, gender CHAR(1), major VARCHAR(10)
        );'''

        create_courses_table = '''
            CREATE TABLE IF NOT EXISTS Courses (
                course_prefix CHAR(3),
                course_number CHAR(4),
                dept_id VARCHAR(9),
                credits INTEGER,
                PRIMARY KEY (course_prefix, course_number)
        );'''

        create_departments_table = '''
            CREATE TABLE IF NOT EXISTS Departments(dept_id VARCHAR(10) PRIMARY KEY, name VARCHAR(50)
        );'''

        create_instructors_table = '''
            CREATE TABLE IF NOT EXISTS Instructors(instructor_id VARCHAR(9) PRIMARY KEY, dept_id VARCHAR(9), hired_sem CHAR(5), instructor_phone CHAR(4)
        );'''       

        create_staff_table = '''
            CREATE TABLE IF NOT EXISTS Staff(staff_id VARCHAR(9) PRIMARY KEY, dept_id VARCHAR(9), phone CHAR(4)
        );'''

        create_advisors_table = '''
            CREATE TABLE IF NOT EXISTS Advisors(adv_id CHAR(9) PRIMARY KEY, total_hours_reg INTEGER, major_offered VARCHAR(10), dept_id VARCHAR(9), advisor_phone CHAR(4), building CHAR(1), office VARCHAR(5)
        );'''

        create_registeredFor_table = '''
            CREATE TABLE IF NOT EXISTS RegisteredFor(stud_id CHAR(9) PRIMARY KEY, course_prefix CHAR(3), course_number CHAR(4), year_taken CHAR(4), grade VARCHAR(10), semester CHAR(1)
        );'''

        create_teaches_table = '''
            CREATE TABLE IF NOT EXISTS Teaches(instructor_id CHAR(9) PRIMARY KEY, course_prefix CHAR(3), course_number CHAR(4), year_taught CHAR(4), semester CHAR(1)
        );'''

        create_userInfo_table = '''
            CREATE TABLE IF NOT EXISTS UserInfo(username VARCHAR(50) PRIMARY KEY, name VARCHAR(100), privilege VARCHAR(20)
        );'''

        create_log_table = '''
            CREATE TABLE IF NOT EXISTS Log (entry SERIAL PRIMARY KEY, timestamp TIMESTAMPTZ NOT NULL, username VARCHAR(50) REFERENCES UserInfo(username), operationtype VARCHAR(50), old_data TEXT, new_data TEXT
        );'''

        create_student_course_table = '''
        CREATE TABLE IF NOT EXISTS StudentCourse (
            stud_id CHAR(9),
            course_prefix CHAR(3),
            course_number CHAR(4),
            semester CHAR(1),
            year_taken CHAR(4),
            grade VARCHAR(10),
            PRIMARY KEY (stud_id, course_prefix, course_number, semester, year_taken),
            FOREIGN KEY (stud_id) REFERENCES Students(stud_id),
            FOREIGN KEY (course_prefix, course_number) REFERENCES Courses(course_prefix, course_number)
        );'''

        create_instructor_course_table = '''
        CREATE TABLE IF NOT EXISTS InstructorCourse (
            instructor_id CHAR(9),
            course_prefix CHAR(3),
            course_number CHAR(4),
            semester CHAR(1),
            year_taught CHAR(4),
            PRIMARY KEY (instructor_id, course_prefix, course_number, semester, year_taught),
            FOREIGN KEY (instructor_id) REFERENCES Instructors(instructor_id),
            FOREIGN KEY (course_prefix, course_number) REFERENCES Courses(course_prefix, course_number)
        );'''

        # Executes creation statements in database
        cursor = conn.cursor()
        cursor.execute(create_students_table)
        cursor.execute(create_instructors_table)
        cursor.execute(create_departments_table)
        cursor.execute(create_registeredFor_table)
        cursor.execute(create_teaches_table)
        cursor.execute(create_courses_table)
        cursor.execute(create_staff_table)
        cursor.execute(create_advisors_table)
        cursor.execute(create_userInfo_table)
        cursor.execute(create_log_table)
        cursor.execute(create_student_course_table)
        cursor.execute(create_instructor_course_table)
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
    def staff_add_course(database_operations_instance, course_data, staff_user):
        course_data['department_id'] = staff_user.department_id
        database_operations_instance.add_entry('Courses', course_data)

    def staff_remove_course(database_operations_instance, course_id, staff_user):
        condition = {'course_id': course_id, 'department_id': staff_user.department_id}
        database_operations_instance.remove_entry('Courses', condition)

    def staff_modify_course(database_operations_instance, course_id, updates, staff_user):
        condition = {'course_id': course_id, 'department_id': staff_user.department_id}
        database_operations_instance.modify_entry('Courses', updates, condition)

    def staff_add_instructor(database_operations_instance, instructor_data, staff_user):
        instructor_data['department_id'] = staff_user.department_id
        database_operations_instance.add_entry('Instructors', instructor_data)

    def staff_remove_instructor(database_operations_instance, instructor_id, staff_user):
        condition = {'instructor_id': instructor_id, 'department_id': staff_user.department_id}
        database_operations_instance.remove_entry('Instructors', condition)

    def staff_modify_instructor(database_operations_instance, instructor_id, updates, staff_user):
        condition = {'instructor_id': instructor_id, 'department_id': staff_user.department_id}
        database_operations_instance.modify_entry('Instructors', updates, condition)

    def staff_add_student(database_operations_instance, student_data, staff_user):
        student_data['department_id'] = staff_user.department_id
        database_operations_instance.add_entry('Students', student_data)

    def staff_remove_student(database_operations_instance, student_id, staff_user):
        condition = {'student_id': student_id, 'department_id': staff_user.department_id}
        database_operations_instance.remove_entry('Students', condition)

    def staff_modify_student(database_operations_instance, student_id, updates, staff_user):
        condition = {'student_id': student_id, 'department_id': staff_user.department_id}
        database_operations_instance.modify_entry('Students', updates, condition)

    def staff_assign_course_to_instructor(database_operations_instance, instructor_id, course_id, staff_user):
        instructor_condition = {'instructor_id': instructor_id, 'department_id': staff_user.department_id}
        course_condition = {'course_id': course_id, 'department_id': staff_user.department_id}
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

    # Staff not allowed to touch "RegisteredFor" table! (Can't add or remove student from a course)

##########################################################################################################################
##########################################################################################################################
# Requirement 2:
# Advisors are allowed to add and drop students form courses as long as they are in the same department
# Student selection and course selections will appear in UI displaying infomration that matches:
# Student and user object match 

def advisor_add_drop_student():
    def advisor_add_student(database_operations_instance, student, course):
        """
        Adds a student to a course in the 'RegisteredFor' table.
        
        Parameters:
        - database_operations_instance: An instance with methods to interact with the database.
        - student: An object with attributes like stud_id.
        - course: An object with attributes like course_prefix, course_number, semester, year_taken, and grade.
        """
        # Constructing the data to insert directly
        data = {
            'stud_id': student.stud_id,
            'course_prefix': course.course_prefix,
            'course_number': course.course_number,
            'semester': course.semester,
            'year_taken': course.year_taken,
            'grade': course.grade  # Optional, depending on whether grade is known at this stage
        }
        
        # Inserting into 'RegisteredFor' table
        database_operations_instance.add_entry('RegisteredFor', data)

    def advisor_drop_student(database_operations_instance, student, course):
        """
        Removes a student from a course in the 'RegisteredFor' table.
        
        Parameters:
        - database_operations_instance: An instance with methods to interact with the database.
        - student: An object with attributes like stud_id.
        - course: An object with attributes like course_prefix, course_number, semester, and year_taken.
        """
        # Constructing the condition for deletion directly
        conditions = {
            'stud_id': student.stud_id,
            'course_prefix': course.course_prefix,
            'course_number': course.course_number,
            'semester': course.semester,
            'year_taken': course.year_taken
        }
        
        # Removing from 'RegisteredFor' table
        database_operations_instance.remove_entry('RegisteredFor', conditions)


##########################################################################################################################
##########################################################################################################################
# Requirement 3:
# Student and instructor users of the system are authorized to view information or read data that is related to him/her only

# Kind of already fulfilled by the view data method

##########################################################################################################################
##########################################################################################################################
# Requirement 4:
# Adding duplicate is not allowed

# Covered by the add to database method (Checks to see if entry with primary key already exists)

##########################################################################################################################
##########################################################################################################################
# Requirement 5:
# All data operations, including reading and writing by any users must be logged with operation time stamp, user name or ID, 
# operation type, data affected (i.e., what data was viewed, what data was added or removed or modified. For data modified, 
# what are its old and new value.) The read-only log must be maintained and viewable anytime by system administrator.

from datetime import datetime

def log_operation(database_operations_instance, username, operation_type, old_data=None, new_data=None):
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
        'username': username,        # User performing the operation
        'operationtype': operation_type,  # Type of operation
        'old_data': str(old_data) if old_data else None,  # Old data (if any)
        'new_data': str(new_data) if new_data else None   # New data (if any)
    }
    
    # Insert the log entry into the Log table
    database_operations_instance.add_entry('Log', log_data)

def view_log(database_operations_instance):
    """
    Allows the system administrator to view all logs.
    
    Parameters:
    - database_operations_instance: An instance of the DatabaseOperations class.
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
# Requirement 7:

##########################################################################################################################
##########################################################################################################################



# Run main function
main()

