"""Evaluation module for SpendSense.

This module calculates metrics for the SpendSense system including:
- Coverage: Percentage of users with personas and behaviors
- Explainability: Percentage of recommendations with rationales
- Latency: Average, max, and p95 latency for recommendation generation
- Auditability: Percentage of recommendations with decision traces
- Persona distribution: Distribution of users across personas
"""

import json
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import db
from src.recommend.engine import generate_recommendations


def calculate_coverage() -> Dict[str, Any]:
    """Calculate coverage metric.
    
    Coverage measures:
    - Percentage of users with persona assignments
    - Percentage of users with ≥3 behaviors (computed features)
    
    Returns:
        Dictionary with coverage metrics
    """
    # Get all users
    users_query = "SELECT user_id FROM users"
    users = db.fetch_all(users_query)
    total_users = len(users)
    
    if total_users == 0:
        return {
            "total_users": 0,
            "users_with_personas": 0,
            "users_with_3plus_behaviors": 0,
            "coverage_personas": 0.0,
            "coverage_behaviors": 0.0
        }
    
    # Count users with persona assignments (30d window)
    persona_query = """
        SELECT COUNT(DISTINCT user_id) as count
        FROM persona_assignments
        WHERE time_window = '30d'
    """
    persona_row = db.fetch_one(persona_query)
    users_with_personas = persona_row["count"] if persona_row else 0
    
    # Count users with ≥3 behaviors (computed features for 30d window)
    behavior_query = """
        SELECT user_id, COUNT(*) as behavior_count
        FROM computed_features
        WHERE time_window = '30d'
        GROUP BY user_id
        HAVING behavior_count >= 3
    """
    behavior_rows = db.fetch_all(behavior_query)
    users_with_3plus_behaviors = len(behavior_rows)
    
    coverage_personas = (users_with_personas / total_users * 100) if total_users > 0 else 0.0
    coverage_behaviors = (users_with_3plus_behaviors / total_users * 100) if total_users > 0 else 0.0
    
    return {
        "total_users": total_users,
        "users_with_personas": users_with_personas,
        "users_with_3plus_behaviors": users_with_3plus_behaviors,
        "coverage_personas": round(coverage_personas, 2),
        "coverage_behaviors": round(coverage_behaviors, 2)
    }


def calculate_explainability() -> Dict[str, Any]:
    """Calculate explainability metric.
    
    Explainability measures:
    - Percentage of recommendations with non-empty rationales
    
    Returns:
        Dictionary with explainability metrics
    """
    # Get all recommendations
    rec_query = """
        SELECT recommendation_id, rationale
        FROM recommendations
    """
    recommendations = db.fetch_all(rec_query)
    
    total_recommendations = len(recommendations)
    
    if total_recommendations == 0:
        return {
            "total_recommendations": 0,
            "recommendations_with_rationales": 0,
            "explainability_percentage": 0.0
        }
    
    # Count recommendations with non-empty rationales
    recommendations_with_rationales = sum(
        1 for rec in recommendations 
        if rec["rationale"] and rec["rationale"].strip()
    )
    
    explainability_percentage = (
        recommendations_with_rationales / total_recommendations * 100
    ) if total_recommendations > 0 else 0.0
    
    return {
        "total_recommendations": total_recommendations,
        "recommendations_with_rationales": recommendations_with_rationales,
        "explainability_percentage": round(explainability_percentage, 2)
    }


