/*
================================================================================
Example 5: Multivalued Dependency
================================================================================
SOURCE: https://en.wikipedia.org/wiki/Multivalued_dependency
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.MVD_UniversityCourses;
GO

-- Create table demonstrating multivalued dependency
CREATE TABLE norm.MVD_UniversityCourses (
    Course VARCHAR(50) NOT NULL,
    Book VARCHAR(50) NOT NULL,
    Lecturer VARCHAR(50) NOT NULL,

    CONSTRAINT PK_MVD_UniversityCourses PRIMARY KEY (Course, Book, Lecturer)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.MVD_UniversityCourses (Course, Book, Lecturer) VALUES
('AHA', 'Silberschatz', 'John D'),
('AHA', 'Nederpelt', 'John D'),
('AHA', 'Silberschatz', 'William M'),
('AHA', 'Nederpelt', 'William M'),
('AHA', 'Silberschatz', 'Christian G'),
('AHA', 'Nederpelt', 'Christian G'),
('OSO', 'Silberschatz', 'John D'),
('OSO', 'Silberschatz', 'William M');
GO

PRINT 'UniversityCourses table created successfully!';
GO

