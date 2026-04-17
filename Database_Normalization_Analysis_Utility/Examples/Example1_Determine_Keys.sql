/*
================================================================================
Example 1: Determine Keys
================================================================================
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.Keys_Example;
GO

-- Create table with composite primary key
CREATE TABLE norm.Keys_Example (
    ColumnA INT NOT NULL,
    ColumnB INT NOT NULL,
    ColumnC INT NOT NULL,
    ColumnD INT NOT NULL,
    ColumnE INT NOT NULL,
    ColumnF VARCHAR(50),
    ColumnG VARCHAR(50),

    -- Composite Primary Key
    CONSTRAINT PK_Keys_Example PRIMARY KEY (ColumnA, ColumnB)
);
GO

-- Create composite unique key on {ColumnC, ColumnD}
CREATE UNIQUE INDEX UQ_Keys_Example_CD
    ON norm.Keys_Example (ColumnC, ColumnD);
GO

-- Create single-column unique key on ColumnE
CREATE UNIQUE INDEX UQ_Keys_Example_E
    ON norm.Keys_Example (ColumnE);
GO

-- Example 2: Single-column primary key with multiple unique keys
DROP TABLE IF EXISTS norm.Keys_Example2;
GO

CREATE TABLE norm.Keys_Example2 (
    ID INT NOT NULL,
    Email VARCHAR(100) NOT NULL,
    SSN VARCHAR(11) NOT NULL,
    EmployeeNumber VARCHAR(20) NOT NULL,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),

    -- Single-column Primary Key
    CONSTRAINT PK_Keys_Example2 PRIMARY KEY (ID),

    -- Multiple unique keys
    CONSTRAINT UQ_Keys_Example2_Email UNIQUE (Email),
    CONSTRAINT UQ_Keys_Example2_SSN UNIQUE (SSN),
    CONSTRAINT UQ_Keys_Example2_EmpNum UNIQUE (EmployeeNumber)
);
GO

-- Example 3: Three-column composite primary key
DROP TABLE IF EXISTS norm.Keys_Example3;
GO

CREATE TABLE norm.Keys_Example3 (
    Year INT NOT NULL,
    Month INT NOT NULL,
    Day INT NOT NULL,
    EventName VARCHAR(100),
    Location VARCHAR(100),

    -- Three-column composite primary key
    CONSTRAINT PK_Keys_Example3 PRIMARY KEY (Year, Month, Day)
);
GO

PRINT 'Keys examples created successfully!';
GO

