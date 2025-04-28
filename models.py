# models.py

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Table, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum 

# Database URL
DATABASE_URL = "sqlite:///./documents.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Association Table for Student-Class Many-to-Many ---
student_class_association = Table(
    'student_class_association',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('class_id', Integer, ForeignKey('classes.id'))
)

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)

    classes = relationship("Class", back_populates="instructor")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)

    classes = relationship(
        "Class",
        secondary=student_class_association,
        back_populates="students"
    )
    assignments = relationship("Assignment", back_populates="student")


class SemesterEnum(enum.Enum):
    FALL = "Fall"
    SPRING = "Spring"

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    year = Column(Integer)
    semester = Column(Enum(SemesterEnum), nullable=False) 

    instructor_id = Column(Integer, ForeignKey('instructors.id'))
    instructor = relationship("Instructor", back_populates="classes")

    students = relationship(
        "Student",
        secondary=student_class_association,
        back_populates="classes"
    )
    assignments = relationship("Assignment", back_populates="class_obj")  

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    grade = Column(String(10))
    feedback = Column(Text)

    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    student = relationship("Student", back_populates="assignments")

    class_id = Column(Integer, ForeignKey('classes.id'))
    class_obj = relationship("Class", back_populates="assignments")
    comment = relationship("Comment", uselist=False, back_populates="assignment")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
# --- Create all tables ---

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    student_comment = Column(Text)
    instructor_response = Column(Text)
    assignment = relationship("Assignment", back_populates="comment")
Base.metadata.create_all(bind=engine)
