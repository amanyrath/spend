"""
Credit Offers Pre-Qualification Module
Provides credit card pre-qualification logic with balance transfer focus
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
import base64
import uuid
from datetime import datetime


class CreditRating(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class UtilizationLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AccountUtilization(BaseModel):
    account_id: str
    utilization: float
    credit_limit: float
    balance: float


class CustomerInfo(BaseModel):
    # Credit metrics
    total_utilization: float = Field(..., ge=0, le=100, description="Overall credit utilization percentage")
    utilization_level: UtilizationLevel = Field(..., description="Categorized utilization level")
    interest_charged: float = Field(..., ge=0, description="Total interest charges in analysis window")
    minimum_payment_only: bool = Field(..., description="Customer only making minimum payments")
    is_overdue: bool = Field(..., description="Has overdue payments")
    online_spending_share: float = Field(..., ge=0, le=100, description="Percentage of credit spending online")
    per_account_utilization: Optional[List[AccountUtilization]] = Field(None, description="Detailed per-account utilization")
    
    # Savings metrics
    total_savings: float = Field(..., ge=0, description="Total savings balance")
    net_inflow: float = Field(..., description="Net savings growth in period")
    growth_rate: float = Field(..., description="Savings growth rate percentage")
    emergency_fund_coverage: float = Field(..., ge=0, description="Months of expenses covered by savings")
    avg_monthly_savings: float = Field(..., description="Average monthly savings over last 90 days")


class ImageData(BaseModel):
    imageType: str
    url: str
    altText: str


class ProductOffer(BaseModel):
    productId: str
    code: str
    productDisplayName: str
    priority: int
    tier: str
    creditRating: CreditRating
    images: dict
    introPurchaseApr: Optional[str] = None
    purchaseApr: str
    introBalanceTransferApr: Optional[str] = None
    balanceTransferFee: Optional[str] = None
    annualMembershipFee: str
    mainMarketingCopy: List[str]
    extraMarketingCopy: List[str]
    applyNowLink: str
    matchPercentage: float
    matchReason: str
    bonusAmount: Optional[str] = None
    bonusRequirement: Optional[str] = None
    estimatedSavings: Optional[str] = None


class PrequalificationResponse(BaseModel):
    prequalificationId: str
    qualifiedProducts: List[ProductOffer]
    customerCreditRating: CreditRating
    timestamp: str


def generate_card_svg(card_name: str, card_type: str, color_scheme: dict) -> str:
    """Generate a simple SVG card design"""
    svg = f'''<svg width="400" height="250" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad_{card_type}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color_scheme['start']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color_scheme['end']};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="400" height="250" rx="15" fill="url(#grad_{card_type})"/>
  <text x="30" y="50" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="white">{card_name}</text>
  <text x="30" y="220" font-family="Arial, sans-serif" font-size="16" fill="white" opacity="0.9">{card_type}</text>
  <circle cx="350" cy="40" r="25" fill="white" opacity="0.3"/>
  <circle cx="370" cy="40" r="25" fill="white" opacity="0.3"/>
</svg>'''
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


# Define product catalog with qualification rules
PRODUCT_CATALOG = {
    "balance_transfer": {
        "productId": "BT-001",
        "code": "BALANCE_XFER_PLATINUM",
        "productDisplayName": "Platinum Balance Transfer Card",
        "tier": "PREMIUM",
        "color_scheme": {"start": "#1e3a8a", "end": "#3b82f6"},
        "introPurchaseApr": "0% for 12 months",
        "purchaseApr": "16.99% - 24.99% variable",
        "introBalanceTransferApr": "0% for 18 months",
        "balanceTransferFee": "3% of transfer amount",
        "annualMembershipFee": "$0",
        "mainMarketingCopy": [
            "0% intro APR on balance transfers for 18 months",
            "No annual fee - save money while paying down debt"
        ],
        "extraMarketingCopy": [
            "Transfer balances from high-interest cards",
            "Online account management and mobile app"
        ],
        "qualification_rules": {
            "max_utilization": 85,
            "allow_overdue": False,
            "allow_minimum_payment_only": True,  # These customers need help!
            "min_interest_charged": 50,  # Target customers paying interest
            "credit_rating": "GOOD"
        }
    },
    "secured": {
        "productId": "SEC-001",
        "code": "SECURED_BUILDER",
        "productDisplayName": "Credit Builder Secured Card",
        "tier": "STARTER",
        "color_scheme": {"start": "#065f46", "end": "#10b981"},
        "introPurchaseApr": None,
        "purchaseApr": "24.99% variable",
        "introBalanceTransferApr": None,
        "balanceTransferFee": None,
        "annualMembershipFee": "$0",
        "mainMarketingCopy": [
            "Build credit with responsible use",
            "Security deposit becomes your credit limit"
        ],
        "extraMarketingCopy": [
            "Graduate to unsecured card after 12 months",
            "No credit check required"
        ],
        "qualification_rules": {
            "max_utilization": 100,
            "allow_overdue": True,
            "allow_minimum_payment_only": True,
            "credit_rating": "POOR"
        }
    },
    "savings": {
        "productId": "SAV-001",
        "code": "AUTO_SAVINGS_REWARDS",
        "productDisplayName": "Automatic Savings Rewards Card",
        "tier": "STANDARD",
        "color_scheme": {"start": "#7c2d12", "end": "#f97316"},
        "introPurchaseApr": "0% for 6 months",
        "purchaseApr": "18.99% - 26.99% variable",
        "introBalanceTransferApr": None,
        "balanceTransferFee": None,
        "annualMembershipFee": "$0",
        "mainMarketingCopy": [
            "Automatically save 1% of every purchase",
            "Round-up purchases to nearest dollar into savings"
        ],
        "extraMarketingCopy": [
            "Build emergency fund while you spend",
            "No minimum balance required"
        ],
        "qualification_rules": {
            "max_utilization": 85,
            "allow_overdue": False,
            "allow_minimum_payment_only": False,
            "max_emergency_fund_coverage": 3,  # Less than 3 months emergency fund
            "max_growth_rate": 5,  # Low savings growth rate
            "credit_rating": "FAIR"
        }
    },
    "restaurant": {
        "productId": "REST-001",
        "code": "DINING_REWARDS_GOLD",
        "productDisplayName": "Gold Dining Rewards Card",
        "tier": "PREMIUM",
        "color_scheme": {"start": "#854d0e", "end": "#eab308"},
        "introPurchaseApr": "0% for 12 months",
        "purchaseApr": "15.99% - 23.99% variable",
        "introBalanceTransferApr": None,
        "balanceTransferFee": None,
        "annualMembershipFee": "$95",
        "mainMarketingCopy": [
            "Earn 4X points on dining and restaurants",
            "2X points on groceries, 1X on everything else"
        ],
        "extraMarketingCopy": [
            "$50 annual dining credit",
            "Complimentary DoorDash DashPass subscription"
        ],
        "qualification_rules": {
            "max_utilization": 30,
            "allow_overdue": False,
            "allow_minimum_payment_only": False,
            "credit_rating": "EXCELLENT"
        }
    },
    "travel": {
        "productId": "TRVL-001",
        "code": "TRAVEL_ELITE_PLATINUM",
        "productDisplayName": "Elite Travel Platinum Card",
        "tier": "PREMIUM",
        "color_scheme": {"start": "#4c1d95", "end": "#a855f7"},
        "introPurchaseApr": "0% for 15 months",
        "purchaseApr": "16.99% - 24.99% variable",
        "introBalanceTransferApr": None,
        "balanceTransferFee": None,
        "annualMembershipFee": "$95",
        "mainMarketingCopy": [
            "Earn 5X points on flights and hotels",
            "3X points on travel and dining worldwide"
        ],
        "extraMarketingCopy": [
            "50,000 bonus points after $3,000 spend in 3 months",
            "No foreign transaction fees, priority boarding"
        ],
        "qualification_rules": {
            "max_utilization": 30,
            "allow_overdue": False,
            "allow_minimum_payment_only": False,
            "credit_rating": "EXCELLENT"
        }
    },
    "bank_bonus": {
        "productId": "BANK-001",
        "code": "SAVINGS_BONUS_500",
        "productDisplayName": "High-Yield Savings Account Bonus",
        "tier": "BANKING",
        "color_scheme": {"start": "#0c4a6e", "end": "#0ea5e9"},
        "introPurchaseApr": None,
        "purchaseApr": "4.50% APY",
        "introBalanceTransferApr": None,
        "balanceTransferFee": None,
        "annualMembershipFee": "$0",
        "bonusAmount": "$500",
        "bonusRequirement": "Deposit $5,000 within 90 days",
        "mainMarketingCopy": [
            "Earn $500 bonus when you deposit $5,000",
            "Competitive 4.50% APY on all balances"
        ],
        "extraMarketingCopy": [
            "No monthly maintenance fees",
            "FDIC insured up to $250,000"
        ],
        "qualification_rules": {
            "min_avg_monthly_savings": 1666.67,  # ~$5k over 3 months
            "allow_overdue": False,
            "credit_rating": "GOOD"
        }
    }
}


def calculate_match_percentage(customer: CustomerInfo, rules: dict, product_type: str) -> tuple[Optional[float], str]:
    """
    Calculate match percentage based on qualification rules
    Returns (match_percentage, reason) tuple
    """
    score = 100.0
    reasons = []
    
    # Special handling for bank bonus
    if product_type == "bank_bonus":
        if customer.avg_monthly_savings < rules["min_avg_monthly_savings"]:
            return None, ""
        if customer.is_overdue and not rules["allow_overdue"]:
            return None, ""
        
        # High match if they significantly exceed savings requirement
        if customer.avg_monthly_savings >= rules["min_avg_monthly_savings"] * 1.5:
            reasons.append("Strong savings history qualifies for $500 bonus")
            return 95.0, "; ".join(reasons)
        
        reasons.append("Qualified for $500 bonus with current savings rate")
        return 85.0, "; ".join(reasons)
    
    # Balance Transfer Card - Aggressive matching for high interest payers
    if product_type == "balance_transfer":
        if customer.is_overdue and not rules["allow_overdue"]:
            return None, ""
        
        if customer.total_utilization > rules["max_utilization"]:
            return None, ""
        
        # Boost score significantly for high interest charges
        if customer.interest_charged >= rules.get("min_interest_charged", 0):
            interest_boost = min(customer.interest_charged / 100 * 2, 25)  # Up to 25 point boost
            score += interest_boost
            
            # Calculate estimated savings
            estimated_savings = customer.interest_charged * 18 / 12  # 18 months of current interest
            reasons.append(f"Could save ~${estimated_savings:.0f} in interest over 18 months")
        
        # Reward customers trying to pay down debt
        if customer.minimum_payment_only and customer.interest_charged > 100:
            reasons.append("Break free from minimum payment cycle")
            score += 10
        
        if customer.utilization_level == UtilizationLevel.HIGH:
            score -= 15
            reasons.append("High utilization - consolidate to improve credit")
        
        reasons.append("0% APR for 18 months on balance transfers")
        return min(score, 100.0), "; ".join(reasons)
    
    # Auto Savings Card - Target customers who need help saving
    if product_type == "savings":
        if customer.is_overdue and not rules["allow_overdue"]:
            return None, ""
        
        if customer.minimum_payment_only and not rules["allow_minimum_payment_only"]:
            return None, ""
        
        if customer.total_utilization > rules["max_utilization"]:
            return None, ""
        
        # Check if customer needs help saving
        needs_savings_help = False
        
        if customer.emergency_fund_coverage < rules.get("max_emergency_fund_coverage", 3):
            score += 15
            needs_savings_help = True
            reasons.append(f"Build emergency fund (currently {customer.emergency_fund_coverage:.1f} months)")
        
        if customer.growth_rate < rules.get("max_growth_rate", 5):
            score += 10
            needs_savings_help = True
            reasons.append("Automatic savings to boost your savings rate")
        
        if not needs_savings_help:
            # Customer doesn't really need this card
            score -= 20
        
        reasons.append("Round-up purchases automatically into savings")
        return min(score, 100.0), "; ".join(reasons)
    
    # Premium Cards (Restaurant & Travel) - Strict requirements
    if product_type in ["restaurant", "travel"]:
        if customer.is_overdue and not rules["allow_overdue"]:
            return None, ""
        
        if customer.minimum_payment_only and not rules["allow_minimum_payment_only"]:
            return None, ""
        
        if customer.total_utilization > rules["max_utilization"]:
            return None, ""
        
        # Reward excellent credit management
        if customer.utilization_level == UtilizationLevel.LOW:
            score += 10
            reasons.append("Excellent credit utilization")
        
        if customer.interest_charged < 10:  # Paying in full
            score += 5
            reasons.append("Strong payment history")
        
        if product_type == "restaurant":
            reasons.append("4X points on dining")
        else:
            reasons.append("5X points on travel")
        
        return min(score, 100.0), "; ".join(reasons)
    
    # Secured Card - Most lenient
    if product_type == "secured":
        reasons.append("Build credit with secured deposit")
        if customer.total_utilization > 80:
            reasons.append("Improve credit score with responsible use")
        return 80.0, "; ".join(reasons)
    
    # Default qualification
    if customer.is_overdue:
        return None, ""
    
    if customer.total_utilization > 85:
        return None, ""
    
    return 70.0, "Qualified for this product"


def determine_credit_rating(customer: CustomerInfo) -> CreditRating:
    """Infer credit rating from customer info"""
    if customer.is_overdue or customer.utilization_level == UtilizationLevel.HIGH:
        if customer.minimum_payment_only:
            return CreditRating.POOR
        return CreditRating.FAIR
    
    if customer.minimum_payment_only or customer.total_utilization > 50:
        return CreditRating.FAIR
    
    if customer.total_utilization > 30 or customer.interest_charged > 100:
        return CreditRating.GOOD
    
    return CreditRating.EXCELLENT


def create_prequalification(customer: CustomerInfo) -> PrequalificationResponse:
    """
    Create a pre-qualification check for credit offers
    Returns only products that meet qualification threshold
    """
    qualified_products = []
    customer_rating = determine_credit_rating(customer)
    
    for product_key, product_data in PRODUCT_CATALOG.items():
        rules = product_data["qualification_rules"]
        match_pct, reason = calculate_match_percentage(customer, rules, product_key)
        
        if match_pct is not None and match_pct >= 60:
            # Generate card image
            card_svg = generate_card_svg(
                product_data["productDisplayName"],
                product_data["tier"],
                product_data["color_scheme"]
            )
            
            # Calculate estimated savings for balance transfer
            estimated_savings = None
            if product_key == "balance_transfer" and customer.interest_charged > 0:
                savings_amount = customer.interest_charged * 18 / 12
                estimated_savings = f"${savings_amount:.0f}"
            
            offer = ProductOffer(
                productId=product_data["productId"],
                code=product_data["code"],
                productDisplayName=product_data["productDisplayName"],
                priority=len(qualified_products) + 1,
                tier=product_data["tier"],
                creditRating=customer_rating,
                images={
                    "cardArt": {
                        "imageType": "CardArt",
                        "url": card_svg,
                        "altText": f"{product_data['productDisplayName']} card art"
                    },
                    "cardName": {
                        "imageType": "CardName",
                        "url": card_svg,
                        "altText": product_data["productDisplayName"]
                    }
                },
                introPurchaseApr=product_data["introPurchaseApr"],
                purchaseApr=product_data["purchaseApr"],
                introBalanceTransferApr=product_data["introBalanceTransferApr"],
                balanceTransferFee=product_data["balanceTransferFee"],
                annualMembershipFee=product_data["annualMembershipFee"],
                mainMarketingCopy=product_data["mainMarketingCopy"],
                extraMarketingCopy=product_data["extraMarketingCopy"],
                applyNowLink=f"https://example.com/apply/{product_data['code']}",
                matchPercentage=round(match_pct, 2),
                matchReason=reason,
                bonusAmount=product_data.get("bonusAmount"),
                bonusRequirement=product_data.get("bonusRequirement"),
                estimatedSavings=estimated_savings
            )
            qualified_products.append(offer)
    
    # Sort by match percentage (highest first)
    qualified_products.sort(key=lambda x: x.matchPercentage, reverse=True)
    
    # Update priorities after sorting
    for idx, product in enumerate(qualified_products):
        product.priority = idx + 1
    
    return PrequalificationResponse(
        prequalificationId=str(uuid.uuid4()),
        qualifiedProducts=qualified_products,
        customerCreditRating=customer_rating,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )







