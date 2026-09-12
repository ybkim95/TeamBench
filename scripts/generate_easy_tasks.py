#!/usr/bin/env python3
"""
Generate 100+ easy and industry tasks for TeamBench
"""

import os
from pathlib import Path

# Easy task templates
EASY_TASKS = [
    {
        "id": "EASY3_list_sorting",
        "title": "Fix List Sorting Bug",
        "problem": "A function that sorts a list of dictionaries by age is sorting in the wrong direction",
        "bug": "sorted(people, key=lambda x: x['age'], reverse=False)  # Should be reverse=True",
        "fix": "Change reverse=False to reverse=True",
    },
    {
        "id": "EASY4_json_parsing", 
        "title": "Fix JSON Parsing Error",
        "problem": "JSON loading function fails due to incorrect exception handling",
        "bug": "except JSONDecodeError  # Missing 'as e'",
        "fix": "Add 'as e' to exception handling",
    },
    {
        "id": "EASY5_variable_scope",
        "title": "Fix Variable Scope Issue", 
        "problem": "Function has UnboundLocalError due to variable scope",
        "bug": "Modifying global variable without 'global' keyword",
        "fix": "Add 'global' declaration or use return value",
    },
    {
        "id": "EASY6_import_error",
        "title": "Fix Import Statement",
        "problem": "Module import is incorrect causing ImportError",
        "bug": "from datetime import datetime as dt  # Wrong alias",
        "fix": "Use correct import or fix usage",
    },
    {
        "id": "EASY7_string_methods",
        "title": "Fix String Method Call",
        "problem": "String cleaning function uses wrong method",
        "bug": "text.strip()  # Should be text.lower().strip()",
        "fix": "Chain string methods correctly",
    },
    {
        "id": "EASY8_loop_condition",
        "title": "Fix Loop Condition",
        "problem": "While loop has off-by-one error",
        "bug": "while i < len(items):  # Should be <= for inclusive range",
        "fix": "Correct loop boundary condition",
    },
    {
        "id": "EASY9_dict_access",
        "title": "Fix Dictionary Access",
        "problem": "KeyError when accessing dictionary with missing key",
        "bug": "return data[key]  # Should use .get() with default",
        "fix": "Use data.get(key, default_value)",
    },
    {
        "id": "EASY10_file_handling",
        "title": "Fix File Handle Leak",
        "problem": "File is opened but never closed",
        "bug": "f = open('file.txt'); return f.read()  # No close()",
        "fix": "Use 'with' statement for proper file handling",
    },
]

# Industry task templates
INDUSTRY_TASKS = [
    {
        "id": "INDUSTRY3_database_connection_pooling",
        "title": "Database Connection Pool Optimization",
        "domain": "Backend Engineering",
        "problem": "High latency and connection exhaustion in database access",
        "solution": "Implement connection pooling with proper lifecycle management",
    },
    {
        "id": "INDUSTRY4_cache_invalidation",
        "title": "Cache Invalidation Strategy",
        "domain": "Performance Engineering", 
        "problem": "Stale cache data causing inconsistent user experience",
        "solution": "Implement cache tags and smart invalidation patterns",
    },
    {
        "id": "INDUSTRY5_log_aggregation",
        "title": "Distributed Log Aggregation",
        "domain": "DevOps",
        "problem": "Difficult to trace requests across microservices",
        "solution": "Implement structured logging with correlation IDs",
    },
    {
        "id": "INDUSTRY6_auth_token_refresh",
        "title": "JWT Token Refresh Mechanism",
        "domain": "Security",
        "problem": "Users get logged out frequently due to token expiration", 
        "solution": "Implement sliding token refresh with secure storage",
    },
    {
        "id": "INDUSTRY7_message_queue_backpressure",
        "title": "Message Queue Backpressure Handling",
        "domain": "Distributed Systems",
        "problem": "Queue overflow during traffic spikes causes message loss",
        "solution": "Implement backpressure and circuit breaker patterns",
    },
    {
        "id": "INDUSTRY8_feature_flag_rollout",
        "title": "Feature Flag Rollout System",
        "domain": "Product Engineering",
        "problem": "Need safe, gradual feature rollouts with instant rollback",
        "solution": "Build percentage-based rollout with real-time controls",
    },
    {
        "id": "INDUSTRY9_metrics_alerting",
        "title": "Intelligent Metrics Alerting",
        "domain": "SRE",
        "problem": "Too many false positive alerts causing alert fatigue",
        "solution": "Implement anomaly detection and alert correlation",
    },
    {
        "id": "INDUSTRY10_data_pipeline_monitoring",
        "title": "Data Pipeline Health Monitoring",
        "domain": "Data Engineering",
        "problem": "Silent failures in ETL pipelines causing data quality issues",
        "solution": "Build comprehensive data validation and monitoring",
    },
]

