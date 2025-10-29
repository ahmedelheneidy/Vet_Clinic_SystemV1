# patient.py

import logging
from datetime import date, timedelta

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTreeWidget, QTreeWidgetItem, QDialog, QMessageBox, QComboBox,
    QDateEdit, QListWidget, QDialogButtonBox
)

from styles import BUTTON_STYLE, GROUPBOX_STYLE, HEADER_LABEL_STYLE, LISTSTYLE

# Vaccine options per pet type.
VACCINES_BY_TYPE = {
    "Dog": ["ثنائي", "خماسي", "ثماني", "Rabies (مصري)", "Rabies (هندي)", "Rabies (امريي)"],
    "Cat": ["ثلاثي", "رباعي", "Rabies (مصري)", "Rabies (هندي)", "Rabies (امريي)"],
    "Bird": ["Bird Vaccine A", "Bird Vaccine B"],
    "Other": ["Other"],
}

def show_error(widget, title, message):
    """Helper to display an error message and log it."""
    logging.error(message)
    QMessageBox.critical(widget, title, message)

class PatientManagementTab(QWidget):
    def __init__(self, app):
        super().__init__()
        # Import required objects from main.
        from main import session_scope, User, Pet, Vaccine, _, validate_phone, validate_weight, CURRENT_LANG
        self.app = app
        self.session_scope = session_scope
        self.User = User
        self.Pet = Pet
        self.Vaccine = Vaccine
        self._ = _
        self.validate_phone = validate_phone
        self.validate_weight = validate_weight
        self.rtl = (CURRENT_LANG == "ar")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top buttons.
        btn_layout = QHBoxLayout()
        self.btn_add_pet = QPushButton(self._("➕ Add Pet"))
        self.btn_add_pet.setStyleSheet(BUTTON_STYLE)
        self.btn_add_pet.clicked.connect(self.add_pet_gui)

        self.btn_delete_pet = QPushButton(self._("🗑 Delete Pet"))
        self.btn_delete_pet.setStyleSheet(BUTTON_STYLE)
        self.btn_delete_pet.clicked.connect(self.delete_pet_gui)

        self.btn_modify_record = QPushButton(self._("✏️ Modify Record"))
        self.btn_modify_record.setStyleSheet(BUTTON_STYLE)
        self.btn_modify_record.clicked.connect(self.modify_record_gui)

        self.btn_vaccine_rem = QPushButton(self._("💉 Vaccine Reminders"))
        self.btn_vaccine_rem.setStyleSheet(BUTTON_STYLE)
        self.btn_vaccine_rem.clicked.connect(self.vaccine_reminders_gui)

        self.btn_calendar = QPushButton(self._("📅 View Vaccine Calendar"))
        self.btn_calendar.setStyleSheet(BUTTON_STYLE)
        self.btn_calendar.clicked.connect(self.view_vaccine_calendar)

        self.btn_refresh = QPushButton(self._("🔁 Refresh Records"))
        self.btn_refresh.setStyleSheet(BUTTON_STYLE)
        self.btn_refresh.clicked.connect(self.show_records)

        for btn in [self.btn_add_pet, self.btn_delete_pet, self.btn_modify_record,
                    self.btn_vaccine_rem, self.btn_calendar, self.btn_refresh]:
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        # Search layout.
        search_layout = QHBoxLayout()
        self.lbl_search = QLabel(self._("Search:"))
        self.lbl_search.setStyleSheet(HEADER_LABEL_STYLE)
        self.search_entry = QLineEdit()
        self.search_entry.setStyleSheet("font-size: 16px; padding: 5px;")
        self.btn_go = QPushButton(self._("Go"))
        self.btn_go.setStyleSheet(BUTTON_STYLE)
        self.btn_go.clicked.connect(self.search_records)
        search_layout.addWidget(self.lbl_search)
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(self.btn_go)
        layout.addLayout(search_layout)

        # Tree widget to display records.
        self.tree = QTreeWidget()
        self.tree.setStyleSheet(LISTSTYLE)
        self.tree.setColumnCount(10)
        self.tree.setHeaderLabels([
            self._("Name"), self._("Phone"), self._("Pet"),
            self._("Type"), self._("Gender"), self._("Age (Months)"),
            self._("Weight"), self._("Vaccine Type"), self._("Vaccine Date"),
            self._("Next Vaccine Date")
        ])
        self.tree.setSortingEnabled(True)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.tree)
        self.show_records()

        self.setLayout(layout)

    def refresh_language(self):
        try:
            _ = self.app._
        except AttributeError:
            from main import _
        self.btn_add_pet.setText(_( "➕ Add Pet"))
        self.btn_delete_pet.setText(_( "🗑 Delete Pet"))
        self.btn_modify_record.setText(_( "✏️ Modify Record"))
        self.btn_vaccine_rem.setText(_( "💉 Vaccine Reminders"))
        self.btn_calendar.setText(_( "📅 View Vaccine Calendar"))
        self.btn_refresh.setText(_( "🔁 Refresh Records"))
        self.lbl_search.setText(_( "Search:"))
        self.btn_go.setText(_( "Go"))
        headers = [
            _( "Name"), _( "Phone"), _( "Pet"),
            _( "Type"), _( "Gender"), _( "Age (Months)"),
            _( "Weight"), _( "Vaccine Type"), _( "Vaccine Date"),
            _( "Next Vaccine Date")
        ]
        self.tree.setHeaderLabels(headers)
        self.show_records()

    def clear_tree(self):
        self.tree.clear()

    def show_records(self, query=None):
        """Display user and pet records, optionally filtered by query."""
        try:
            self.clear_tree()
            with self.session_scope() as session:
                q = session.query(self.User)
                if query:
                    q = q.filter(
                        (self.User.user_name.ilike(f"%{query}%")) |
                        (self.User.phone_number.ilike(f"%{query}%")) |
                        (self.User.pets.any(self.Pet.pet_name.ilike(f"%{query}%")))
                    )
                users = q.all()
                for user in users:
                    for pet in user.pets:
                        if hasattr(pet, "vaccines") and pet.vaccines:
                            latest = sorted(pet.vaccines, key=lambda v: v.vaccine_date, reverse=True)[0]
                            vaccine_type = latest.vaccine_type
                            vaccine_date_str = latest.vaccine_date.strftime("%Y-%m-%d")
                            next_vaccine_date_str = (latest.next_vaccine_date.strftime("%Y-%m-%d")
                                                     if latest.next_vaccine_date else "")
                        else:
                            vaccine_type = ""
                            vaccine_date_str = ""
                            next_vaccine_date_str = ""
                        item = QTreeWidgetItem([
                            user.user_name,
                            user.phone_number,
                            pet.pet_name,
                            pet.type,
                            pet.gender,
                            str(pet.age),
                            str(pet.weight),
                            vaccine_type,
                            vaccine_date_str,
                            next_vaccine_date_str
                        ])
                        # Highlight if vaccine is due today.
                        if next_vaccine_date_str and date.today().strftime("%Y-%m-%d") == next_vaccine_date_str:
                            for i in range(item.columnCount()):
                                item.setBackground(i, QBrush(QColor("yellow")))
                        self.tree.addTopLevelItem(item)
        except Exception as e:
            show_error(self.app, self._("Error"), self._("Failed to display records: ") + str(e))

    def get_selected_item(self) -> QTreeWidgetItem | None:
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.warning(self.app, self._("Warning"), self._("No record selected."))
            return None
        return items[0]

    def open_vaccine_dialog(self, pet_type: str):
        """Display a dialog for adding a vaccine record for a pet."""
        dialog = QDialog(self.app)
        dialog.setWindowTitle(self._("Add Vaccine Record"))
        form = QtWidgets.QFormLayout(dialog)
        options = list(VACCINES_BY_TYPE.get(pet_type, []))
        if "Other" not in options:
            options.append("Other")
        vaccine_type_combo = QComboBox()
        vaccine_type_combo.addItems(options)
        custom_entry = QLineEdit()
        custom_entry.setEnabled(False)
        vaccine_date_edit = QDateEdit()
        vaccine_date_edit.setDisplayFormat("yyyy-MM-dd")
        vaccine_date_edit.setCalendarPopup(True)
        vaccine_date_edit.setDate(QDate.currentDate())
        next_vaccine_combo = QComboBox()
        next_vaccine_combo.addItems(["1 week", "2 weeks", "3 weeks", "1 month", "1 year"])

        form.addRow(self._("Vaccine Type"), vaccine_type_combo)
        form.addRow(self._("Specify Vaccine Type"), custom_entry)
        form.addRow(self._("Vaccine Date"), vaccine_date_edit)
        form.addRow(self._("Next Vaccine In"), next_vaccine_combo)

        def on_vaccine_type_change(index):
            if vaccine_type_combo.currentText().lower() == "other":
                custom_entry.setEnabled(True)
            else:
                custom_entry.clear()
                custom_entry.setEnabled(False)
        vaccine_type_combo.currentIndexChanged.connect(on_vaccine_type_change)

        btn_box = QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btn_box)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            try:
                if vaccine_type_combo.currentText().lower() == "other":
                    vt = custom_entry.text().strip()
                    if not vt:
                        QMessageBox.critical(self.app, self._("Error"), self._("Please specify the vaccine type."))
                        return None
                    # Update vaccine types list if new type is provided.
                    if pet_type in VACCINES_BY_TYPE:
                        if vt not in VACCINES_BY_TYPE[pet_type]:
                            try:
                                idx = VACCINES_BY_TYPE[pet_type].index("Other")
                                VACCINES_BY_TYPE[pet_type].insert(idx, vt)
                            except ValueError:
                                VACCINES_BY_TYPE[pet_type].append(vt)
                    else:
                        VACCINES_BY_TYPE[pet_type] = [vt, "Other"]
                    vaccine_type = vt
                else:
                    vaccine_type = vaccine_type_combo.currentText()

                vaccine_date = vaccine_date_edit.date().toPyDate()
                next_str = next_vaccine_combo.currentText()
                if "1 week" in next_str:
                    td = timedelta(weeks=1)
                elif "2 weeks" in next_str:
                    td = timedelta(weeks=2)
                elif "3 weeks" in next_str:
                    td = timedelta(weeks=3)
                elif "1 month" in next_str:
                    td = timedelta(days=30)
                elif "1 year" in next_str:
                    td = timedelta(days=365)
                else:
                    td = timedelta(0)
                next_vaccine_date = vaccine_date + td
                return {
                    "vaccine_type": vaccine_type,
                    "vaccine_date": vaccine_date,
                    "next_vaccine_date": next_vaccine_date
                }
            except Exception as e:
                show_error(self.app, self._("Error"), self._("Failed to create vaccine record: ") + str(e))
                return None
        return None

    def add_pet_gui(self):
        dialog = QDialog(self.app)
        dialog.setWindowTitle(self._("Add Pet"))
        layout = QVBoxLayout(dialog)
        form_layout = QtWidgets.QFormLayout()

        phone_entry = QLineEdit()
        name_entry = QLineEdit()
        email_entry = QLineEdit()
        email_entry.setPlaceholderText(self._("Email (optional)"))
        address_entry = QLineEdit()
        address_entry.setPlaceholderText(self._("Address (optional)"))
        pet_entry = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(["Dog", "Cat", "Bird", "Other"])
        gender_combo = QComboBox()
        gender_combo.addItems(["Male", "Female"])
        age_entry = QLineEdit()
        weight_entry = QLineEdit()

        form_layout.addRow(self._("Phone Number"), phone_entry)
        form_layout.addRow(self._("User Name"), name_entry)
        form_layout.addRow(self._("Email"), email_entry)
        form_layout.addRow(self._("Address"), address_entry)
        form_layout.addRow(self._("Pet Name"), pet_entry)
        form_layout.addRow(self._("Type"), type_combo)
        form_layout.addRow(self._("Gender"), gender_combo)
        form_layout.addRow(self._("Age (Months)"), age_entry)
        form_layout.addRow(self._("Weight (kg)"), weight_entry)
        layout.addLayout(form_layout)

        vaccine_records = []
        vaccine_list_widget = QListWidget()
        btn_add_vaccine = QPushButton(self._("Add Vaccine"))
        btn_add_vaccine.setStyleSheet(BUTTON_STYLE)

        def add_vaccine_record():
            pet_type = type_combo.currentText()
            record = self.open_vaccine_dialog(pet_type)
            if record is not None:
                vaccine_records.append(record)
                summary = f"{record['vaccine_type']} on {record['vaccine_date'].strftime('%Y-%m-%d')} (next: {record['next_vaccine_date'].strftime('%Y-%m-%d')})"
                vaccine_list_widget.addItem(summary)
        btn_add_vaccine.clicked.connect(add_vaccine_record)

        layout.addWidget(QLabel(self._("Vaccine Records")))
        layout.addWidget(vaccine_list_widget)
        layout.addWidget(btn_add_vaccine)

        def save_pet():
            try:
                phone = self.validate_phone(phone_entry.text().strip())
                if not phone:
                    raise ValueError(self._("Invalid phone number. Use digits only (8–15 characters, optional '+')."))
                with self.session_scope() as session:
                    user = session.query(self.User).filter_by(phone_number=phone).first()
                    if not user:
                        uname = name_entry.text().strip()
                        if not uname:
                            raise ValueError(self._("User name cannot be empty."))
                        user = self.User(
                            user_name=uname,
                            phone_number=phone,
                            email=email_entry.text().strip() or None,
                            address=address_entry.text().strip() or None
                        )
                        session.add(user)
                        session.flush()
                    pet_name_val = pet_entry.text().strip()
                    if not pet_name_val:
                        raise ValueError(self._("Pet name cannot be empty."))
                    if any(p.pet_name.lower() == pet_name_val.lower() for p in user.pets):
                        raise ValueError(self._("This pet already exists for this user."))
                    pet_type = type_combo.currentText()
                    gender = gender_combo.currentText()
                    try:
                        age_val = float(age_entry.text())
                        if age_val < 0:
                            raise ValueError
                    except ValueError:
                        raise ValueError(self._("Invalid age. Please enter a positive number (months)."))
                    weight_val = self.validate_weight(weight_entry.text().strip())
                    if weight_val is None:
                        raise ValueError(self._("Invalid weight. Enter a positive number."))
                    new_pet = self.Pet(
                        owner=user,
                        pet_name=pet_name_val,
                        type=pet_type,
                        gender=gender,
                        age=int(age_val),
                        weight=weight_val
                    )
                    session.add(new_pet)
                    session.flush()
                    for record in vaccine_records:
                        new_vaccine = self.Vaccine(
                            pet=new_pet,
                            vaccine_type=record["vaccine_type"],
                            vaccine_date=record["vaccine_date"],
                            next_vaccine_date=record["next_vaccine_date"]
                        )
                        session.add(new_vaccine)
                QMessageBox.information(
                    self.app, self._("Success"),
                    self._("Pet '{pet}' added successfully.").format(pet=pet_name_val)
                )
                dialog.accept()
                self.show_records()
                if hasattr(self.app, 'billing_tab'):
                    self.app.billing_tab.load_patients()
            except Exception as e:
                show_error(dialog, self._("Error"), str(e))
        btn_save = QPushButton(self._("Save"))
        btn_save.setStyleSheet(BUTTON_STYLE)
        btn_save.clicked.connect(save_pet)
        layout.addWidget(btn_save, alignment=QtCore.Qt.AlignCenter)
        dialog.exec_()

    def delete_pet_gui(self):
        selected_item = self.get_selected_item()
        if not selected_item:
            return
        phone = selected_item.text(1)
        pet_name = selected_item.text(2)
        reply = QMessageBox.question(
            self.app,
            self._("Confirm Delete"),
            self._("Are you sure you want to delete pet '{pet}'?").format(pet=pet_name),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                with self.session_scope() as session:
                    user = session.query(self.User).filter_by(phone_number=phone).first()
                    if user:
                        pet = next((p for p in user.pets if p.pet_name.lower() == pet_name.lower()), None)
                        if pet:
                            session.delete(pet)
                QMessageBox.information(
                    self.app, self._("Deleted"),
                    self._("Pet '{pet}' deleted.").format(pet=pet_name)
                )
                self.show_records()
            except Exception as e:
                show_error(self.app, self._("Error"), self._("Failed to delete pet: ") + str(e))

    def modify_record_gui(self):
        selected_item = self.get_selected_item()
        if not selected_item:
            return
        phone = selected_item.text(1)
        pet_name = selected_item.text(2)
        try:
            with self.session_scope() as session:
                user = session.query(self.User).filter_by(phone_number=phone).first()
                if not user:
                    raise ValueError(self._("User not found."))
                pet_obj = next((p for p in user.pets if p.pet_name.lower() == pet_name.lower()), None)
                if not pet_obj:
                    raise ValueError(self._("Pet not found."))
                current_user_name = user.user_name
                pet_data = {
                    "pet_name": pet_obj.pet_name,
                    "type": pet_obj.type,
                    "gender": pet_obj.gender,
                    "age": pet_obj.age,
                    "weight": pet_obj.weight,
                }
                existing_vaccines = []
                if hasattr(pet_obj, "vaccines"):
                    for vac in pet_obj.vaccines:
                        summary = f"{vac.vaccine_type} on {vac.vaccine_date.strftime('%Y-%m-%d')} (next: {vac.next_vaccine_date.strftime('%Y-%m-%d') if vac.next_vaccine_date else ''})"
                        existing_vaccines.append(summary)
                pet_id = pet_obj.id
        except Exception as e:
            show_error(self.app, self._("Error"), self._("Failed to retrieve record: ") + str(e))
            return

        dialog = QDialog(self.app)
        dialog.setWindowTitle(self._("Modify Record for {pet}").format(pet=pet_data["pet_name"]))
        layout = QtWidgets.QGridLayout(dialog)
        row = 0
        layout.addWidget(QLabel(self._("User Information")), row, 0, 1, 2)
        row += 1

        lbl_user_name = QLabel(self._("User Name"))
        user_name_entry = QLineEdit()
        user_name_entry.setText(current_user_name)
        layout.addWidget(lbl_user_name, row, 0)
        layout.addWidget(user_name_entry, row, 1)
        row += 1

        layout.addWidget(QLabel(self._("Pet Information")), row, 0, 1, 2)
        row += 1

        lbl_pet_name = QLabel(self._("Pet Name"))
        pet_name_entry = QLineEdit()
        pet_name_entry.setText(pet_data["pet_name"])
        layout.addWidget(lbl_pet_name, row, 0)
        layout.addWidget(pet_name_entry, row, 1)
        row += 1

        lbl_type = QLabel(self._("Type"))
        type_combo = QComboBox()
        type_combo.addItems(list(VACCINES_BY_TYPE.keys()))
        type_combo.setCurrentText(pet_data["type"])
        layout.addWidget(lbl_type, row, 0)
        layout.addWidget(type_combo, row, 1)
        row += 1

        lbl_gender = QLabel(self._("Gender"))
        gender_combo = QComboBox()
        gender_combo.addItems(["Male", "Female"])
        gender_combo.setCurrentText(pet_data["gender"])
        layout.addWidget(lbl_gender, row, 0)
        layout.addWidget(gender_combo, row, 1)
        row += 1

        lbl_age = QLabel(self._("Age (Months)"))
        age_entry = QLineEdit()
        age_entry.setText(str(pet_data["age"]))
        layout.addWidget(lbl_age, row, 0)
        layout.addWidget(age_entry, row, 1)
        row += 1

        lbl_weight = QLabel(self._("Weight (kg)"))
        weight_entry = QLineEdit()
        weight_entry.setText(str(pet_data["weight"]))
        layout.addWidget(lbl_weight, row, 0)
        layout.addWidget(weight_entry, row, 1)
        row += 1

        vaccine_list_widget = QListWidget()
        for rec in existing_vaccines:
            vaccine_list_widget.addItem(rec)
        new_vaccine_records = []
        btn_add_vaccine = QPushButton(self._("Add Vaccine"))
        btn_add_vaccine.setStyleSheet(BUTTON_STYLE)
        def add_vaccine_record_mod():
            pet_type = type_combo.currentText()
            record = self.open_vaccine_dialog(pet_type)
            if record is not None:
                new_vaccine_records.append(record)
                summary = f"{record['vaccine_type']} on {record['vaccine_date'].strftime('%Y-%m-%d')} (next: {record['next_vaccine_date'].strftime('%Y-%m-%d')})"
                vaccine_list_widget.addItem(summary)
        btn_add_vaccine.clicked.connect(add_vaccine_record_mod)
        layout.addWidget(QLabel(self._("Vaccine Records")), row, 0, 1, 2)
        row += 1
        layout.addWidget(vaccine_list_widget, row, 0, 1, 2)
        row += 1

        def save_modifications():
            try:
                new_user_name = user_name_entry.text().strip()
                if not new_user_name:
                    raise ValueError(self._("User name cannot be empty."))
                new_pet_name = pet_name_entry.text().strip()
                if not new_pet_name:
                    raise ValueError(self._("Pet name cannot be empty."))
                new_type = type_combo.currentText()
                new_gender = gender_combo.currentText()
                try:
                    new_age = float(age_entry.text())
                    if new_age < 0:
                        raise ValueError
                except ValueError:
                    raise ValueError(self._("Invalid age. Please enter a positive number (months)."))
                new_weight = self.validate_weight(weight_entry.text().strip())
                if new_weight is None:
                    raise ValueError(self._("Invalid weight. Enter a positive number."))
                with self.session_scope() as session:
                    user_to_update = session.query(self.User).filter_by(phone_number=phone).first()
                    pet_to_update = session.query(self.Pet).get(pet_id)
                    if user_to_update is None or pet_to_update is None:
                        raise ValueError(self._("Record not found in the database."))
                    user_to_update.user_name = new_user_name
                    pet_to_update.pet_name = new_pet_name
                    pet_to_update.type = new_type
                    pet_to_update.gender = new_gender
                    pet_to_update.age = int(new_age)
                    pet_to_update.weight = new_weight
                    for record in new_vaccine_records:
                        new_vac = self.Vaccine(
                            pet=pet_to_update,
                            vaccine_type=record["vaccine_type"],
                            vaccine_date=record["vaccine_date"],
                            next_vaccine_date=record["next_vaccine_date"]
                        )
                        session.add(new_vac)
                QMessageBox.information(self.app, self._("Success"), self._("Record updated successfully."))
                dialog.accept()
                self.show_records()
            except Exception as ex:
                show_error(dialog, self._("Error"), str(ex))
        btn_save = QPushButton(self._("Save Changes"))
        btn_save.setStyleSheet(BUTTON_STYLE)
        btn_save.clicked.connect(save_modifications)
        layout.addWidget(btn_save, row, 0, 1, 2)
        dialog.exec_()

    def vaccine_reminders_gui(self):
        try:
            today_date = date.today()
            with self.session_scope() as session:
                pets_due = session.query(self.Vaccine).filter(self.Vaccine.next_vaccine_date == today_date).all()
                if not pets_due:
                    reminders = self._("No vaccine reminders today.")
                else:
                    reminders_list = []
                    for vac in pets_due:
                        reminders_list.append(
                            f"⚠ {vac.pet.pet_name} ({vac.pet.owner.user_name}) is due for vaccine {vac.vaccine_type} on {vac.next_vaccine_date.strftime('%Y-%m-%d')}"
                        )
                    reminders = "\n".join(reminders_list)
            QMessageBox.information(self.app, self._("Vaccine Reminders"), reminders)
        except Exception as e:
            show_error(self.app, self._("Error"), self._("Failed to retrieve reminders: ") + str(e))

    def search_records(self):
        query = self.search_entry.text().strip()
        self.show_records(query=query)

    def view_vaccine_calendar(self):
        """Display a calendar with highlighted vaccine dates."""
        try:
            dialog = QDialog(self.app)
            dialog.setWindowTitle(self._("Vaccine Calendar"))
            dialog.resize(600, 400)
            layout = QtWidgets.QVBoxLayout(dialog)
            calendar = QtWidgets.QCalendarWidget()
            layout.addWidget(calendar)
            details = QtWidgets.QTextEdit()
            details.setReadOnly(True)
            layout.addWidget(details)
            appointments = {}
            with self.session_scope() as session:
                vaccines = session.query(self.Vaccine).all()
                for vac in vaccines:
                    if vac.next_vaccine_date:
                        d = QDate(vac.next_vaccine_date.year, vac.next_vaccine_date.month, vac.next_vaccine_date.day)
                        appointments.setdefault(d, []).append(
                            f"{vac.pet.pet_name} ({vac.pet.owner.user_name}) - {vac.vaccine_type}"
                        )
            from PyQt5.QtGui import QTextCharFormat
            fmt = QTextCharFormat()
            fmt.setBackground(QtCore.Qt.yellow)
            for apt_date in appointments:
                calendar.setDateTextFormat(apt_date, fmt)
            def update_details():
                selected = calendar.selectedDate()
                appts = appointments.get(selected, [])
                if appts:
                    details.setPlainText("\n".join(appts))
                else:
                    details.setPlainText(self._("No appointments for selected date."))
            calendar.selectionChanged.connect(update_details)
            update_details()
            dialog.exec_()
        except Exception as e:
            show_error(self.app, self._("Error"), self._("Failed to display vaccine calendar: ") + str(e))