def measure_latency(sample_size: int = 10) -> Dict[str, Any]:
    """Measure latency for recommendation generation.
    
    Measures the time taken to generate recommendations for a sample of users.
    Calculates average, max, and p95 latency.
    
    Args:
        sample_size: Number of users to sample for latency measurement
    
    Returns:
        Dictionary with latency metrics
    """
    # Get sample of users
    users_query = "SELECT user_id FROM users LIMIT ?"
    users = db.fetch_all(users_query, (sample_size,))
    
    if len(users) == 0:
        return {
            "sample_size": 0,
            "average_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "latencies_ms": []
        }
    
    latencies = []
    
    for user_row in users:
        user_id = user_row["user_id"]
        
        try:
            # Measure time for recommendation generation
            start_time = time.time()
            generate_recommendations(user_id, "30d")
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        except Exception as e:
            # Skip users that error out
            print(f"Warning: Error measuring latency for user {user_id}: {e}")
            continue
    
    if len(latencies) == 0:
        return {
            "sample_size": len(users),
            "average_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "latencies_ms": []
        }
    
    sorted_latencies = sorted(latencies)
    average_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    
    # Calculate p95
    p95_index = int(len(sorted_latencies) * 0.95)
    p95_latency = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
    
    return {
        "sample_size": len(latencies),
        "average_latency_ms": round(average_latency, 2),
        "max_latency_ms": round(max_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "latencies_ms": [round(l, 2) for l in latencies]
    }


def calculate_auditability() -> Dict[str, Any]:
    """Calculate auditability metric.
    
    Auditability measures:
    - Percentage of recommendations with decision traces
    
    Returns:
        Dictionary with auditability metrics
    """
    # Get all recommendations
    rec_query = """
        SELECT recommendation_id, decision_trace
        FROM recommendations
    """
    recommendations = db.fetch_all(rec_query)
    
    total_recommendations = len(recommendations)
    
    if total_recommendations == 0:
        return {
            "total_recommendations": 0,
            "recommendations_with_traces": 0,
            "auditability_percentage": 0.0
        }
    
    # Count recommendations with valid decision traces
    recommendations_with_traces = 0
    for rec in recommendations:
        decision_trace = rec["decision_trace"]
        if decision_trace:
            try:
                # Check if it's valid JSON
                json.loads(decision_trace)
                recommendations_with_traces += 1
            except (json.JSONDecodeError, TypeError):
                pass
    
    auditability_percentage = (
        recommendations_with_traces / total_recommendations * 100
    ) if total_recommendations > 0 else 0.0
    
    return {
        "total_recommendations": total_recommendations,
        "recommendations_with_traces": recommendations_with_traces,
        "auditability_percentage": round(auditability_percentage, 2)
    }


def calculate_persona_distribution() -> Dict[str, Any]:
    """Calculate persona distribution.
    
    Counts users per persona for the 30d time window.
    
    Returns:
        Dictionary with persona distribution
    """
    # Get persona assignments for 30d window
    # Use the most recent assignment per user
    persona_query = """
        SELECT persona, COUNT(*) as count
        FROM (
            SELECT user_id, persona,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY assigned_at DESC) as rn
            FROM persona_assignments
            WHERE time_window = '30d'
        )
        WHERE rn = 1
        GROUP BY persona
    """
    
    # Simplified query (SQLite may not support ROW_NUMBER in older versions)
    # Use a simpler approach
    persona_query = """
        SELECT DISTINCT user_id, persona
        FROM persona_assignments
        WHERE time_window = '30d'
    """
    
    persona_rows = db.fetch_all(persona_query)
    
    # Group by persona, taking the most recent per user
    user_personas = {}
    for row in persona_rows:
        user_id = row["user_id"]
        persona = row["persona"]
        # Get most recent persona for each user
        most_recent_query = """
            SELECT persona
            FROM persona_assignments
            WHERE user_id = ? AND time_window = '30d'
            ORDER BY assigned_at DESC
            LIMIT 1
        """
        most_recent = db.fetch_one(most_recent_query, (user_id,))
        if most_recent:
            user_personas[user_id] = most_recent["persona"]
    
    # Count by persona
    persona_counts = {}
    for persona in user_personas.values():
        persona_counts[persona] = persona_counts.get(persona, 0) + 1
    
    total = sum(persona_counts.values())
    
    # Calculate percentages
    persona_distribution = {}
    for persona, count in persona_counts.items():
        persona_distribution[persona] = {
            "count": count,
            "percentage": round((count / total * 100) if total > 0 else 0.0, 2)
        }
    
    return {
        "total_users": total,
        "distribution": persona_distribution
    }


def run_evaluation() -> Dict[str, Any]:
    """Run full evaluation and return all metrics.
    
    Returns:
        Dictionary with all evaluation metrics
    """
    print("Running evaluation metrics...")
    
    print("  Calculating coverage...")
    coverage = calculate_coverage()
    
    print("  Calculating explainability...")
    explainability = calculate_explainability()
    
    print("  Measuring latency (this may take a moment)...")
    latency = measure_latency(sample_size=10)
    
    print("  Calculating auditability...")
    auditability = calculate_auditability()
    
    print("  Calculating persona distribution...")
    persona_distribution = calculate_persona_distribution()
    
    evaluation_results = {
        "timestamp": datetime.now().isoformat(),
        "coverage": coverage,
        "explainability": explainability,
        "latency": latency,
        "auditability": auditability,
        "persona_distribution": persona_distribution
    }
    
    return evaluation_results


def generate_report_json(results: Dict[str, Any], output_path: Path) -> None:
    """Generate JSON evaluation report.
    
    Args:
        results: Evaluation results dictionary
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"JSON report saved to {output_path}")


def generate_summary_text(results: Dict[str, Any], output_path: Path) -> None:
    """Generate human-readable summary report.
    
    Args:
        results: Evaluation results dictionary
        output_path: Path to output text file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    coverage = results["coverage"]
    explainability = results["explainability"]
    latency = results["latency"]
    auditability = results["auditability"]
    persona_dist = results["persona_distribution"]
    
    summary_lines = [
        "=" * 70,
        "SpendSense Evaluation Report",
        "=" * 70,
        f"\nGenerated: {results['timestamp']}\n",
        "METRICS SUMMARY",
        "-" * 70,
        "",
        f"Coverage:",
        f"  Total Users: {coverage['total_users']}",
        f"  Users with Personas: {coverage['users_with_personas']} ({coverage['coverage_personas']}%)",
        f"  Users with 3+ Behaviors: {coverage['users_with_3plus_behaviors']} ({coverage['coverage_behaviors']}%)",
        "",
        f"Explainability:",
        f"  Total Recommendations: {explainability['total_recommendations']}",
        f"  With Rationales: {explainability['recommendations_with_rationales']} ({explainability['explainability_percentage']}%)",
        "",
        f"Latency:",
        f"  Sample Size: {latency['sample_size']} users",
        f"  Average: {latency['average_latency_ms']} ms",
        f"  Maximum: {latency['max_latency_ms']} ms",
        f"  P95: {latency['p95_latency_ms']} ms",
        "",
        f"Auditability:",
        f"  Total Recommendations: {auditability['total_recommendations']}",
        f"  With Decision Traces: {auditability['recommendations_with_traces']} ({auditability['auditability_percentage']}%)",
        "",
        f"Persona Distribution:",
        f"  Total Users: {persona_dist['total_users']}",
    ]
    
    for persona, data in persona_dist["distribution"].items():
        persona_display = persona.replace("_", " ").title()
        summary_lines.append(f"  {persona_display}: {data['count']} ({data['percentage']}%)")
    
    summary_lines.extend([
        "",
        "=" * 70,
        "TARGET METRICS",
        "-" * 70,
        "",
        "Target: Coverage >= 100%",
        f"Status: {'✓ PASS' if coverage['coverage_personas'] >= 100 else '✗ FAIL'}",
        "",
        "Target: Explainability >= 100%",
        f"Status: {'✓ PASS' if explainability['explainability_percentage'] >= 100 else '✗ FAIL'}",
        "",
        "Target: Latency < 5000ms per user",
        f"Status: {'✓ PASS' if latency['average_latency_ms'] < 5000 else '✗ FAIL'}",
        "",
        "Target: Auditability >= 100%",
        f"Status: {'✓ PASS' if auditability['auditability_percentage'] >= 100 else '✗ FAIL'}",
        "",
        "=" * 70
    ])
    
    summary_text = "\n".join(summary_lines)
    
    with open(output_path, 'w') as f:
        f.write(summary_text)
    
    print(f"Summary report saved to {output_path}")


def main():
    """Main function to run evaluation and generate reports."""
    print("Starting SpendSense evaluation...\n")
    
    # Ensure database schema is initialized
    db.init_schema()
    
    # Run evaluation
    results = run_evaluation()
    
    # Generate reports
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    json_path = results_dir / "evaluation_report.json"
    summary_path = results_dir / "summary.txt"
    
    generate_report_json(results, json_path)
    generate_summary_text(results, summary_path)
    
    print("\nEvaluation complete!")
    print(f"\nReports generated:")
    print(f"  JSON: {json_path}")
    print(f"  Summary: {summary_path}")


if __name__ == "__main__":
    main()

