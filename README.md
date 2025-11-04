# SpendSense

Financial Education Platform - Behavioral Signal Detection & Personalized Recommendations

## Overview

SpendSense is a local-first financial education system that analyzes synthetic transaction data to deliver personalized, explainable financial guidance. This demonstration project focuses on core algorithms and explainability.

## Features

- Synthetic data generation for 50-100 users
- Behavioral signal detection (subscriptions, credit utilization, savings, income stability)
- Persona-based personalization with clear rationales
- Operator oversight and auditability interface
- Evaluation metrics (coverage, explainability, latency, auditability)

## Setup

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd spend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
spendsense/
├── data/              # Data files (CSV, JSON) and database
├── src/               # Source code
│   ├── ingest/       # Data generation and loading
│   ├── features/     # Signal detection
│   ├── personas/     # Persona assignment
│   ├── recommend/    # Recommendation engine
│   ├── guardrails/   # Tone and eligibility validation
│   ├── api/          # FastAPI endpoints
│   └── database/     # Database schema and utilities
├── operator_ui/      # Operator interface (future)
├── eval/             # Evaluation metrics
├── tests/            # Test suite
├── docs/             # Documentation
└── results/          # Evaluation reports
```

## Quick Start

1. Generate synthetic data:
```bash
python src/ingest/data_generator.py
python src/ingest/data_loader.py
```

2. Compute features:
```bash
python src/features/compute_all.py
```

3. Assign personas:
```bash
python src/personas/assign_all.py
```

4. Generate recommendations:
```bash
python src/recommend/generate_all.py
```

5. Start the API:
```bash
uvicorn src.api.main:app --reload
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Documentation

See `docs/` directory for:
- Decision log
- Schema documentation
- Limitations

## License

[Your License Here]

