# Guardrails AI Integration Setup

This project uses [Guardrails AI](https://github.com/guardrails-ai/guardrails) for validating LLM responses and protecting PII.

## Installation

1. Install the package:
```bash
pip install guardrails-ai
```

2. Configure Guardrails Hub (optional but recommended):
```bash
guardrails configure
```

3. Install validators from Guardrails Hub:
```bash
# For output validation
guardrails hub install hub://guardrails/toxic_language

# For PII detection (optional, fallback to regex patterns if not installed)
guardrails hub install hub://guardrails/detect_pii
```

## Configuration

The Guardrails AI integration is configured in `src/guardrails/guardrails_ai.py`.

### Validators Used

1. **ToxicLanguage** - Detects toxic or harmful language in responses
   - Threshold: 0.5
   - Validation method: sentence-level

2. **DetectPII** - Detects PII in inputs/outputs (optional)
   - Entities: phone_number, email, ssn, credit_card
   - Falls back to regex patterns if not installed

3. **ProhibitedPhrasesValidator** - Custom validator for financial education context
   - Detects judgmental phrases like "overspending", "bad habits", etc.
   - Prevents shaming language in financial education responses

## PII Protection

See [SECURITY_AND_PII_PROTECTION.md](./SECURITY_AND_PII_PROTECTION.md) for detailed information on:
- PII detection and scrubbing
- Financial data sanitization
- Security best practices

## Usage

```python
from src.guardrails.guardrails_ai import get_guardrails

guardrails = get_guardrails()
is_valid, validated_text, errors = guardrails.validate(text)

if not is_valid:
    print(f"Validation failed: {errors}")
```

## Features

- **Multi-layer validation**: Combines toxic language detection with custom prohibited phrases
- **PII protection**: Detects and scrubs PII before sending to LLM
- **Automatic retry**: Failed validations trigger LLM retry with feedback
- **Backward compatibility**: Old `validate_tone()` function still works
- **Error reporting**: Detailed error messages for debugging

## Customization

To add more prohibited phrases, edit `PROHIBITED_PHRASES` in `src/guardrails/guardrails_ai.py`.

To add more validators from Guardrails Hub, update the `ChatGuardrails.__init__()` method.
