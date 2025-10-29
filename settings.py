"""
settings.py – Application Settings

This module defines constants for the application.
Environment variables (if set) override these defaults.
A helper function is provided to fetch all settings as a dictionary.
"""

import os
import sys

# Determine the base directory for resource files.
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# File paths for translations and configuration.
TRANSLATIONS_FILE = os.environ.get('TRANSLATIONS_FILE', os.path.join(BASE_DIR, "translations.json"))
CONFIG_FILE       = os.environ.get('CONFIG_FILE', os.path.join(BASE_DIR, "config.ini"))

# Database settings.
DB_FILENAME = os.environ.get('DB_FILENAME', "vet_clinic.db")
DB_URL = os.environ.get('DB_URL', f"sqlite:///{os.path.join(BASE_DIR, DB_FILENAME)}")

# Default application appearance and language.
DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', "ar")    # "ar" for Arabic, "en" for English.
DEFAULT_THEME    = os.environ.get('DEFAULT_THEME', "default")

# Table names (if needed elsewhere).
USERS_TABLE     = "users"
PETS_TABLE      = "pets"
INVENTORY_TABLE = "inventory"

# Regex pattern for phone number validation.
PHONE_REGEX = r'^\+?\d{8,15}$'

# Window settings.
WINDOW_TITLE    = os.environ.get('WINDOW_TITLE', "Vet Clinic Management System")
WINDOW_GEOMETRY = os.environ.get('WINDOW_GEOMETRY', "1100x700")
BG_COLOR        = os.environ.get('BG_COLOR', "#f4f6f8")

# Logging settings.
LOG_FORMAT = os.environ.get('LOG_FORMAT', "%(asctime)s [%(levelname)s] %(message)s")
LOG_LEVEL  = os.environ.get('LOG_LEVEL', "INFO")

# Additional settings.
LOW_STOCK_THRESHOLD = int(os.environ.get('LOW_STOCK_THRESHOLD', 5))
CURRENCY = os.environ.get('CURRENCY', "LE")
BACKUP_FREQUENCY = os.environ.get('BACKUP_FREQUENCY', "7")  # in days.

def get_all_settings():
    """
    Returns a dictionary of all configuration settings.
    Environment variables override the built-in defaults.
    """
    return {
        "BASE_DIR": BASE_DIR,
        "TRANSLATIONS_FILE": TRANSLATIONS_FILE,
        "CONFIG_FILE": CONFIG_FILE,
        "DB_FILENAME": DB_FILENAME,
        "DB_URL": DB_URL,
        "DEFAULT_LANGUAGE": DEFAULT_LANGUAGE,
        "DEFAULT_THEME": DEFAULT_THEME,
        "USERS_TABLE": USERS_TABLE,
        "PETS_TABLE": PETS_TABLE,
        "INVENTORY_TABLE": INVENTORY_TABLE,
        "PHONE_REGEX": PHONE_REGEX,
        "WINDOW_TITLE": WINDOW_TITLE,
        "WINDOW_GEOMETRY": WINDOW_GEOMETRY,
        "BG_COLOR": BG_COLOR,
        "LOG_FORMAT": LOG_FORMAT,
        "LOG_LEVEL": LOG_LEVEL,
        "LOW_STOCK_THRESHOLD": LOW_STOCK_THRESHOLD,
        "CURRENCY": CURRENCY,
        "BACKUP_FREQUENCY": BACKUP_FREQUENCY
    }

# Export a list of public objects.
__all__ = [
    "BASE_DIR", "TRANSLATIONS_FILE", "CONFIG_FILE", "DB_FILENAME", "DB_URL",
    "DEFAULT_LANGUAGE", "DEFAULT_THEME", "USERS_TABLE", "PETS_TABLE",
    "INVENTORY_TABLE", "PHONE_REGEX", "WINDOW_TITLE", "WINDOW_GEOMETRY",
    "BG_COLOR", "LOG_FORMAT", "LOG_LEVEL", "LOW_STOCK_THRESHOLD", "CURRENCY",
    "BACKUP_FREQUENCY", "get_all_settings"
]
