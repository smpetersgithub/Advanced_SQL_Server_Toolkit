WITH StatsColumns AS
(
    SELECT
        sc.object_id,
        sc.stats_id,
        STRING_AGG(c.name, ', ')
            WITHIN GROUP (ORDER BY sc.stats_column_id) AS stats_columns
    FROM sys.stats_columns sc
    JOIN sys.columns c
        ON sc.object_id = c.object_id
       AND sc.column_id = c.column_id
    GROUP BY sc.object_id, sc.stats_id
)
SELECT
    @@SERVERNAME as server_name,
    DB_NAME() AS database_name,
    sch.name AS schema_name,
    obj.name AS table_name,
    st.name AS stats_name,
    st.stats_id,
    st.auto_created,
    st.user_created,
    st.no_recompute,
    st.has_filter,
    st.filter_definition,
    st.is_incremental,
    st.is_temporary,
    st.has_persisted_sample,
    --st.auto_drop,
    sc.stats_columns,

    sp.last_updated,
    sp.rows,
    sp.rows_sampled,
    sp.steps,
    sp.unfiltered_rows,
    sp.modification_counter,
    sp.persisted_sample_percent

FROM sys.stats st
JOIN sys.objects obj
    ON st.object_id = obj.object_id
JOIN sys.schemas sch
    ON obj.schema_id = sch.schema_id
LEFT JOIN StatsColumns sc
    ON st.object_id = sc.object_id
   AND st.stats_id = sc.stats_id
OUTER APPLY sys.dm_db_stats_properties(st.object_id, st.stats_id) sp
WHERE obj.type = 'U'   -- user tables only
ORDER BY
    sch.name,
    obj.name,
    st.name;