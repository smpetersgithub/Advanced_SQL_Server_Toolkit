# SQL Server Query Plan Cache Pollution Analysis Prompt

## Context
You are a SQL Server performance tuning expert specializing in **plan cache pollution** and **plan stability** issues. I need you to analyze queries with excessive execution plans from SQL Server Query Store to identify root causes and provide actionable solutions for plan proliferation problems.

## Understanding Query Store Data Structure

### Query vs Plan Relationship
- **One Query can have Multiple Plans**: SQL Server may generate different execution plans for the same query due to parameter sniffing, statistics updates, schema changes, temp table variations, or recompilation.
- **Query ID**: Unique identifier for a specific query text (e.g., Query ID 9895)
- **Plan ID**: Unique identifier for a specific execution plan for that query (e.g., Plan IDs 9876, 9877, 9878, etc.)
- **High Plan Count**: Queries where many different plans exist, indicating plan cache pollution

### File Naming Convention
JSON execution plan files follow this pattern: `<ObjectName>_QueryID_[query_id]_PlanID_[plan_id].json`

**Examples:**
- `spCL_GetFacilityProgressNoteExtraction_QueryID_9895_PlanID_9876.json` - Query 9895, Plan 9876
- `spCL_GetFacilityProgressNoteExtraction_QueryID_9895_PlanID_9877.json` - Query 9895, Plan 9877 (different plan for same query)
- `spCL_GetFacilityProgressNoteExtraction_QueryID_9895_PlanID_9878.json` - Query 9895, Plan 9878 (yet another plan)

### How to Match Files
1. Look at `queries_with_high_plan_count.json` to find the query_id and plan_ids
2. The `plan_ids` field contains multiple comma-separated plan IDs (e.g., "9876,9877,9878,9879,9880,...")
3. Find ALL corresponding JSON execution plan files with matching QueryID in the filename
4. **Analyze a representative sample** of plans to understand why so many plans exist

**Example:**
```json
{
  "query_id": 9895,
  "plan_count": 94,
  "plan_ids": "9876,9877,9878,9879,9880,...,9969",
  "total_executions": 121,
  "avg_duration_ms": 35.07
}
```
This means 94 different plans exist for a single query! This is plan cache pollution.

### Why High Plan Count Matters
- **Memory waste**: Each plan consumes memory in the plan cache
- **Plan cache churn**: Excessive plans can cause useful plans to be evicted
- **Compilation overhead**: More plans = more compilation time
- **Unpredictable performance**: Different plans may have vastly different performance
- **Root cause indicator**: Often indicates parameter sniffing, temp table issues, or missing parameterization
- **Critical priority**: High plan count queries waste resources and cause instability

## Data Files to Analyze

Please analyze the following JSON files from the **Queries with High Plan Count** report:

1. **Queries with High Plan Count**: `../Output/Queries_With_High_Plan_Count/queries_with_high_plan_count.json`
   - Contains queries ranked by plan_count (number of cached plans)
   - Includes total_executions, avg_duration_ms, first/last execution times
   - Higher plan_count = more severe plan cache pollution

2. **JSON Execution Plans**: `../Output/Queries_With_High_Plan_Count/json_execution_plans/` (all .json files)
   - Detailed execution plan analysis for EACH plan of EACH query
   - Contains statement details, operators, node-level information, missing indexes, warnings, and statistics usage
   - **Note**: For queries with 50+ plans, analyze a representative sample (first, last, and middle plans)

3. **Index Details**: `../Output/Queries_With_High_Plan_Count/index_details.json`
   - Current index configuration for tables referenced in the execution plans
   - Includes index usage statistics (seeks, scans, lookups, updates)
   - Index size and fragmentation information

4. **Statistics Details**: `../Output/Queries_With_High_Plan_Count/statistics_details.json`
   - Statistics metadata for tables referenced in the execution plans
   - Includes last update time, modification counters, and sampling percentages
   - **Critical for plan count analysis**: Statistics changes often trigger new plan creation

**Note**: This utility supports multiple report types (Top Resource Consuming, Regressed Queries, etc.).
The active report is configured in `Config/active-report.json`. Each report has its own dedicated output folder.

## Analysis Requirements

For each query in the high plan count list, provide a comprehensive analysis covering:

