"""
main.py – Core Application and Settings

Rewritten with enhanced error handling and improved functionalities:
• More robust handling of configuration and translations file loading.
• Enhanced database backup functionality for SQLite databases.
• Extended error checking and logging across settings and other operations.
"""

import os
import json
import re
import logging
import configparser
import shutil
from datetime import date, datetime
from contextlib import contextmanager

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QAction, QMessageBox,
    QComboBox, QPushButton, QLineEdit, QLabel
)

# Import shared styles.
from styles import BUTTON_STYLE, HEADER_LABEL_STYLE, GROUPBOX_STYLE

# Import settings constants.
from settings import (
    TRANSLATIONS_FILE,
    CONFIG_FILE,
    DB_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    WINDOW_TITLE,
    WINDOW_GEOMETRY,
    BG_COLOR,
    PHONE_REGEX,
    LOG_FORMAT,
    LOG_LEVEL,
    LOW_STOCK_THRESHOLD,
    CURRENCY,
    BACKUP_FREQUENCY
)

# Setup logging.
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)

# Load Translations with error handling.
if not os.path.exists(TRANSLATIONS_FILE):
    error_msg = f"Translations file '{TRANSLATIONS_FILE}' not found! Please ensure it is placed next to main.py."
    logging.error(error_msg)
    raise FileNotFoundError(error_msg)

try:
    with open(TRANSLATIONS_FILE, encoding="utf-8") as f:
        TRANSLATIONS = json.load(f)
except json.JSONDecodeError as e:
    error_msg = f"Failed to parse {TRANSLATIONS_FILE}: {e}"
    logging.error(error_msg)
    raise RuntimeError(error_msg)
except Exception as e:
    error_msg = f"Unexpected error loading translations file: {e}"
    logging.error(error_msg)
    raise RuntimeError(error_msg)

# Load or create configuration.
config = configparser.ConfigParser()
if os.path.exists(CONFIG_FILE):
    try:
        config.read(CONFIG_FILE, encoding="utf-8")
    except Exception as e:
        logging.exception("Error reading config file")
        config["Settings"] = {}
else:
    config["Settings"] = {
        "language": DEFAULT_LANGUAGE,
        "theme": DEFAULT_THEME,
        "low_stock_threshold": str(LOW_STOCK_THRESHOLD),
        "currency": CURRENCY,
        "backup_frequency": BACKUP_FREQUENCY,
        "log_level": LOG_LEVEL
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
    except Exception as e:
        logging.exception("Failed to create configuration file")
        raise

CURRENT_LANG = config.get("Settings", "language", fallback=DEFAULT_LANGUAGE)

def _(key: str) -> str:
    """
    Retrieve the translation for a given key based on the current language.
    Logs a warning if the key is not found.
    """
    entry = TRANSLATIONS.get(key)
    if entry:
        return entry.get(CURRENT_LANG, key)
    logging.warning(f"Translation key '{key}' not found.")
    return key

# Database Setup using SQLAlchemy.
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)  # Extra column for email.
    address = Column(String, nullable=True)  # Extra column for address.
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<User(name='{self.user_name}', phone='{self.phone_number}')>"

class Pet(Base):
    __tablename__ = 'pets'
    id = Column(Integer, primary_key=True)
    pet_name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="pets")
    vaccines = relationship("Vaccine", back_populates="pet", cascade="all, delete-orphan")
    def __repr__(self):
        owner_name = self.owner.user_name if self.owner else "Unknown"
        return f"<Pet(name='{self.pet_name}', owner='{owner_name}')>"

class Vaccine(Base):
    __tablename__ = 'vaccines'
    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)
    vaccine_type = Column(String, nullable=False, default="Unknown")
    vaccine_date = Column(Date, nullable=False)
    next_vaccine_date = Column(Date, nullable=True)
    pet = relationship("Pet", back_populates="vaccines")
    def __repr__(self):
        pet_name = self.pet.pet_name if self.pet else "Unknown"
        return f"<Vaccine(pet='{pet_name}', type='{self.vaccine_type}', date='{self.vaccine_date}')>"

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=True)
    appointment_datetime = Column(DateTime, nullable=False)
    purpose = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    user = relationship("User")
    pet = relationship("Pet")
    def __repr__(self):
        return f"<Appointment(datetime='{self.appointment_datetime}', purpose='{self.purpose}')>"

