# SQL Server Query Performance Analysis Prompt

## Context
You are a SQL Server performance tuning expert. I need you to analyze execution plans and related metadata from SQL Server Query Store to identify performance issues and provide actionable tuning recommendations.

## Understanding Query Store Data Structure

### Query vs Plan Relationship
- **One Query can have Multiple Plans**: SQL Server may generate different execution plans for the same query due to parameter sniffing, statistics updates, schema changes, or recompilation.
- **Query ID**: Unique identifier for a specific query text (e.g., Query ID 1182)
- **Plan ID**: Unique identifier for a specific execution plan for that query (e.g., Plan IDs 1117, 12762)

### File Naming Convention
JSON execution plan files follow this pattern: `<ObjectName>_QueryID_[query_id]_PlanID_[plan_id].json`

**Examples:**
- `spAR_OccupancyRateCalc_QueryID_1181_PlanID_1117.json` - spAR_OccupancyRateCalc, Query 1181, Plan 1117
- `spAR_OccupancyRateCalc_QueryID_1181_PlanID_12762.json` - spAR_OccupancyRateCalc, Query 1181, Plan 12762 (different plan for same query)
- `spAR_OccupancyRateCalc_QueryID_1182_PlanID_1118.json` - spAR_OccupancyRateCalc, Query 1182, Plan 1118

### How to Match Files
1. Look at `top_resource_consuming_queries.json` to find the query_id and plan_ids
2. The `plan_ids` field may contain multiple comma-separated plan IDs (e.g., "1117,12762")
3. Find all corresponding JSON execution plan files with matching QueryID in the filename
4. Analyze ALL plans for a given query to understand plan variations and identify the best/worst performing plan

**Example:**
```json
{
  "query_id": 1181,
  "plan_ids": "1117,12762",
  "plan_count": 2
}
```
This means you need to analyze BOTH:
- `spAR_OccupancyRateCalc_QueryID_1181_PlanID_1117.json`
- `spAR_OccupancyRateCalc_QueryID_1181_PlanID_12762.json`

### Why Multiple Plans Matter
- **Plan regression**: A newer plan may perform worse than an older plan
- **Parameter sniffing**: Different parameter values may generate different plans
- **Statistics changes**: Updated statistics may cause plan changes
- **Best practice**: Compare all plans for the same query and identify which is optimal

## Data Files to Analyze

Please analyze the following JSON files from the **Top Resource Consuming Queries** report:

1. **Top Resource Consuming Queries**: `../Output/Top_Resource_Consuming_Queries/top_resource_consuming_queries.json`
   - Contains the top resource-consuming queries ranked by total logical reads
   - Includes execution counts, CPU time, duration, and execution time ranges

2. **JSON Execution Plans**: `../Output/Top_Resource_Consuming_Queries/json_execution_plans/` (all .json files)
   - Detailed execution plan analysis for each query
   - Contains statement details, operators, node-level information, missing indexes, warnings, and statistics usage

3. **Index Details**: `../Output/Top_Resource_Consuming_Queries/index_details.json`
   - Current index configuration for tables referenced in the execution plans
   - Includes index usage statistics (seeks, scans, lookups, updates)
   - Index size and fragmentation information

4. **Statistics Details**: `../Output/Top_Resource_Consuming_Queries/statistics_details.json`
   - Statistics metadata for tables referenced in the execution plans
   - Includes last update time, modification counters, and sampling percentages

**Note**: This utility supports multiple report types (Regressed Queries, High Variation Queries, etc.).
The active report is configured in `Config/active-report.json`. Each report has its own dedicated output folder.

## Analysis Requirements

For each query in the top resource-consuming queries list, provide a comprehensive analysis covering:

### 1. **Query Identification**
- Query ID and ALL associated Plan ID(s)
- Object name (stored procedure/query)
- **SQL Statement**: Include the full SQL query text from the `statement_text` field in the JSON execution plan
- Execution frequency and resource consumption metrics
- **If multiple plans exist**: Identify which plan is currently active and compare performance characteristics

### 2. **Multiple Plan Comparison** (if applicable)
If a query has multiple plans (plan_count > 1):
- **Compare estimated costs** across all plans
- **Identify plan differences**: Different join orders, index choices, operator types
- **Determine root cause**:
  - Check statistics.last_update timestamps between plans to see if stats changes caused plan variation
  - **Parameter sniffing detection**: Look for significant differences in estimated_rows across plans for the same operators
  - Check if plans have different seek predicates or join strategies
