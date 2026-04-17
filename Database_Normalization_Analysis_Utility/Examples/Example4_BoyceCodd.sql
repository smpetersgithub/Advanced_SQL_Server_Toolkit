/*
================================================================================
Example 4: Boyce-Codd Normal Form (BCNF) Violation
================================================================================

SOURCE:
Wikipedia - Boyce-Codd Normal Form
https://en.wikipedia.org/wiki/Boyce%E2%80%93Codd_normal_form
*/

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'norm')
BEGIN
    EXEC('CREATE SCHEMA norm');
END
GO

/*
================================================================================
VERSION 1: CourtBookings_WithPK (WITH Primary Key)
================================================================================
*/

-- Drop table if exists
DROP TABLE IF EXISTS norm.BCNF_CourtBookings_WithPK;
GO

-- Create table that VIOLATES BCNF (WITH Primary Key)
CREATE TABLE norm.BCNF_CourtBookings_WithPK (
    Court INT NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    RateType VARCHAR(20) NOT NULL,

    -- Composite Primary Key
    CONSTRAINT PK_BCNF_CourtBookings_WithPK PRIMARY KEY (Court, StartTime)
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.BCNF_CourtBookings_WithPK (Court, StartTime, EndTime, RateType) VALUES
(1, '09:30', '10:30', 'SAVER'),
(1, '11:00', '12:00', 'SAVER'),
(1, '14:00', '15:30', 'STANDARD'),
(2, '10:00', '11:30', 'PREMIUM-B'),
(2, '11:30', '13:30', 'PREMIUM-B'),
(2, '15:00', '16:30', 'PREMIUM-A');
GO


/*
================================================================================
VERSION 2: CourtBookings_NoPK (WITHOUT Primary Key)
================================================================================
*/

-- Drop table if exists
DROP TABLE IF EXISTS norm.BCNF_CourtBookings_NoPK;
GO

-- Create table that VIOLATES BCNF (WITHOUT Primary Key)
CREATE TABLE norm.BCNF_CourtBookings_NoPK (
    Court INT NOT NULL,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    RateType VARCHAR(20) NOT NULL

    -- NO Primary Key defined
);
GO

-- Insert test data from Wikipedia example
INSERT INTO norm.BCNF_CourtBookings_NoPK (Court, StartTime, EndTime, RateType) VALUES
(1, '09:30', '10:30', 'SAVER'),
(1, '11:00', '12:00', 'SAVER'),
(1, '14:00', '15:30', 'STANDARD'),
(2, '10:00', '11:30', 'PREMIUM-B'),
(2, '11:30', '13:30', 'PREMIUM-B'),
(2, '15:00', '16:30', 'PREMIUM-A');
GO

PRINT 'CourtBookings_WithPK table created successfully!';
GO

PRINT 'CourtBookings_NoPK table created successfully!';
GO


