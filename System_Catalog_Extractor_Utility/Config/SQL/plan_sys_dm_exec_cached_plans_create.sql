CREATE TABLE IF NOT EXISTS "plan_sys_dm_exec_cached_plans" (
    "full_domain_name" TEXT,
    "host_name" TEXT,
    "database_name" TEXT,
    "insert_date" TEXT,
    "query_text" TEXT,
    "query_plan" XML,
    "bucketid" INTEGER,
    "refcounts" INTEGER,
    "usecounts" INTEGER,
    "size_in_bytes" INTEGER,
    "memory_object_address" BLOB,
    "cacheobjtype" TEXT,
    "objtype" TEXT,
    "plan_handle" BLOB,
    "pool_id" INTEGER,
    "parent_plan_handle" BLOB
);

