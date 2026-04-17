# SQL Server Query Performance Variation Analysis Prompt

## Context
You are a SQL Server performance tuning expert specializing in **parameter sniffing** and **plan stability** issues. I need you to analyze queries with high performance variation from SQL Server Query Store to identify root causes and provide actionable solutions for plan instability.

## Understanding Query Store Data Structure

### Query vs Plan Relationship
- **One Query can have Multiple Plans**: SQL Server may generate different execution plans for the same query due to parameter sniffing, statistics updates, schema changes, or recompilation.
- **Query ID**: Unique identifier for a specific query text (e.g., Query ID 2211)
- **Plan ID**: Unique identifier for a specific execution plan for that query (e.g., Plan IDs 2113, 6873, 6882, etc.)
- **High Variation**: Queries where different plans show dramatically different performance characteristics

### File Naming Convention
JSON execution plan files follow this pattern: `<ObjectName>_QueryID_[query_id]_PlanID_[plan_id].json`

**Examples:**
- `sp_schedule_admins_QueryID_2211_PlanID_2113.json` - sp_schedule_admins, Query 2211, Plan 2113
- `sp_schedule_admins_QueryID_2211_PlanID_6873.json` - sp_schedule_admins, Query 2211, Plan 6873 (different plan for same query)
- `sp_schedule_admins_QueryID_2211_PlanID_6882.json` - sp_schedule_admins, Query 2211, Plan 6882 (yet another plan)

### How to Match Files
1. Look at `queries_with_high_variation.json` to find the query_id and plan_ids
2. The `plan_ids` field contains multiple comma-separated plan IDs (e.g., "2113,6873,6882,8874,12523,16988,16991,17169,17259,17993")
3. Find ALL corresponding JSON execution plan files with matching QueryID in the filename
4. **Analyze ALL plans** for a given query to understand variation patterns and identify the root cause

**Example:**
```json
{
  "query_id": 2211,
  "plan_ids": "2113,6873,6882,8874,12523,16988,16991,17169,17259,17993",
  "plan_count": 10,
  "variation_ratio": 1389.52
}
```
This means you need to analyze ALL 10 plans to understand why performance varies by 1389x!

### Why High Variation Matters
- **Parameter sniffing**: Different parameter values generate drastically different plans
- **Plan regression**: Newer plans may perform significantly worse than older plans
- **Unpredictable performance**: Users experience inconsistent response times
- **Production incidents**: Slow plans can cause timeouts and application failures
- **Critical priority**: High variation queries are often the root cause of intermittent performance issues

## Data Files to Analyze

Please analyze the following JSON files from the **Queries With High Variation** report:

1. **Queries With High Variation**: `../Output/Queries_With_High_Variation/queries_with_high_variation.json`
   - Contains queries ranked by variation_ratio (max_duration / min_duration)
   - Includes plan_count, total_executions, min/max duration metrics
   - Higher variation_ratio = more severe performance instability

2. **JSON Execution Plans**: `../Output/Queries_With_High_Variation/json_execution_plans/` (all .json files)
   - Detailed execution plan analysis for EACH plan of EACH query
   - Contains statement details, operators, node-level information, missing indexes, warnings, and statistics usage
   - **Critical**: Compare ALL plans for the same query to identify variation patterns

3. **Index Details**: `../Output/Queries_With_High_Variation/index_details.json`
   - Current index configuration for tables referenced in the execution plans
   - Includes index usage statistics (seeks, scans, lookups, updates)
   - Index size and fragmentation information

4. **Statistics Details**: `../Output/Queries_With_High_Variation/statistics_details.json`
   - Statistics metadata for tables referenced in the execution plans
   - Includes last update time, modification counters, and sampling percentages
   - **Critical for variation analysis**: Statistics changes often trigger plan variations

**Note**: This utility supports multiple report types (Top Resource Consuming, Regressed Queries, etc.).
The active report is configured in `Config/active-report.json`. Each report has its own dedicated output folder.

## Analysis Requirements

For each query in the high variation list, provide a comprehensive analysis covering:

### 1. **Query Identification & Variation Metrics**
- Query ID and ALL associated Plan ID(s)
- Object name (stored procedure/query)
- **SQL Statement**: Include the full SQL query text from the `statement_text` field in the JSON execution plan
- **Variation Ratio**: How many times slower is the worst plan vs the best plan?
- **Plan Count**: Total number of different plans observed
- Execution frequency and time ranges (first_execution_time to last_execution_time)
- **Severity Assessment**: Based on variation_ratio and execution frequency