### 1. **Query Identification & Plan Count Metrics**
- Query ID and total Plan Count
- Object name (stored procedure/query)
- **SQL Statement**: Include the full SQL query text from the `statement_text` field in the JSON execution plan
- **Plan Count**: Total number of different plans observed
- **Execution Metrics**: Total executions, average duration
- **Time Window**: First execution to last execution time
- **Severity Assessment**: Based on plan_count and execution frequency
- **Plan-to-Execution Ratio**: plan_count / total_executions (higher = worse)

### 2. **Plan Proliferation Pattern Analysis** (CRITICAL)
This is the MOST IMPORTANT section for high plan count analysis.

**Analyze a representative sample of plans:**
- If plan_count < 10: Analyze ALL plans
- If plan_count 10-50: Analyze first 5, middle 5, last 5 plans
- If plan_count > 50: Analyze first 10, middle 10, last 10 plans

**Create a comparison table** showing:
- Plan ID
- Estimated cost
- Estimated rows (for key operators)
- Join strategies used
- Index choices (seeks vs scans)
- Temp table usage (if applicable)
- Missing index count
- Warnings count
- Plan creation pattern

**Example:**
| Plan ID | Est. Cost | Key Op Rows | Join Type | Index Choice | Temp Tables | Warnings | Pattern |
|---------|-----------|-------------|-----------|--------------|-------------|----------|---------|
| 9876    | 0.063     | 1 row       | Nested Loop | Index Seek | #patients (1 row) | 0 | Small dataset |
| 9920    | 45.230    | 5,000 rows  | Hash Join | Index Scan | #patients (5K rows) | 0 | Medium dataset |
| 9969    | 187.560   | 50,000 rows | Hash Join | Index Scan | #patients (50K rows) | 1 | Large dataset |

**Pattern Assessment:**
- Are plans similar or drastically different?
- Do estimated rows vary significantly across plans?
- Are different join strategies used?
- Do temp table row counts vary?

### 3. **Root Cause Analysis** (CRITICAL)
Identify WHY so many plans exist. Common causes:

