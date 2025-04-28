from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import httpx
import shutil
import uuid
import os
import re
import csv, io
from openai import OpenAI
from models import Assignment, Class, Student, Instructor
from sqlalchemy.orm import Session
import datetime

error_log = 'error_logs.txt'


def log_error(message):
    with open(error_log, 'a') as f:
        f.write(message + '\n')

# In-memory storage

# --- Simulated GPT Call ---
async def evaluate_grade(file_content: str) -> (str, str):
    try:
        prompt = f'''
        You are a teacher who is grading the class assignments. Grade the following assignment and give feedback to the student.
        
        Output Format:
        ```Grade: A (or B, C, D, F etc.)```
        Feedback: <detailed explanation>
        
        Assignment Text:
        {file_content}
        '''
        client = OpenAI( )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = completion.choices[0].message.content

        grade_match = re.search(r"```Grade:\s*(.*?)```", content, re.DOTALL | re.IGNORECASE)
        grade_query = grade_match.group(1).strip() if grade_match else None

        explanation_match = re.search(r"Feedback:\s*(.*)", content, re.DOTALL)
        explanation = explanation_match.group(1).strip() if explanation_match else None

        if grade_query is None or explanation is None:
            raise ValueError("Could not extract grade or explanation properly.")

        return grade_query, explanation

    except Exception as e:
        log_error(f"Error in evaluate_grade: {str(e)}")
        return "Error", "Could not generate feedback."

# --- Background Grading Task ---
async  def process_file(content: bytes, filename: str, class_name: str, db: Session, student_id: int):
    try:
        # Find the student object
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            log_error(f"Student ID {student_id} not found.")
            return

        # Find the class object
        class_obj = db.query(Class).filter(Class.name == class_name).first()
        if not class_obj:
            log_error(f"Class {class_name} not found.")
            return

        # --- Create structured file name ---
        clean_student_email = student.email.replace('@', '_at_')  # (optional: replace special chars)
        clean_class_name = class_obj.name.replace(' ', '_')       # (optional: remove spaces if any)
        timestamp = datetime.datetime.now()
        structured_filename = f"{clean_student_email}-{clean_class_name}-{timestamp}-{filename}"
        documents_dir = "documents"
        os.makedirs(documents_dir, exist_ok=True)

        saved_path = os.path.join(documents_dir, structured_filename)

        # Save file
        with open(saved_path, "wb") as f:
            f.write(content)

        # Then grading etc. as before
        grade, feedback = await evaluate_grade(content.decode('utf-8', errors='ignore') if filename.endswith('.txt') else "PDF parsing...")  # (simplified here)

        # Save to database
        new_assignment = Assignment(
            filename=structured_filename, 
            grade=grade,
            feedback=feedback,
            student_id=student.id,
            class_id=class_obj.id
        )
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

    except Exception as e:
        log_error(f"Error processing file {filename}: {str(e)}")

async def upload_csv(file_content: bytes, db):
    decoded = file_content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))

    inserted_students = 0
    inserted_instructors = 0
    inserted_classes = 0

    for row in reader:
        row_type = row.get('type', '').strip().lower()
        if row_type == 'student':
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()

            if name and email:
                existing_student = db.query(Student).filter(Student.email == email).first()
                if not existing_student:
                    new_student = Student(name=name, email=email)
                    db.add(new_student)
                    db.flush()
                    inserted_students += 1

        elif row_type == 'instructor':
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()

            if name and email:
                existing_instructor = db.query(Instructor).filter(Instructor.email == email).first()
                if not existing_instructor:
                    new_instructor = Instructor(name=name, email=email)
                    db.add(new_instructor)
                    db.flush()
                    inserted_instructors += 1

        elif row_type == 'class':
            name = row.get('name', '').strip()
            year = row.get('year', '').strip()
            semester = row.get('semester', '').strip().upper()
            instructor_email = row.get('instructor_email', '').strip()
            student_emails = row.get('student_emails', '').strip()

            instructor = db.query(Instructor).filter(Instructor.email == instructor_email).first()

            if name and year and semester and instructor:
                existing_class = db.query(Class).filter(Class.name == name).first()

                if not existing_class:
                    new_class = Class(
                        name=name,
                        year=int(year),
                        semester=semester,
                        instructor_id=instructor.id
                    )
                    db.add(new_class)
                    db.flush()
                    target_class = new_class
                    inserted_classes += 1
                    print(f"✅ New class {name} created.")
                else:
                    target_class = existing_class
                    print(f"ℹ️ Class {name} already exists, adding students to it.")

                if student_emails:
                    email_list = [email.strip() for email in student_emails.split(",")]
                    for email in email_list:
                        student = db.query(Student).filter(Student.email == email).first()
                        if student:
                            if student not in target_class.students:
                                target_class.students.append(student)
                                print(f"Student {student.email} added to class {target_class.name}")
                            else:
                                print(f"Student {student.email} already enrolled in {target_class.name}")
                        else:
                            print(f" Student with email {email} not found!")

    db.commit()
    db.close()
    return {
        "students_inserted": inserted_students,
        "instructors_inserted": inserted_instructors,
        "classes_inserted": inserted_classes
    }