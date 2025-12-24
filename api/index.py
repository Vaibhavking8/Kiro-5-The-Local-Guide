"""
Vercel serverless entry point for Taste & Trails Korea Flask application.
"""

import sys
import os
import logging

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app