#### **A. Temp Table Variations** (MOST COMMON)
- **Check for temp table usage** (#temp or @table variables)
- **Analyze temp table row count variations**:
  - Different row counts in temp tables cause different optimal plans
  - Example: #patients with 1 row → Nested Loop, #patients with 50K rows → Hash Join
- **Temp table statistics**:
  - Temp tables often lack statistics or have inaccurate statistics
  - Each different row count may trigger a new plan
- **Solution indicators**:
  - If temp table row counts vary widely → OPTION (RECOMPILE) is best solution
  - If temp table structure varies → Code refactoring needed

**Temp Table Indicators:**
- ✅ **Confirmed**: Query uses temp tables AND estimated rows vary by >10x across plans
- ⚠️ **Likely**: Query uses temp tables AND plan count > 20
- ℹ️ **Possible**: Query uses temp tables AND plan count > 5

#### **B. Parameter Sniffing** (COMMON)
- **Check for parameter variations**:
  - Different parameter values cause different row estimates
  - Example: @Status = 'Active' (1000 rows) vs @Status = 'Inactive' (10 rows)
- **Analyze estimated rows across plans**:
  - Large discrepancies (>10x) indicate parameter sniffing
  - Different join strategies for same query = parameter sniffing
- **Review execution time ranges**:
  - Plans created over time may reflect different parameter distributions

**Parameter Sniffing Indicators:**
- ✅ **Confirmed**: Estimated rows vary by >100x across plans for same operation
- ⚠️ **Likely**: Estimated rows vary by 10-100x, or different join types used
- ℹ️ **Possible**: Estimated rows vary by 2-10x, or minor plan differences

#### **C. Statistics Changes** (COMMON)
- **Cross-reference with statistics_details.json**:
  - Check last_updated timestamps for statistics used by the query
  - Compare statistics update times with plan creation times
  - If statistics were updated between plan creations, this explains new plans
- **Check modification_counter**:
  - High modification counts (>20% of rows) indicate stale statistics
  - Statistics updates trigger plan recompilation with different estimates
- **Auto-created statistics**:
  - Presence of auto-created stats may indicate missing indexes
  - New auto-created stats can change plan choices

#### **D. Schema Changes** (LESS COMMON)
- **Index additions/removals**:
  - New indexes cause optimizer to create new plans
  - Check index_details.json for recently created indexes
- **Table structure changes**:
  - Column additions, data type changes can affect plans
  - Note: This data may not be directly visible in Query Store

#### **E. OPTION (RECOMPILE) Paradox** (RARE BUT CRITICAL)
- **Check if query has OPTION (RECOMPILE)**:
  - This hint should prevent plan caching entirely
  - If present AND plan_count > 1, investigate why:
    - Plans may be historical (created before hint was added)
    - Hint may be ignored due to dynamic SQL wrapper
    - Plan guides may override the hint
    - Nested procedures may bypass the hint
- **Verification**:
  - Check procedure modification date vs plan creation dates
  - If all plans are old, hint was likely added later
  - If new plans still being created, hint is not working

### 4. **Individual Execution Plan Analysis**
For a representative sample of plans:
- Review the corresponding JSON execution plan files
- Identify expensive operators (high estimated cost, high row counts)
- Check for problematic patterns:
  - **Table scans** on large tables (especially if other plans use seeks)
  - **Key lookups** (RID/Key Lookup operations) - covering index opportunities
  - **Nested loops with high outer row counts** (should be hash join)
  - **Hash joins with low row counts** (should be nested loop)
  - **Sort operations** that could be avoided with proper indexes
  - **Parallelism differences** (some plans parallel, others serial)
  - **Implicit conversions** causing index scans instead of seeks
  - **Spills to tempdb** (memory grant issues)

### 5. **Missing Index Analysis**
- Review missing index recommendations from a sample of plans
- **Compare missing indexes across plans**:
  - Do all plans suggest the same missing index?
  - Do different plans suggest different indexes?
  - This can indicate which parameter values or temp table sizes are most common
- Prioritize by impact percentage (focus on >50% impact)
- Provide specific CREATE INDEX statements with:
  - Appropriate index name following naming conventions
  - Equality columns (in optimal order based on selectivity)
  - Inequality columns
  - INCLUDE columns (covering index to eliminate lookups)
- **Consider**: Will the missing index reduce plan count?

### 6. **Index Usage Analysis**
- Cross-reference execution plans with `index_details.json`
- Identify:
  - **Indexes used inconsistently**: Some plans use seeks, others use scans
  - **Missing indexes** that would benefit all plans
  - **Unused indexes**: High update count but zero seeks (consider dropping)
  - **Fragmented indexes**: May cause plan variations
- Recommend index modifications that will reduce plan proliferation

### 7. **Statistics Health Check**
- Cross-reference statistics used in execution plans with `statistics_details.json`
- Check for:
  - **Stale statistics**: High modification_counter relative to row count (>20% is concerning)
  - **Outdated statistics**: Last_updated timestamp is old (>7 days for active tables)
  - **Low sampling**: sampling_percent < 100% on small-to-medium tables
  - **Auto-created statistics**: May indicate missing indexes
  - **Statistics updated between plan creations**: Explains plan proliferation
- Recommend UPDATE STATISTICS commands where needed
- **Consider**: Will updating statistics reduce plan count or increase it?

### 8. **Warnings and Issues**
- Identify all warnings in the sampled execution plans
- **Compare warnings across plans**:
  - Do some plans have warnings that others don't?
  - Common warnings in high-plan-count queries:
    - **Unmatched indexes**: Statistics don't match current data
    - **No join predicate**: Cartesian product (very bad)
    - **Excessive memory grant**: Plan over-allocates memory
    - **Insufficient memory grant**: Spills to tempdb (very slow)
    - **Type conversions**: Implicit conversions prevent index usage
    - **Cardinality estimate warnings**: Optimizer unsure about row counts

### 9. **Plan Cache Pollution Solutions** (CRITICAL)
Based on the root cause analysis, recommend the BEST solution:

#### **Solution 1: OPTION (RECOMPILE)** (Best for Temp Tables)
**When to use**: Query uses temp tables with highly variable row counts
```sql
-- Add to the end of the query or in stored procedure
OPTION (RECOMPILE)
```
**Pros**: Always gets optimal plan for current temp table size, eliminates plan cache pollution
**Cons**: Compilation overhead (acceptable if query is infrequent or slow)
**Impact**: Reduces plan_count to 0 (no caching)

#### **Solution 2: Plan Forcing** (Quick Fix for Parameter Sniffing)
**When to use**: One plan works well for 80%+ of executions, parameter sniffing is the cause
```sql
-- Force the best performing plan
EXEC sp_query_store_force_plan @query_id = [query_id], @plan_id = [best_plan_id];
```
**Pros**: Immediate fix, no code changes, reduces plan_count to 1
**Cons**: May not be optimal for all parameter values, requires monitoring
**Impact**: Reduces plan_count to 1 (forced plan)

#### **Solution 3: Update Statistics Regularly** (For Statistics-Driven Proliferation)
**When to use**: Plans correlate with statistics update times
```sql
-- Schedule regular statistics updates
UPDATE STATISTICS [schema].[table] WITH FULLSCAN;

-- Or create a maintenance job
CREATE STATISTICS [stat_name] ON [schema].[table]([columns]) WITH FULLSCAN;
```
**Pros**: Prevents plan proliferation due to stale stats
**Cons**: Requires ongoing maintenance
**Impact**: Reduces plan_count by preventing statistics-triggered recompilations



#### **Solution 4: Temp Table Statistics** (For Temp Table Issues)
**When to use**: Query uses temp tables but RECOMPILE is not desired
```sql
-- Create temp table with proper indexes and statistics
CREATE TABLE #temp (
    col1 INT PRIMARY KEY,
    col2 VARCHAR(100)
);

-- Populate temp table
INSERT INTO #temp SELECT ...;

-- Update statistics before using temp table
UPDATE STATISTICS #temp WITH FULLSCAN;

-- Now run your query
SELECT ... FROM #temp ...;
```
**Pros**: Better plan quality without recompilation overhead
**Cons**: Requires code changes, adds complexity
**Impact**: May reduce plan_count if temp table statistics are the issue

#### **Solution 5: OPTION (OPTIMIZE FOR UNKNOWN)** (Conservative Approach)
**When to use**: Need consistent (not optimal) performance, reduce plan variations
```sql
-- Use average density for all parameters
OPTION (OPTIMIZE FOR UNKNOWN)
```
**Pros**: Reduces plan variations, more predictable performance
**Cons**: May not be optimal for any specific parameter value
**Impact**: Reduces plan_count significantly (1-3 plans typical)

#### **Solution 6: Query Redesign** (Long-term Fix)
**When to use**: Query can be split based on parameter values or temp table sizes
```sql
-- Use IF/ELSE to route to different query branches
IF (SELECT COUNT(*) FROM #temp) < 100
    -- Query optimized for small temp tables (nested loops)
    SELECT ... OPTION (LOOP JOIN)
ELSE
    -- Query optimized for large temp tables (hash joins)
    SELECT ... OPTION (HASH JOIN)
```
**Pros**: Optimal performance for all cases, controlled plan count
**Cons**: Code complexity, maintenance overhead
**Impact**: Reduces plan_count to 2-3 (one per branch)

#### **Solution 7: Missing Indexes** (Eliminate Variation)
**When to use**: Missing index would make all plans perform similarly
```sql
-- Create index that benefits all parameter values and temp table sizes
CREATE NONCLUSTERED INDEX [IX_Table_Columns]
ON [schema].[table] ([key_columns])
INCLUDE ([covering_columns])
WITH (ONLINE = ON, SORT_IN_TEMPDB = ON);
```
**Pros**: Improves all plans, may reduce plan variations
**Cons**: Index maintenance overhead
**Impact**: May reduce plan_count if index eliminates need for different strategies

**Recommendation Priority**:
1. **First**: Identify root cause (temp tables, parameter sniffing, statistics)
2. **Second**: If temp tables with variable sizes → OPTION (RECOMPILE)
3. **Third**: If parameter sniffing → Force best plan or OPTIMIZE FOR UNKNOWN
4. **Fourth**: If statistics-driven → Update statistics regularly
5. **Fifth**: Create missing indexes (if high impact)
6. **Sixth**: Monitor and adjust

### 10. **Query Rewrite Opportunities**
Based on execution plan patterns, suggest:
- **Temp table improvements**: Add proper indexes, update statistics, use table variables
- **Better join strategies**: Force join order if optimizer chooses poorly
- **Predicate improvements**: Ensure SARGable predicates (avoid functions on columns)
- **Eliminate scalar functions**: In WHERE/JOIN clauses (prevent index usage)
- **Use EXISTS vs IN vs JOIN**: Based on data distribution
- **Break complex queries**: Use multiple steps with temp tables
- **Filtered indexes**: For queries with common WHERE clause values
- **Indexed views**: For frequently-joined tables
- **Query hints**: Use sparingly and justify (FORCE ORDER, LOOP JOIN, etc.)

### 11. **Overall Recommendations**
Prioritize recommendations by:

**Critical** (Immediate Action Required):
- Plan count > 50 AND plan-to-execution ratio > 0.5
- Query uses OPTION (RECOMPILE) but still has many cached plans
- Temp table with highly variable row counts causing plan proliferation
- Memory waste > 100MB due to excessive plans

**High** (Action Required This Week):
- Plan count 20-50 with moderate execution frequency
- Parameter sniffing causing plan proliferation
- Statistics-driven plan creation (correlates with stats updates)
- Plan cache churn affecting other queries

**Medium** (Action Required This Month):
- Plan count 10-20
- Minor plan variations
- Missing indexes that would stabilize plans
- Statistics updates needed

**Low** (Monitor):
- Plan count < 10
- Low execution frequency
- Plans are similar (minor variations)
- Nice-to-have optimizations

## Output Format

### File Organization
For each query analyzed, create a separate markdown file:
- **Filename**: `<ObjectName>_QueryID_[query_id]_Analysis.md`
- **Location**: Save to `../Output/Queries_With_High_Plan_Count/Analysis/` folder
- **Example**: `../Output/Queries_With_High_Plan_Count/Analysis/spCL_GetFacilityProgressNoteExtraction_QueryID_9895_Analysis.md`

This allows you to:
- Organize analysis by query
- Track analysis history
- Share specific query analyses
- Build a knowledge base of plan cache pollution solutions
- Keep analyses separate for each report type

### Content Structure
For each query analyzed, provide:

```markdown
<!-- File: ../Output/Queries_With_High_Plan_Count/Analysis/<ObjectName>_QueryID_[ID]_Analysis.md -->

# Query Analysis: [Object Name] (Query ID: [ID])

## Summary
- **Rank**: #X by plan count
- **Plan Count**: [number] plans (CRITICAL/HIGH/MODERATE)
- **Plan IDs**: [first 10]...[last 10] (if > 20 plans)
- **Executions**: [count] executions
- **Plan-to-Execution Ratio**: [ratio] ([assessment])
- **Avg Duration**: [ms] per execution
- **Time Window**: [first] to [last] execution
- **Severity**: [Critical/High/Medium/Low]

## SQL Statement
```sql
-- Full SQL query text from the execution plan
[Include the complete SQL statement here from the statement_text field in the JSON execution plan]
```

**Statement Type**: [SELECT/INSERT/UPDATE/DELETE/MERGE]
**Complexity**: [Simple/Moderate/Complex]
**Temp Tables Used**: [Yes/No - list temp table names if yes]
**Has OPTION (RECOMPILE)**: [Yes/No]

## Plan Proliferation Analysis

### Plan Sample Comparison
Analyzed [X] representative plans out of [total]:

| Plan ID | Est. Cost | Key Op Rows | Join Type | Index Choice | Temp Table Rows | Warnings | Pattern |
|---------|-----------|-------------|-----------|--------------|-----------------|----------|---------|
| [ID]    | [cost]    | [rows]      | [type]    | [seek/scan]  | [count]         | [count]  | [desc]  |
| ...     | ...       | ...         | ...       | ...          | ...             | ...      | ...     |

**Pattern Assessment**:
- [Are plans similar or drastically different?]
- [Do estimated rows vary significantly?]
- [Are different join strategies used?]
- [Summary of variation pattern]

## Root Cause Analysis

**Primary Root Cause**: [Temp Tables / Parameter Sniffing / Statistics Changes / Schema Changes / RECOMPILE Paradox]

**Evidence**:
1. [Specific evidence from plan analysis]
2. [Specific evidence from statistics/indexes]
3. [Specific evidence from execution patterns]

**Detailed Analysis**:
[Explain WHY so many plans exist - be specific and reference the data]

### Temp Table Analysis (if applicable)
- **Temp Tables Used**: [list]
- **Row Count Variation**: [min] to [max] rows
- **Impact on Plans**: [how row count affects plan choice]
- **Statistics**: [present/absent, accurate/inaccurate]

### Parameter Sniffing Analysis (if applicable)
- **Parameters**: [list parameters]
- **Estimated Row Variations**: [describe variations across plans]
- **Join Strategy Changes**: [describe how joins change]
- **Sniffing Severity**: [Confirmed/Likely/Possible]

### Statistics Analysis
- **Key Statistics**: [list statistics used by query]
- **Last Updated**: [timestamps]
- **Modification Counter**: [counts and percentages]
- **Correlation with Plan Creation**: [Yes/No - explain]

## Key Findings
1. [Most critical finding with impact assessment]
2. [Second most critical finding]
3. [Additional findings...]

## Missing Indexes (High Impact)
```sql
-- Impact: XX.X% improvement (from Plan ID [id])
-- Benefit: [Explain how this index would help reduce plan count]
CREATE NONCLUSTERED INDEX [IX_TableName_Columns]
ON [schema].[table] ([equality_cols])
INCLUDE ([include_cols])
WITH (ONLINE = ON, SORT_IN_TEMPDB = ON);
```

**Expected Impact on Plan Count**:
- [Will this index reduce plan count? By how much?]

## Statistics Issues
- **[Table].[Statistic]**: [Issue description - stale/outdated/low sampling]
  - **Last Updated**: [timestamp]
  - **Modification Counter**: [count] ([percentage]% of rows)
  - **Impact on Plan Count**: [How this contributes to plan proliferation]
  ```sql
  UPDATE STATISTICS [schema].[table]([statistic_name]) WITH FULLSCAN;
  ```

## Recommended Solution

**Primary Recommendation**: [Solution name from Section 9]

**Justification**:
- [Why this solution is best for this specific query]
- [Expected impact on plan count]
- [Trade-offs and considerations]

**Implementation**:
```sql
-- [Specific T-SQL code for the recommended solution]
[Include complete, ready-to-execute code]
```

**Expected Results**:
- **Plan Count**: Reduce from [current] to [target]
- **Memory Savings**: [estimated MB saved]
- **Performance**: [expected impact on execution time]
- **Stability**: [expected improvement in plan stability]

**Alternative Solutions** (if primary fails):
1. **[Solution 2 name]**: [Brief description and when to use]
2. **[Solution 3 name]**: [Brief description and when to use]

## Monitoring Recommendations
After implementing the solution, monitor:
- **Plan count**: Should reduce significantly
- **Query Store metrics**: Check plan_count over time
- **Execution times**: Should become more consistent
- **Memory usage**: Plan cache should use less memory

**Monitoring Query**:
```sql
-- Check plan count after changes
SELECT
    q.query_id,
    COUNT(DISTINCT p.plan_id) AS plan_count,
    SUM(rs.count_executions) AS total_executions,
    CAST(COUNT(DISTINCT p.plan_id) AS FLOAT) / NULLIF(SUM(rs.count_executions), 0) AS plan_to_execution_ratio
FROM sys.query_store_query q
JOIN sys.query_store_plan p ON q.query_id = p.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
WHERE q.query_id = [query_id]
    AND rs.last_execution_time >= DATEADD(day, -7, GETDATE())
GROUP BY q.query_id;
```

## Priority
**[Critical/High/Medium/Low]** - [Brief justification based on plan count, ratio, and resource impact]

**Risk Assessment**:
- **Implementation Risk**: [Low/Medium/High]
- **Performance Risk**: [Low/Medium/High]
- **Rollback Plan**: [How to undo changes if needed]

## Expected Outcomes
- **Plan Count**: Reduce from [current] to [target]
- **Plan-to-Execution Ratio**: Reduce from [current] to [target]
- **Memory Savings**: [estimated MB]
- **Performance**: [Expected improvement]
- **Stability**: [Expected improvement in consistency]

---
```

## Additional Notes
- **Focus on root cause**: Don't just count plans, explain WHY they exist
- **Temp tables are the #1 cause**: Look for temp table usage first
- **OPTION (RECOMPILE) paradox**: If present, investigate why plans still exist
- **Provide specific solutions**: Each query may need a different approach
- **Quantify the impact**: Always state expected reduction in plan count
- **Consider memory waste**: High plan counts waste valuable plan cache memory
- **Monitor after changes**: Plan count queries require ongoing monitoring

## Success Criteria
A successful analysis should:
1. ✅ Identify the root cause of plan proliferation (not just symptoms)
2. ✅ Analyze a representative sample of plans in detail
3. ✅ Provide a specific, actionable recommendation with T-SQL code
4. ✅ Explain WHY the recommended solution will reduce plan count
5. ✅ Quantify expected reduction in plan count and memory savings
6. ✅ Include monitoring queries to verify improvement
7. ✅ Assess risks and provide rollback plans
8. ✅ Prioritize based on severity and resource impact