- **Recommend plan forcing** if one plan is significantly better: Provide `sp_query_store_force_plan` command
- **Flag plan regression**: If newer plan (higher Plan ID) performs worse than older plan

### 3. **Individual Execution Plan Analysis**
- Review the corresponding JSON execution plan file(s)
- Identify expensive operators (high estimated cost, high row counts)
- Check for problematic patterns:
  - Table scans or index scans on large tables
  - Key lookups (RID/Key Lookup operations)
  - Nested loops with high outer row counts
  - Hash joins or sort operations that could be avoided
  - Parallelism issues (excessive parallelism or lack of parallelism)
  - Implicit conversions
  - Spills to tempdb

### 4. **Missing Index Analysis**
- Review all missing index recommendations from the execution plans
- Prioritize by impact percentage (focus on >50% impact)
- Provide specific CREATE INDEX statements with:
  - Appropriate index name following naming conventions
  - Equality columns (in optimal order based on selectivity)
  - Inequality columns
  - INCLUDE columns (if beneficial)
- Consider if existing indexes could be modified instead of creating new ones

### 5. **Index Usage Analysis**
- Cross-reference execution plans with `index_details.json`
- Identify:
  - **Unused indexes**: High update count but zero or very low seeks
  - **Missing seeks**: Indexes that should be used but show only scans
  - **Excessive scans**: Clustered indexes with high scan counts
  - **Lookup-heavy indexes**: High lookup counts indicating covering index opportunities
- Recommend index modifications, additions, or removals

### 6. **Statistics Health Check**
- Cross-reference statistics used in execution plans with `statistics_details.json`
- Check for:
  - **Stale statistics**: High modification_counter relative to row count (>20% is concerning)
  - **Outdated statistics**: Last_updated timestamp is old (>7 days for active tables)
  - **Low sampling**: sampling_percent < 100% on small-to-medium tables
  - **Auto-created statistics**: May indicate missing indexes
- Recommend UPDATE STATISTICS commands where needed

### 7. **Warnings and Issues**
- Identify all warnings in the execution plans
- Common warnings to flag:
  - Unmatched indexes
  - No join predicate
  - Excessive memory grant
  - Insufficient memory grant (spills)
  - Type conversions
  - Cardinality estimate warnings

### 8. **Parameter Sniffing Analysis**
If multiple plans exist or performance is inconsistent:
- **Identify parameter sniffing symptoms**:
  - Multiple plans with drastically different estimated_rows for same operations
  - Wide variation in execution times (check first_execution_time vs last_execution_time)
  - Plans optimized for different parameter value distributions
  - Significant difference between estimated_rows and actual_rows (if available)

- **Analyze plan variations**:
  - Compare node_details.estimated_rows across different plans for the same query
  - Look for different join types (Nested Loop vs Hash Join vs Merge Join) between plans
  - Check for different index choices (Index Seek vs Index Scan) between plans

- **Recommend solutions** based on severity:
  - **OPTION (RECOMPILE)**: For queries with highly variable parameters
    ```sql
    -- Add to the end of the query
    OPTION (RECOMPILE)
    ```
  - **OPTION (OPTIMIZE FOR)**: For queries with typical parameter values
    ```sql
    -- Optimize for most common parameter values
    OPTION (OPTIMIZE FOR (@param1 = 'typical_value', @param2 = 100))
    ```
  - **OPTION (OPTIMIZE FOR UNKNOWN)**: For queries needing average statistics
    ```sql
    -- Use average density for all parameters
    OPTION (OPTIMIZE FOR UNKNOWN)
    ```
  - **Plan forcing**: If one plan works well for most cases
    ```sql
    EXEC sp_query_store_force_plan @query_id = [id], @plan_id = [best_plan_id];
    ```
  - **Local variables**: Copy parameters to local variables to avoid sniffing
    ```sql
    DECLARE @local_param INT = @input_param;
    -- Use @local_param in query instead of @input_param
    ```

### 9. **Query Rewrite Opportunities**
- Based on the execution plan patterns, suggest:
  - Better join strategies
  - Predicate improvements (SARGable predicates)
  - Elimination of scalar functions in WHERE/JOIN clauses
  - Use of EXISTS vs IN vs JOIN
  - Temp table strategies for complex queries
  - Query hints (use sparingly and justify)

### 10. **Overall Recommendations**
Prioritize recommendations by:
- **Critical** (High impact, low effort):
  - Missing indexes with >70% impact
  - Stale statistics on heavily-used tables (>50% modification rate)
  - Confirmed parameter sniffing with multiple poor-performing plans
