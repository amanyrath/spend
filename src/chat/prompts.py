"""System prompts for chat functionality."""

from typing import List, Dict, Any, Optional

from src.utils.category_utils import get_primary_category
from src.chat.transaction_analysis import (
    calculate_weekday_spending,
    calculate_monthly_progression,
    calculate_spending_velocity,
    build_detailed_category_analysis,
    analyze_merchant_patterns,
    analyze_payment_channels,
    analyze_by_account,
    analyze_pending_transactions
)

SYSTEM_PROMPT = """You are a helpful financial education assistant for SpendSense. Your role is to provide educational information about users' financial data, NOT financial advice.

CRITICAL GUIDELINES:
1. EDUCATIONAL ONLY: Provide information and insights about financial data. Never give specific financial advice (e.g., "you should invest in X" or "you should pay off Y debt first").
2. NO SHAMING: Use neutral, supportive language. Never use judgmental phrases like "overspending", "bad habits", "poor choices", "irresponsible", or "wasteful".
3. DATA CITATIONS: Always cite specific data points from the user's financial information when making statements. Use exact numbers, percentages, and account details.
4. POSITIVE TONE: Frame insights constructively. Focus on patterns and opportunities rather than problems.
5. TEMPORAL AWARENESS: When discussing spending patterns, reference time periods and trends (e.g., weekday vs weekend, month-to-date progress).
6. PAYMENT CHANNELS: Acknowledge differences in online vs in-store spending when relevant.
7. PENDING TRANSACTIONS: Be aware of pending transactions that will impact future balances.
8. DISCLAIMER: Always end responses with: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."

RESPONSE FORMAT:
- Be concise and clear
- Use bullet points for multiple insights
- Highlight specific data points (e.g., "Your Visa ending in 4523 shows 65% utilization")
- Include relevant context from their financial profile
- Reference temporal patterns when discussing spending behavior
- Mention payment channel preferences when relevant

EXAMPLE RESPONSES:
Good: "Based on your recent transactions, you have 3 recurring subscriptions totaling $47/month: Netflix ($15), Spotify ($10), and Adobe ($22). This represents about 3% of your monthly income."
Bad: "You're overspending on subscriptions. You should cancel some of these wasteful services."

Good: "Your spending this month is trending 15% higher than the first half of the month, with weekend spending averaging $85 compared to $62 on weekdays."
Bad: "You have bad spending habits on weekends."

Remember: Your goal is education and awareness, not judgment or advice.
"""


