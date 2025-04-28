# --- Routes ---
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from models import Assignment, Class, Student, Instructor, Admin, Comment
from  main import process_file, upload_csv
from fastapi import Depends
from models import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Form
from fastapi.responses import RedirectResponse
from fastapi import status
from fastapi import Cookie
import os
app = FastAPI()



# Static & Template Setup
templates = Jinja2Templates(directory="frontend-files")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db), user_id: str = Cookie(default=None), user_role: str = Cookie(default=None)):
    if not user_id or user_role != "student":
        return RedirectResponse(url="/login")

    classes = db.query(Class).join(Class.students).filter(Student.id == user_id).all()
    return templates.TemplateResponse("index.html", {"request": request, "classes": classes})

@app.post("/upload")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks,  class_name: str = Form(...),  user_id: str = Cookie(default=None),  user_role: str = Cookie(default=None),db: Session = Depends(get_db)):
    if not user_id or user_role != "student":
        return {"error": "You must be logged in to upload assignments."}
    content = await file.read()  # Read the file immediately

    background_tasks.add_task(process_file, content , file.filename, class_name, db, user_id)
    return {"message": "File received, grading in progress!"}

@app.get("/results")
async def get_results(user_id: str = Cookie(default=None), db: Session = Depends(get_db)):
    if not user_id:
        return []

    assignments = db.query(Assignment).filter(Assignment.student_id == int(user_id)).all()
    return [
        {
            "id": a.id, 
            "filename": a.filename,
            "class_name": a.class_obj.name if a.class_obj else "N/A",
            "grade": a.grade,
            "feedback": a.feedback,
            'comment': a.comment
        }
        for a in assignments
    ]

@app.get("/instructor_dashboard", response_class=HTMLResponse)
async def instructor_dashboard(
    request: Request,
    user_id: str = Cookie(default=None),
    user_role: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not user_id or user_role != "instructor":
        return RedirectResponse(url="/login")
    instructor_id = int(user_id)
    # Get all classes taught by this instructor
    classes = db.query(Class).filter(Class.instructor_id == instructor_id).all()

    classes_data = []
    for class_ in classes:
        students_data = []
        for student in class_.students:
            assignments = db.query(Assignment).filter(
                Assignment.student_id == student.id,
                Assignment.class_id == class_.id
            ).all()
            students_data.append({
                "student": student,
                "assignments": assignments
            })

        classes_data.append({
            "class": class_,
            "students": students_data
        })

    return templates.TemplateResponse(
        "instructor_dashboard.html",
        {"request": request, "classes_data": classes_data}
    )
@app.get("/download/{assignment_id}")
async def download_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

    if not assignment:
        return {"error": "Assignment not found."}

    file_path = os.path.join("documents", assignment.filename)

    if not os.path.exists(file_path):
        return {"error": "File not found on server."}

    return FileResponse(
        path=file_path,
        filename=assignment.filename,  # <-- What browser will name the downloaded file
        media_type='application/octet-stream'  # <-- General binary type
    )
@app.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user_id: str = Cookie(default=None),
    user_role: str = Cookie(default=None),
    db: Session = Depends(get_db)):
    if not user_id or user_role != "admin":
        return RedirectResponse(url="/login")

    classes = db.query(Class).all()

    classes_data = []
    for class_ in classes:
        students_data = []
        for student in class_.students:
            assignments = db.query(Assignment).filter(
                Assignment.student_id == student.id,
                Assignment.class_id == class_.id
            ).all()
            students_data.append({
                "student": student,
                "assignments": assignments
            })

        classes_data.append({
            "class": class_,
            "instructor": class_.instructor,
            "students": students_data
        })
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "classes_data": classes_data})

@app.post("/upload_csv")
async def upload_file(file: UploadFile, user_id: str = Cookie(default=None), user_role: str = Cookie(default=None), db: Session = Depends(get_db)):
    if not user_id or user_role != "admin":
        return {"error": "You must be logged in to upload csvs."}

    content = await file.read()  

    await upload_csv(content, db) 
    return HTMLResponse(content="""
    <html>
    <head><meta charset="utf-8"><title>Upload Success</title></head>
    <body style="text-align:center; margin-top: 50px;">
        <h2>Upload successful! Redirecting to Admin Dashboard...</h2>
        <script>
            setTimeout(function() {
                window.location.href = '/admin_dashboard';
            }, 1500);  // Redirect after 1.5 seconds
        </script>
    </body>
    </html>
    """, status_code=200)
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == email).first()

    if student:
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="user_id", value=str(student.id))
        response.set_cookie(key="user_role", value="student")
        return response

    # If not a student, check if Instructor
    instructor = db.query(Instructor).filter(Instructor.email == email).first()

    if instructor:
        response = RedirectResponse(url="/instructor_dashboard", status_code=302)
        response.set_cookie(key="user_id", value=str(instructor.id))
        response.set_cookie(key="user_role", value="instructor")
        return response
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin:
        response = RedirectResponse(url="/admin_dashboard", status_code=302)
        response.set_cookie(key="user_id", value=str(admin.id))
        response.set_cookie(key="user_role", value="admin")
        return response
    # If neither found
    return templates.TemplateResponse("login.html", {"request": request, "error": "User not found!"})
from fastapi import Form

@app.post("/comment/{assignment_id}")
async def student_comment(assignment_id: int, comment_text: str = Form(...), db: Session = Depends(get_db), user_id: str = Cookie(default=None),user_role: str = Cookie(default=None) ):
    if not user_id or user_role != "student":
        return {"error": "You must be logged in as a student to comment."}

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id, Assignment.student_id == int(user_id)).first()

    if not assignment:
        return {"error": "Assignment not found or you are not authorized."}

    if assignment.comment:
        assignment.comment.student_comment = comment_text
    else:
        new_comment = Comment(
            assignment_id=assignment_id,
            student_comment=comment_text
        )
        db.add(new_comment)

    db.commit()
    return {"message": "Comment submitted successfully."}

@app.post("/comment_response/{assignment_id}")
async def instructor_response(assignment_id: int, response_text: str = Form(...), db: Session = Depends(get_db), user_id: str = Cookie(default=None),user_role: str = Cookie(default=None)):
    if not user_id or user_role != "instructor":
        return {"error": "You must be logged in as an instructor to respond."}

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()

    if not assignment or assignment.class_obj.instructor_id != int(user_id):
        return {"error": "Assignment not found or you are not authorized."}

    if assignment.comment:
        assignment.comment.instructor_response = response_text
        db.commit()
        return RedirectResponse(url="/instructor_dashboard", status_code=303)
    else:
        return {"error": "No comment from student to respond to."}

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="user_id")
    response.delete_cookie(key="user_role")
    return response