### 2. **Comprehensive Plan Comparison** (CRITICAL)
This is the MOST IMPORTANT section for high variation analysis.

**For ALL plans of the query:**
- **Create a comparison table** showing:
  - Plan ID
  - Estimated cost
  - Estimated rows (for key operators)
  - Join strategies used
  - Index choices (seeks vs scans)
  - Missing index count
  - Warnings count
  - Performance assessment (Best/Good/Poor/Worst)

**Example:**
| Plan ID | Est. Cost | Key Op Rows | Join Type | Index Choice | Missing Idx | Warnings | Assessment |
|---------|-----------|-------------|-----------|--------------|-------------|----------|------------|
| 2113    | 0.063     | 1 row       | Nested Loop | Index Seek | 0 | 1 | ✅ Best |
| 6882    | 87.560    | 50,000 rows | Hash Join | Index Scan | 0 | 1 | ❌ Worst |




### 3. **Root Cause Analysis** (CRITICAL)
Identify WHY the plans vary. Common causes:

#### **A. Parameter Sniffing Detection**
- **Compare estimated_rows** across all plans for the same operators
  - Example: Plan 2113 estimates 1 row, Plan 6882 estimates 50,000 rows for same table scan
  - Large discrepancies (>10x difference) indicate parameter sniffing
- **Check for different join strategies**:
  - Nested Loop (optimal for small datasets) vs Hash Join (optimal for large datasets)
  - If same query uses both, it's likely parameter sniffing
- **Analyze seek predicates**:
  - Different plans may use different columns in WHERE clause
  - Check if parameter values affect index selection
- **Review execution time ranges**:
  - Plans created at different times may have been optimized for different parameter values

**Parameter Sniffing Indicators:**
- ✅ **Confirmed**: Estimated rows vary by >100x across plans for same operation
- ⚠️ **Likely**: Estimated rows vary by 10-100x, or different join types used
- ℹ️ **Possible**: Estimated rows vary by 2-10x, or minor plan differences

#### **B. Statistics Changes**
- **Cross-reference with statistics_details.json**:
  - Check last_updated timestamps for statistics used by the query
  - Compare statistics update times with plan creation times (from execution time ranges)
  - If statistics were updated between plan creations, this may explain variation
- **Check modification_counter**:
  - High modification counts (>20% of rows) indicate stale statistics
  - Statistics updates can trigger plan recompilation with different estimates
- **Auto-created statistics**:
  - Presence of auto-created stats may indicate missing indexes
  - New auto-created stats can change plan choices

#### **C. Schema Changes**
- **Index additions/removals**:
  - New indexes may cause optimizer to choose different plans
  - Check index_details.json for recently created indexes (if timestamps available)
- **Table structure changes**:
  - Column additions, data type changes can affect plans
  - Note: This data may not be directly visible in Query Store

#### **D. Query Store Plan Forcing**
- **Check if any plans are forced**:
  - Look for is_forced_plan indicators in the data
  - Forced plans may explain why certain plans are used despite being suboptimal

### 4. **Individual Execution Plan Analysis**
For EACH plan (especially best and worst):
- Review the corresponding JSON execution plan file
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
- Review missing index recommendations from ALL plans
- **Compare missing indexes across plans**:
  - Do all plans suggest the same missing index?
  - Do different plans suggest different indexes?
  - This can indicate which parameter values are most common
- Prioritize by impact percentage (focus on >50% impact)
- Provide specific CREATE INDEX statements with:
  - Appropriate index name following naming conventions
  - Equality columns (in optimal order based on selectivity)
  - Inequality columns
  - INCLUDE columns (covering index to eliminate lookups)
- **Consider**: Will the missing index eliminate plan variation?

### 6. **Index Usage Analysis**
- Cross-reference execution plans with `index_details.json`
- Identify:
  - **Indexes used by best plan but not worst plan**: Why?
  - **Indexes scanned in worst plan but seeked in best plan**: Statistics issue?
  - **Missing indexes** that would benefit all plans
  - **Unused indexes**: High update count but zero seeks (consider dropping)
- Recommend index modifications that will stabilize plan choice

