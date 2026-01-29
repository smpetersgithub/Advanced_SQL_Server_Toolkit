/*----------------------------------------------------------------------------------------------------------

Determine Object Dependency Paths - Direct Execution Version

This script analyzes reverse dependencies (what references a given object) without using stored procedures.
The object name is passed via the $(object_name) variable.

Example: EXECUTE with object_name = 'qa07_greg.dbo.spAR_AncillaryCapDetail_Trigger_Insert'

----------------------------------------------------------------------------------------------------------*/

USE [master];

-----------------------------------------------------------------
-- Declare variables
-----------------------------------------------------------------
DECLARE @v_object_name VARCHAR(256) = '$(object_name)';
DECLARE @v_database_list VARCHAR(8000) = NULL;
DECLARE @v_database_list_local VARCHAR(8000);
DECLARE @v_sql_statement NVARCHAR(MAX);
DECLARE @v_database_id INT;
DECLARE @v_database_name NVARCHAR(256);
DECLARE @v_row_count INT;
DECLARE @v_depth INT;

-----------------------------------------------------------------
-- Drop existing temporary tables to ensure clean state
-----------------------------------------------------------------
DROP TABLE IF EXISTS ##databases;
DROP TABLE IF EXISTS ##sql_statements;
DROP TABLE IF EXISTS ##sql_expression_dependencies;
DROP TABLE IF EXISTS ##sys_objects;
DROP TABLE IF EXISTS ##path_list;
DROP TABLE IF EXISTS ##path_list_reverse;
DROP TABLE IF EXISTS ##path;
DROP TABLE IF EXISTS ##path_list_preprocess;
DROP TABLE IF EXISTS ##path_list_report;
DROP TABLE IF EXISTS ##path_reverse;
DROP TABLE IF EXISTS ##path_list_preprocess_reverse;
DROP TABLE IF EXISTS ##path_list_report_reverse;

-----------------------------------------------------------------
-- Create temporary tables
-----------------------------------------------------------------

-- Stores list of databases to analyze
CREATE TABLE ##databases (
    database_id INT PRIMARY KEY,
    [database_name] VARCHAR(256)
);

-- Use the third part of @v_object_name as default database if @v_database_list is NULL
SET @v_database_list_local = CASE WHEN @v_database_list IS NULL THEN PARSENAME(@v_object_name, 3) ELSE @v_database_list END;

-- Format database list for IN clause
SET @v_database_list_local = '''' + REPLACE(@v_database_list_local, ',', ''',''') + '''';
SET @v_database_list_local = REPLACE(@v_database_list_local,' ','');

-- Build and execute dynamic SQL to populate databases table
SET @v_sql_statement = REPLACE('INSERT INTO ##databases (database_id, [database_name]) SELECT database_id, [name] FROM sys.databases WHERE NAME IN (<DATABASE_STRING>);','<DATABASE_STRING>', @v_database_list_local);
EXEC sp_executesql @v_sql_statement;

-- Stores dependency information from sys.sql_expression_dependencies
CREATE TABLE ##sql_expression_dependencies (
    sql_expression_dependencies_id INT IDENTITY(1,1) PRIMARY KEY,
    referencing_id INT,
    referencing_database_name VARCHAR(256),
    referencing_schema_name VARCHAR(256),
    referencing_object_name VARCHAR(256),
    referencing_type_desc VARCHAR(256),
    referenced_id INT,
    referenced_database_name VARCHAR(256),
    referenced_schema_name VARCHAR(256),
    referenced_object_name VARCHAR(256),
    referenced_type_desc VARCHAR(256),
    depth INT,
    referencing_object_fullname VARCHAR(256),
    referenced_object_fullname VARCHAR(256),
    referencing_minor_id INT,
    referencing_class_desc VARCHAR(256),
    is_schema_bound_reference INT,
    referenced_class INT,
    referenced_class_desc VARCHAR(256),
    referenced_server_name VARCHAR(256),
    referenced_minor_id INT,
    is_caller_dependent INT,
    is_ambiguous INT
);

-- Stores object metadata from sys.objects
CREATE TABLE ##sys_objects (
    [object_id] INT,
    [database_name] VARCHAR(256),
    [schema_name] VARCHAR(256),
    [object_name] VARCHAR(256),
    [type_desc] VARCHAR(256),
    CONSTRAINT PK_sys_objects PRIMARY KEY ([object_id], [database_name])
);

-- Stores reverse dependency paths
CREATE TABLE ##path_list_reverse (
    server_name VARCHAR(256),
    [object_name] VARCHAR(256),
    depth INT,
    referencing_id INT,
    referenced_id INT,
    object_name_path VARCHAR(8000),
    object_type_path VARCHAR(8000),
    object_type_desc_path VARCHAR(8000),
    object_id_path VARCHAR(8000),
    referencing_object_fullname VARCHAR(256),
    referenced_object_fullname VARCHAR(256),
    referenced_type_desc VARCHAR(256)
);

