/*
================================================================================
Example 6: Fourth Normal Form (4NF)
================================================================================
SOURCE: https://en.wikipedia.org/wiki/Fourth_normal_form
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

-- Drop table if exists
DROP TABLE IF EXISTS norm.NF4_PizzaDelivery;
GO

-- Create table demonstrating 4NF violation
CREATE TABLE norm.NF4_PizzaDelivery (
    Restaurant VARCHAR(50) NOT NULL,
    PizzaVariety VARCHAR(50) NOT NULL,
    DeliveryArea VARCHAR(50) NOT NULL,

    CONSTRAINT PK_NF4_PizzaDelivery PRIMARY KEY (Restaurant, PizzaVariety, DeliveryArea)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.NF4_PizzaDelivery (Restaurant, PizzaVariety, DeliveryArea) VALUES
('A1 Pizza', 'Thick Crust', 'Springfield'),
('A1 Pizza', 'Thick Crust', 'Shelbyville'),
('A1 Pizza', 'Thick Crust', 'Capital City'),
('A1 Pizza', 'Stuffed Crust', 'Springfield'),
('A1 Pizza', 'Stuffed Crust', 'Shelbyville'),
('A1 Pizza', 'Stuffed Crust', 'Capital City'),
('Elite Pizza', 'Thin Crust', 'Capital City'),
('Elite Pizza', 'Stuffed Crust', 'Capital City'),
('Vincenzo''s Pizza', 'Thick Crust', 'Springfield'),
('Vincenzo''s Pizza', 'Thick Crust', 'Shelbyville'),
('Vincenzo''s Pizza', 'Thin Crust', 'Springfield'),
('Vincenzo''s Pizza', 'Thin Crust', 'Shelbyville');
GO

PRINT 'PizzaDelivery table created successfully!';
GO

