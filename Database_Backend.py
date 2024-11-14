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
        self.user_type = self.__class__.__name__  # Determines table based on the class name

    @classmethod
    def from_database(cls, conn, user_id):
        """Creates an instance of the subclass and populates its fields from the database"""
        cursor = conn.cursor()
        query = f"SELECT * FROM {cls.__name__} WHERE {cls.primary_key} = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if result:
            return cls(*result)  # Passes each result as an argument to the constructor
        else:
            raise ValueError(f"No record found in {cls.__name__} for ID {user_id}")

# Student class
class Students(User):
    primary_key = 'stud_id'

    def __init__(self, stud_id, gender=None, major=None):
        super().__init__(stud_id)
        self.gender = gender
        self.major = major

# Instructor class
class Instructors(User):
    primary_key = 'instructor_id'

    def __init__(self, instructor_id, dept_id=None, hired_sem=None, instructor_phone=None):
        super().__init__(instructor_id)
        self.dept_id = dept_id
        self.hired_sem = hired_sem
        self.instructor_phone = instructor_phone

# Staff class
class Staff(User):
    primary_key = 'staff_id'

    def __init__(self, staff_id, dept_id=None, phone=None):
        super().__init__(staff_id)
        self.dept_id = dept_id
        self.phone = phone

# Advisor class
class Advisors(User):
    primary_key = 'adv_id'

    def __init__(self, adv_id, total_hours_reg=None, major_offered=None, dept_id=None, advisor_phone=None, building=None, office=None):
        super().__init__(adv_id)
        self.total_hours_reg = total_hours_reg
        self.major_offered = major_offered
        self.dept_id = dept_id
        self.advisor_phone = advisor_phone
        self.building = building
        self.office = office

########################################################################################################################
########################################################################################################################
# Remaining Tables

