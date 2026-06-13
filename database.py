import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'student.db')

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        student_name TEXT,
        major TEXT,
        starting_year INTEGER,
        total_attendance INTEGER,
        years INTEGER,
        last_attendance_time TEXT,
        student_image BLOB,
        Gender TEXT
    )
    """)
connection.commit()
#connection.close()

def convert_to_binary_data(filename):
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data

def insert_new_student():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    student_id = input("Enter Student ID: ")
    cursor.execute("SELECT student_name FROM students WHERE student_id = ?", (student_id,))
    existing_student = cursor.fetchone()

    if existing_student:
        print(f"\nStudent ID {student_id} already exists for {existing_student[0]}!")
        connection.close()
        return

    student_name = input("Enter Student Name: ")
    major = input("Enter Major: ")
    starting_year = int(input("Enter Starting Year: "))
    total_attendance = int(input("Enter Total Attendance: "))
    years = int(input("Enter Years: "))
    last_attendance_time = input("Enter Last Attendance Time (YYYY-MM-DD HH:MM:SS): ")
    gender = input("Enter Gender: ")
    image_path = input("Enter Image Path: ")

    try:
        image_blob = convert_to_binary_data(image_path)
    except FileNotFoundError:
        print("Image file not found! Student record not created.")
        connection.close()
        return

    cursor.execute("""
    INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?)
    """, (student_id, student_name, major, starting_year, total_attendance,
          years, last_attendance_time, image_blob, gender))

    connection.commit()
    print(f"\nSuccessfully created record for {student_name} ({student_id})")
    connection.close()


def update_student():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    student_id = input("Enter Student ID to update: ")
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    student_data = cursor.fetchone()

    if not student_data:
        print(f"\nStudent ID {student_id} not found!")
        connection.close()
        return
    print("\nCurrent Student Information:")
    print(f"1. Name: {student_data[1]}")
    print(f"2. Major: {student_data[2]}")
    print(f"3. Starting Year: {student_data[3]}")
    print(f"4. Total Attendance: {student_data[4]}")
    print(f"5. Years: {student_data[5]}")
    print(f"6. Last Attendance Time: {student_data[6]}")
    print(f"7. Gender: {student_data[8]}")
    print("8. Update Image")

    choice = input("\nEnter field number to update (1-8) or 'cancel' to abort: ")
    if choice.lower() == 'cancel':
        connection.close()
        return

    update_fields = {
        '1': ('student_name', 'Enter new name: '),
        '2': ('major', 'Enter new major: '),
        '3': ('starting_year', 'Enter new starting year: '),
        '4': ('total_attendance', 'Enter new total attendance: '),
        '5': ('years', 'Enter new years: '),
        '6': ('last_attendance_time', 'Enter new last attendance time (YYYY-MM-DD HH:MM:SS): '),
        '7': ('Gender', 'Enter new gender: '),
        '8': ('student_image', 'Enter new image path: ')
    }

    if choice not in update_fields:
        print("Invalid choice!")
        connection.close()
        return

    column, prompt = update_fields[choice]
    new_value = input(prompt)

    # Handle special cases
    if column == 'student_image':
        try:
            new_value = convert_to_binary_data(new_value)
        except FileNotFoundError:
            print("Image file not found! Update aborted.")
            connection.close()
            return
    elif column in ('starting_year', 'total_attendance', 'years'):
        new_value = int(new_value)

    # Execute update
    cursor.execute(f"""
    UPDATE students SET {column} = ? WHERE student_id = ?
    """, (new_value, student_id))

    connection.commit()
    print("\nStudent record updated successfully!")
    connection.close()


def display_student():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    student_id = input("Enter Student ID to display: ")
    cursor.execute("""
    SELECT student_id, student_name, major, starting_year,
           total_attendance, years, last_attendance_time, Gender
    FROM students WHERE student_id = ?
    """, (student_id,))

    student_data = cursor.fetchone()

    if not student_data:
        print(f"\nStudent ID {student_id} not found!")
        connection.close()
        return

    print("\nStudent Information:")
    print(f"ID: {student_data[0]}")
    print(f"Name: {student_data[1]}")
    print(f"Major: {student_data[2]}")
    print(f"Starting Year: {student_data[3]}")
    print(f"Total Attendance: {student_data[4]}")
    print(f"Years: {student_data[5]}")
    print(f"Last Attendance: {student_data[6]}")
    print(f"Gender: {student_data[7]}")
    connection.close()


def main_menu():
    display_student()
    insert_new_student()
    update_student()
