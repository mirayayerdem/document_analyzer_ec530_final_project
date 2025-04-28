# document_analyzer_ec530_final_project
# Author: Miray Ayerdem

## Components Used From Course

During the implementation of this project, I incorporated various concepts and techniques covered throughout the course:

- **Database (SQL ORM)**: I used SQLAlchemy ORM, which is an easier and cleaner version compared to raw sqlite3 operations, for managing database tables and queries. I used sqlite3 in the previous assignments but i found sql orm easier to implement this assignment.
- **Client-Server Architecture**: I designed the system following a client-server model because it was the best architecture for handling student and instructor interactions with the system. The system's purpose is to create an environment to analyze students' documents using main server. 
- **Asynchronous Implementation**: I implemented async functions and FastAPI's `BackgroundTasks` for uploading and grading assignments and handling file processing without blocking the server. Users can do whatever they want while the main server is processing their files.
- **Error Logging**: I developed a `log_error` function to write any processing or runtime errors into a file (`error_logs.txt`), ensuring easier debugging and maintenance.
- **Dockerization**: I dockerized the application to ensure that it can be easily deployed and run in any environment without manual configuration.
- **Use of GPT API**: I integrated OpenAI's GPT models to automatically grade the uploaded assignments and provide detailed feedback to the students.
- **CSV-to-DB Conversion**: I reused the idea from earlier assignments by implementing a function that reads a CSV file and populates students, instructors, and class tables in the database.
- **Unit Testing**: I wrote unit tests to ensure critical parts of the application (e.g., database models, API endpoints) work correctly.
- **Git and GitHub Actions**: I used Git for version control throughout the development. Additionally, I configured GitHub Actions to automatically run unit tests on every push, ensuring code quality.

---

## Application Overview

### Users

- **Students**: Can upload their assignments, view grades and feedback, leave comments regarding their grading, and download their uploaded files.
- **Instructors**: Can view their classes, the students enrolled, assignments submitted by students, view student comments, and provide responses to comments.
- **Admin**: Can upload CSV files to bulk create students, instructors, and classes, and view all classes, instructors, and enrolled students from a centralized dashboard.

### Main Features

#### Authentication

- Basic login functionality using email-based login for students, instructors, and admins.
- Session management using cookies.

#### Upload and Grading

- Students upload `.txt` or `.pdf` files.
- Files are processed asynchronously in the background.
- Assignment content is sent to the GPT API for grading and feedback.
- Graded results are saved into the database and displayed to the student.

#### Comments System

- Students can submit comments for their assignments if they have questions about their grade.
- Instructors can respond to student comments directly from their dashboard.
- Comments and responses are visible under each assignment.

#### Error Handling

- Any unexpected issues (file reading problems, GPT API issues, database problems) are logged into an `error_logs.txt` file.

#### Admin Dashboard

- Admins can upload a CSV containing students, instructors, and class associations.
- Automatically creates records in the database based on the CSV file.
- Admins can view all classes, assigned instructors, and enrolled students.

#### Assignment Download

- Both students and instructors can download the original uploaded assignment files.
- Files are named systematically with student email, class name, and original filename.

#### Docker Support

- The application includes a Dockerfile that enables easy containerization.
- Run the full system (server + database) in one command.

#### Testing and CI

- Unit tests written using `pytest`.
- GitHub Actions pipeline automatically runs unit tests on every push.
- Ensures that all code changes are validated before being merged.

### Technologies Used

- **FastAPI**: Backend API framework.
- **SQLite with SQLAlchemy**: Lightweight database with ORM for easier development.
- **Jinja2**: Simple HTML template rendering.
- **Docker**: Application containerization.
- **OpenAI API**: Automated assignment grading.
- **GitHub Actions**: CI/CD for testing.
- **Python Asyncio**: For background tasks and asynchronous programming.

---

## How to Run

1. Clone the repository:

```bash
git clone <repo_url>
cd document-analyzer
```

2. Build and run with Docker:

```bash
docker build -t document-analyzer .
docker run -p 8000:8000 document-analyzer
```

3. Access the application:

- Visit `http://localhost:8000` to use the system.

4. Run tests manually (optional):

```bash
pytest
```

---

## Future Improvements

- Add email notifications for grading completion.
- Allow students to edit their submitted comments.
- Add pagination to dashboards for better scalability.
- Improve authentication with password support.

---