- **High** (High impact, medium effort):
  - Index modifications
  - Query rewrites
  - Parameter sniffing mitigation (OPTIMIZE FOR, plan forcing)
- **Medium** (Medium impact, various effort):
  - Index cleanup
  - Statistics tuning
  - Possible parameter sniffing investigation
- **Low** (Low impact or high effort):
  - Nice-to-have optimizations
  - Minor query improvements

## Output Format

### File Organization
For each query analyzed, create a separate markdown file:
- **Filename**: `<ObjectName>_QueryID_[query_id]_Analysis.md`
- **Location**: Save to `../Output/Top_Resource_Consuming_Queries/Analysis/` folder
- **Example**: `../Output/Top_Resource_Consuming_Queries/Analysis/spAR_OccupancyRateCalc_QueryID_1181_Analysis.md`

This allows you to:
- Organize analysis by query
- Track analysis history
- Share specific query analyses
- Build a knowledge base of tuning decisions
- Keep analyses separate for each report type

### Content Structure
For each query analyzed, provide:

```markdown
<!-- File: ../Output/Top_Resource_Consuming_Queries/Analysis/<ObjectName>_QueryID_[ID]_Analysis.md -->

# Query Analysis: [Object Name] (Query ID: [ID])

### Summary
- **Rank**: #X by logical reads
- **Plan Count**: [number] plan(s)
- **Plan IDs**: [comma-separated list]
- **Executions**: [count] executions
- **Total Logical Reads**: [formatted number]
- **Avg Duration**: [ms] per execution
- **Performance Rating**: [Critical/Poor/Fair/Good]

### SQL Statement
```sql
-- Full SQL query text from the execution plan
[Include the complete SQL statement here from the statement_text field in the JSON execution plan]
```

**Statement Type**: [SELECT/INSERT/UPDATE/DELETE/MERGE]
**Complexity**: [Simple/Moderate/Complex]

### Plan Comparison (if multiple plans exist)
| Plan ID | Estimated Cost | Statements | Missing Indexes | Warnings | Recommendation |
|---------|---------------|------------|-----------------|----------|----------------|
| 1117    | 0.379         | 1          | 1 (87% impact)  | 0        | ⚠️ Suboptimal  |
| 12762   | 0.195         | 1          | 0               | 0        | ✅ Preferred   |

**Plan Forcing Recommendation:**
```sql
-- Force the better performing plan (Plan ID: 12762)
EXEC sp_query_store_force_plan @query_id = 1181, @plan_id = 12762;
```

### Key Findings
1. [Finding 1]
2. [Finding 2]
...

### Missing Indexes (High Impact)
```sql
-- Impact: XX.X% improvement
CREATE NONCLUSTERED INDEX [IX_TableName_Columns]
ON [schema].[table] ([equality_cols])
INCLUDE ([include_cols]);
```

### Statistics Issues
- **[Table].[Statistic]**: [Issue description]
  ```sql
  UPDATE STATISTICS [schema].[table]([statistic_name]) WITH FULLSCAN;
  ```

### Index Recommendations
- **Remove**: [Index name] - Reason: [unused, redundant, etc.]
- **Modify**: [Index name] - Reason: [add columns, change order, etc.]

### Parameter Sniffing Assessment
**Status**: [Not Detected / Possible / Confirmed]

**Evidence**:
- [List evidence if detected, e.g., "5 different plans with varying estimated rows"]
- [Estimated rows variation: Plan 1117 = 89 rows, Plan 12762 = 1500 rows]

**Recommended Solution**:
```sql
-- Option 1: Recompile for highly variable parameters
ALTER PROCEDURE [schema].[procedure_name]
WITH RECOMPILE;

-- Option 2: Optimize for typical values
OPTION (OPTIMIZE FOR (@payerID = 100, @LeaveType = 'A'))

-- Option 3: Force the best plan
EXEC sp_query_store_force_plan @query_id = 1181, @plan_id = 12762;
```

### Query Tuning Suggestions
1. [Specific suggestion with code example if applicable]
2. [Specific suggestion with code example if applicable]

### Priority
**[Critical/High/Medium/Low]** - [Brief justification]

---
```

## Additional Notes
- Focus on actionable recommendations with specific T-SQL code
- Consider the trade-offs of each recommendation (e.g., index maintenance overhead)
- Highlight any patterns across multiple queries that suggest systemic issues
- If actual execution statistics are missing (actual_rows = 0), note this limitation
- Cross-reference modification_counter in execution plans with statistics_details.json for accuracy

