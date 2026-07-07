-- Parameter for number of queries to return
DECLARE @top_n_queries INT = 10;  -- Default value, can be overridden by calling application

WITH cte_PlanList AS
(
    SELECT
        q.query_id,
        STRING_AGG(CAST(p.plan_id AS varchar(20)), ',') WITHIN GROUP (ORDER BY p.plan_id) AS plan_ids,
        COUNT(DISTINCT p.plan_id) AS plan_count
    FROM sys.query_store_query q
    JOIN sys.query_store_plan p
        ON q.query_id = p.query_id
    GROUP BY q.query_id
),
cte_RuntimeAgg AS
(
    SELECT
        q.query_id,
        q.object_id,
        SUM(rs.count_executions) AS total_executions,
        SUM(rs.avg_cpu_time * rs.count_executions) / 1000.0 AS total_cpu_ms,
        SUM(rs.avg_duration * rs.count_executions) / 1000.0 AS total_duration_ms,
        SUM(rs.avg_logical_io_reads * rs.count_executions) AS total_logical_reads,
        MIN(rs.first_execution_time) AS first_execution_time,
        MAX(rs.last_execution_time) AS last_execution_time
    FROM sys.query_store_query q
    JOIN sys.query_store_plan p
        ON q.query_id = p.query_id
    JOIN sys.query_store_runtime_stats rs
        ON p.plan_id = rs.plan_id
    GROUP BY q.query_id, q.object_id
)
SELECT TOP (@top_n_queries)
    ROW_NUMBER() OVER (ORDER BY r.total_cpu_ms DESC) AS myRank,
    @@SERVERNAME as server_name,
    DB_NAME() AS database_name,
    OBJECT_NAME(r.object_id) AS object_name,
    r.query_id,
    pl.plan_ids,
    pl.plan_count,
    r.total_executions,
    r.total_cpu_ms,
    r.total_duration_ms,
    r.total_logical_reads,
    r.first_execution_time,
    r.last_execution_time
FROM cte_RuntimeAgg r
JOIN cte_PlanList pl
    ON r.query_id = pl.query_id
ORDER BY myRank;