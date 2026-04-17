/*
================================================================================
Example 8: Sixth Normal Form (6NF)
================================================================================
SOURCE: https://en.wikipedia.org/wiki/Sixth_normal_form
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.NF6_Medic;
GO

-- Create table demonstrating 6NF violation
CREATE TABLE norm.NF6_Medic (
    MedicID INT NOT NULL,
    MedicName VARCHAR(50) NOT NULL,
    Occupation VARCHAR(50) NOT NULL,
    Type VARCHAR(50) NOT NULL,
    PracticeInYears INT NOT NULL,

    CONSTRAINT PK_NF6_Medic PRIMARY KEY (MedicID)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.NF6_Medic (MedicID, MedicName, Occupation, Type, PracticeInYears) VALUES
(1, 'Smith James', 'Orthopedic', 'Specialist', 23),
(2, 'Miller Michael', 'Orthopedic', 'Probationer', 4),
(3, 'Thomas Linda', 'Neurologist', 'Probationer', 5),
(4, 'Scott Nancy', 'Orthopedic', 'Resident', 1),
(5, 'Allen Brian', 'Neurologist', 'Specialist', 12),
(6, 'Turner Steven', 'Ophthalmologist', 'Probationer', 3),
(7, 'Collins Kevin', 'Ophthalmologist', 'Specialist', 7),
(8, 'King Donald', 'Neurologist', 'Resident', 1),
(9, 'Harris Sarah', 'Ophthalmologist', 'Resident', 2);
GO

PRINT 'Medic table created successfully!';
GO

