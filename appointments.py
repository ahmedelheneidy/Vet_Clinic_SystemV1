from datetime import datetime
import logging

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout, QListWidget, QPushButton, QDialog, QLineEdit, QLabel,
    QDateTimeEdit, QFormLayout, QMessageBox, QHBoxLayout, QListWidgetItem
)
from styles import BUTTON_STYLE, HEADER_LABEL_STYLE, LISTSTYLE


class AppointmentsTab(QtWidgets.QWidget):
    """
    A widget to display, add, edit, and delete appointments.
    Appointments are loaded from the database and displayed in a list widget.
    Editing extracts necessary data within an active session to avoid detached instance issues.
    """
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.init_ui()

    def init_ui(self):
        """Initialize the UI layout with appointment list and control buttons."""
        try:
            main_layout = QVBoxLayout(self)

            # Appointment list displays each appointment with its scheduled time, purpose and user phone.
            self.appointment_list = QListWidget()
            self.appointment_list.setStyleSheet(LISTSTYLE)
            self.appointment_list.itemDoubleClicked.connect(self.show_edit_dialog)
            main_layout.addWidget(self.appointment_list)

            # Button bar with Add, Edit, Delete, and Refresh actions.
            btn_layout = QHBoxLayout()
            self.add_button = QPushButton(self.app._("Add Appointment"))
            self.add_button.setStyleSheet(BUTTON_STYLE)
            self.add_button.clicked.connect(self.show_add_dialog)
            btn_layout.addWidget(self.add_button)

            self.edit_button = QPushButton(self.app._("Edit Appointment"))
            self.edit_button.setStyleSheet(BUTTON_STYLE)
            self.edit_button.clicked.connect(self.show_edit_dialog)
            btn_layout.addWidget(self.edit_button)

            self.delete_button = QPushButton(self.app._("Delete Appointment"))
            self.delete_button.setStyleSheet(BUTTON_STYLE)
            self.delete_button.clicked.connect(self.delete_appointment)
            btn_layout.addWidget(self.delete_button)

            self.refresh_button = QPushButton(self.app._("Refresh"))
            self.refresh_button.setStyleSheet(BUTTON_STYLE)
            self.refresh_button.clicked.connect(self.load_appointments)
            btn_layout.addWidget(self.refresh_button)

            main_layout.addLayout(btn_layout)
            self.setLayout(main_layout)
            self.load_appointments()
        except Exception as e:
            logging.exception("Error initializing appointments UI")
            QMessageBox.critical(self, self.app._("Error"), str(e))

    def load_appointments(self):
        """
        Load appointments from the database and populate the list widget.
        Each appointment list item stores its database ID (using Qt.UserRole) for future reference.
        """
        try:
            from main import session_scope, Appointment, _
            with session_scope() as session:
                self.appointment_list.clear()
                appointments = session.query(Appointment).order_by(Appointment.appointment_datetime).all()
                for appt in appointments:
                    # Compose display text.
                    display = f"{appt.appointment_datetime.strftime('%Y-%m-%d %H:%M')} - {appt.purpose} ({appt.user.phone_number})"
                    item = QListWidgetItem(display)
                    # Save the appointment id for editing/deleting.
                    item.setData(Qt.UserRole, appt.id)
                    self.appointment_list.addItem(item)
        except Exception as e:
            logging.exception("Error loading appointments")
            QMessageBox.critical(self, self.app._("Error"), str(e))

    def show_add_dialog(self):
        """
        Display a dialog to add a new appointment.
        Validates that a phone number is provided and the user exists before saving.
        """
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle(self.app._("Add New Appointment"))
            form = QFormLayout(dialog)
            phone_entry = QLineEdit()
            pet_entry = QLineEdit()
            datetime_entry = QDateTimeEdit(datetime.now())
            datetime_entry.setCalendarPopup(True)
            purpose_entry = QLineEdit()
            notes_entry = QLineEdit()
            form.addRow(self.app._("Phone Number:"), phone_entry)
            form.addRow(self.app._("Pet (optional):"), pet_entry)
            form.addRow(self.app._("Appointment Date & Time:"), datetime_entry)
            form.addRow(self.app._("Purpose:"), purpose_entry)
            form.addRow(self.app._("Notes:"), notes_entry)
            btn_save = QPushButton(self.app._("Save"))
            btn_save.setStyleSheet(BUTTON_STYLE)
            form.addRow(btn_save)

            def save_appointment():
                try:
                    phone = phone_entry.text().strip()
                    if not phone:
                        QMessageBox.critical(dialog, self.app._("Error"), self.app._("Phone number is required."))
                        return
                    from main import session_scope, User, Appointment
                    with session_scope() as session:
                        user = session.query(User).filter_by(phone_number=phone).first()
                        if not user:
                            QMessageBox.critical(dialog, self.app._("Error"), self.app._("User not found."))
                            return
                        new_appt = Appointment(
                            user_id=user.id,
                            pet_id=None,  # Extend later if you wish to associate a pet.
                            appointment_datetime=datetime_entry.dateTime().toPyDateTime(),
                            purpose=purpose_entry.text().strip(),
                            notes=notes_entry.text().strip()
                        )
                        session.add(new_appt)
                    self.load_appointments()
                    dialog.accept()
                except Exception as ex:
                    logging.exception("Error saving new appointment")
                    QMessageBox.critical(dialog, self.app._("Error"), str(ex))

            btn_save.clicked.connect(save_appointment)
            dialog.exec_()
        except Exception as e:
            logging.exception("Error in add appointment dialog")
            QMessageBox.critical(self, self.app._("Error"), str(e))

    def show_edit_dialog(self, item=None):
        """
        Display a dialog to edit an existing appointment.
        If triggered via double-click, an item is passed; otherwise, the currently selected item is used.
        To avoid DetachedInstanceError, extract appointment attributes while the session is active.
        """
        try:
            if item is None:
                item = self.appointment_list.currentItem()
            if not item:
                QMessageBox.warning(self, self.app._("Warning"), self.app._("Please select an appointment to edit."))
                return
            appt_id = item.data(Qt.UserRole)
            # Load appointment details within a session context.
            from main import session_scope, Appointment, User
            with session_scope() as session:
                appointment = session.get(Appointment, appt_id)
                if not appointment:
                    QMessageBox.critical(self, self.app._("Error"), self.app._("Appointment not found."))
                    return
                # Extract necessary attributes and store locally.
                appt_datetime = appointment.appointment_datetime
                appt_purpose = appointment.purpose
                appt_notes = appointment.notes
                user_phone = appointment.user.phone_number
            # Create the edit dialog using the stored values.
            dialog = QDialog(self)
            dialog.setWindowTitle(self.app._("Edit Appointment"))
            form = QFormLayout(dialog)
            phone_entry = QLineEdit(user_phone)
            phone_entry.setReadOnly(True)
            pet_entry = QLineEdit()  # Optional pet field; can be preloaded if stored.
            datetime_entry = QDateTimeEdit(appt_datetime)
            datetime_entry.setCalendarPopup(True)
            purpose_entry = QLineEdit(appt_purpose)
            notes_entry = QLineEdit(appt_notes)
            form.addRow(self.app._("Phone Number:"), phone_entry)
            form.addRow(self.app._("Pet (optional):"), pet_entry)
            form.addRow(self.app._("Appointment Date & Time:"), datetime_entry)
            form.addRow(self.app._("Purpose:"), purpose_entry)
            form.addRow(self.app._("Notes:"), notes_entry)
            btn_save = QPushButton(self.app._("Save Changes"))
            btn_save.setStyleSheet(BUTTON_STYLE)
            form.addRow(btn_save)

            def save_changes():
                try:
                    from main import session_scope, Appointment
                    with session_scope() as session:
                        appt_to_update = session.get(Appointment, appt_id)
                        if not appt_to_update:
                            QMessageBox.critical(dialog, self.app._("Error"), self.app._("Appointment not found."))
                            return
                        # Update appointment with new values.
                        appt_to_update.appointment_datetime = datetime_entry.dateTime().toPyDateTime()
                        appt_to_update.purpose = purpose_entry.text().strip()
                        appt_to_update.notes = notes_entry.text().strip()
                        # Optionally, update pet info if integrated.
                    self.load_appointments()
                    dialog.accept()
                except Exception as ex:
                    logging.exception("Error updating appointment")
                    QMessageBox.critical(dialog, self.app._("Error"), str(ex))

            btn_save.clicked.connect(save_changes)
            dialog.exec_()
        except Exception as e:
            logging.exception("Error in edit appointment dialog")
            QMessageBox.critical(self, self.app._("Error"), str(e))

    def delete_appointment(self):
        """
        Delete the currently selected appointment after a confirmation dialog.
        """
        try:
            item = self.appointment_list.currentItem()
            if not item:
                QMessageBox.warning(self, self.app._("Warning"), self.app._("Please select an appointment to delete."))
                return
            appt_id = item.data(Qt.UserRole)
            reply = QMessageBox.question(
                self, self.app._("Confirm Delete"),
                self.app._("Are you sure you want to delete this appointment?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                from main import session_scope, Appointment
                with session_scope() as session:
                    appointment = session.get(Appointment, appt_id)
                    if appointment:
                        session.delete(appointment)
                self.load_appointments()
                QMessageBox.information(self, self.app._("Success"), self.app._("Appointment deleted."))
        except Exception as e:
            logging.exception("Error deleting appointment")
            QMessageBox.critical(self, self.app._("Error"), str(e))


    def refresh_language(self):
        """Update all static texts in the Appointments tab."""
        _ = self.app._
        self.add_button.setText(_("Add Appointment"))
        self.edit_button.setText(_("Edit Appointment"))
        self.delete_button.setText(_("Delete Appointment"))
        self.refresh_button.setText(_("Refresh"))
        # Update list display header texts if applicable.
        self.load_appointments()