class InventoryItem(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False)
    stock_count = Column(Integer, nullable=False)
    purchase_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    def __repr__(self):
        return f"<InventoryItem(name='{self.item_name}', stock={self.stock_count})>"
    @property
    def profit(self) -> float:
        return (self.selling_price - self.purchase_price) * self.stock_count

class BillingRecord(Base):
    __tablename__ = 'billings'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    total = Column(Float, nullable=False)
    details = Column(Text, nullable=True)
    def __repr__(self):
        return f"<BillingRecord(date='{self.date}', total={self.total})>"

class ExpenseRecord(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    def __repr__(self):
        return f"<ExpenseRecord(date='{self.date}', category='{self.category}', amount={self.amount})>"

Index('idx_phone', User.phone_number)

try:
    engine = create_engine(DB_URL, echo=False)
    Base.metadata.create_all(engine)
except Exception as e:
    logging.exception("Database initialization failed")
    raise

Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.
    Rolls back the session on exception.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        logging.exception("Session rollback due to exception")
        session.rollback()
        raise
    finally:
        session.close()

def validate_phone(phone: str) -> str | None:
    """
    Validate phone number against PHONE_REGEX.
    """
    return phone if re.match(PHONE_REGEX, phone) else None

def validate_weight(weight: str) -> float | None:
    """
    Validate and convert weight to a positive float.
    """
    try:
        w = float(weight)
        return w if w > 0 else None
    except ValueError:
        return None

def get_user_by_phone(phone: str):
    """
    Retrieve a user by their phone number from the database.
    """
    with session_scope() as s:
        return s.query(User).filter_by(phone_number=phone).first()

# Import UI Tabs.
from patient import PatientManagementTab
from inventory import InventoryManagementTab
from billing import BillingTab
from analytics import AnalyticsTab
from dashboard import DashboardTab   # New Tab.
from appointments import AppointmentsTab   # New Tab.

class VetClinicApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self._ = _
        self.setWindowTitle(_(WINDOW_TITLE))
        self.setGeometry(100, 100, 1100, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Initialize tabs.
        self.dashboard_tab = DashboardTab(self)
        self.patient_tab = PatientManagementTab(self)
        self.inventory_tab = InventoryManagementTab(self)
        self.billing_tab = BillingTab(self)
        self.analytics_tab = AnalyticsTab(self)
        self.appointments_tab = AppointmentsTab(self)

        # Add tabs in desired order.
        self.tab_widget.addTab(self.dashboard_tab, _("Dashboard"))
        self.tab_widget.addTab(self.patient_tab, _("Patients"))
        self.tab_widget.addTab(self.inventory_tab, _("Manage Inventory"))
        self.tab_widget.addTab(self.billing_tab, _("Billing"))
        self.tab_widget.addTab(self.analytics_tab, _("Analytics"))
        self.tab_widget.addTab(self.appointments_tab, _("Appointments"))

        # Setup menu actions.
        settings_action = QAction(_("Settings"), self)
        settings_action.triggered.connect(self.open_settings)
        backup_action = QAction(_("Backup Database"), self)
        backup_action.triggered.connect(self.backup_database)
        menubar = self.menuBar()
        settings_menu = menubar.addMenu(_("Settings"))
        settings_menu.addAction(settings_action)
        menubar.addAction(backup_action)

    def open_settings(self):
        """
        Open the settings dialog with unified styling.
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(_("Settings"))
        layout = QVBoxLayout(dialog)

        # Use a group box to wrap settings.
        settings_group = QtWidgets.QGroupBox(_("Application Settings"))
        settings_group.setStyleSheet(GROUPBOX_STYLE)
        group_layout = QVBoxLayout(settings_group)

        # Theme
        theme_label = QLabel(_("Theme"))
        theme_label.setStyleSheet(HEADER_LABEL_STYLE)
        themes = ["default"]  # Future themes can be added here.
        theme_combo = QComboBox()
        theme_combo.addItems(themes)
        theme_combo.setCurrentText(config.get("Settings", "theme", fallback=DEFAULT_THEME))

        # Language
        lang_label = QLabel(_("Language"))
        lang_label.setStyleSheet(HEADER_LABEL_STYLE)
        lang_combo = QComboBox()
        lang_combo.addItems(["English", "Arabic"])
        current_lang = "Arabic" if config.get("Settings", "language", fallback=DEFAULT_LANGUAGE) == "ar" else "English"
        lang_combo.setCurrentText(current_lang)

        # Other settings
        low_stock_label = QLabel(_("Low Stock Threshold"))
        low_stock_label.setStyleSheet(HEADER_LABEL_STYLE)
        low_stock_entry = QLineEdit()
        low_stock_entry.setText(config.get("Settings", "low_stock_threshold", fallback=str(LOW_STOCK_THRESHOLD)))
        currency_label = QLabel(_("Currency"))
        currency_label.setStyleSheet(HEADER_LABEL_STYLE)
        currency_entry = QLineEdit()
        currency_entry.setText(config.get("Settings", "currency", fallback=CURRENCY))
        backup_label = QLabel(_("Backup Frequency (days)"))
        backup_label.setStyleSheet(HEADER_LABEL_STYLE)
        backup_entry = QLineEdit()
        backup_entry.setText(config.get("Settings", "backup_frequency", fallback=BACKUP_FREQUENCY))
        log_level_label = QLabel(_("Log Level"))
        log_level_label.setStyleSheet(HEADER_LABEL_STYLE)
        log_level_combo = QComboBox()
        log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_combo.setCurrentText(config.get("Settings", "log_level", fallback=LOG_LEVEL))

        # Add widgets to group layout.
        group_layout.addWidget(theme_label)
        group_layout.addWidget(theme_combo)
        group_layout.addWidget(lang_label)
        group_layout.addWidget(lang_combo)
        group_layout.addWidget(low_stock_label)
        group_layout.addWidget(low_stock_entry)
        group_layout.addWidget(currency_label)
        group_layout.addWidget(currency_entry)
        group_layout.addWidget(backup_label)
        group_layout.addWidget(backup_entry)
        group_layout.addWidget(log_level_label)
        group_layout.addWidget(log_level_combo)
        layout.addWidget(settings_group)

        # Apply button.
        btn_apply = QPushButton(_("Apply"))
        btn_apply.setStyleSheet(BUTTON_STYLE)
        layout.addWidget(btn_apply)

        def apply_settings():
            try:
                new_lang = "ar" if lang_combo.currentText() == "Arabic" else "en"
                global CURRENT_LANG
                CURRENT_LANG = new_lang
                config["Settings"]["language"] = new_lang
                config["Settings"]["theme"] = theme_combo.currentText()
                config["Settings"]["low_stock_threshold"] = low_stock_entry.text()
                config["Settings"]["currency"] = currency_entry.text()
                config["Settings"]["backup_frequency"] = backup_entry.text()
                config["Settings"]["log_level"] = log_level_combo.currentText()

                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    config.write(f)

                # Refresh language for all tabs.
                self.patient_tab.refresh_language()
                self.appointments_tab.refresh_language()
                self.inventory_tab.refresh_language()
                self.billing_tab.refresh_language()
                self.analytics_tab.refresh_language()
                if hasattr(self.dashboard_tab, 'refresh_language'):
                    self.dashboard_tab.refresh_language()
                

                QMessageBox.information(self, _("Settings"), _("Settings applied successfully."))
                dialog.accept()
            except Exception as ex:
                logging.exception("Failed to apply settings")
                QMessageBox.critical(self, _("Settings"), _("Failed to apply settings: ") + str(ex))

        btn_apply.clicked.connect(apply_settings)
        dialog.exec_()

    def backup_database(self):
        """
        Backup the SQLite database file if applicable.
        For non-SQLite databases, informs the user that automatic backup is not supported.
        """
        try:
            if DB_URL.startswith("sqlite:///"):
                db_file = DB_URL.replace("sqlite:///", "")
                if os.path.exists(db_file):
                    backup_file = f"{db_file}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                    shutil.copy(db_file, backup_file)
                    QMessageBox.information(
                        self,
                        _("Backup Database"),
                        _("Database successfully backed up to ") + backup_file
                    )
                else:
                    QMessageBox.warning(self, _("Backup Database"), _("Database file not found for backup."))
            else:
                QMessageBox.information(
                    self,
                    _("Backup Database"),
                    _("Automatic backup is not supported for non-SQLite databases.")
                )
        except Exception as e:
            logging.exception("Database backup failed")
            QMessageBox.critical(self, _("Backup Database"), _("Failed to backup database: ") + str(e))

if __name__ == "__main__":
    try:
        import sys
        app = QtWidgets.QApplication(sys.argv)
        window = VetClinicApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.exception("Application failed to start")
        raise
