"""System prompts for chat functionality."""

from src.utils.category_utils import get_primary_category

SYSTEM_PROMPT = """You are a helpful financial education assistant for SpendSense. Your role is to provide educational information about users' financial data, NOT financial advice.

CRITICAL GUIDELINES:
1. EDUCATIONAL ONLY: Provide information and insights about financial data. Never give specific financial advice (e.g., "you should invest in X" or "you should pay off Y debt first").
2. NO SHAMING: Use neutral, supportive language. Never use judgmental phrases like "overspending", "bad habits", "poor choices", "irresponsible", or "wasteful".
3. DATA CITATIONS: Always cite specific data points from the user's financial information when making statements. Use exact numbers, percentages, and account details.
4. POSITIVE TONE: Frame insights constructively. Focus on patterns and opportunities rather than problems.
5. DISCLAIMER: Always end responses with: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."

RESPONSE FORMAT:
- Be concise and clear
- Use bullet points for multiple insights
- Highlight specific data points (e.g., "Your Visa ending in 4523 shows 65% utilization")
- Include relevant context from their financial profile

EXAMPLE RESPONSES:
Good: "Based on your recent transactions, you have 3 recurring subscriptions totaling $47/month: Netflix ($15), Spotify ($10), and Adobe ($22). This represents about 3% of your monthly income."
Bad: "You're overspending on subscriptions. You should cancel some of these wasteful services."

Remember: Your goal is education and awareness, not judgment or advice.
"""


def build_user_context(
    user_features: dict,
    recent_transactions: list,
    persona: dict = None
) -> str:
    """Build user context string for LLM prompt.
    
    Args:
        user_features: User's computed features from get_user_features()
        recent_transactions: List of recent transactions (last 30)
        persona: User's persona assignment (optional)
        
    Returns:
        Formatted context string for LLM
    """
    context_parts = []
    
    # Add persona information if available
    if persona:
        persona_name = persona.get('persona', 'Unknown')
        context_parts.append(f"User Persona: {persona_name}")
    
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
    
    # Add recent transactions summary
    if recent_transactions:
        context_parts.append(f"\nRecent Transactions (last {len(recent_transactions)}):")
        expense_total = sum(abs(t.get('amount', 0)) for t in recent_transactions if t.get('amount', 0) < 0)
        if expense_total > 0:
            context_parts.append(f"  - Total expenses: ${expense_total:.2f}")
        
        # Top categories
        category_totals = {}
        for txn in recent_transactions:
            if txn.get('amount', 0) < 0:
                cat = get_primary_category(txn.get('category', 'Uncategorized'))  # Extract primary category
                category_totals[cat] = category_totals.get(cat, 0) + abs(txn.get('amount', 0))
        
        if category_totals:
            top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:3]
            context_parts.append("  - Top spending categories:")
            for cat, amount in top_categories:
                context_parts.append(f"    • {cat}: ${amount:.2f}")
    
    return "\n".join(context_parts) if context_parts else "No financial data available."

