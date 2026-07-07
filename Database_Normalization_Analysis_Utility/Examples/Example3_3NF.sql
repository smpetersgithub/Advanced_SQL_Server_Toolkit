/*
================================================================================
Example 3: Third Normal Form (3NF) Violation
================================================================================

SOURCE:
Wikipedia - Third Normal Form
https://en.wikipedia.org/wiki/Third_normal_form
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.NF3_Tournament;
GO

-- Create table that VIOLATES 3NF
CREATE TABLE norm.NF3_Tournament (
    Name VARCHAR(100) NOT NULL,
    Year INT NOT NULL,
    WinnerID INT NOT NULL,
    WinnerName VARCHAR(100) NOT NULL,
    WinnerBirthdate DATE NOT NULL,

    -- Composite Primary Key
    CONSTRAINT PK_NF3_Tournament PRIMARY KEY (Name, Year)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.NF3_Tournament (Name, Year, WinnerID, WinnerName, WinnerBirthdate) VALUES
('Indiana Invitational', 1998, 1, 'Al Fredrickson', '1975-07-21'),
('Cleveland Open', 1999, 2, 'Bob Albertson', '1968-09-28'),
('Des Moines Masters', 1999, 1, 'Al Fredrickson', '1975-07-21'),
('Indiana Invitational', 1999, 3, 'Chip Masterson', '1977-03-14');
GO

PRINT 'Tournament table created successfully!';
GO
