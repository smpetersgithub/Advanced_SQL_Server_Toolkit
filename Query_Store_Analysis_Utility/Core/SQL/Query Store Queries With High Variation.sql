-- Parameter for number of queries to return
DECLARE @top_n_queries INT = 10;  -- Default value, can be overridden by calling application

WITH cte_PlanPerf AS
(
    -- Aggregate runtime per plan
    SELECT
        q.query_id,
        q.object_id,
        p.plan_id,
        SUM(rs.count_executions) AS plan_executions,
        SUM(rs.avg_duration * rs.count_executions)
            / NULLIF(SUM(rs.count_executions),0) AS weighted_avg_duration,
        SUM(rs.avg_cpu_time * rs.count_executions)
            / NULLIF(SUM(rs.count_executions),0) AS weighted_avg_cpu_time,
        SUM(rs.avg_logical_io_reads * rs.count_executions)
            / NULLIF(SUM(rs.count_executions),0) AS weighted_avg_logical_reads,
        MIN(rs.first_execution_time) AS first_execution_time,
        MAX(rs.last_execution_time) AS last_execution_time
    FROM sys.query_store_query q
    JOIN sys.query_store_plan p
        ON q.query_id = p.query_id
    JOIN sys.query_store_runtime_stats rs
        ON p.plan_id = rs.plan_id
    GROUP BY q.query_id, q.object_id, p.plan_id
),
cte_QueryVariation AS
(
    SELECT
        query_id,
        object_id,
        COUNT(*) AS plan_count,
        SUM(plan_executions) AS total_executions,
        MIN(weighted_avg_duration) AS min_avg_duration,
        MAX(weighted_avg_duration) AS max_avg_duration,
        MAX(weighted_avg_duration)
            / NULLIF(MIN(weighted_avg_duration),0) AS variation_ratio,
        SUM(weighted_avg_cpu_time * plan_executions)
            / NULLIF(SUM(plan_executions),0) AS avg_cpu_time,
        SUM(weighted_avg_logical_reads * plan_executions)
            / NULLIF(SUM(plan_executions),0) AS avg_logical_reads,
        MIN(first_execution_time) AS first_execution_time,
        MAX(last_execution_time) AS last_execution_time
    FROM cte_PlanPerf
    GROUP BY query_id, object_id
    HAVING COUNT(*) > 1  -- multi-plan only
),
cte_PlanIDs AS
(
    -- Get comma-separated list of plan IDs for each query
    SELECT
        query_id,
        STRING_AGG(CAST(plan_id AS VARCHAR(20)), ',') WITHIN GROUP (ORDER BY plan_id) AS plan_ids
    FROM sys.query_store_plan
    GROUP BY query_id
)
SELECT TOP (@top_n_queries)
    ROW_NUMBER() OVER (ORDER BY variation_ratio DESC) AS myRank,
    @@SERVERNAME AS server_name,
    DB_NAME() AS database_name,
    OBJECT_NAME(qv.object_id) AS object_name,
    qv.query_id,
    pi.plan_ids,
    qv.plan_count,
    qv.total_executions,
    qv.avg_cpu_time / 1000.0 AS total_cpu_ms,
    (qv.min_avg_duration + qv.max_avg_duration) / 2.0 / 1000.0 AS total_duration_ms,
    qv.avg_logical_reads AS total_logical_reads,
    qv.min_avg_duration / 1000.0 AS min_avg_duration_ms,
    qv.max_avg_duration / 1000.0 AS max_avg_duration_ms,
    qv.variation_ratio,
    CAST(qv.first_execution_time AS datetime2(7)) AS first_execution_time,
    CAST(qv.last_execution_time AS datetime2(7)) AS last_execution_time
FROM cte_QueryVariation qv
LEFT JOIN cte_PlanIDs pi ON qv.query_id = pi.query_id
ORDER BY myRank;