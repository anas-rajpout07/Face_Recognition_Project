import sys
import os
import sqlite3
import datetime
import pickle
import cv2
import face_recognition
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

db_path = os.path.join(BASE_DIR, 'student.db')


from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QComboBox, QFormLayout, QCheckBox,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QToolButton
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from database import convert_to_binary_data


class AttendanceThread(QThread):
    finished_signal = pyqtSignal()

    def run(self):
        proj_path = os.path.join(BASE_DIR, "proj.py")
        subprocess.run([sys.executable, proj_path], cwd=BASE_DIR)
        self.finished_signal.emit()

# Login Dialog
login_stylesheet = """
/* Overall Login Dialog */
QDialog {
    background-color: #F5F7FA; /* Same background as main interface */
    border: 1px solid #E1E5EB;
    border-radius: 8px;
}

/* Left Panel with Blue Gradient (like #infoFrame in main interface) */
#LeftPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #024a94, /* Dark Blue */
        stop: 1 #5aa2e0  /* Lighter Blue */
    );
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
}

/* Labels on Left Panel */
#WelcomeLabel {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: bold;
}

#SigninLabel {
    color: #FFFFFF;
    font-size: 16px;
}

/* Right Panel with White Background */
#RightPanel {
    background: #FFFFFF;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}

/* Labels on Right Panel */
#HelloLabel {
    font-size: 24px;
    font-weight: bold;
    color: #333333;
}

#LoginLabel {
    font-size: 16px;
    color: #555555;
}

/* Forgot Password Link */
#ForgotLabel {
    color: #888888;
    text-decoration: underline;
}
#ForgotLabel:hover {
    color: #555555;
}

/* QLineEdit Fields */
QLineEdit {
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 8px;
    font-size: 14px;
}
QLineEdit:focus {
    border: 1px solid #5aa2e0; /* Focus color from main interface */
}

/* Submit Button with Horizontal Gradient (matching main interface buttons) */
#SubmitButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #024a94,
        stop: 1 #5aa2e0
    );
    color: #FFFFFF;
    border-radius: 5px;
    padding: 10px;
    font-size: 16px;
    font-weight: bold;
}
#SubmitButton:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #035aa9, /* Slightly lighter dark blue */
        stop: 1 #69b4f2  /* Brighter light blue */
    );
}
#SubmitButton:pressed {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #023d6e, /* Deeper dark blue */
        stop: 1 #4b82c0  /* Darkened light blue */
    );
}

/* Create Account Button as an outlined version of the main interface colors */
#CreateAccountButton {
    background-color: transparent;
    color: #024a94;
    border: 1px solid #024a94;
    border-radius: 5px;
    padding: 8px;
    font-size: 14px;
}
#CreateAccountButton:hover {
    background: #024a94;
    color: #FFFFFF;
}
#CreateAccountButton:pressed {
    background: #023d6e;
    color: #FFFFFF;
}
"""
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teacher Login")
        self.setFixedSize(800, 500)

        main_layout = QHBoxLayout(self)

        # Left Panel
        self.left_panel = QWidget()
        self.left_panel.setObjectName("LeftPanel")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.addStretch()
        welcome_label = QLabel("Welcome Page")
        welcome_label.setObjectName("WelcomeLabel")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signin_label = QLabel("Sign In To Your Account")
        signin_label.setObjectName("SigninLabel")
        signin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(welcome_label)
        left_layout.addWidget(signin_label)
        left_layout.addStretch()

        # Right Panel Login Form Fields
        self.right_panel = QWidget()
        self.right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.addStretch()
        hello_label = QLabel("Hello! Good Morning")
        hello_label.setObjectName("HelloLabel")
        hello_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_label = QLabel("Login Your Account")
        login_label.setObjectName("LoginLabel")
        login_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(hello_label)
        right_layout.addWidget(login_label)
        right_layout.addSpacing(20)

        # Username field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("username")
        self.email_input.setFixedWidth(262)
        right_layout.addWidget(self.email_input)

        # Password field with toggle button
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("password")
        password_layout.addWidget(self.password_input)

        # Eye button to toggle password visibility
        self.eye_button = QToolButton()
        # Set the initial icon for the closed-eye (masked) state.
        self.eye_button.setIcon(QIcon(os.path.join(BASE_DIR, "close-eye.png")))
        self.eye_button.setCheckable(True)
        self.eye_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_button.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.eye_button)

        right_layout.addLayout(password_layout)
        right_layout.addSpacing(10)

        # Checkbox and Forgot Password
        remember_layout = QHBoxLayout()
        self.remember_checkbox = QCheckBox("Remember")
        forgot_label = QLabel("<a href='#'>Forgot Password?</a>")
        forgot_label.setOpenExternalLinks(False)
        forgot_label.setTextFormat(Qt.TextFormat.RichText)
        forgot_label.setObjectName("ForgotLabel")
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        remember_layout.addWidget(forgot_label)
        right_layout.addLayout(remember_layout)
        right_layout.addSpacing(10)

        submit_button = QPushButton("SUBMIT")
        submit_button.setObjectName("SubmitButton")
        submit_button.clicked.connect(self.attempt_login)
        create_account_button = QPushButton("Create Account")
        create_account_button.setObjectName("CreateAccountButton")
        right_layout.addWidget(submit_button)
        right_layout.addSpacing(10)
        right_layout.addWidget(create_account_button)
        right_layout.addStretch()

        main_layout.addWidget(self.left_panel, stretch=3)
        main_layout.addWidget(self.right_panel, stretch=2)

        self.setStyleSheet(login_stylesheet)

    def toggle_password_visibility(self):
        if self.eye_button.isChecked():
            # Button is toggled on: show password with open eye icon.
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_button.setIcon(QIcon(os.path.join(BASE_DIR, "open-eye.png")))
        else:
            # Button is toggled off: mask password with closed eye icon.
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_button.setIcon(QIcon(os.path.join(BASE_DIR, "close-eye.png")))

    def attempt_login(self):
        username = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if username == "teacher" and password == "password":
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