-- Index for ##sys_objects
CREATE NONCLUSTERED INDEX IX_sys_objects_schema_type
ON [dbo].[##sys_objects] ([schema_name], [type_desc])
INCLUDE ([object_name]);

-- Index for ##sys_objects
CREATE NONCLUSTERED INDEX IX_sys_objects_db_schema_object_type
ON [dbo].[##sys_objects] ([database_name], [schema_name], [object_name], [type_desc]);

-- Index for ##sql_expression_dependencies (referenced db and schema)
CREATE NONCLUSTERED INDEX IX_sql_expr_deps_refdb_refschema
ON [dbo].[##sql_expression_dependencies] ([referenced_database_name], [referenced_schema_name])
INCLUDE ([referenced_object_name]);

-- Index for ##sql_expression_dependencies (referencing_id only)
CREATE NONCLUSTERED INDEX IX_sql_expr_deps_refid
ON [dbo].[##sql_expression_dependencies] ([referencing_id]);

-- Index for ##sql_expression_dependencies (is_caller_dependent only)
CREATE NONCLUSTERED INDEX IX_sql_expr_deps_is_caller
ON [dbo].[##sql_expression_dependencies] ([is_caller_dependent])
INCLUDE ([referencing_database_name], [referenced_object_name]);

-----------------------------------------------------------------
-- Build SQL statement templates
-----------------------------------------------------------------

-- Create table containing SQL statement templates
SELECT sql_statement_id, row_id, sql_line
INTO   ##sql_statements
FROM (VALUES
    -----------------------------------------------------------------
    -- Dynamic SQL for inserting into ##sql_expression_dependencies
    -----------------------------------------------------------------
    (1, 10, 'WITH cte_sql_expression_dependencies AS'),
    (1, 20, '('),
    (1, 30, 'SELECT *'),
    (1, 40, 'FROM   vdatabase_name.sys.sql_expression_dependencies'),
    (1, 50, 'WHERE  1=1'),
    (1, 60, ')'),
    -----------------------------------------------
    (1, 70, 'INSERT INTO ##sql_expression_dependencies ('),
    -----------------------------------------------
    (1, 80, 'referencing_id,'),
    (1, 90, 'referencing_database_name,'),
    (1, 100, 'referencing_schema_name,'),
    (1, 110, 'referencing_object_name,'),
    (1, 120, 'referencing_type_desc,'),
    (1, 130, 'referenced_database_name,'),
    (1, 140, 'referenced_schema_name,'),
    (1, 150, 'referenced_object_name,'),
    (1, 160, 'referenced_id,'),
    (1, 170, 'referencing_minor_id,'),
    (1, 180, 'referencing_class_desc,'),
    (1, 190, 'is_schema_bound_reference,'),
    (1, 200, 'referenced_class,'),
    (1, 210, 'referenced_class_desc,'),
    (1, 220, 'referenced_server_name,'),
    (1, 230, 'referenced_minor_id,'),
    (1, 240, 'is_caller_dependent,'),
    (1, 250, 'is_ambiguous'),
    (1, 260, ')'),
    -----------------------------------------------
    (1, 270, 'SELECT'),
    (1, 280, 'd.referencing_id,'),
    (1, 290, 'DB_NAME(vdatabase_id) AS referencing_database_name,'),
    (1, 300, 's.[name] AS referencing_schema_name,'),    
    (1, 310, 'o.name AS referencing_object_name,'),
    (1, 320, 'o.type_desc AS referencing_type_desc,'),
    (1, 330, 'd.referenced_database_name,'),
    (1, 340, 'd.referenced_schema_name,'),
    (1, 350, 'd.referenced_entity_name,'),
    (1, 360, 'd.referenced_id,'),
    (1, 370, 'referencing_minor_id,'),
    (1, 380, 'referencing_class_desc,'),
    (1, 390, 'is_schema_bound_reference,'),
    (1, 400, 'referenced_class,'),
    (1, 410, 'referenced_class_desc,'),
    (1, 420, 'referenced_server_name,'),
    (1, 430, 'referenced_minor_id,'),
    (1, 440, 'is_caller_dependent,'),
    (1, 450, 'is_ambiguous'),
    -----------------------------------------------
    (1, 460, 'FROM'),
    (1, 470, 'cte_sql_expression_dependencies d'),
    (1, 480, 'INNER JOIN vdatabase_name.sys.objects o ON d.referencing_id = o.object_id'),
    (1, 490, 'INNER JOIN vdatabase_name.sys.schemas s ON o.schema_id = s.schema_id;'),
    -----------------------------------------------------------------
    -- Dynamic SQL for inserting into ##sys_objects
    -----------------------------------------------------------------
    (2, 10, 'INSERT INTO ##sys_objects (object_id, database_name, schema_name, object_name, type_desc)'),
    (2, 20,  'SELECT'),
    (2, 25,  'o.object_id,'),
    (2, 30,  '''vdatabase_name'','),
    (2, 40,  's.name AS schema_name,'),
    (2, 50,  'o.name AS object_name,'),
    (2, 60,  'type_desc'),
    (2, 70,  'FROM vdatabase_name.sys.objects o INNER JOIN'),
    (2, 80,  'vdatabase_name.sys.schemas s ON o.schema_id = s.schema_id'),
    (2, 90,  'WHERE is_ms_shipped = 0;')
) AS a(sql_statement_id, row_id, sql_line);

-----------------------------------------------------------------
-- Populate sql_expression_dependencies table
-----------------------------------------------------------------

DECLARE mycursor CURSOR FOR SELECT database_id, [database_name] FROM ##databases;
OPEN mycursor;
FETCH NEXT FROM mycursor INTO @v_database_id, @v_database_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    SELECT @v_sql_statement = STRING_AGG(sql_line, ' ')
    FROM   ##sql_statements
    WHERE  sql_statement_id = 1;

    SET @v_sql_statement = REPLACE(@v_sql_statement, 'vdatabase_name', @v_database_name);
    SET @v_sql_statement = REPLACE(@v_sql_statement, 'vdatabase_id', CAST(@v_database_id AS NVARCHAR));
    EXEC sp_executesql @v_sql_statement;

    FETCH NEXT FROM mycursor INTO @v_database_id, @v_database_name;
END;

CLOSE mycursor;
DEALLOCATE mycursor;

-----------------------------------------------------------------
-- Populate sys_objects table
-----------------------------------------------------------------

DECLARE mycursor2 CURSOR FOR SELECT database_id, [database_name] FROM ##databases;
OPEN mycursor2;
FETCH NEXT FROM mycursor2 INTO @v_database_id, @v_database_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    SELECT @v_sql_statement = STRING_AGG(sql_line, ' ')
    FROM   ##sql_statements
    WHERE  sql_statement_id = 2;

    SET @v_sql_statement = REPLACE(@v_sql_statement, 'vdatabase_name', @v_database_name);
    SET @v_sql_statement = REPLACE(@v_sql_statement, 'vdatabase_id', CAST(@v_database_id AS NVARCHAR));
    EXEC sp_executesql @v_sql_statement;

    FETCH NEXT FROM mycursor2 INTO @v_database_id, @v_database_name;
END;

CLOSE mycursor2;
DEALLOCATE mycursor2;

-----------------------------------------------------------------
-- Apply modifications to sql_expression_dependencies data
-----------------------------------------------------------------

UPDATE ##sql_expression_dependencies
SET    referenced_id = b.object_id
FROM   ##sql_expression_dependencies a INNER JOIN
       ##sys_objects b ON a.referenced_object_name = b.object_name AND a.referencing_database_name = b.[database_name]
WHERE  a.is_caller_dependent = 1 AND
       b.schema_name = 'dbo' AND
       b.[type_desc] = 'SQL_STORED_PROCEDURE';

DELETE ##sql_expression_dependencies
WHERE  referenced_id = referencing_id;

UPDATE ##sql_expression_dependencies
SET    referenced_id = o.[object_id],
       referenced_type_desc = o.[type_desc]
FROM   ##sql_expression_dependencies db INNER JOIN
       ##sys_objects o ON
           CONCAT_WS('.',db.referenced_database_name, db.referenced_schema_name, db.referenced_object_name) =
           CONCAT_WS('.',o.[database_name], o.[schema_name], o.[object_name])
WHERE  db.referenced_database_name IS NOT NULL AND
       db.referenced_schema_name IS NOT NULL;

UPDATE ##sql_expression_dependencies
SET    referenced_id = o.[object_id],
       referenced_type_desc = o.[type_desc],
       referenced_database_name = o.[database_name],
       referenced_schema_name = o.[schema_name]
FROM   ##sql_expression_dependencies db INNER JOIN
       ##sys_objects o ON db.referenced_id = o.[object_id] AND db.referencing_database_name = o.[database_name];

INSERT INTO ##sql_expression_dependencies
(
referencing_id,
referencing_type_desc,
referencing_database_name,
referencing_schema_name,
referencing_object_name,
depth
)
SELECT [object_id],
       [type_desc],
       [database_name],
       [schema_name],
       [object_name],
       1 AS depth
FROM   ##sys_objects
WHERE  [object_id] NOT IN (SELECT referencing_id FROM ##sql_expression_dependencies);

UPDATE ##sql_expression_dependencies
SET    referenced_object_fullname = CONCAT_WS('.',referenced_database_name, referenced_schema_name, referenced_object_name, ISNULL(referenced_type_desc,'UNKNOWN')),
       referencing_object_fullname = CONCAT_WS('.',referencing_database_name, referencing_schema_name, referencing_object_name, ISNULL(referencing_type_desc,'UNKNOWN'));

UPDATE ##sql_expression_dependencies
SET    referenced_object_fullname = NULL
WHERE  referenced_object_fullname = 'UNKNOWN';

-----------------------------------------------------------------
-- Determine reverse dependency paths
-----------------------------------------------------------------

SELECT DISTINCT
       @@SERVERNAME AS server_name,
       @v_object_name AS [object_name],
       referencing_id,
       referenced_id,
       referencing_database_name,
       referencing_schema_name,
       referencing_type_desc,
       referencing_object_name,
       referencing_object_fullname,
       referenced_database_name,
       referenced_schema_name,
       referenced_type_desc,
       referenced_object_name,
       referenced_object_fullname
INTO   ##path_reverse
FROM   ##sql_expression_dependencies;

INSERT INTO ##path_list_reverse (server_name, [object_name], depth, object_name_path, object_id_path, object_type_desc_path, referencing_id, referenced_id, referencing_object_fullname, referenced_object_fullname, referenced_type_desc)
SELECT @@SERVERNAME AS server_name,
       @v_object_name AS [object_name],
       1 AS depth,
       CONCAT(referencing_object_fullname, ',', referenced_object_fullname) AS object_name_path,
       CONCAT(referencing_id, ',', referenced_id) AS object_id_path,
       CONCAT(referencing_type_desc, ',', ISNULL(referenced_type_desc, 'UNKNOWN')) AS object_type_desc_path,
       referencing_id,
       referenced_id,
       referencing_object_fullname,
       referenced_object_fullname,
       referenced_type_desc
FROM   ##path_reverse
WHERE  CONCAT_WS('.',referenced_database_name, referenced_schema_name, referenced_object_name) = @v_object_name AND
       referencing_id IS NOT NULL;

SET @v_row_count = 1;
SET @v_depth = 2;

WHILE @v_row_count >= 1
BEGIN
    WITH cte_determine_referencing_object AS
    (
    SELECT referencing_id,
           referenced_id,
           object_name_path,
           object_id_path,
           object_type_desc_path,
           referencing_object_fullname,
           referenced_type_desc
    FROM   ##path_list_reverse
    WHERE  depth = @v_depth - 1
    )
    INSERT INTO ##path_list_reverse (depth, object_name_path, object_id_path, object_type_desc_path, referencing_object_fullname, referenced_object_fullname, referenced_type_desc)
    SELECT @v_depth AS depth,
           CONCAT_WS(',', b.referencing_object_fullname, a.object_name_path) AS object_name_path,
           CONCAT_WS(',', b.referencing_id, a.object_id_path) AS object_id_path,
           CONCAT_WS(',', b.referencing_type_desc, a.object_type_desc_path) AS object_type_desc_path,
           b.referencing_object_fullname,
           a.referencing_object_fullname AS referenced_object_fullname,
           b.referenced_type_desc
   FROM    cte_determine_referencing_object a INNER JOIN
           ##path_reverse b ON a.referencing_object_fullname = b.referenced_object_fullname
                           AND b.referencing_object_fullname IS NOT NULL
                           AND CHARINDEX(b.referencing_object_fullname, a.object_name_path) = 0;

   SET @v_row_count = @@ROWCOUNT;
   SET @v_depth = @v_depth + 1;
END;

-----------------------------------------------------------------
-- Final output
-----------------------------------------------------------------

SELECT @@SERVERNAME AS server_name,
       @v_object_name AS [object_name],
       object_name_path,
       object_id_path,
       object_type_desc_path,
       referenced_object_fullname,
       referenced_type_desc
INTO   ##path_list_preprocess_reverse
FROM   ##path_list_reverse r1
WHERE  NOT EXISTS (SELECT 1 FROM ##path_list_reverse r2 WHERE r2.object_name_path LIKE r1.object_name_path + ',%');

WITH cte_Distinct AS
(
SELECT DISTINCT
       @@SERVERNAME AS server_name,
       @v_object_name AS [object_name],
       SUBSTRING(object_name_path, 1, CHARINDEX(',', object_name_path) - 1) AS referencing_object_fullname
FROM   ##path_list_preprocess_reverse
)
SELECT *,
       PARSENAME(referencing_object_fullname,2) AS referencing_object
FROM   cte_Distinct

UNION ALL

SELECT @@SERVERNAME AS server_name,
       @v_object_name AS [object_name],
       CONCAT(@v_object_name, '.SQL_STORED_PROCEDURE') AS referencing_object_fullname,
       PARSENAME(@v_object_name, 1) AS referencing_object;

