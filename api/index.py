"""Vercel serverless function entry point for SpendSense API."""
from src.api.main import app

# Vercel expects 'app' or handler in api/ folder
handler = app
