"""Content catalog for SpendSense recommendations.

This module defines the education content and partner offers that can be
recommended to users based on their personas and behavioral signals.
"""

from typing import Dict, List, Any, Optional

# Education content items
EDUCATION_CONTENT: List[Dict[str, Any]] = [
    # High Utilization Persona (5 items)
    {
        "content_id": "edu_credit_util_101",
        "type": "education",
        "title": "Understanding Credit Utilization",
        "category": "credit",
        "personas": ["high_utilization"],
        "trigger_signals": ["credit_utilization_high"],
        "summary": "Learn why keeping credit card balances low improves your credit score and reduces interest costs.",
        "full_content": """Credit utilization is the ratio of your current credit card balances to your credit limits. 
        It's a key factor in your credit score calculation. Keeping your utilization below 30% is ideal, 
        as higher utilization can signal financial stress to lenders and negatively impact your score. 
        Lower utilization also means less interest charges over time.""",
        "rationale_template": "Your {card_name} is at {utilization}% utilization ({balance} of {limit} limit). Bringing this below 30% could improve your credit score and reduce interest charges."
    },
    {
        "content_id": "edu_minimum_payments_101",
        "type": "education",
        "title": "The Real Cost of Minimum Payments",
        "category": "credit",
        "personas": ["high_utilization"],
        "trigger_signals": ["minimum_payment_only", "interest_charged"],
        "summary": "Understand how making only minimum payments extends your debt timeline and increases total interest paid.",
        "full_content": """Making only minimum payments on credit cards can keep you in debt for years. 
        While it may seem manageable, the interest charges accumulate quickly. For example, a $5,000 balance 
        at 18% APR with minimum payments could take over 15 years to pay off and cost thousands in interest. 
        Paying even slightly more than the minimum can dramatically reduce both time and interest costs.""",
        "rationale_template": "You're currently paying ${interest_charged} per month in interest on your credit cards. Increasing your payment amount could save you significant money over time."
    },
    {
        "content_id": "edu_debt_strategies_101",
        "type": "education",
        "title": "Debt Avalanche vs. Debt Snowball",
        "category": "credit",
        "personas": ["high_utilization"],
        "trigger_signals": ["credit_utilization_high"],
        "summary": "Compare two popular debt payoff strategies and choose the one that works best for your situation.",
        "full_content": """Two common strategies for paying down debt are the Debt Avalanche and Debt Snowball methods.
        The Debt Avalanche focuses on paying off debts with the highest interest rates first, saving the most money overall.
        The Debt Snowball method focuses on paying off the smallest balances first for psychological wins.
        Both methods work - choose based on whether you're motivated by saving money or seeing quick progress.""",
        "rationale_template": "With {utilization}% utilization across your credit cards, a structured payoff plan could help you reduce debt more efficiently."
    },
    {
        "content_id": "edu_autopay_setup_101",
        "type": "education",
        "title": "How to Set Up Autopay",
        "category": "credit",
        "personas": ["high_utilization"],
        "trigger_signals": ["is_overdue", "minimum_payment_only"],
        "summary": "Learn how to set up autopay to avoid late fees and protect your credit score.",
        "full_content": """Autopay is a simple way to ensure you never miss a credit card payment. 
        You can set it up to pay the minimum amount, the full balance, or a fixed amount each month.
        Setting up autopay helps you avoid late fees, protect your credit score, and gives you peace of mind.
        Most banks and credit card companies offer this feature through their online portal or mobile app.""",
        "rationale_template": "Setting up autopay on your credit cards can help ensure you never miss a payment and avoid late fees."
    },
    {
        "content_id": "edu_debt_paydown_plan_101",
        "type": "education",
        "title": "Building a Debt Paydown Plan",
        "category": "credit",
        "personas": ["high_utilization"],
        "trigger_signals": ["credit_utilization_high"],
        "summary": "Create a step-by-step plan to pay down your credit card debt systematically.",
        "full_content": """A structured debt paydown plan starts with understanding your full financial picture.
        List all your debts, their balances, interest rates, and minimum payments. Then create a budget 
        that allocates extra money toward debt repayment. Consider consolidating high-interest debts or 
        transferring balances to lower-rate cards. Track your progress monthly and adjust as needed.""",
        "rationale_template": "With {total_balance} in credit card debt, a structured paydown plan could help you become debt-free faster."
    },
    
    # Variable Income Persona (3 items)
    {
        "content_id": "edu_irregular_income_budgeting_101",
        "type": "education",
        "title": "Budgeting with Irregular Income",
        "category": "budgeting",
        "personas": ["variable_income"],
        "trigger_signals": ["irregular_frequency", "median_pay_gap_high"],
        "summary": "Learn budgeting strategies tailored for freelancers, contractors, and others with variable income.",
        "full_content": """Budgeting with irregular income requires a different approach than traditional monthly budgeting.
        Start by calculating your average monthly income over the past 6-12 months. Then build your budget 
        based on your lowest expected income month. During higher-income months, prioritize building an 
        emergency fund and paying down debt. Use percentage-based budgeting where expenses are allocated 
        as percentages of income rather than fixed dollar amounts.""",
        "rationale_template": "With {median_pay_gap} days between paychecks and a {cash_flow_buffer}-month cash buffer, budgeting strategies for irregular income could help you manage cash flow better."
    },
    {
        "content_id": "edu_cash_flow_buffer_101",
        "type": "education",
        "title": "Building a Cash-Flow Buffer",
        "category": "savings",
        "personas": ["variable_income"],
        "trigger_signals": ["cash_flow_buffer_low"],
        "summary": "Why having a cash buffer matters for those with irregular income, and how to build one.",
        "full_content": """A cash-flow buffer is money set aside to cover expenses during months when income is lower than expected.
        For people with irregular income, a buffer of 2-3 months of expenses is ideal. This buffer acts as 
        a bridge between high and low income months. Start by saving a small amount from each paycheck, 
        even if it's just $50-100. Automate transfers to a separate savings account to make it easier.
        Once you have a buffer, you can smooth out income fluctuations without relying on credit.""",
        "rationale_template": "Your current cash buffer covers {cash_flow_buffer} months of expenses. Building this to 2-3 months could provide more stability during income fluctuations."
    },
    {
        "content_id": "edu_503020_rule_adapted_101",
        "type": "education",
        "title": "The 50/30/20 Rule (Adapted)",
        "category": "budgeting",
        "personas": ["variable_income"],
        "trigger_signals": ["irregular_frequency"],
        "summary": "Adapt the popular 50/30/20 budgeting rule for variable income situations.",
        "full_content": """The 50/30/20 rule allocates 50% of income to needs, 30% to wants, and 20% to savings.
        For variable income, adapt this by calculating percentages based on your average monthly income.
        During high-income months, allocate extra to savings and debt repayment. During low-income months,
        prioritize needs and reduce wants. The key is maintaining flexibility while keeping overall spending 
        aligned with your average income.""",
        "rationale_template": "With irregular income patterns, a flexible budgeting approach like the adapted 50/30/20 rule could help you manage expenses more effectively."
    },
    
    # Subscription-Heavy Persona (4 items)
    {
        "content_id": "edu_subscription_audit_101",
        "type": "education",
        "title": "The $200 Question: Are You Using All Your Subscriptions?",
        "category": "spending",
        "personas": ["subscription_heavy"],
        "trigger_signals": ["subscription_count_high", "monthly_recurring_high"],
        "summary": "A practical guide to auditing your subscriptions and identifying which ones you actually use.",
        "full_content": """Many people pay for subscriptions they rarely or never use. Start by listing all your 
        recurring subscriptions - streaming services, gym memberships, software subscriptions, etc. 
        Track your usage for a month to see which ones you actually use. Cancel unused subscriptions immediately.
        For partially used subscriptions, consider if you could share accounts with family or switch to a lower tier.
        Even small monthly charges add up to hundreds of dollars per year.""",
        "rationale_template": "You have {subscription_count} active subscriptions totaling ${monthly_recurring} per month. Reviewing which ones you actually use could free up money for other goals."
    },
    {
        "content_id": "edu_negotiate_bills_101",
        "type": "education",
        "title": "How to Negotiate Lower Bills",
        "category": "spending",
        "personas": ["subscription_heavy"],
        "trigger_signals": ["monthly_recurring_high"],
        "summary": "Learn negotiation tactics to reduce your monthly subscription and service bills.",
        "full_content": """Many subscription and service providers will negotiate lower rates if you ask, especially 
        if you're a long-time customer or threaten to cancel. Call customer service and mention competitors' 
        lower prices. Be polite but firm. Ask for retention offers or promotional rates. If they won't budge,
        cancel and wait for a win-back offer. Bundle services when possible for discounts. 
        Set calendar reminders to renegotiate annually.""",
        "rationale_template": "With ${monthly_recurring} in monthly subscriptions, negotiating lower rates could save you significant money each year."
    },
    {
        "content_id": "edu_subscription_cancellation_101",
        "type": "education",
        "title": "Subscription Cancellation Made Easy",
        "category": "spending",
        "personas": ["subscription_heavy"],
        "trigger_signals": ["subscription_count_high"],
        "summary": "Step-by-step guide to canceling subscriptions without hassle.",
        "full_content": """Canceling subscriptions can feel overwhelming, but it's usually straightforward. 
        Most services allow cancellation through their website or app. Look for Account Settings or 
        Subscription Management. Some services require calling customer service - be persistent.
        For services that make cancellation difficult, consider using a virtual credit card number that 
        you can cancel without affecting your main card. Keep a list of all subscriptions and their 
        cancellation dates to avoid being charged unexpectedly.""",
        "rationale_template": "You have {subscription_count} active subscriptions. Canceling unused ones could free up ${monthly_recurring} per month for other priorities."
    },
    {
        "content_id": "edu_bill_alerts_101",
        "type": "education",
        "title": "Setting Up Bill Alerts",
        "category": "spending",
        "personas": ["subscription_heavy"],
        "trigger_signals": ["subscription_count_high"],
        "summary": "Use automated alerts to track subscription renewals and avoid surprise charges.",
        "full_content": """Bill alerts help you stay on top of subscription charges and catch price increases early.
        Set up alerts in your bank's mobile app for recurring charges. Use calendar reminders for annual 
        subscriptions. Some apps can track all your subscriptions and alert you before renewals.
        Review your credit card statements monthly to catch any forgotten subscriptions. 
        Early detection of price increases gives you time to negotiate or cancel before being charged.""",
        "rationale_template": "With {subscription_count} active subscriptions, setting up alerts can help you track charges and catch any unexpected price increases."
    },
    
    # Savings Builder Persona (3 items)
    {
        "content_id": "edu_savings_to_investing_101",
        "type": "education",
        "title": "From Savings to Investing: When Are You Ready?",
        "category": "investing",
        "personas": ["savings_builder"],
        "trigger_signals": ["savings_growth_rate_positive", "emergency_fund_adequate"],
        "summary": "Learn when you've saved enough to start investing and how to begin.",
        "full_content": """Before investing, ensure you have an emergency fund of 3-6 months of expenses 
        and no high-interest debt. Once those foundations are in place, you can start investing.
        Start with low-cost index funds or ETFs through a robo-advisor or brokerage account.
        Consider employer-sponsored retirement accounts first, especially if they offer matching contributions.
        Automate investments to build the habit, even if it's just $50-100 per month initially.""",
        "rationale_template": "Your savings have grown by {growth_rate}% over the past 6 months. With an adequate emergency fund, you might be ready to start investing for longer-term goals."
    },
    {
        "content_id": "edu_hysa_explained_101",
        "type": "education",
        "title": "High-Yield Savings Accounts Explained",
        "category": "savings",
        "personas": ["savings_builder"],
        "trigger_signals": ["savings_balance_positive"],
        "summary": "Understand how high-yield savings accounts work and why they're better than traditional savings.",
        "full_content": """High-yield savings accounts (HYSAs) offer interest rates significantly higher than 
        traditional savings accounts - often 4-5% APY compared to 0.01-0.05%. They're FDIC insured up to $250,000,
        so your money is safe. Most HYSAs are online-only, which allows them to offer better rates.
        There are usually no monthly fees or minimum balance requirements. Your money remains liquid and 
        accessible, making HYSAs ideal for emergency funds and short-term savings goals.""",
        "rationale_template": "With ${total_savings} in savings, moving your money to a high-yield savings account could earn you significantly more interest."
    },
    {
        "content_id": "edu_smart_financial_goals_101",
        "type": "education",
        "title": "Setting SMART Financial Goals",
        "category": "planning",
        "personas": ["savings_builder"],
        "trigger_signals": ["savings_growth_rate_positive"],
        "summary": "Learn the SMART framework for setting and achieving meaningful financial goals.",
        "full_content": """SMART goals are Specific, Measurable, Achievable, Relevant, and Time-bound.
        Instead of 'save more money,' try 'Save $5,000 for a down payment in 12 months by saving $417 per month.'
        Break large goals into smaller milestones. Track progress monthly and adjust as needed.
        Celebrate small wins along the way. Having clear, specific goals makes it easier to stay motivated 
        and make financial decisions that align with your priorities.""",
        "rationale_template": "Your savings are growing at {growth_rate}% per month. Setting specific financial goals could help you direct this progress toward your priorities."
    },
    
    # General Wellness Persona (5 items)
    {
        "content_id": "edu_budgeting_basics_101",
        "type": "education",
        "title": "Budgeting Basics: Your First Budget",
        "category": "budgeting",
        "personas": ["general_wellness"],
        "trigger_signals": [],
        "summary": "Learn the fundamentals of creating and sticking to a budget that works for your lifestyle.",
        "full_content": """A budget is simply a plan for your money. Start by tracking your income and expenses 
        for one month to understand where your money goes. Then create categories for needs (housing, food, 
        utilities), wants (entertainment, dining out), and savings/debt repayment. Use the 50/30/20 rule as 
        a starting point: 50% needs, 30% wants, 20% savings and debt. Review and adjust your budget monthly 
        to reflect changes in income or expenses. Remember, a budget is a tool to help you reach your goals, 
        not a restriction.""",
        "rationale_template": "Creating a budget can help you gain clarity on your spending and make progress toward your financial goals."
    },
    {
        "content_id": "edu_emergency_fund_101",
        "type": "education",
        "title": "Building Your Emergency Fund",
        "category": "savings",
        "personas": ["general_wellness"],
        "trigger_signals": [],
        "summary": "Why an emergency fund is essential and how to build one, even on a tight budget.",
        "full_content": """An emergency fund is money set aside to cover unexpected expenses like medical bills, 
        car repairs, or job loss. Most experts recommend saving 3-6 months of expenses, but start with 
        $1,000 as a first goal. Build it gradually by setting aside a small amount each month, even if it's 
        just $25-50. Keep your emergency fund in a separate savings account so you're not tempted to spend it.
        Only use it for true emergencies. Having this buffer provides peace of mind and prevents you from 
        going into debt when unexpected expenses arise.""",
        "rationale_template": "Building an emergency fund provides a financial safety net and can help you avoid debt when unexpected expenses occur."
    },
    {
        "content_id": "edu_credit_score_basics_101",
        "type": "education",
        "title": "Understanding Your Credit Score",
        "category": "credit",
        "personas": ["general_wellness"],
        "trigger_signals": [],
        "summary": "Learn what factors affect your credit score and how to improve it over time.",
        "full_content": """Your credit score is a three-digit number that lenders use to assess your creditworthiness.
        The main factors are payment history (35%), credit utilization (30%), length of credit history (15%), 
        credit mix (10%), and new credit inquiries (10%). To improve your score, pay all bills on time, 
        keep credit card balances low, avoid opening too many new accounts, and maintain a mix of credit types.
        Check your credit report regularly for errors. Building good credit takes time, but consistent 
        responsible behavior will improve your score over months and years.""",
        "rationale_template": "Understanding how credit scores work can help you build and maintain good credit, which opens doors to better financial opportunities."
    },
    {
        "content_id": "edu_banking_basics_101",
        "type": "education",
        "title": "Banking Basics: Choosing the Right Accounts",
        "category": "banking",
        "personas": ["general_wellness"],
        "trigger_signals": [],
        "summary": "Learn about different types of bank accounts and how to choose the right ones for your needs.",
        "full_content": """Different bank accounts serve different purposes. Checking accounts are for daily 
        transactions and bill payments. Savings accounts earn interest but have withdrawal limits. High-yield 
        savings accounts offer better rates but are often online-only. Money market accounts combine features 
        of both. When choosing accounts, consider fees, minimum balance requirements, interest rates, and 
        accessibility. Many online banks offer better rates and lower fees than traditional banks. 
        Look for accounts with no monthly maintenance fees and features like mobile banking and ATM access.""",
        "rationale_template": "Choosing the right bank accounts can help you save money on fees and earn more interest on your savings."
    },
    {
        "content_id": "edu_financial_health_check_101",
        "type": "education",
        "title": "Monthly Financial Health Check",
        "category": "planning",
        "personas": ["general_wellness"],
        "trigger_signals": [],
        "summary": "A simple monthly checklist to review and improve your financial health.",
        "full_content": """A monthly financial health check helps you stay on track with your goals. 
        Review your spending to see if it aligns with your budget. Check your account balances and ensure 
        you're not overdrafting. Review any recurring subscriptions or bills to see if you can reduce costs.
        Check your credit card statements for any unauthorized charges. Update your budget if income or 
        expenses have changed. Review progress toward savings goals. This monthly check-in takes just 15-20 
        minutes but helps you catch issues early and stay focused on your financial goals.""",
        "rationale_template": "Regular financial check-ins help you stay aware of your money and make adjustments before small issues become big problems."
    }
]

