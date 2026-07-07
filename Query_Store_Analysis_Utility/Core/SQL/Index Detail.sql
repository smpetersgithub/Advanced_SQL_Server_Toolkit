WITH IndexColumns AS
(
    SELECT
        ic.object_id,
        ic.index_id,
        STRING_AGG(
            CASE 
                WHEN ic.is_descending_key = 1 
                    THEN c.name + ' DESC'
                ELSE c.name
            END, ', '
        ) WITHIN GROUP (ORDER BY ic.key_ordinal) AS key_columns,
        STRING_AGG(
            CASE 
                WHEN ic.is_included_column = 1 
                    THEN c.name
            END, ', '
        ) AS included_columns
    FROM sys.index_columns ic
    JOIN sys.columns c
        ON ic.object_id = c.object_id
       AND ic.column_id = c.column_id
    GROUP BY ic.object_id, ic.index_id
),
IndexSize AS
(
    SELECT
        p.object_id,
        p.index_id,
        SUM(a.total_pages) * 8.0 / 1024 AS total_size_mb,
        SUM(a.used_pages) * 8.0 / 1024 AS used_size_mb,
        SUM(a.data_pages) * 8.0 / 1024 AS data_size_mb,
        SUM(p.rows) AS row_count
    FROM sys.partitions p
    JOIN sys.allocation_units a
        ON p.partition_id = a.container_id
    GROUP BY p.object_id, p.index_id
)
SELECT
    @@SERVERNAME as server_name,
    DB_NAME() AS database_name,
    s.name AS schema_name,
    o.name AS table_name,
    i.name AS index_name,
    i.index_id,
    i.type_desc,
    i.is_unique,
    i.is_primary_key,
    i.is_unique_constraint,
    i.is_disabled,
    i.is_hypothetical,
    i.fill_factor,
    i.has_filter,
    i.filter_definition,
    ds.name AS filegroup_name,
    ic.key_columns,
    ic.included_columns,
    i.allow_row_locks,
    i.allow_page_locks,
    i.ignore_dup_key,
    i.data_space_id,
    i.compression_delay,
    i.optimize_for_sequential_key,
    sz.row_count,
    sz.total_size_mb,
    sz.used_size_mb,
    sz.data_size_mb,
    us.user_seeks,
    us.user_scans,
    us.user_lookups,
    us.user_updates,
    us.last_user_seek,
    us.last_user_scan,
    us.last_user_lookup,
    us.last_user_update
FROM sys.indexes i
JOIN sys.objects o
    ON i.object_id = o.object_id
JOIN sys.schemas s
    ON o.schema_id = s.schema_id
LEFT JOIN sys.data_spaces ds
    ON i.data_space_id = ds.data_space_id
LEFT JOIN IndexColumns ic
    ON i.object_id = ic.object_id
   AND i.index_id = ic.index_id
LEFT JOIN IndexSize sz
    ON i.object_id = sz.object_id
   AND i.index_id = sz.index_id
LEFT JOIN sys.dm_db_index_usage_stats us
    ON i.object_id = us.object_id
   AND i.index_id = us.index_id
   AND us.database_id = DB_ID()
WHERE o.type = 'U'   -- user tables only
ORDER BY sz.total_size_mb DESC, s.name, o.name, i.index_id;