def build_user_context(
    user_features: dict,
    recent_transactions: list,
    persona: dict = None,
    user_accounts: List[Dict[str, Any]] = None,
    transaction_window_days: int = 30
) -> str:
    """Build user context string for LLM prompt.
    
    Args:
        user_features: User's computed features from get_user_features()
        recent_transactions: List of recent transactions
        persona: User's persona assignment (optional)
        user_accounts: List of user account dictionaries (optional)
        transaction_window_days: Number of days in transaction window
        
    Returns:
        Formatted context string for LLM
    """
    context_parts = []
    user_accounts = user_accounts or []
    
    # Add time window context
    context_parts.append(f"Transaction Window: Last {transaction_window_days} days ({len(recent_transactions)} transactions)")
    
    # Add persona information if available
    if persona:
        if isinstance(persona, dict):
            persona_name = persona.get('persona', 'Unknown')
        elif isinstance(persona, str):
            persona_name = persona
        else:
            persona_name = 'Unknown'
        context_parts.append(f"\nUser Persona: {persona_name}")
    
    # Add temporal spending patterns
    if recent_transactions:
        weekday_analysis = calculate_weekday_spending(recent_transactions)
        if weekday_analysis['weekday_count'] > 0 or weekday_analysis['weekend_count'] > 0:
            context_parts.append("\nSpending Patterns:")
            if weekday_analysis['weekday_count'] > 0:
                context_parts.append(
                    f"  - Weekday: {weekday_analysis['weekday_count']} transactions, "
                    f"${weekday_analysis['weekday_total']:.2f} total (avg ${weekday_analysis['weekday_avg']:.2f})"
                )
            if weekday_analysis['weekend_count'] > 0:
                context_parts.append(
                    f"  - Weekend: {weekday_analysis['weekend_count']} transactions, "
                    f"${weekday_analysis['weekend_total']:.2f} total (avg ${weekday_analysis['weekend_avg']:.2f})"
                )
            if weekday_analysis['highest_day'] != 'Unknown':
                context_parts.append(
                    f"  - Highest spending day: {weekday_analysis['highest_day']} "
                    f"(${weekday_analysis['highest_day_total']:.2f})"
                )
        
        # Add month-to-date progression
        mtd_analysis = calculate_monthly_progression(recent_transactions)
        if mtd_analysis['spent_mtd'] > 0:
            context_parts.append(f"\nMonth-to-Date ({mtd_analysis['current_month']}):")
            context_parts.append(
                f"  - Spent so far: ${mtd_analysis['spent_mtd']:.2f} "
                f"({mtd_analysis['transaction_count_mtd']} transactions)"
            )
            context_parts.append(
                f"  - Daily average: ${mtd_analysis['daily_avg']:.2f} "
                f"({mtd_analysis['days_elapsed']} days elapsed, {mtd_analysis['days_remaining']} remaining)"
            )
            context_parts.append(f"  - Projected monthly: ${mtd_analysis['projected_monthly']:.2f}")
        
        # Add spending velocity/trend
        if transaction_window_days >= 14:  # Only show trend for longer windows
            velocity = calculate_spending_velocity(recent_transactions, transaction_window_days)
            if velocity['trend'] != 'stable':
                context_parts.append(f"\nSpending Trend: {velocity['trend'].title()}")
                context_parts.append(
                    f"  - First half: ${velocity['first_half_spending']:.2f}, "
                    f"Second half: ${velocity['second_half_spending']:.2f} "
                    f"({velocity['change_pct']:+.1f}%)"
                )
    
    # Add feature summaries
    if user_features.get('credit_utilization'):
        cu = user_features['credit_utilization']
        if cu.get('accounts'):
            context_parts.append("\nCredit Utilization:")
            for acc in cu['accounts']:
                utilization_pct = round(acc.get('utilization', 0) * 100, 1)
                context_parts.append(
                    f"  - {acc.get('account_mask', 'Account')}: {utilization_pct}% "
                    f"(${acc.get('balance', 0):.2f} of ${acc.get('limit', 0):.2f})"
                )
    
    if user_features.get('subscriptions'):
        subs = user_features['subscriptions']
        monthly_total = subs.get('monthly_recurring', 0)
        if monthly_total > 0:
            context_parts.append(f"\nRecurring Subscriptions: ${monthly_total:.2f}/month")
            for merchant in subs.get('recurring_merchants', [])[:5]:
                context_parts.append(
                    f"  - {merchant.get('merchant', 'Unknown')}: ${merchant.get('amount', 0):.2f}/month"
                )
    
    if user_features.get('savings_behavior'):
        sb = user_features['savings_behavior']
        avg_income = sb.get('avg_monthly_income', 0)
        avg_expenses = sb.get('avg_monthly_expenses', 0)
        if avg_income > 0:
            savings_rate = ((avg_income - avg_expenses) / avg_income) * 100
            context_parts.append(
                f"\nSavings Behavior: Average monthly income ${avg_income:.2f}, "
                f"expenses ${avg_expenses:.2f} (savings rate: {savings_rate:.1f}%)"
            )
    
    # Add detailed category breakdown
    if recent_transactions:
        category_analysis = build_detailed_category_analysis(recent_transactions)
        if category_analysis:
            context_parts.append("\nSpending by Category:")
            for cat in category_analysis[:5]:  # Top 5 categories
                context_parts.append(
                    f"  - {cat['category']}: ${cat['amount']:.2f} ({cat['percentage']:.1f}%) - "
                    f"{cat['transaction_count']} transactions (avg ${cat['avg_transaction']:.2f})"
                )
        
        # Add payment channel analysis
        channel_analysis = analyze_payment_channels(recent_transactions)
        if channel_analysis:
            context_parts.append("\nPayment Channels:")
            for channel, data in channel_analysis.items():
                if data['count'] > 0:
                    context_parts.append(
                        f"  - {channel.replace('_', ' ').title()}: {data['count']} transactions, "
                        f"${data['amount']:.2f}"
                    )
        
        # Add frequent merchant analysis
        frequent_merchants = analyze_merchant_patterns(recent_transactions)
        if frequent_merchants:
            context_parts.append("\nFrequent Merchants (3+ visits):")
            for merchant, data in frequent_merchants:
                avg_per_visit = data['total_spent'] / data['visit_count']
                context_parts.append(
                    f"  - {merchant}: {data['visit_count']} visits, "
                    f"${data['total_spent']:.2f} total (avg ${avg_per_visit:.2f} per visit)"
                )
        
        # Add pending transaction analysis
        pending_analysis = analyze_pending_transactions(recent_transactions)
        if pending_analysis['count'] > 0:
            context_parts.append(f"\nPending Transactions:")
            context_parts.append(f"  - Count: {pending_analysis['count']}")
            if pending_analysis['pending_charges'] > 0:
                context_parts.append(f"  - Pending charges: ${pending_analysis['pending_charges']:.2f}")
            if pending_analysis['pending_deposits'] > 0:
                context_parts.append(f"  - Pending deposits: ${pending_analysis['pending_deposits']:.2f}")
            context_parts.append(f"  - Net pending: ${pending_analysis['net_pending']:.2f}")
        
        # Add account-specific activity
        if user_accounts:
            account_activity = analyze_by_account(recent_transactions, user_accounts)
            if account_activity:
                context_parts.append("\nAccount Activity:")
                for account_id, activity in account_activity.items():
                    mask_display = f"ending in {activity['mask']}" if activity['mask'] != 'Unknown' else activity['mask']
                    context_parts.append(
                        f"  - {activity['subtype'].title()} {mask_display}: "
                        f"{activity['transaction_count']} transactions, "
                        f"${activity['total_spent']:.2f} spent"
                    )
                    if activity['total_income'] > 0:
                        context_parts[-1] += f", ${activity['total_income']:.2f} deposited"
    
    return "\n".join(context_parts) if context_parts else "No financial data available."