# Edit Student Data Dialog
Edit_student_dialog = """
/* Dialog background, matching main interface */
QMainWindow, QDialog {
    background-color: #F5F7FA;
    border: 1px solid #E1E5EB;
    border-radius: 8px;
}

/* Info Frame with the same gradient as #infoFrame in main interface */
QFrame#infoFrame {
    border: none;
    border-radius: 12px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #024a94,
        stop:1 #5aa2e0
    );
    padding: 20px;
}

/* Labels inside infoFrame: same 20px, 600 weight as main interface #infoFrame labels */
QFrame#infoFrame QLabel {
    font-size: 20px;
    font-weight: 600;
    color: #FFFFFF;  /* White text to stand out on the blue gradient */
}

/* Table styling, matching main interface QTableWidget */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E1E5EB;
    border-radius: 8px;
    alternate-background-color: #F9FAFC;
    gridline-color: #E1E5EB;
    padding: 10px;
    selection-background-color: #5aa2e0;
    selection-color: #FFFFFF;
}

/* Table header with vertical blue gradient, matching main interface */
QHeaderView::section {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #024a94,
        stop:1 #5aa2e0
    );
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
    padding: 10px;
    border: none;
}
QTableWidget QTableCornerButton::section {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #024a94,
        stop:1 #5aa2e0
    );
}

/* Buttons with the same horizontal gradient as in main interface */
QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #024a94,
        stop:1 #5aa2e0
    );
    color: #FFFFFF;
    border: none;
    padding: 14px 24px;
    border-radius: 8px;
    font-size: 14px;   /* Matching main interface button text size */
    font-weight: 600;  /* Matching main interface button weight */
}
QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #035aa9,
        stop:1 #69b4f2
    );
}
QPushButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #023d6e,
        stop:1 #4b82c0
    );
}

/* Generic QLabel styling, same base font color & size as main interface */
QLabel {
    color: #333333;
    font-size: 14px;
    font-weight: 600;
    padding: 5px;
}

/* Line edits & combo boxes: same border, radius, font as main interface */
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    border: 2px solid #E1E5EB;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    margin-top: 5px;
    color: #333333;
}
"""
class EditStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Student Data")
        self.setFixedSize(550, 500)
        self.setStyleSheet(Edit_student_dialog)
        layout = QVBoxLayout(self)

        # Section: Enter Student ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Enter Student ID:"))
        self.id_input = QLineEdit()
        id_layout.addWidget(self.id_input)
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_student)
        id_layout.addWidget(self.search_btn)
        layout.addLayout(id_layout)

        # Form layout for student details (initially hidden)
        self.form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.major_edit = QLineEdit()
        self.starting_year_edit = QLineEdit()
        self.attendance_edit = QLineEdit()
        self.years_edit = QLineEdit()
        self.last_attendance_edit = QLineEdit()
        self.gender_edit = QLineEdit()
        self.form_layout.addRow("Name:", self.name_edit)
        self.form_layout.addRow("Major:", self.major_edit)
        self.form_layout.addRow("Starting Year:", self.starting_year_edit)
        self.form_layout.addRow("Total Attendance:", self.attendance_edit)
        self.form_layout.addRow("Years:", self.years_edit)
        self.form_layout.addRow("Last Attendance:", self.last_attendance_edit)
        self.form_layout.addRow("Gender:", self.gender_edit)
        layout.addLayout(self.form_layout)
        self.set_form_visible(False)

        # Buttons: Save, Cancel, and Delete Record
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn
        btn_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        self.delete_btn = QPushButton("Delete Record")
        self.delete_btn.clicked.connect(self.delete_record)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

    def set_form_visible(self, visible):
        for i in range(self.form_layout.count()):
            widget = self.form_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(visible)

    def search_student(self):
        student_id = self.id_input.text().strip()
        if not student_id:
            QMessageBox.warning(self, "Input Error", "Please enter a Student ID.")
            return
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_name, major, starting_year, total_attendance, years, last_attendance_time, Gender 
            FROM students WHERE student_id = ?
        """, (student_id,))
        record = cursor.fetchone()
        conn.close()
        if not record:
            QMessageBox.warning(self, "Not Found", f"Student ID {student_id} not found!")
            self.set_form_visible(False)
            return
        # Populate the fields
        self.name_edit.setText(record[0])
        self.major_edit.setText(record[1])
        self.starting_year_edit.setText(str(record[2]))
        self.attendance_edit.setText(str(record[3]))
        self.years_edit.setText(str(record[4]))
        self.last_attendance_edit.setText(record[5])
        self.gender_edit.setText(record[6])
        self.set_form_visible(True)

    def save_changes(self):
        student_id = self.id_input.text().strip()
        name = self.name_edit.text().strip()
        major = self.major_edit.text().strip()
        try:
            starting_year = int(self.starting_year_edit.text().strip())
            total_attendance = int(self.attendance_edit.text().strip())
            years = int(self.years_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Starting Year, Total Attendance, and Years must be integers.")
            return
        last_attendance = self.last_attendance_edit.text().strip()
        gender = self.gender_edit.text().strip()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students 
            SET student_name = ?, major = ?, starting_year = ?, total_attendance = ?, years = ?, last_attendance_time = ?, Gender = ?
            WHERE student_id = ?
        """, (name, major, starting_year, total_attendance, years, last_attendance, gender, student_id))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Success", "Student record updated successfully!")
        self.accept()

    def delete_record(self):
        student_id = self.id_input.text().strip()
        if not student_id:
            QMessageBox.warning(self, "Input Error", "No Student ID provided!")
            return
        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete the record for Student ID {student_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Deleted", f"Student record for ID {student_id} has been deleted.")
            self.accept()

# Main Window
main_interface_stylesheet = """
/* General widget styling */
QWidget {
    background-color: #F5F7FA;  /* Clean, professional light background */
    color: #333333;
    font-family: "Segoe UI", sans-serif;
}

/* Top info panel with a defined dark-to-light blue gradient */
#infoFrame {
    border: none;
    border-radius: 12px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #024a94,  /* Slightly lighter dark blue for better contrast */
        stop:1 #5aa2e0   /* Softer light blue */
    );
    padding: 20px;
}
#infoFrame QLabel {
    font-size: 20px;
    font-weight: 600;
}

/* Match 'Edit Student Dialog' field style (without changing color scheme) */
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    border: 2px solid #E1E5EB; /* Main interface border color */
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    margin-top: 5px;
    color: #333333;
}

/* Student table styling */
QTableWidget {
    border: 1px solid #E1E5EB;
    border-radius: 8px;
    background-color: #FFFFFF;
    alternate-background-color: #F9FAFC;
    gridline-color: #E1E5EB;
    padding: 10px;
    selection-background-color: #5aa2e0;
    selection-color: #FFFFFF;
}

/* Table header with a vertical gradient */
QHeaderView::section {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #024a94,  /* Slightly lighter dark blue */
        stop:1 #5aa2e0   /* Softer light blue */
    );
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 600;
    padding: 10px;
    border: none;
}

/* Buttons with a horizontal gradient */
QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #024a94,
        stop:1 #5aa2e0
    );
    color: #FFFFFF;
    border: none;
    padding: 14px 15px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;

}
QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #035aa9,  /* Slightly lighter dark blue */
        stop:1 #69b4f2   /* Brighter light blue */
    );
}
QPushButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #023d6e,  /* Deeper dark blue */
        stop:1 #4b82c0   /* Darkened light blue */
    );
}

/* Dialog styling to match overall aesthetics */
QDialog {
    background-color: #F5F7FA;
    border: 1px solid #E1E5EB;
    border-radius: 8px;
}
"""
class MainWindow(QMainWindow):
    def __init__(self, teacher_username):
        super().__init__()
        self.setWindowTitle("Facial Recognition Attendance System - Main Menu")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet(main_interface_stylesheet)
        self.teacher_username = teacher_username

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Top Info Panel
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")

        info_layout = QGridLayout(info_frame)
        instructor_label = QLabel("Instructor Name: Dr. Smith")
        subject_label = QLabel("Subject Name: Machine Learning")
        semester_label = QLabel("Semester: 5")
        self.total_strength_label = QLabel("Total Strength: 0")
        self.males_label = QLabel("Males: 0")
        self.females_label = QLabel("Females: 0")
        info_layout.addWidget(instructor_label, 0, 0)
        info_layout.addWidget(subject_label, 0, 1)
        info_layout.addWidget(semester_label, 0, 2)
        info_layout.addWidget(self.total_strength_label, 1, 0)
        info_layout.addWidget(self.males_label, 1, 1)
        info_layout.addWidget(self.females_label, 1, 2)
        main_layout.addWidget(info_frame)

        # Student List Table
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4)
        self.students_table.setHorizontalHeaderLabels(
            ["Student ID", "Name", "Major", "Total Attendance"]
        )
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.students_table.setMinimumHeight(300)
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.students_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.students_table)

        # Bottom Buttons
        btn_layout = QHBoxLayout()

        self.register_btn = QPushButton("Register Student")
        self.register_btn.setFixedSize(325, 50)
        self.register_btn.clicked.connect(self.open_register_dialog)
        btn_layout.addWidget(self.register_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.edit_btn = QPushButton("Edit Student Data")
        self.edit_btn.setFixedSize(325, 50)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        btn_layout.addWidget(self.edit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.attendance_btn = QPushButton("Take Attendance")
        self.attendance_btn.setFixedSize(325, 50)
        self.attendance_btn.clicked.connect(self.start_attendance)
        btn_layout.addWidget(self.attendance_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(btn_layout)

        self.refresh_stats()

    def refresh_stats(self):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students WHERE Gender = 'Male'")
        male = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students WHERE Gender = 'Female'")
        female = cursor.fetchone()[0]
        self.total_strength_label.setText(f"Total Strength: {total}")
        self.males_label.setText(f"Males: {male}")
        self.females_label.setText(f"Females: {female}")

        # Update the Student table data
        cursor.execute("SELECT student_id, student_name, major, total_attendance FROM students")
        records = cursor.fetchall()
        self.students_table.setRowCount(len(records))
        for row_idx, row_data in enumerate(records):
            for col_idx, value in enumerate(row_data):
                self.students_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        conn.close()

    def open_register_dialog(self):
        dialog = RegisterStudentDialog(self)
        dialog.setStyleSheet(main_interface_stylesheet)
        dialog.exec()
        self.refresh_stats()

    def open_edit_dialog(self):
        dialog = EditStudentDialog(self)
        dialog.setStyleSheet(main_interface_stylesheet)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_stats()

    def start_attendance(self):
        self.attendance_thread = AttendanceThread()
        self.attendance_thread.finished_signal.connect(
            lambda: QMessageBox.information(self, "Attendance", "Attendance session ended.")
        )
        self.attendance_thread.start()

# Registration Dialog
class RegisterStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Student")
        self.setFixedSize(800, 500)
        self.setStyleSheet(main_interface_stylesheet)
        self.image_path = None

        layout = QGridLayout()
        def convert_to_binary_data(filename):
            with open(filename, 'rb') as file:
                blob_data = file.read()
            return blob_data
        layout.addWidget(QLabel("Student ID:"), 0, 0)
        self.student_id_edit = QLineEdit()
        layout.addWidget(self.student_id_edit, 0, 1)

        layout.addWidget(QLabel("Student Name:"), 1, 0)
        self.student_name_edit = QLineEdit()
        layout.addWidget(self.student_name_edit, 1, 1)

        layout.addWidget(QLabel("Major:"), 2, 0)
        self.major_edit = QLineEdit()
        layout.addWidget(self.major_edit, 2, 1)

        layout.addWidget(QLabel("Starting Year:"), 3, 0)
        self.starting_year_edit = QLineEdit()
        layout.addWidget(self.starting_year_edit, 3, 1)

        layout.addWidget(QLabel("Total Attendance:"), 4, 0)
        self.total_attendance_edit = QLineEdit()
        layout.addWidget(self.total_attendance_edit, 4, 1)

        layout.addWidget(QLabel("Years:"), 5, 0)
        self.years_edit = QLineEdit()
        layout.addWidget(self.years_edit, 5, 1)

        layout.addWidget(QLabel("Last Attendance (YYYY-MM-DD HH:MM:SS):"), 6, 0)
        self.last_attendance_edit = QLineEdit(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        layout.addWidget(self.last_attendance_edit, 6, 1)

        layout.addWidget(QLabel("Gender:"), 7, 0)
        self.gender_edit = QComboBox()
        self.gender_edit.addItems(["Male", "Female", "Other"])
        layout.addWidget(self.gender_edit, 7, 1)

        self.upload_pic_btn = QPushButton("Upload Picture (Capture)")
        self.upload_pic_btn.clicked.connect(self.upload_picture)
        layout.addWidget(self.upload_pic_btn, 8, 0)

        self.encode_pic_btn = QPushButton("Encode Picture")
        self.encode_pic_btn.clicked.connect(self.encode_picture)
        layout.addWidget(self.encode_pic_btn, 8, 1)

        self.image_preview = QLabel("No image captured")
        self.image_preview.setFixedSize(200, 200)
        layout.addWidget(self.image_preview, 0, 2, 5, 1)

        self.submit_btn = QPushButton("Submit Registration")
        self.submit_btn.clicked.connect(self.submit_registration)
        layout.addWidget(self.submit_btn, 9, 0)

        self.return_btn = QPushButton("Return")
        self.return_btn.clicked.connect(self.close)
        layout.addWidget(self.return_btn, 9, 1)

        self.setLayout(layout)

    def upload_picture(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.warning(self, "Camera Error", "Camera could not be opened!")
            return
        QMessageBox.information(self, "Capture", "Press 's' to capture the image.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Capture Picture - Press 's' to save", frame)
            key = cv2.waitKey(1)
            if key == ord('s'):
                image_path = os.path.join(BASE_DIR, "captured_student.jpg")
                cv2.imwrite(image_path, frame)
                self.image_path = image_path
                QMessageBox.information(self, "Image Captured", f"Image saved as {image_path}")
                pixmap = QPixmap(image_path)
                pixmap = pixmap.scaled(self.image_preview.width(), self.image_preview.height(),
                                       Qt.AspectRatioMode.KeepAspectRatio)
                self.image_preview.setPixmap(pixmap)
                break
        cap.release()
        cv2.destroyAllWindows()

    def encode_picture(self):
        if not self.image_path or not os.path.exists(self.image_path):
            QMessageBox.warning(self, "No Image", "Please capture an image first!")
            return
        image = cv2.imread(self.image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(image_rgb)
        if not encodings:
            QMessageBox.warning(self, "Encoding Error", "No face detected in the image!")
            return
        encoding = encodings[0]
        encode_file_path = os.path.join(BASE_DIR, "EncodeFile.p")
        if os.path.exists(encode_file_path):
            with open(encode_file_path, "rb") as f:
                data = pickle.load(f)
            encodelist, id_list = data
        else:
            encodelist, id_list = [], []
        student_id = self.student_id_edit.text().strip()
        if not student_id:
            QMessageBox.warning(self, "Missing Data", "Enter Student ID before encoding!")
            return
        encodelist.append(encoding)
        id_list.append(student_id)
        with open(encode_file_path, "wb") as f:
            pickle.dump([encodelist, id_list], f)
        QMessageBox.information(self, "Success", "Face encoding saved successfully.")

    def submit_registration(self):
        student_id = self.student_id_edit.text().strip()
        student_name = self.student_name_edit.text().strip()
        major = self.major_edit.text().strip()
        try:
            starting_year = int(self.starting_year_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Starting Year must be an integer.")
            return
        try:
            total_attendance = int(self.total_attendance_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Total Attendance must be an integer.")
            return
        try:
            years = int(self.years_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Years must be an integer.")
            return
        last_attendance_time = self.last_attendance_edit.text().strip()
        gender = self.gender_edit.currentText()

        if not self.image_path or not os.path.exists(self.image_path):
            QMessageBox.warning(self, "No Image", "Please capture and upload an image!")
            return
        try:
            image_blob = convert_to_binary_data(self.image_path)
        except Exception as e:
            QMessageBox.warning(self, "Image Error", str(e))
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT student_name FROM students WHERE student_id = ?", (student_id,))
        if cursor.fetchone():
            QMessageBox.warning(self, "Duplicate Entry", f"Student ID {student_id} already exists!")
            conn.close()
            return

        cursor.execute("""
            INSERT INTO students (student_id, student_name, major, starting_year, total_attendance, years, last_attendance_time, student_image, Gender)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, student_name, major, starting_year, total_attendance, years, last_attendance_time, image_blob, gender))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Success", f"Student {student_name} registered successfully!")
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        main_win = MainWindow(login_dialog.email_input.text().strip())
        main_win.setStyleSheet(main_interface_stylesheet)
        main_win.show()
        sys.exit(app.exec())