def create_task_directory(task_id, base_path="/u/ybkim95/TeamBench/tasks"):
    """Create task directory structure"""
    task_dir = Path(base_path) / task_id
    task_dir.mkdir(exist_ok=True)
    
    workspace_dir = task_dir / "workspace"
    workspace_dir.mkdir(exist_ok=True)
    
    return task_dir

def generate_easy_task(task_info):
    """Generate an easy task from template"""
    task_dir = create_task_directory(task_info["id"])
    
    # Create spec.md
    spec_content = f'''# {task_info["id"].upper()}: {task_info["title"]}

## Problem
{task_info["problem"]}.

## Bug Description (Planner Only)
The issue is: {task_info["bug"]}

## Solution
{task_info["fix"]}

## Test Cases
The existing tests should pass after the fix.

## Success Criteria
- Fix the identified bug
- All tests pass
- Code follows Python best practices
'''
    
    with open(task_dir / "spec.md", "w") as f:
        f.write(spec_content)
    
    # Create brief.md
    brief_content = f'''# {task_info["id"].upper()}: {task_info["title"]}

## Problem
{task_info["problem"]}.

## Your Task
Fix the bug in the provided code and ensure all tests pass.

## Testing
Run the test file to verify your fix.
'''
    
    with open(task_dir / "brief.md", "w") as f:
        f.write(brief_content)

def generate_industry_task(task_info):
    """Generate an industry task from template"""
    task_dir = create_task_directory(task_info["id"])
    
    # Create spec.md
    spec_content = f'''# {task_info["id"].upper()}: {task_info["title"]}

## Domain
{task_info["domain"]}

## Business Problem
{task_info["problem"]}.

## Technical Solution
{task_info["solution"]}.

## Implementation Requirements
- Design scalable architecture
- Implement monitoring and alerting
- Handle edge cases and failures
- Provide operational documentation

## Success Criteria
- System handles production load
- Monitoring provides actionable insights
- Implementation is maintainable
- Documentation is comprehensive

## Industry Context
This is a common problem in {task_info["domain"].lower()} that affects:
- System reliability
- User experience  
- Operational efficiency
- Business metrics
'''
    
    with open(task_dir / "spec.md", "w") as f:
        f.write(spec_content)
    
    # Create brief.md
    brief_content = f'''# {task_info["id"].upper()}: {task_info["title"]}

## Domain
{task_info["domain"]}

## Problem
{task_info["problem"]}.

## Your Mission
Implement a production-ready solution that solves this business problem.

## Requirements
- Build scalable system
- Add proper monitoring
- Handle failures gracefully
- Document your approach
'''
    
    with open(task_dir / "brief.md", "w") as f:
        f.write(brief_content)

def main():
    """Generate all easy and industry tasks"""
    print("Generating easy tasks...")
    for task in EASY_TASKS:
        generate_easy_task(task)
        print(f"Created {task['id']}")
    
    print("Generating industry tasks...")
    for task in INDUSTRY_TASKS:
        generate_industry_task(task)
        print(f"Created {task['id']}")
    
    print(f"Generated {len(EASY_TASKS) + len(INDUSTRY_TASKS)} new tasks!")

if __name__ == "__main__":
    main()