### 7. **Statistics Health Check**
- Cross-reference statistics used in execution plans with `statistics_details.json`
- Check for:
  - **Stale statistics**: High modification_counter relative to row count (>20% is concerning)
  - **Outdated statistics**: Last_updated timestamp is old (>7 days for active tables)
  - **Low sampling**: sampling_percent < 100% on small-to-medium tables
  - **Auto-created statistics**: May indicate missing indexes
  - **Statistics used by different plans**: Do they have different update times?
- Recommend UPDATE STATISTICS commands where needed
- **Consider**: Will updating statistics stabilize plans or cause more variation?

### 8. **Warnings and Issues**
- Identify all warnings in ALL execution plans
- **Compare warnings across plans**:
  - Do some plans have warnings that others don't?
  - Common warnings in high-variation queries:
    - **Unmatched indexes**: Statistics don't match current data
    - **No join predicate**: Cartesian product (very bad)
    - **Excessive memory grant**: Plan over-allocates memory
    - **Insufficient memory grant**: Spills to tempdb (very slow)
    - **Type conversions**: Implicit conversions prevent index usage
    - **Cardinality estimate warnings**: Optimizer unsure about row counts

### 9. **Parameter Sniffing Solutions** (CRITICAL)
Based on the root cause analysis, recommend the BEST solution:

#### **Solution 1: Plan Forcing** (Quick Fix)
**When to use**: One plan works well for 80%+ of executions
```sql
-- Force the best performing plan
EXEC sp_query_store_force_plan @query_id = [query_id], @plan_id = [best_plan_id];
```
**Pros**: Immediate fix, no code changes
**Cons**: May not be optimal for all parameter values, requires monitoring

#### **Solution 2: OPTION (RECOMPILE)** (Best for High Variation)
**When to use**: Parameter values vary widely, no single plan works well
```sql
-- Add to the end of the query or in stored procedure
OPTION (RECOMPILE)
```
**Pros**: Always gets optimal plan for current parameters
**Cons**: Compilation overhead (acceptable if query is infrequent or slow)

#### **Solution 3: OPTION (OPTIMIZE FOR)** (Best for Known Common Values)
**When to use**: 80%+ of executions use similar parameter values
```sql
-- Optimize for most common parameter values
OPTION (OPTIMIZE FOR (@param1 = 'typical_value', @param2 = 100))
```
**Pros**: Predictable performance for common cases
**Cons**: Poor performance for uncommon parameter values

#### **Solution 4: OPTION (OPTIMIZE FOR UNKNOWN)** (Conservative Approach)
**When to use**: Need consistent (not optimal) performance across all parameter values
```sql
-- Use average density for all parameters
OPTION (OPTIMIZE FOR UNKNOWN)
```
**Pros**: Consistent performance, no extreme outliers
**Cons**: May not be optimal for any specific parameter value

#### **Solution 5: Local Variables** (Avoid Sniffing)
**When to use**: Simple queries where optimizer should use average statistics
```sql
-- Copy parameters to local variables
DECLARE @local_param INT = @input_param;
-- Use @local_param in query instead of @input_param
```
**Pros**: Prevents parameter sniffing entirely
**Cons**: Optimizer uses average statistics (may not be optimal)

#### **Solution 6: Query Redesign** (Long-term Fix)
**When to use**: Query can be split based on parameter values
```sql
-- Use IF/ELSE to route to different query branches
IF @param1 < 100
    -- Query optimized for small values
ELSE
    -- Query optimized for large values
```
**Pros**: Optimal performance for all cases
**Cons**: Code complexity, maintenance overhead

#### **Solution 7: Missing Indexes** (Eliminate Variation)
**When to use**: Missing index would make all plans perform similarly
```sql
-- Create index that benefits all parameter values
CREATE NONCLUSTERED INDEX [IX_Table_Columns]
ON [schema].[table] ([key_columns])
INCLUDE ([covering_columns]);
```
**Pros**: Improves all plans, may eliminate variation
**Cons**: Index maintenance overhead

**Recommendation Priority**:
1. **First**: Create missing indexes (if high impact)
2. **Second**: Update stale statistics
3. **Third**: Choose parameter sniffing solution based on variation pattern
4. **Fourth**: Monitor and adjust

### 10. **Query Rewrite Opportunities**
Based on execution plan patterns, suggest:
- **Better join strategies**: Force join order if optimizer chooses poorly
- **Predicate improvements**: Ensure SARGable predicates (avoid functions on columns)
- **Eliminate scalar functions**: In WHERE/JOIN clauses (prevent index usage)
- **Use EXISTS vs IN vs JOIN**: Based on data distribution
- **Temp table strategies**: Break complex queries into steps
- **Filtered indexes**: For queries with common WHERE clause values
- **Indexed views**: For frequently-joined tables
- **Query hints**: Use sparingly and justify (FORCE ORDER, LOOP JOIN, etc.)

