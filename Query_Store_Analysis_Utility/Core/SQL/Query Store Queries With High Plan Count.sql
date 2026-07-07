-- Parameter for number of queries to return
DECLARE @top_n_queries INT = 10;  -- Default value, can be overridden by calling application

WITH PlanCounts AS
(
    SELECT
        q.query_id,
        q.object_id,
        q.query_text_id,
        COUNT(DISTINCT p.plan_id) AS plan_count,
        STRING_AGG(CAST(p.plan_id AS varchar(20)), ',')
            WITHIN GROUP (ORDER BY p.plan_id) AS plan_ids
    FROM sys.query_store_query q
    JOIN sys.query_store_plan p
        ON q.query_id = p.query_id
    GROUP BY q.query_id, q.object_id, q.query_text_id
),
RuntimeAgg AS
(
    SELECT
        q.query_id,
        MIN(rs.first_execution_time) AS first_execution_time,
        MAX(rs.last_execution_time)  AS last_execution_time,
        SUM(rs.count_executions)     AS total_executions,
        -- Weighted average duration (microseconds → ms)
        SUM(rs.avg_duration * rs.count_executions) 
            / NULLIF(SUM(rs.count_executions),0) / 1000.0 AS avg_duration_ms
    FROM sys.query_store_query q
    JOIN sys.query_store_plan p
        ON q.query_id = p.query_id
    JOIN sys.query_store_runtime_stats rs
        ON p.plan_id = rs.plan_id
    GROUP BY q.query_id
)
SELECT TOP (@top_n_queries)
    ROW_NUMBER() OVER (ORDER BY pc.plan_count DESC) AS myRank,
    @@SERVERNAME AS server_name,
    DB_NAME() AS database_name,
    OBJECT_NAME(pc.object_id) AS object_name,
    pc.query_id,
    pc.plan_count,
    pc.plan_ids,
    ra.total_executions,
    ra.avg_duration_ms,
    CONVERT(VARCHAR(30), ra.first_execution_time, 121) AS first_execution_time,
    CONVERT(VARCHAR(30), ra.last_execution_time, 121) AS last_execution_time,
    LEFT(REPLACE(qt.query_sql_text, CHAR(13) + CHAR(10), ' '), 10000) AS sql_text_10000
FROM PlanCounts pc
JOIN RuntimeAgg ra
    ON pc.query_id = ra.query_id
JOIN sys.query_store_query_text qt
    ON pc.query_text_id = qt.query_text_id
WHERE pc.plan_count > 1
--AND query_sql_text like '%RECOMPILE%'
ORDER BY myRank;

