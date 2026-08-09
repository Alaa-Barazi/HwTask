USE university_db;

-- Teachers
INSERT INTO Teacher (Name) VALUES
('Alice'),
('David'),
('Sarah');

-- Students
INSERT INTO Student (Name) VALUES
('Bob'),
('Maya'),
('Omar');

-- Courses
INSERT INTO Course (Name, Points) VALUES
('OOP',4),
('Databases',3),
('Algorithms',5),
('Networks', 4),
('Web', 3),
('DataStructure', 5);

-- Semesters
INSERT INTO Semester (Year, Season) VALUES
(2026, 'Fall'),
(2026, 'Spring'),
(2025, 'Fall');

-- Offerings (CourseByTeacher)
-- Alice teaches OOP in Fall 2026, Databases in Spring 2026
-- David teaches Algorithms in Fall 2026
-- Sarah teaches OOP in Fall 2025 (different semester, allowed)
INSERT INTO CourseByTeacher (TeacherID, CourseID, SemesterID, Hours) VALUES
(1, 1, 1, 60),  -- OfferingID 1: Alice, OOP, Fall 2026
(1, 2, 2, 45),  -- OfferingID 2: Alice, Databases, Spring 2026
(2, 3, 1, 50),  -- OfferingID 3: David, Algorithms, Fall 2026
(3, 1, 3, 60);  -- OfferingID 4: Sarah, OOP, Fall 2025

-- Grades (CourseGrade)
-- Bob took OOP with Alice in Fall 2026, and Algorithms with David in Fall 2026
-- Maya took Databases with Alice in Spring 2026
-- Omar took OOP with Alice in Fall 2026
INSERT INTO CourseGrade (StudentID, OfferingID, Grade) VALUES
(1, 1, 88.50),  -- Bob, OOP/Alice/Fall2026
(1, 3, 76.00),  -- Bob, Algorithms/David/Fall2026
(2, 2, 91.00),  -- Maya, Databases/Alice/Spring2026
(3, 1, 65.00);  -- Omar, OOP/Alice/Fall2026