### 11. **Overall Recommendations**
Prioritize recommendations by:

**Critical** (Immediate Action Required):
- Variation ratio > 100x AND high execution frequency (>1000/day)
- Confirmed parameter sniffing with production impact
- Missing indexes with >80% impact that would stabilize plans
- Stale statistics (>50% modification rate) on key tables

**High** (Action Required This Week):
- Variation ratio 10-100x with moderate execution frequency
- Likely parameter sniffing with intermittent issues
- Missing indexes with 50-80% impact
- Multiple plans with significantly different strategies

**Medium** (Action Required This Month):
- Variation ratio 2-10x
- Possible parameter sniffing
- Missing indexes with 20-50% impact
- Statistics updates needed

**Low** (Monitor):
- Variation ratio < 2x
- Minor plan differences
- Low execution frequency
- Nice-to-have optimizations

## Output Format

### File Organization
For each query analyzed, create a separate markdown file:
- **Filename**: `<ObjectName>_QueryID_[query_id]_Analysis.md`
- **Location**: Save to `../Output/Queries_With_High_Variation/Analysis/` folder
- **Example**: `../Output/Queries_With_High_Variation/Analysis/sp_schedule_admins_QueryID_2211_Analysis.md`

This allows you to:
- Organize analysis by query
- Track analysis history
- Share specific query analyses
- Build a knowledge base of parameter sniffing solutions
- Keep analyses separate for each report type

### Content Structure
For each query analyzed, provide:

```markdown
<!-- File: ../Output/Queries_With_High_Variation/Analysis/<ObjectName>_QueryID_[ID]_Analysis.md -->

# Query Variation Analysis: [Object Name] (Query ID: [ID])

### Summary
- **Rank**: #X by variation ratio
- **Variation Ratio**: [number]x (worst plan is [number]x slower than best plan)
- **Plan Count**: [number] different plans observed
- **Plan IDs**: [comma-separated list]
- **Total Executions**: [count] executions
- **Execution Time Range**: [first_execution_time] to [last_execution_time]
- **Severity**: [Critical/High/Medium/Low]

### SQL Statement
```sql
-- Full SQL query text from the execution plan
[Include the complete SQL statement here from the statement_text field in the JSON execution plan]
```

**Statement Type**: [SELECT/INSERT/UPDATE/DELETE/MERGE]
**Complexity**: [Simple/Moderate/Complex]
**Parameters**: [List parameters if visible]

### Plan Comparison Table (CRITICAL)
| Plan ID | Est. Cost | Key Op Rows | Join Type | Index Choice | Missing Idx | Warnings | Assessment |
|---------|-----------|-------------|-----------|--------------|-------------|----------|------------|
| [id]    | [cost]    | [rows]      | [type]    | [seek/scan]  | [count]     | [count]  | ✅/⚠️/❌   |
| [id]    | [cost]    | [rows]      | [type]    | [seek/scan]  | [count]     | [count]  | ✅/⚠️/❌   |

**Plan Performance Summary**:
- **Best Plan**: Plan ID [id] - [reason why it's best]
- **Worst Plan**: Plan ID [id] - [reason why it's worst]
- **Variation Factor**: [worst_cost / best_cost]x difference

### Root Cause Analysis

**Primary Cause**: [Parameter Sniffing / Statistics Changes / Schema Changes / Other]

**Evidence**:
1. [Specific evidence from plan comparison]
2. [Specific evidence from statistics analysis]
3. [Specific evidence from execution patterns]

**Parameter Sniffing Status**: [✅ Confirmed / ⚠️ Likely / ℹ️ Possible / ❌ Not Detected]

**Detailed Analysis**:
- **Estimated Rows Variation**: [Describe differences across plans]
- **Join Strategy Differences**: [Describe if plans use different join types]
- **Index Selection Differences**: [Describe if plans use different indexes]
- **Statistics Update Timeline**: [Compare stats update times with plan creation times]

### Key Findings
1. [Most critical finding with impact assessment]
2. [Second most critical finding]
3. [Additional findings...]

### Missing Indexes (High Impact)
```sql
-- Impact: XX.X% improvement (from Plan ID [id])
-- Benefit: [Explain how this index would help stabilize plans]
CREATE NONCLUSTERED INDEX [IX_TableName_Columns]
ON [schema].[table] ([equality_cols])
INCLUDE ([include_cols])
WITH (ONLINE = ON, SORT_IN_TEMPDB = ON);
```

**Expected Impact on Variation**:
- [Will this index eliminate variation? Reduce it? Stabilize plan choice?]

### Statistics Issues
- **[Table].[Statistic]**: [Issue description - stale/outdated/low sampling]
  - **Last Updated**: [timestamp]
  - **Modification Counter**: [count] ([percentage]% of rows)
  - **Impact on Plans**: [Which plans were affected?]
  ```sql
  UPDATE STATISTICS [schema].[table]([statistic_name]) WITH FULLSCAN;
  ```

### Index Recommendations
- **Add**: [Index name] - Reason: [stabilize plan choice, eliminate variation]
- **Modify**: [Index name] - Reason: [add covering columns to benefit all plans]
- **Remove**: [Index name] - Reason: [unused, not helping any plan]

### Recommended Solution

**Primary Recommendation**: [Solution name from Section 9]

**Justification**:
- [Why this solution is best for this specific query]
- [Expected impact on variation ratio]
- [Trade-offs and considerations]

**Implementation**:
```sql
-- [Specific T-SQL code for the recommended solution]
[Include complete, ready-to-execute code]
```

**Alternative Solutions** (if primary fails):
1. **[Solution 2 name]**: [Brief description and when to use]
2. **[Solution 3 name]**: [Brief description and when to use]

### Query Tuning Suggestions
1. **[Suggestion 1]**: [Description]
   ```sql
   -- [Code example if applicable]
   ```
2. **[Suggestion 2]**: [Description]
   ```sql
   -- [Code example if applicable]
   ```

### Monitoring Recommendations
After implementing the solution, monitor:
- **Query Store metrics**: Check if variation_ratio decreases
- **Plan count**: Should stabilize (ideally to 1-2 plans)
- **Execution times**: Should become more consistent
- **Plan forcing status**: If forced, ensure it remains optimal

**Monitoring Query**:
```sql
-- Check plan stability after changes
SELECT
    q.query_id,
    COUNT(DISTINCT p.plan_id) AS plan_count,
    MAX(rs.avg_duration) / NULLIF(MIN(rs.avg_duration), 0) AS variation_ratio,
    SUM(rs.count_executions) AS total_executions
