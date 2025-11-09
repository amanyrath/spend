# Common Issues and Fixes

## Issue 1: "pip install src" Error

**Problem:** You tried to install `src` as a package, but `src` is your source code directory, not a package.

**Solution:** Don't install `src`. Just make sure you're in the project root and have activated your venv:

```bash
cd /Users/alexismanyrath/Code/spend
source venv/bin/activate
python3 src/ingest/data_generator.py
```

## Issue 2: "ModuleNotFoundError: No module named 'src'"

**Problem:** When running scripts directly, Python doesn't know about the `src` module.

**Solution:** The scripts have been fixed to automatically add the project root to the Python path. Just make sure you:
1. Are in the project root directory (`/Users/alexismanyrath/Code/spend`)
2. Have activated your venv
3. Run the script from the project root

```bash
# Make sure you're here:
pwd
# Should show: /Users/alexismanyrath/Code/spend

# Then run:
python3 src/ingest/data_generator.py
python3 src/ingest/data_loader.py
```

## Alternative: Run as Module

You can also run scripts as Python modules:

```bash
python3 -m src.ingest.data_generator
python3 -m src.ingest.data_loader
```

## Verify Everything Works

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Make sure you're in project root
cd /Users/alexismanyrath/Code/spend

# 3. Generate data
python3 src/ingest/data_generator.py

# 4. Load data
python3 src/ingest/data_loader.py

# 5. Verify files exist
ls -lh data/
```