# Partner offer items
PARTNER_OFFERS: List[Dict[str, Any]] = [
    {
        "offer_id": "offer_balance_transfer",
        "type": "partner_offer",
        "title": "0% APR Balance Transfer Credit Card",
        "partner": "Example Bank",
        "summary": "Transfer high-interest balances and save on interest for 18 months with 0% APR.",
        "eligibility_criteria": {
            "credit_utilization": {"min": 0.5},
            "is_overdue": {"equals": False},
            "min_credit_score": 670
        },
        "rationale_template": "You're currently paying ${interest_charged} per month in interest. This card could help you save on interest while you pay down your balance."
    },
    {
        "offer_id": "offer_hysa",
        "type": "partner_offer",
        "title": "High-Yield Savings Account (4.5% APY)",
        "partner": "Example Savings Bank",
        "summary": "Earn 4.5% APY on your savings with no monthly fees or minimum balance requirements.",
        "eligibility_criteria": {
            "savings_balance": {"min": 100}
        },
        "rationale_template": "Your current savings account earns minimal interest. A high-yield savings account could help your ${total_savings} grow faster."
    },
    {
        "offer_id": "offer_budgeting_app",
        "type": "partner_offer",
        "title": "Budgeting App (Mint Alternative)",
        "partner": "Example Budgeting Co",
        "summary": "Track spending, set budgets, and get insights into your financial habits with our budgeting app.",
        "eligibility_criteria": {},
        "rationale_template": "This budgeting app could help you track your spending and identify opportunities to save more."
    },
    {
        "offer_id": "offer_subscription_manager",
        "type": "partner_offer",
        "title": "Subscription Management Tool",
        "partner": "Example Subscription Co",
        "summary": "Track all your subscriptions in one place, get renewal reminders, and find easy cancellation links.",
        "eligibility_criteria": {
            "subscription_count": {"min": 3}
        },
        "rationale_template": "With {subscription_count} active subscriptions, a subscription management tool could help you track and optimize your recurring expenses."
    },
    {
        "offer_id": "offer_credit_monitoring",
        "type": "partner_offer",
        "title": "Credit Monitoring Service",
        "partner": "Example Credit Co",
        "summary": "Monitor your credit score and get alerts for changes to your credit report.",
        "eligibility_criteria": {},
        "rationale_template": "Credit monitoring can help you track your credit score improvements as you work on your financial goals."
    },
    {
        "offer_id": "offer_financial_planning",
        "type": "partner_offer",
        "title": "Financial Planning Consultation",
        "partner": "Example Financial Advisors",
        "summary": "Get personalized financial advice from certified financial planners to help you reach your goals.",
        "eligibility_criteria": {},
        "rationale_template": "A financial planning consultation could help you create a comprehensive plan tailored to your specific situation."
    },
    {
        "offer_id": "offer_debt_consolidation",
        "type": "partner_offer",
        "title": "Debt Consolidation Loan",
        "partner": "Example Lending Co",
        "summary": "Consolidate multiple high-interest debts into a single lower-rate loan with one monthly payment.",
        "eligibility_criteria": {
            "credit_utilization": {"min": 0.4},
            "is_overdue": {"equals": False}
        },
        "rationale_template": "Consolidating your ${total_balance} in credit card debt into a single loan could simplify payments and potentially reduce your interest rate."
    },
    {
        "offer_id": "offer_cashback_card",
        "type": "partner_offer",
        "title": "Cashback Credit Card",
        "partner": "Example Rewards Bank",
        "summary": "Earn cashback on everyday purchases with no annual fee.",
        "eligibility_criteria": {
            "credit_utilization": {"max": 0.7},
            "is_overdue": {"equals": False}
        },
        "rationale_template": "A cashback credit card could help you earn rewards on your regular spending while you manage your finances."
    },
    {
        "offer_id": "offer_emergency_fund_savings",
        "type": "partner_offer",
        "title": "Emergency Fund Savings Account",
        "partner": "Example Emergency Savings Bank",
        "summary": "Start building your emergency fund with automatic transfers and bonus interest.",
        "eligibility_criteria": {},
        "rationale_template": "Building an emergency fund provides financial security. This account makes it easy to save automatically."
    },
    {
        "offer_id": "offer_round_up_savings",
        "type": "partner_offer",
        "title": "Round-Up Savings App",
        "partner": "Example Savings Tech",
        "summary": "Automatically save spare change by rounding up purchases to the nearest dollar.",
        "eligibility_criteria": {},
        "rationale_template": "Round-up savings can help you build savings effortlessly by automatically setting aside small amounts from each purchase."
    },
    {
        "offer_id": "offer_automated_investing",
        "type": "partner_offer",
        "title": "Automated Investing Platform",
        "partner": "Example Robo-Advisor",
        "summary": "Start investing with as little as $5. Automated portfolio management with low fees.",
        "eligibility_criteria": {
            "savings_balance": {"min": 1000}
        },
        "rationale_template": "With your savings growing, automated investing could help you start building long-term wealth with minimal effort."
    },
    {
        "offer_id": "offer_bill_negotiation_service",
        "type": "partner_offer",
        "title": "Bill Negotiation Service",
        "partner": "Example Bill Negotiators",
        "summary": "Professional negotiators work to lower your monthly bills and subscriptions.",
        "eligibility_criteria": {
            "monthly_recurring": {"min": 50}
        },
        "rationale_template": "A bill negotiation service could help you reduce your monthly expenses by negotiating better rates on your behalf."
    },
    # Credit offer products from credit offers API
    {
        "offer_id": "BT-001",
        "type": "partner_offer",
        "title": "Platinum Balance Transfer Card",
        "partner": "Credit Partner",
        "summary": "0% intro APR on balance transfers for 18 months. No annual fee - save money while paying down debt.",
        "eligibility_criteria": {
            "credit_utilization": {"max": 0.85},
            "is_overdue": {"equals": False}
        },
        "rationale_template": "You're currently paying ${interest_charged} per month in interest. This card could help you save on interest while you pay down your balance.",
        "credit_metadata": {
            "tier": "PREMIUM",
            "intro_purchase_apr": "0% for 12 months",
            "purchase_apr": "16.99% - 24.99% variable",
            "intro_balance_transfer_apr": "0% for 18 months",
            "balance_transfer_fee": "3% of transfer amount",
            "annual_fee": "$0"
        }
    },
    {
        "offer_id": "SEC-001",
        "type": "partner_offer",
        "title": "Credit Builder Secured Card",
        "partner": "Credit Partner",
        "summary": "Build credit with responsible use. Security deposit becomes your credit limit.",
        "eligibility_criteria": {
            "credit_utilization": {"max": 1.0}
        },
        "rationale_template": "Build credit with secured deposit. Improve credit score with responsible use.",
        "credit_metadata": {
            "tier": "STARTER",
            "purchase_apr": "24.99% variable",
            "annual_fee": "$0"
        }
    },
    {
        "offer_id": "SAV-001",
        "type": "partner_offer",
        "title": "Automatic Savings Rewards Card",
        "partner": "Credit Partner",
        "summary": "Automatically save 1% of every purchase. Round-up purchases to nearest dollar into savings.",
        "eligibility_criteria": {
            "credit_utilization": {"max": 0.85},
            "is_overdue": {"equals": False}
        },
        "rationale_template": "Build emergency fund while you spend. Automatic savings to boost your savings rate.",
        "credit_metadata": {
            "tier": "STANDARD",
            "intro_purchase_apr": "0% for 6 months",
            "purchase_apr": "18.99% - 26.99% variable",
            "annual_fee": "$0"
        }
    },
    {
        "offer_id": "REST-001",
        "type": "partner_offer",
        "title": "Gold Dining Rewards Card",
        "partner": "Credit Partner",
        "summary": "Earn 4X points on dining and restaurants. 2X points on groceries, 1X on everything else.",
        "eligibility_criteria": {
            "credit_utilization": {"max": 0.30},
            "is_overdue": {"equals": False}
        },
        "rationale_template": "4X points on dining. $50 annual dining credit. Complimentary DoorDash DashPass subscription.",
        "credit_metadata": {
            "tier": "PREMIUM",
            "intro_purchase_apr": "0% for 12 months",
            "purchase_apr": "15.99% - 23.99% variable",
            "annual_fee": "$95"
        }
    },
    {
        "offer_id": "TRVL-001",
        "type": "partner_offer",
        "title": "Elite Travel Platinum Card",
        "partner": "Credit Partner",
        "summary": "Earn 5X points on flights and hotels. 3X points on travel and dining worldwide.",
        "eligibility_criteria": {
            "credit_utilization": {"max": 0.30},
            "is_overdue": {"equals": False}
        },
        "rationale_template": "5X points on travel. 50,000 bonus points after $3,000 spend in 3 months. No foreign transaction fees, priority boarding.",
        "credit_metadata": {
            "tier": "PREMIUM",
            "intro_purchase_apr": "0% for 15 months",
            "purchase_apr": "16.99% - 24.99% variable",
            "annual_fee": "$95"
        }
    },
    {
        "offer_id": "BANK-001",
        "type": "partner_offer",
        "title": "High-Yield Savings Account Bonus",
        "partner": "Credit Partner",
        "summary": "Earn $500 bonus when you deposit $5,000. Competitive 4.50% APY on all balances.",
        "eligibility_criteria": {
            "savings_balance": {"min": 5000},  # Approximate 3 months of min_avg_monthly_savings
            "is_overdue": {"equals": False}
        },
        "rationale_template": "Qualified for $500 bonus with current savings rate. Strong savings history qualifies for $500 bonus.",
        "credit_metadata": {
            "tier": "BANKING",
            "purchase_apr": "4.50% APY",
            "annual_fee": "$0",
            "bonus_amount": "$500",
            "bonus_requirement": "Deposit $5,000 within 90 days"
        }
    }
]


def get_education_content() -> List[Dict[str, Any]]:
    """Get all education content items.
    
    Returns:
        List of education content dictionaries
    """
    return EDUCATION_CONTENT.copy()


def get_partner_offers() -> List[Dict[str, Any]]:
    """Get all partner offer items.
    
    Returns:
        List of partner offer dictionaries
    """
    return PARTNER_OFFERS.copy()


def get_content_by_id(content_id: str) -> Optional[Dict[str, Any]]:
    """Get content item by ID.
    
    Args:
        content_id: Content ID to look up
        
    Returns:
        Content dictionary or None if not found
    """
    all_content = EDUCATION_CONTENT + PARTNER_OFFERS
    for item in all_content:
        if item.get("content_id") == content_id or item.get("offer_id") == content_id:
            return item
    return None


def get_content_by_persona(persona: str) -> List[Dict[str, Any]]:
    """Get education content items for a specific persona.
    
    Args:
        persona: Persona name
        
    Returns:
        List of education content dictionaries matching the persona
    """
    return [item for item in EDUCATION_CONTENT if persona in item.get("personas", [])]