FROM sys.query_store_query q
JOIN sys.query_store_plan p ON q.query_id = p.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
WHERE q.query_id = [query_id]
    AND rs.last_execution_time >= DATEADD(day, -7, GETDATE())
GROUP BY q.query_id;
```

### Priority
**[Critical/High/Medium/Low]** - [Brief justification based on variation ratio, execution frequency, and business impact]

**Risk Assessment**:
- **Implementation Risk**: [Low/Medium/High]
- **Performance Risk**: [Low/Medium/High]
- **Rollback Plan**: [How to undo changes if needed]

### Expected Outcomes
- **Variation Ratio**: Reduce from [current]x to [target]x
- **Plan Stability**: Reduce from [current] plans to [target] plans
- **Performance**: [Expected improvement for typical executions]
- **Consistency**: [Expected improvement in execution time predictability]

---
```

## Additional Notes
- **Focus on plan comparison**: This is the most critical aspect of high variation analysis
- **Identify the root cause**: Don't just describe symptoms, explain WHY plans vary
- **Provide specific solutions**: Each query may need a different parameter sniffing solution
- **Consider the variation pattern**:
  - If one plan is always best → Force that plan
  - If different plans are best for different parameters → Use RECOMPILE or query redesign
  - If variation is due to stale stats → Update statistics
- **Quantify the impact**: Always state expected improvement in variation ratio
- **Think holistically**: Sometimes the best solution is a combination (e.g., create index + force plan)
- **Monitor after changes**: High variation queries require ongoing monitoring to ensure stability

## Success Criteria
A successful analysis should:
1. ✅ Identify the root cause of variation (not just symptoms)
2. ✅ Compare ALL plans for each query in detail
3. ✅ Provide a specific, actionable recommendation with T-SQL code
4. ✅ Explain WHY the recommended solution will reduce variation
5. ✅ Include monitoring queries to verify improvement
6. ✅ Assess risks and provide rollback plans
7. ✅ Prioritize based on business impact and implementation effort

