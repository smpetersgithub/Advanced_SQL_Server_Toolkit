USE WideWorldImporters;
GO


CREATE OR ALTER PROC SpPivotData
/*----------------------------------------------------

This script creates the stored procedure "SpPivotData" that can be used to
automate the creation of pivoted data sets.

See example uses at the end of this script.

*/----------------------------------------------------

@vQuery    AS NVARCHAR(MAX),
@vOnRows  AS NVARCHAR(MAX),
@vOnColumns  AS NVARCHAR(MAX),
@vAggFunction AS NVARCHAR(257) = N'MAX',
@vAggColumns  AS NVARCHAR(MAX)
AS
BEGIN TRY

    -- Input validation
    IF @vQuery IS NULL OR @vOnRows IS NULL OR @vOnColumns IS NULL OR @vAggFunction IS NULL OR @vAggColumns IS NULL
         THROW 50001, 'Invalid input parameters.', 1;


    DECLARE
    @vSql AS NVARCHAR(MAX),
    @vColumns AS NVARCHAR(MAX),
    @vNewLine AS NVARCHAR(2) = NCHAR(13) + NCHAR(10);

    --If the input is a valid table or view, construct a SELECT statement
    IF COALESCE(OBJECT_ID(@vQuery, 'U'), OBJECT_ID(@vQuery, 'V')) IS NOT NULL
        SET @vQuery = 'SELECT * FROM ' + @vQuery;

    --Make the query a derived table
    SET @vQuery = '(' + @vQuery + N') AS Query';

    -- Handle * input in @vAggColumns
    IF @vAggColumns = '*' SET @vAggColumns = '1';

    -- Construct a column list
    SET @vSql =
                'SET @result = '                                      + @vNewLine +
                '  STUFF('                                            + @vNewLine +
                '    (SELECT '',['' + '                               +
                'CAST(pivot_col AS sysname) + '                       +
                ''']'' AS [text()]'                                   + @vNewLine +
                '     FROM (SELECT DISTINCT('                         +
                @vOnColumns + N') AS pivot_col'                       + @vNewLine +
                '           FROM' + @vQuery + N') AS DistinctCols'    + @vNewLine +
                '     ORDER BY pivot_col'                             + @vNewLine +
                '     FOR XML PATH('''')),'                           + @vNewLine +
                '    1, 1, '''');';

    EXEC SP_EXECUTESQL
        @stmt   = @vSql,
        @params = N'@result AS NVARCHAR(MAX) OUTPUT',
        @result = @vColumns OUTPUT;

    --Create the PIVOT query
    SET @vSql = 
                'SELECT *'                                           + @vNewLine +
                'FROM (SELECT '                                      +
                @vOnRows +
                ', ' + @vOnColumns + N' AS pivot_col'                +
                ', ' + @vAggColumns + N' AS agg_col'                 + @vNewLine +
                '      FROM ' + @vQuery + N')' +
                ' AS PivotInput'                                     + @vNewLine +
                '  PIVOT(' + @vAggFunction + N'(agg_col)'            + @vNewLine +
                '    FOR pivot_col IN(' + @vColumns + N')) AS PivotOutput;';

    EXEC SP_EXECUTESQL @vSql;

END TRY
BEGIN CATCH;
    THROW;
END CATCH;
GO


-- Example uses


DROP TABLE IF EXISTS TestPivot
GO

CREATE TABLE TestPivot
(
Distributor VARCHAR(20),
TransactionDate DATE,
TransactionType VARCHAR(20),
TotalTransactions INTEGER,
SumTransactions MONEY
);
GO


-- Examples Below
-- Examples Below
-- Examples Below

INSERT INTO TestPivot VALUES
('ACE','2019-01-01','ATM',1,1),
('ACE','2019-01-02','ATM',2,2),
('ACE','2019-01-03','ATM',3,3),
('ACE','2019-01-04','ATM',4,4),
-----
('ACE','2019-01-01','Signature',5,5),
('ACE','2019-01-03','Signature',6,6),
('ACE','2019-01-04','Signature',7,7),
('ACE','2019-01-05','Signature',8,8),
-----
('IniTech','2019-01-01','ATM',1,1),
('IniTech','2019-01-02','ATM',2,2),
('IniTech','2019-01-03','ATM',3,3),
('IniTech','2019-01-04','ATM',4,4),
-----
('IniTech','2019-01-01','Signature',5,5),
('IniTech','2019-01-03','Signature',6,6),
('IniTech','2019-01-04','Signature',7,7),
('IniTech','2019-01-05','Signature',8,8);
GO

SELECT * FROM TestPivot;

-------------------------------------------------------------
-------------------------------------------------------------
-------------------------------------------------------------
--Create a data dictionary using the pivot
DROP TABLE IF EXISTS ##DataDictionary;
GO

SELECT  c.[Name] AS SchemaName, b.[Name] AS TableName, a.[Name] AS ColumnName, d.[Name] AS DataType
INTO    ##DataDictionary
FROM    sys.Columns a INNER JOIN
        sys.Tables b on a.object_id = b.object_id INNER JOIN
        sys.Schemas c on b.schema_id = c.schema_id INNER JOIN
        sys.Types d on a.user_type_id = d.user_type_id
WHERE b.[Name] = 'TestPivot';

--Pivot the data by [SchemaName, TableName, ColumnName]
--Count the number of data types [date, int, varchar, etc..]
EXEC SpPivotData
  @vQuery    = 'SELECT SchemaName, TableName, ColumnName, DataType FROM ##DataDictionary',
  @vOnRows  =  'SchemaName, TableName, ColumnName',
  @vOnColumns  = 'DataType',
  @vAggFunction = 'COUNT',
  @vAggColumns  = '*';

--Number of datatypes [date, int, varchar, etc...] by table name [TestPivot]
EXEC SpPivotData
  @vQuery    = 'SELECT TableName, DataType, COUNT(*) AS NumberOfDataTypes FROM ##DataDictionary GROUP BY TableName, DataType',
  @vOnRows  = 'TableName',
  @vOnColumns  = 'DataType',
  @vAggFunction = 'SUM',
  @vAggColumns  = 'NumberOfDataTypes';

-------------------------------------------------------------
-------------------------------------------------------------
-------------------------------------------------------------
--Show each [TransactionType] in the [dbo.TestPivot] table and pivot by [TransactionDate]
--SUM the [TotalTransactions] column
EXEC SpPivotData
  @vQuery    = 'dbo.TestPivot',
  @vOnRows  = 'TransactionType',
  @vOnColumns  = 'TransactionDate',
  @vAggFunction = 'SUM',
  @vAggColumns  = 'TotalTransactions';

--Same as above, but now add [Distributor] to the row variable
EXEC SpPivotData
  @vQuery    = 'dbo.TestPivot',
  @vOnRows  = 'Distributor, TransactionType',
  @vOnColumns  = 'TransactionDate',
  @vAggFunction = 'SUM',
  @vAggColumns  = 'TotalTransactions';

--This example provides the average amount per transaction
--using the MAX function
EXEC dbo.SpPivotData
  @vQuery    = 'dbo.TestPivot',
  @vOnRows  = 'Distributor, TransactionType',
  @vOnColumns  = 'TransactionDate',
  @vAggFunction = 'MAX',
  @vAggColumns  = 'SumTransactions/TotalTransactions';
GO

