SELECT
    @@SERVERNAME AS full_domain_name,
    @@SERVERNAME AS host_name,
    DB_NAME() AS database_name,
    GETDATE() AS insert_date,
    st.text as query_text,
    qp.query_plan,
    bucketid,
    refcounts,
    usecounts,
    size_in_bytes,
    memory_object_address,
    cacheobjtype,
    objtype,
    plan_handle,
    pool_id,
    parent_plan_handle
from sys.dm_exec_cached_plans cp
CROSS APPLY
    sys.dm_exec_sql_text(cp.plan_handle) AS st
CROSS APPLY 
    sys.dm_exec_query_plan(cp.plan_handle) AS qp