# Financial Data Security and PII Protection Guide

This document outlines the security measures implemented for protecting financial data and PII (Personally Identifiable Information) when interacting with LLM services.

## Overview

SpendSense implements multiple layers of data protection:

1. **Input Sanitization** - Scrubs PII from user messages before sending to LLM
2. **Financial Data Sanitization** - Removes sensitive fields from financial context
3. **Output Validation** - Validates LLM responses don't contain sensitive data
4. **Audit Logging** - Tracks all interactions for security monitoring

## PII Detection and Scrubbing

### User Message Sanitization

All user messages are automatically sanitized before being sent to the LLM:

- **Account Numbers**: Full account numbers (13-19 digits) → `[ACCOUNT_NUMBER]`
- **Routing Numbers**: Bank routing numbers (9 digits) → `[ROUTING_NUMBER]`
- **SSN**: Social Security Numbers → `[SSN]`
- **Email**: Email addresses → `[EMAIL]`
- **Phone**: Phone numbers → `[PHONE]`

### Financial Data Sanitization

Financial context data is sanitized before being sent to LLM:

#### Credit Utilization Data
- Only last 4 digits of account mask are sent
- Full account numbers are never included

#### Transaction Data
- Location data is removed (address, city, region, postal code, lat/lon)
- Authorization dates are removed
- Merchant names are checked for email patterns

#### Subscription Data
- Merchant names are sanitized to remove email patterns
- Only subscription amounts and frequencies are included

#### Income/Expense Data
- Amounts are rounded to 2 decimal places
- No exact account balances are shared (only utilization percentages)

## Guardrails AI Integration

### Input Validation

Guardrails AI is used to detect PII in user inputs:

```python
from guardrails.hub import DetectPII

# Detects: phone_number, email, ssn, credit_card
guard = Guard().use(DetectPII(pii_entities=["phone_number", "email", "ssn", "credit_card"]))
```

### Output Validation

LLM responses are validated for:
- **Toxic Language**: Detects harmful or inappropriate content
- **Prohibited Phrases**: Blocks judgmental financial language
- **PII Leakage**: Prevents LLM from generating PII in responses

## Configuration

### Required Guardrails Hub Validators

Install required validators:

```bash
guardrails hub install hub://guardrails/toxic_language
guardrails hub install hub://guardrails/detect_pii
```

### Environment Variables

Set these environment variables for production:

```bash
# OpenAI configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Data retention (optional)
DATA_RETENTION_DAYS=90  # How long to keep chat logs
```

## Security Best Practices

### 1. Data Minimization

Only send necessary data to LLM:
- ✅ Aggregated statistics (utilization %, savings rate)
- ✅ Category summaries (top spending categories)
- ✅ Masked account identifiers (last 4 digits only)
- ❌ Full account numbers
- ❌ Exact addresses or locations
- ❌ SSN or other identifiers

### 2. Audit Logging

All interactions are logged with:
- Original user message (for audit trail)
- Sanitized message sent to LLM
- Detected PII types
- Guardrails validation status

### 3. Monitoring

Monitor for:
- PII detection in user messages
- Failed guardrails validations
- Unusual patterns in chat logs

### 4. Response Sanitization

Even if LLM generates PII, responses are validated and sanitized before returning to users.

## What Data is Safe to Send

✅ **Safe to Send:**
- Account masks (last 4 digits only)
- Transaction amounts and categories
- Aggregated statistics (utilization %, savings rate)
- Merchant names (generic, non-PII)
- Spending patterns and trends

❌ **Never Send:**
- Full account numbers
- SSN or tax IDs
- Email addresses
- Phone numbers
- Physical addresses
- Exact account balances (only percentages/ratios)
- Location coordinates

## Implementation Details

### Data Sanitizer Module

Located in `src/guardrails/data_sanitizer.py`:

- `sanitize_user_message()` - Cleans user inputs
- `sanitize_financial_context()` - Cleans financial data
- `redact_sensitive_data()` - Removes PII patterns

### Integration Points

1. **API Endpoint** (`src/api/main.py`):
   - Sanitizes user message before processing
   - Logs PII detection events

2. **Chat Service** (`src/chat/service.py`):
   - Sanitizes financial context before building prompt
   - Uses sanitized data for LLM interaction

## Compliance Considerations

### PCI DSS
- No full credit card numbers are stored or transmitted
- Only last 4 digits (account mask) are used

### GDPR / CCPA
- User messages with PII are sanitized before processing
- Original messages stored for audit purposes only
- Detection events logged for compliance monitoring

### Financial Regulations
- Financial data is aggregated and anonymized
- No exact account balances sent to third parties
- All interactions logged for auditability

## Testing

Test PII detection:

```python
from src.guardrails.data_sanitizer import get_sanitizer

sanitizer = get_sanitizer()
message = "My SSN is 123-45-6789 and my card is 4532-1234-5678-9010"
sanitized, detected = sanitizer.sanitize_user_message(message)
# sanitized: "My SSN is [SSN] and my card is [ACCOUNT_NUMBER]"
# detected: ['ssn', 'account_number']
```

## Production Checklist

- [ ] Install Guardrails Hub validators
- [ ] Configure security logging system
- [ ] Set up PII detection alerts
- [ ] Review data retention policies
- [ ] Test PII scrubbing with sample data
- [ ] Monitor guardrails validation rates
- [ ] Set up audit log review process











