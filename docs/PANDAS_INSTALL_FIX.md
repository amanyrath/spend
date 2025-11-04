# Fixing pandas Installation Error with Python 3.14

## Problem
Pandas 2.1.3 doesn't support Python 3.14. You're seeing compilation errors like:
```
error: too few arguments to function call, expected 6, have 5
```

## Solutions

### Option 1: Use Python 3.13 (Available on your system)

You have Python 3.13 available. Try using it:

```bash
# Remove old venv
rm -rf venv

# Create new venv with Python 3.13
python3.13 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Install Python 3.12 via Homebrew (Recommended)

Python 3.12 has the best compatibility:

```bash
# Install Python 3.12
brew install python@3.12

# Remove old venv
rm -rf venv

# Create venv with Python 3.12
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Update pandas (if you must use Python 3.14)

I've already updated requirements.txt to use `pandas>=2.2.0`. Try:

```bash
# Remove old venv
rm -rf venv

# Create new venv (will still use Python 3.14)
python3 -m venv venv
source venv/bin/activate

# Install dependencies (should get pandas 2.2.0+)
pip install -r requirements.txt --upgrade
```

Note: pandas 2.2.0+ may have better Python 3.14 support, but Python 3.11/3.12 is still recommended.

### Option 4: Use pyenv (Best for managing multiple Python versions)

```bash
# Install pyenv if not installed
brew install pyenv

# Install Python 3.12
pyenv install 3.12.7

# Set local Python version for this project
cd /Users/alexismanyrath/Code/spend
pyenv local 3.12.7

# Create venv (will use Python 3.12.7)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Fix (Right Now)

**Try Python 3.13 first:**

```bash
cd /Users/alexismanyrath/Code/spend
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If that doesn't work, install Python 3.12:

```bash
brew install python@3.12
rm -rf venv
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

