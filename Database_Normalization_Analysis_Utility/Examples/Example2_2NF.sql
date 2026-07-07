/*
================================================================================
Example 2: Second Normal Form (2NF) Violation
================================================================================
SOURCE: https://en.wikipedia.org/wiki/Second_normal_form
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.NF2_Toothbrush;
GO

-- Create table that VIOLATES 2NF
CREATE TABLE norm.NF2_Toothbrush (
    Manufacturer VARCHAR(50) NOT NULL,
    Model VARCHAR(50) NOT NULL,
    ManufacturerCountry VARCHAR(50) NOT NULL,

    -- Composite Primary Key
    CONSTRAINT PK_NF2_Toothbrush PRIMARY KEY (Manufacturer, Model)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.NF2_Toothbrush (Manufacturer, Model, ManufacturerCountry) VALUES
('Forte', 'X-Prime', 'Italy'),
('Forte', 'Ultraclean', 'Italy'),
('Dent-o-Fresh', 'EZbrush', 'USA'),
('Brushmaster', 'SuperBrush', 'USA'),
('Kobayashi', 'ST-60', 'Japan'),
('Hoch', 'Toothmaster', 'Germany'),
('Hoch', 'X-Prime', 'Germany');
GO

PRINT 'Toothbrush table created successfully!';
GO

