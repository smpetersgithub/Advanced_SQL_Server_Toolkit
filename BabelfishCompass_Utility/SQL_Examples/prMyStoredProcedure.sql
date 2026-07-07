USE foo
GO

CREATE OR ALTER PROCEDURE dbo.prMyStoredProcedure
    @vMyInput INT = NULL
AS
BEGIN
    SET NOCOUNT ON

/*

    This code comment has the words IF SELECT WHERE WITH FROM GROUP BY in it for testing.

*/

    DECLARE @myValue INT = 0,
            @myValue2 INT

    IF EXISTS (SELECT 1 FROM dbo.Transactions)
    BEGIN
        SELECT 'hello world' AS Greeting

        UPDATE dbo.Users
        SET UserID = 1

        UPDATE u
        SET UserID = 1
        FROM dbo.Users AS u
        INNER JOIN dbo.History h ON u.UserID = h.UserID

        INSERT INTO dbo.Customers (CustomerID)
        SELECT CustomerID
        FROM dbo.Customers
    END

    ------------------------------------------------------------
    -- SELECT within a SELECT
    ------------------------------------------------------------
    SELECT 
        e.EmployeeID,
        e.FirstName,
        e.LastName,
        e.Salary,
        (SELECT AVG(Salary) FROM dbo.Employees) AS AvgSalary,
        e.Salary - (SELECT AVG(Salary) FROM dbo.Employees) AS SalaryDifference
    FROM dbo.Employees e
    WHERE e.Salary > (
        SELECT AVG(Salary)
        FROM dbo.Employees
        WHERE DepartmentID = e.DepartmentID
    )
    ORDER BY e.Salary DESC


    ------------------------------------------------------------
    --Commented code
    ------------------------------------------------------------

    /*
    SELECT * FROM Orders
    */

    --SELECT * FROM Orders

    ------------------------------------------------------------
    -- Correlated Subquery
    ------------------------------------------------------------
    SELECT 
        e.EmployeeID,
        e.FirstName,
        e.LastName,
        e.DepartmentID,
        e.Salary,
        (SELECT AVG(e2.Salary)
         FROM dbo.Employees e2
         WHERE e2.DepartmentID = e.DepartmentID) AS DeptAvgSalary,
        (SELECT COUNT(*)
         FROM dbo.Employees e3
         WHERE e3.DepartmentID = e.DepartmentID
           AND e3.Salary > e.Salary) AS EmployeesEarningMore
    FROM dbo.Employees e
    WHERE e.Salary > (
        SELECT AVG(e4.Salary)
        FROM dbo.Employees e4
        WHERE e4.DepartmentID = e.DepartmentID
    )
    ORDER BY e.DepartmentID, e.Salary DESC

    ------------------------------------------------------------
    -- Common Table Expressions (CTE)
    ------------------------------------------------------------
    WITH DeptAvgSalary AS (
        SELECT 
            DepartmentID,
            AVG(Salary) AS AvgSalary
        FROM dbo.Employees
        GROUP BY DepartmentID
    ),
    HighEarners AS (
        SELECT 
            e.EmployeeID,
            e.FirstName,
            e.LastName,
            e.DepartmentID,
            e.Salary
        FROM dbo.Employees e
        INNER JOIN DeptAvgSalary d ON e.DepartmentID = d.DepartmentID
        WHERE e.Salary > d.AvgSalary
    )
    SELECT 
        h.FirstName,
        h.LastName,
        h.Salary,
        d.DepartmentName,
        (SELECT 'Hello World') AS Greeting
    FROM HighEarners h
    INNER JOIN dbo.Departments d ON h.DepartmentID = d.DepartmentID
    INNER JOIN dbo.Resources r ON d.ResourceID = r.ResourceID
    INNER JOIN (SELECT DISTINCT ProjectID FROM dbo.Projects) p ON r.ProjectID = p.ProjectID
    ORDER BY h.Salary DESC



    -- Older style - comma-separated tables (same as CROSS JOIN)
    SELECT 
        e.EmployeeID,
        d.DepartmentName
    FROM dbo.Employees e, dbo.Departments d;


    SELECT 
        e.EmployeeID,
        d.DepartmentName
    FROM dbo.Employees e
    CROSS JOIN dbo.Departments d;


END
GO
