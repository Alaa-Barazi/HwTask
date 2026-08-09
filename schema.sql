-- Create and select the database
CREATE DATABASE IF NOT EXISTS university_db;
USE university_db;

-- Teacher
CREATE TABLE Teacher (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL
);

-- Student
CREATE TABLE Student (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL
);

-- Course
CREATE TABLE Course (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Points INT NOT NULL
);

-- Semester (Year + Season together identify it, no separate Name field)
CREATE TABLE Semester (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Year INT NOT NULL,
    Season VARCHAR(20) NOT NULL,
    CONSTRAINT uq_semester UNIQUE (Year, Season)
);

-- CourseByTeacher (the "offering": a specific course, taught by a specific
-- teacher, in a specific semester — a teacher can only teach a given course
-- once per semester, enforced below)
CREATE TABLE CourseByTeacher (
    OfferingID INT AUTO_INCREMENT PRIMARY KEY,
    TeacherID INT NOT NULL,
    CourseID INT NOT NULL,
    SemesterID INT NOT NULL,
    Hours INT NOT NULL,
    CONSTRAINT fk_offering_teacher FOREIGN KEY (TeacherID) REFERENCES Teacher(ID),
    CONSTRAINT fk_offering_course FOREIGN KEY (CourseID) REFERENCES Course(ID),
    CONSTRAINT fk_offering_semester FOREIGN KEY (SemesterID) REFERENCES Semester(ID),
    CONSTRAINT uq_offering UNIQUE (TeacherID, CourseID, SemesterID)
);

-- CourseGrade (a student's grade for a specific offering)
CREATE TABLE CourseGrade (
    StudentID INT NOT NULL,
    OfferingID INT NOT NULL,
    Grade DECIMAL(5,2) NOT NULL,
    PRIMARY KEY (StudentID, OfferingID),
    CONSTRAINT fk_grade_student FOREIGN KEY (StudentID) REFERENCES Student(ID),
    CONSTRAINT fk_grade_offering FOREIGN KEY (OfferingID) REFERENCES CourseByTeacher(OfferingID)
);
