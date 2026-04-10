import datetime
from typing import List, Dict, Any
import math


def predict_90_day_risks(files: List[Dict[str, Any]], components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Predict which components are most likely to cause failures or slowdowns in the next 90 days.
    Uses historical patterns to forecast future risks.
    """
    now = datetime.datetime.utcnow()
    ninety_days_ago = now - datetime.timedelta(days=90)

    # Analyze recent activity patterns
    recent_files = []
    for file in files:
        if isinstance(file, dict) and file.get('last_commit_date'):
            try:
                commit_date = datetime.datetime.fromisoformat(file['last_commit_date'])
                if commit_date > ninety_days_ago:
                    recent_files.append(file)
            except:
                pass

    # Calculate risk velocity (how risk is changing over time)
    predictions = []

    for component in components:
        if not isinstance(component, dict):
            continue

        try:
            matched_files = [f for f in files if isinstance(f, dict) and f.get('file_path') in (component.get('files', []) or [])]

            if not matched_files:
                continue

            # Calculate component risk metrics
            avg_risk = component.get('avg_risk', 0.0)
            avg_bug_resolution = sum(f.get('bug_resolution_rate', 0) for f in matched_files if isinstance(f, dict)) / max(1, len(matched_files))

            # Recent activity score (files touched in last 90 days)
            recent_activity = len([f for f in matched_files if f in recent_files]) / max(1, len(matched_files))

            # Complexity trend (higher complexity + recent changes = higher future risk)
            complexity_score = component.get('avg_complexity', 0) / 100.0  # Normalize

            # Predict 90-day failure probability
            # Formula: base risk + complexity factor + recent activity penalty - bug resolution bonus
            failure_probability = min(0.95, max(0.05,
                avg_risk * 0.4 +
                complexity_score * 0.3 +
                recent_activity * 0.2 -
                avg_bug_resolution * 0.1
            ))

            # Estimate business impact
            impact_score = failure_probability * component.get('avg_complexity', 0) * 0.1

            predictions.append({
                'component': component.get('component', 'Unknown'),
                'failure_probability': round(failure_probability * 100, 1),
                'business_impact_score': round(impact_score, 2),
                'risk_factors': {
                    'current_health': component.get('health_score', 0),
                    'complexity_score': round(complexity_score * 100, 1),
                    'recent_activity': round(recent_activity * 100, 1),
                    'bug_resolution_rate': round(avg_bug_resolution * 100, 1)
                },
                'recommendations': _generate_recommendations(component, failure_probability)
            })
        except Exception:
            continue

    # Sort by failure probability
    predictions.sort(key=lambda x: x['failure_probability'], reverse=True)

    return {
        'predictions': predictions,
        'summary': {
            'total_components_analyzed': len(components),
            'high_risk_components': len([p for p in predictions if p['failure_probability'] > 70]),
            'medium_risk_components': len([p for p in predictions if 40 <= p['failure_probability'] <= 70]),
            'low_risk_components': len([p for p in predictions if p['failure_probability'] < 40]),
            'total_predicted_impact': round(sum(p['business_impact_score'] for p in predictions), 2)
        }
    }


def _generate_recommendations(component: Dict[str, Any], failure_probability: float) -> List[str]:
    """Generate specific recommendations based on component analysis."""
    recommendations = []

    if failure_probability > 0.7:
        recommendations.append("URGENT: Immediate code review and testing required")
        recommendations.append("Consider refactoring high-complexity functions")
        recommendations.append("Implement additional monitoring and alerting")
    elif failure_probability > 0.4:
        recommendations.append("Schedule code review within next sprint")
        recommendations.append("Add comprehensive unit tests")
        recommendations.append("Monitor performance metrics closely")
    else:
        recommendations.append("Continue regular maintenance and monitoring")
        recommendations.append("Consider proactive refactoring opportunities")

    if isinstance(component, dict) and component.get('avg_complexity', 0) > 20:
        recommendations.append("Reduce cyclomatic complexity through function decomposition")

    if isinstance(component, dict) and component.get('avg_risk', 0) > 0.5:
        recommendations.append("Address identified risk factors in next development cycle")

    return recommendations


def estimate_cost_of_inaction(predictions: List[Dict[str, Any]], hourly_rate: float = 75.0) -> Dict[str, Any]:
    """
    Estimate the financial cost of inaction over 90 days.
    Based on predicted failures and their business impact.
    """
    total_impact_hours = 0

    for prediction in predictions:
        # Convert business impact score to estimated hours
        # Higher impact = more hours needed to fix
        impact_hours = prediction['business_impact_score'] * 8  # 8 hours per impact point
        total_impact_hours += impact_hours

    # Calculate costs
    developer_cost = total_impact_hours * hourly_rate
    overhead_cost = developer_cost * 0.3  # 30% overhead
    total_cost = developer_cost + overhead_cost

    return {
        'estimated_hours': round(total_impact_hours, 1),
        'developer_cost': round(developer_cost, 2),
        'overhead_cost': round(overhead_cost, 2),
        'total_cost': round(total_cost, 2),
        'hourly_rate_used': hourly_rate,
        'cost_breakdown': {
            'prevention_savings': round(total_cost * 0.6, 2),  # 60% could be prevented
            'detection_cost': round(total_cost * 0.2, 2),      # 20% for detection
            'recovery_cost': round(total_cost * 0.2, 2)        # 20% for recovery
        }
    }