class Courses:
    def __init__(self, conn, course_prefix):
        """Load course information for a specific course prefix."""
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
        """Load department information for a specific department."""
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
        """Load a specific log entry by entry ID or all logs for a specific username."""
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
            CREATE TABLE IF NOT EXISTS Courses(course_prefix CHAR(3) PRIMARY KEY, course_number CHAR(4), dept_id VARCHAR(9), credits INTEGER
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
        conn.commit()
        #/////////////////////////////////////////////////////////////////////////////////////////////////////////////



        # Initialize StaffDatabaseOperations with connection
        operations = DatabaseOperations(conn)

        # Example test cases
        # Everything being typed here is a dictionary with the attribute and the value of that attribute we are using for the query
        print("Testing add, remove, and modify operations...")

        # Add an entry to the Students table
        student_data = {
            'stud_id': 'S12345678',
            'gender': 'M',
            'major': 'CS'
        }
        operations.add_entry('Students', student_data)

        # Modify an entry in the Students table
        student_updates = {
            'major': 'EE'
        }
        operations.modify_entry('Students', student_updates, {'stud_id': 'S12345678'})

        # Add, modify, and remove for COURSES table
        course_data = {
            'course_prefix': 'CSE',
            'course_number': '1010',
            'dept_id': 'D001',
            'credits': 3
        }
        operations.add_entry('Courses', course_data)

        course_updates = {
            'credits': 4
        }
        operations.modify_entry('Courses', course_updates, {'course_prefix': 'CSE'})

        course_data = {
            'course_prefix': 'CCC',
            'course_number': '1010',
            'dept_id': 'D001',
            'credits': 3
        }
        operations.add_entry('Courses', course_data)

        operations.remove_entry('Courses', {'course_prefix': 'CCC'})

        dept_data = {
            'dept_id': 'D001',
            'name': 'Computer Science'
        }
        operations.add_entry('Departments', dept_data)

        # Modify the entry in the Departments table
        dept_updates = {
            'name': 'Electrical Engineering'
        }
        operations.modify_entry('Departments', dept_updates, {'dept_id': 'D001'})

        # Example: Add an entry to the Instructors table
        instructor_data = {
            'instructor_id': 'I12345678',
            'dept_id': 'D001',
            'hired_sem': 'F23',
            'instructor_phone': '1234'
        }
        operations.add_entry('Instructors', instructor_data)

        # Modify the entry in the Instructors table
        instructor_updates = {
            'instructor_phone': '5678'
        }
        operations.modify_entry('Instructors', instructor_updates, {'instructor_id': 'I12345678'})

        # Example usage
        condition = {'stud_id': 'S12345678'}  # Condition for viewing a specific student
        operations.view_entry('Students', condition)

        print('\n\n\nHere is new outputs\n\n\n')

        #START Test Code

        test_database_operations()

        #END Test Code

    except psycopg2.Error as error:
        print(f"Error: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()



def test_database_operations():
    # Instantiate the database operations class
    db_ops = DatabaseOperations(conn)
    
    # Populate the Students table
    db_ops.add_entry('Students', {'stud_id': 'S001', 'gender': 'M', 'major': 'CS'})
    db_ops.add_entry('Students', {'stud_id': 'S002', 'gender': 'F', 'major': 'Math'})
    
    # Populate the Instructors table
    db_ops.add_entry('Instructors', {'instructor_id': 'I001', 'dept_id': 'D001', 'hired_sem': 'F22', 'instructor_phone': '1234'})
    db_ops.add_entry('Instructors', {'instructor_id': 'I002', 'dept_id': 'D002', 'hired_sem': 'S23', 'instructor_phone': '5678'})
    
    # Populate the Staff table
    db_ops.add_entry('Staff', {'staff_id': 'SF001', 'dept_id': 'D001', 'phone': '9876'})
    db_ops.add_entry('Staff', {'staff_id': 'SF002', 'dept_id': 'D002', 'phone': '6543'})
    
    # Populate the Advisors table
    db_ops.add_entry('Advisors', {'adv_id': 'A001', 'total_hours_reg': 12, 'major_offered': 'Physics', 'dept_id': 'D001', 'advisor_phone': '5555', 'building': 'A', 'office': '101'})
    db_ops.add_entry('Advisors', {'adv_id': 'A002', 'total_hours_reg': 8, 'major_offered': 'Chemistry', 'dept_id': 'D002', 'advisor_phone': '4444', 'building': 'B', 'office': '202'})

    # Populate the Courses table
    db_ops.add_entry('Courses', {'course_prefix': 'CS', 'course_number': '1010', 'dept_id': 'D001', 'credits': 3})
    db_ops.add_entry('Courses', {'course_prefix': 'MAT', 'course_number': '2020', 'dept_id': 'D002', 'credits': 4})

    # Retrieve and print student data
    student_1 = Students.from_database(conn, 'S001')
    student_2 = Students.from_database(conn, 'S002')
    print(f"Student 1: ID={student_1.user_id}, Gender={student_1.gender}, Major={student_1.major}")
    print(f"Student 2: ID={student_2.user_id}, Gender={student_2.gender}, Major={student_2.major}")

    # Retrieve and print instructor data
    instructor_1 = Instructors.from_database(conn, 'I001')
    instructor_2 = Instructors.from_database(conn, 'I002')
    print(f"Instructor 1: ID={instructor_1.user_id}, Dept ID={instructor_1.dept_id}, Hired Semester={instructor_1.hired_sem}, Phone={instructor_1.instructor_phone}")
    print(f"Instructor 2: ID={instructor_2.user_id}, Dept ID={instructor_2.dept_id}, Hired Semester={instructor_2.hired_sem}, Phone={instructor_2.instructor_phone}")

    # Retrieve and print staff data
    staff_1 = Staff.from_database(conn, 'SF001')
    staff_2 = Staff.from_database(conn, 'SF002')
    print(f"Staff 1: ID={staff_1.user_id}, Dept ID={staff_1.dept_id}, Phone={staff_1.phone}")
    print(f"Staff 2: ID={staff_2.user_id}, Dept ID={staff_2.dept_id}, Phone={staff_2.phone}")

    # Retrieve and print advisor data
    advisor_1 = Advisors.from_database(conn, 'A001')
    advisor_2 = Advisors.from_database(conn, 'A002')
    print(f"Advisor 1: ID={advisor_1.user_id}, Total Hours Reg={advisor_1.total_hours_reg}, Major Offered={advisor_1.major_offered}, Dept ID={advisor_1.dept_id}, Phone={advisor_1.advisor_phone}, Building={advisor_1.building}, Office={advisor_1.office}")
    print(f"Advisor 2: ID={advisor_2.user_id}, Total Hours Reg={advisor_2.total_hours_reg}, Major Offered={advisor_2.major_offered}, Dept ID={advisor_2.dept_id}, Phone={advisor_2.advisor_phone}, Building={advisor_2.building}, Office={advisor_2.office}")

    # Retrieve and print course data
    course_1 = Courses(conn, 'CS')
    course_2 = Courses(conn, 'MAT')
    print(f"Course 1: Prefix={course_1.course_prefix}, Number={course_1.course_number}, Dept ID={course_1.dept_id}, Credits={course_1.credits}")
    print(f"Course 2: Prefix={course_2.course_prefix}, Number={course_2.course_number}, Dept ID={course_2.dept_id}, Credits={course_2.credits}")

    # Test additional classes as needed
    # Populate Departments, RegisteredFor, Teaches, UserInfo, and Log similarly
    # Example:
    db_ops.add_entry('Departments', {'dept_id': 'D001', 'name': 'Computer Science'})
    db_ops.add_entry('Departments', {'dept_id': 'D002', 'name': 'Mathematics'})
    
    department_1 = Departments(conn, 'D001')
    department_2 = Departments(conn, 'D002')
    print(f"Department 1: ID={department_1.dept_id}, Name={department_1.name}")
    print(f"Department 2: ID={department_2.dept_id}, Name={department_2.name}")
    
    # Populate and test RegisteredFor, Teaches, UserInfo, Log as needed
    # Add entries to the RegisteredFor and Teaches tables
    db_ops.add_entry('RegisteredFor', {
        'stud_id': 'S001', 
        'course_prefix': 'CS', 
        'course_number': '101', 
        'year_taken': 2023, 
        'grade': 'A', 
        'semester': '1'
    })
    db_ops.add_entry('Teaches', {
        'instructor_id': 'I001', 
        'course_prefix': 'CS', 
        'course_number': '101', 
        'year_taught': 2023, 
        'semester': '1'
    })

    # Add entries to UserInfo and Log tables
    db_ops.add_entry('UserInfo', {
        'username': 'jdoe', 
        'name': 'John Doe', 
        'privilege': 'student'
    })
    db_ops.add_entry('Log', {
        'entry': 1, 
        'timestamp': '2024-11-13 10:00:00', 
        'username': 'jdoe', 
        'operationtype': 'INSERT', 
        'old_data': None, 
        'new_data': '{"dept_id": "D001", "name": "Computer Science"}'
    })

    # Retrieve and display RegisteredFor records
    student_registrations = RegisteredFor(conn, 'S001')
    for record in student_registrations.records:
        print(f"Registration Record: {record}")

    # Retrieve and display Teaches records
    instructor_courses = Teaches(conn, 'I001')
    for record in instructor_courses.records:
        print(f"Teaching Record: {record}")

    # Retrieve and display UserInfo details
    user_info = UserInfo(conn, 'jdoe')
    print(f"User: Username={user_info.username}, Name={user_info.name}, Privilege={user_info.privilege}")

    # Retrieve and display Log records
    log_entry = Log(conn, entry=1)
    print(f"Log Entry: ID={log_entry.entry}, Timestamp={log_entry.timestamp}, Username={log_entry.username}, "
        f"Operation={log_entry.operationtype}, Old Data={log_entry.old_data}, New Data={log_entry.new_data}")



# Run main function
main()

print('Hello World')

