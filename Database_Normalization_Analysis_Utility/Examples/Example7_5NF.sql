/*
================================================================================
Example 7: Fifth Normal Form (5NF)
================================================================================
SOURCE: https://en.wikipedia.org/wiki/Fifth_normal_form
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.NF5_TravelingSalesman;
GO

-- Create table demonstrating 5NF violation
CREATE TABLE norm.NF5_TravelingSalesman (
    TravelingSalesman VARCHAR(50) NOT NULL,
    Brand VARCHAR(50) NOT NULL,
    ProductType VARCHAR(50) NOT NULL,

    CONSTRAINT PK_NF5_TravelingSalesman PRIMARY KEY (TravelingSalesman, Brand, ProductType)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.NF5_TravelingSalesman (TravelingSalesman, Brand, ProductType) VALUES
('Jack Schneider', 'Acme', 'Vacuum cleaner'),
('Jack Schneider', 'Acme', 'Breadbox'),
('Mary Jones', 'Robusto', 'Pruning shears'),
('Mary Jones', 'Robusto', 'Vacuum cleaner'),
('Mary Jones', 'Robusto', 'Breadbox'),
('Mary Jones', 'Robusto', 'Umbrella stand'),
('Louis Ferguson', 'Robusto', 'Vacuum cleaner'),
('Louis Ferguson', 'Robusto', 'Telescope'),
('Louis Ferguson', 'Acme', 'Vacuum cleaner'),
('Louis Ferguson', 'Acme', 'Lava lamp'),
('Louis Ferguson', 'Nimbus', 'Tie rack');
GO

PRINT 'TravelingSalesman table created successfully!';
GO

