import json
import logging
from datetime import date, datetime

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout, QHBoxLayout,
    QComboBox, QCheckBox, QLineEdit, QLabel, QPushButton, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QFileDialog, QMessageBox
)
from styles import BUTTON_STYLE, GROUPBOX_STYLE, HEADER_LABEL_STYLE

# Billing service to process and record the billing details.
class BillService:
    @staticmethod
    def process_bill(app, patient, services_sold, inventory_items, additional_charges, total):
        """
        Processes the bill by adding a BillingRecord to the database.
        Returns an invoice number.
        """
        try:
            from main import session_scope, BillingRecord
            bill_details = {"services": services_sold, "inventory": inventory_items, "additional": additional_charges}
            with session_scope() as session:
                new_bill = BillingRecord(
                    date=date.today(),
                    total=total,
                    details=json.dumps(bill_details)
                )
                session.add(new_bill)
            invoice_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return invoice_no
        except Exception as e:
            logging.exception("Failed to process bill")
            QMessageBox.critical(app, "Error", f"Failed to process bill: {e}")
            return "Error"

class BillingTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        try:
            from main import _  
            self._ = _
        except Exception:
            self._ = lambda s: s
        self.selected_inventory = []
        self.build_ui()

    def build_ui(self):
        try:
            layout = QVBoxLayout(self)
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            layout.addWidget(scroll)
            self.inner = QWidget()
            self.inner_layout = QVBoxLayout(self.inner)
            scroll.setWidget(self.inner)
            self.build_form()
        except Exception as e:
            logging.exception("Error initializing Billing UI")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def build_form(self):
        try:
            # Patient Selection Group
            self.patient_group = QGroupBox(self._("Select Patient"))
            self.patient_group.setStyleSheet(GROUPBOX_STYLE)
            pat_layout = QVBoxLayout(self.patient_group)
            self.patient_combo = QComboBox()
            pat_layout.addWidget(self.patient_combo)
            self.load_patients()
            self.inner_layout.addWidget(self.patient_group)

            # Service Prices Group
            self.service_group = QGroupBox(self._("Service Prices"))
            self.service_group.setStyleSheet(GROUPBOX_STYLE)
            service_layout = QGridLayout()
            self.service_checkboxes = {}
            self.service_price_entries = {}
            self.service_qty_entries = {}
            header_labels = [self._("Service"), self._("Price"), self._("Quantity")]
            for col_idx, text in enumerate(header_labels):
                header_label = QLabel(text)
                header_label.setStyleSheet("font-weight: bold; " + HEADER_LABEL_STYLE)
                service_layout.addWidget(header_label, 0, col_idx)
            default_services = {
                "Consultation": 50.0,
                "Vaccination": 100.0,
                "X-Ray": 150.0,
                "Blood Test": 80.0,
                "Shaving": 30.0,
                "Sonar": 40.0,
                "Shower": 25.0,
                "Nails Cut": 20.0,
                "Nails Cut (Aggressive)": 30.0,
                "Shaving (Small Areas)": 15.0,
                "Sterilization Surgery (Male Cat)": 200.0,
                "Sterilization Surgery (Female Cat)": 250.0,
                "Sterilization Surgery (Male Dog)": 300.0,
                "Sterilization Surgery (Female Dog)": 350.0,
                "Canula": 10.0,
                "IV": 50.0
            }
            row = 1
            for svc, price in default_services.items():
                checkbox = QCheckBox(self._(svc))
                self.service_checkboxes[svc] = checkbox
                service_layout.addWidget(checkbox, row, 0)
                price_edit = QLineEdit()
                price_edit.setText(str(price))
                price_edit.setMaximumWidth(80)
                self.service_price_entries[svc] = price_edit
                service_layout.addWidget(price_edit, row, 1)
                qty_edit = QLineEdit()
                qty_edit.setText("1")
                qty_edit.setMaximumWidth(50)
                self.service_qty_entries[svc] = qty_edit
                service_layout.addWidget(qty_edit, row, 2)
                row += 1
            service_table_layout = QVBoxLayout()
            service_table_layout.addLayout(service_layout)
            other_layout = QHBoxLayout()
            lbl_other = QLabel(self._("Other Service:"))
            self.other_desc = QLineEdit()
            lbl_price = QLabel(self._("Price:"))
            self.other_price = QLineEdit()
            lbl_qty = QLabel(self._("Quantity:"))
            self.other_qty = QLineEdit()
            self.other_qty.setText("1")
            other_layout.addWidget(lbl_other)
            other_layout.addWidget(self.other_desc)
            other_layout.addWidget(lbl_price)
            other_layout.addWidget(self.other_price)
            other_layout.addWidget(lbl_qty)
            other_layout.addWidget(self.other_qty)
            v_layout = QVBoxLayout()
            v_layout.addLayout(service_table_layout)
            v_layout.addLayout(other_layout)
            self.service_group.setLayout(v_layout)
            self.inner_layout.addWidget(self.service_group)

            # Additional Charges Group
            self.extra_group = QGroupBox(self._("Additional Charges"))
            self.extra_group.setStyleSheet(GROUPBOX_STYLE)
            extra_layout = QHBoxLayout(self.extra_group)
            self.tax_entry = QLineEdit()
            self.tax_entry.setPlaceholderText(self._("Tax % (Optional)"))
            self.discount_entry = QLineEdit()
            self.discount_entry.setPlaceholderText(self._("Discount % (Optional)"))
            extra_layout.addWidget(self.tax_entry)
            extra_layout.addWidget(self.discount_entry)
            self.inner_layout.addWidget(self.extra_group)

            # Inventory Selection Group
            self.inv_sel_group = QGroupBox(self._("Select Inventory Item"))
            self.inv_sel_group.setStyleSheet(GROUPBOX_STYLE)
            inv_sel_layout = QHBoxLayout(self.inv_sel_group)
            self.inv_combo = QComboBox()
            self.inv_combo.setEditable(True)
            inv_sel_layout.addWidget(self.inv_combo)
            self.inv_qty = QLineEdit()
            self.inv_qty.setMaximumWidth(50)
            inv_sel_layout.addWidget(self.inv_qty)
            add_inv_btn = QPushButton(self._("Add Item"))
            add_inv_btn.setStyleSheet(BUTTON_STYLE)
            add_inv_btn.clicked.connect(self.add_inventory_item)
            inv_sel_layout.addWidget(add_inv_btn)
            self.inner_layout.addWidget(self.inv_sel_group)
            self.load_inventory_items()

            # Inventory Tree Group
            self.inv_tree_group = QGroupBox(self._("Inventory Used"))
            self.inv_tree_group.setStyleSheet(GROUPBOX_STYLE)
            inv_tree_layout = QVBoxLayout(self.inv_tree_group)
            self.inv_tree = QTreeWidget()
            self.inv_tree.setHeaderLabels([self._("Item"), self._("Qty"), self._("Price"), self._("Total")])
            inv_tree_layout.addWidget(self.inv_tree)
            self.inner_layout.addWidget(self.inv_tree_group)

            # Notes Group
            self.notes_group = QGroupBox(self._("Notes"))
            self.notes_group.setStyleSheet(GROUPBOX_STYLE)
            notes_layout = QVBoxLayout(self.notes_group)
            self.notes_text = QTextEdit()
            self.notes_text.setFixedHeight(100)
            notes_layout.addWidget(self.notes_text)
            self.inner_layout.addWidget(self.notes_group)

            # Buttons for Generate, Email, and Print Bill.
            btn_layout = QHBoxLayout()
            generate_btn = QPushButton(self._("Generate Bill"))
            generate_btn.setStyleSheet(BUTTON_STYLE)
            generate_btn.clicked.connect(self.generate_bill)
            email_btn = QPushButton(self._("Email Bill"))
            email_btn.setStyleSheet(BUTTON_STYLE)
            email_btn.clicked.connect(self.email_bill)
            print_btn = QPushButton(self._("Print Bill"))
            print_btn.setStyleSheet(BUTTON_STYLE)
            print_btn.clicked.connect(self.print_bill)
            btn_layout.addWidget(generate_btn)
            btn_layout.addWidget(email_btn)
            btn_layout.addWidget(print_btn)
            self.inner_layout.addLayout(btn_layout)

            # Bill Display Group
            self.bill_group = QGroupBox(self._("Bill"))
            self.bill_group.setStyleSheet(GROUPBOX_STYLE)
            bill_layout = QVBoxLayout(self.bill_group)
            self.bill_display = QTextEdit()
            self.bill_display.setReadOnly(True)
            bill_layout.addWidget(self.bill_display)
            self.inner_layout.addWidget(self.bill_group)
        except Exception as e:
            logging.exception("Error building billing form")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def load_patients(self):
        try:
            from main import session_scope, User
            with session_scope() as session:
                patients = session.query(User).all()
                self.patient_map = {f"{p.user_name} ({p.phone_number})": p.id for p in patients}
                self.patient_combo.clear()
                self.patient_combo.addItem(self._("Walk-In"))
                self.patient_combo.addItems(list(self.patient_map.keys()))
        except Exception as e:
            logging.exception("Error loading patients")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def load_inventory_items(self):
        try:
            from main import session_scope, InventoryItem
            with session_scope() as session:
                items = session.query(InventoryItem).all()
                names = [item.item_name for item in items]
            self.inv_combo.clear()
            self.inv_combo.addItems(names)
        except Exception as e:
            logging.exception("Error loading inventory items")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def add_inventory_item(self):
        try:
            name = self.inv_combo.currentText().strip()
            try:
                qty = int(self.inv_qty.text())
                if qty <= 0:
                    raise ValueError(self._("Quantity must be a positive integer."))
            except ValueError:
                raise ValueError(self._("Invalid quantity"))
            from main import session_scope, InventoryItem
            with session_scope() as session:
                item = session.query(InventoryItem).filter_by(item_name=name).first()
                if not item:
                    raise ValueError(self._("Item not found"))
                if item.stock_count < qty:
                    raise ValueError(self._("Insufficient stock"))
                price = item.selling_price
                total = price * qty
                tree_item = QTreeWidgetItem([name, str(qty), f"LE{price:.2f}", f"LE{total:.2f}"])
                self.inv_tree.addTopLevelItem(tree_item)
                self.selected_inventory.append((name, qty, price))
                item.stock_count -= qty
        except Exception as e:
            logging.exception("Error adding inventory item")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def generate_bill(self):
        try:
            patient = self.patient_combo.currentText() or self._("Walk-In")
            total = 0.0
            invoice_lines = []
            services_sold = {}
            invoice_lines.append(f"{self._('Patient')}: {patient}")
            invoice_lines.append(f"{self._('Invoice Date')}: {date.today().strftime('%Y-%m-%d')}")
            invoice_lines.append(f"\n{self._('Services')}:")
            for svc, checkbox in self.service_checkboxes.items():
                if checkbox.isChecked():
                    try:
                        price = float(self.service_price_entries[svc].text())
                        qty = int(self.service_qty_entries[svc].text())
                        if price < 0 or qty <= 0:
                            raise ValueError
                    except ValueError:
                        raise ValueError(self._(f"Invalid price or quantity for {svc}"))
                    line_total = price * qty
                    invoice_lines.append(f" - {svc} x{qty}: LE{line_total:.2f}")
                    total += line_total
                    services_sold[svc] = services_sold.get(svc, 0) + qty
            desc = self.other_desc.text().strip()
            price_str = self.other_price.text().strip()
            qty_str = self.other_qty.text().strip()
            if desc and price_str and qty_str:
                try:
                    pr = float(price_str)
                    qt = int(qty_str)
                    if pr < 0 or qt <= 0:
                        raise ValueError
                except ValueError:
                    raise ValueError(self._("Invalid price or quantity for other service"))
                line_total = pr * qt
                invoice_lines.append(f" - {desc} x{qt}: LE{line_total:.2f}")
                total += line_total
                services_sold[desc] = services_sold.get(desc, 0) + qt
            if self.selected_inventory:
                invoice_lines.append(f"\n{self._('Inventory Used')}:")
                for name, qty, price in self.selected_inventory:
                    lt = price * qty
                    invoice_lines.append(f" - {name} x{qty}: LE{lt:.2f}")
                    total += lt
            additional = {"tax": 0.0, "discount": 0.0}
            try:
                tax_percent = float(self.tax_entry.text()) if self.tax_entry.text().strip() else 0.0
                discount_percent = float(self.discount_entry.text()) if self.discount_entry.text().strip() else 0.0
            except ValueError:
                raise ValueError(self._("Invalid tax or discount percentage"))
            if discount_percent:
                discount_val = (discount_percent / 100.0) * total
                additional["discount"] = discount_val
                invoice_lines.append(f"{self._('Discount')} ({discount_percent}%): -LE{discount_val:.2f}")
                total -= discount_val
            if tax_percent:
                tax_val = (tax_percent / 100.0) * total
                additional["tax"] = tax_val
                invoice_lines.append(f"\n{self._('Tax')} ({tax_percent}%): LE{tax_val:.2f}")
                total += tax_val
            invoice_lines.append(f"\n{self._('Total Bill')}: LE{total:.2f}")
            invoice_no = BillService.process_bill(self.app, patient, services_sold, self.selected_inventory, additional, total)
            header = f"{self._('Invoice Number')}: {invoice_no}\n{self._('Date')}: {date.today().strftime('%Y-%m-%d')}\n\n"
            final_bill = header + "\n".join(invoice_lines)
            self.bill_display.setPlainText(final_bill)
            QMessageBox.information(self.app, self._("Bill Generated"), self._("The bill has been generated."))
            if hasattr(self.app, 'inventory_tab'):
                self.app.inventory_tab.refresh_inventory_tree()
        except Exception as e:
            logging.exception("Error generating bill")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def email_bill(self):
        try:
            QMessageBox.information(self.app, self._("Email Bill"), self._("This feature is not implemented yet."))
        except Exception as e:
            logging.exception("Error emailing bill")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def print_bill(self):
        try:
            content = self.bill_display.toPlainText().strip()
            if not content:
                raise ValueError(self._("No bill to print"))
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                self.bill_display.print_(printer)
                QMessageBox.information(self.app, self._("Success"), self._("Bill printed successfully"))
        except Exception as e:
            logging.exception("Error printing bill")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def refresh_language(self):
        try:
            _ = self.app._
            self.patient_group.setTitle(_( "Select Patient"))
            self.service_group.setTitle(_( "Service Prices"))
            for svc, checkbox in self.service_checkboxes.items():
                checkbox.setText(_(svc))
            self.inv_sel_group.setTitle(_( "Select Inventory Item"))
            self.inv_tree_group.setTitle(_( "Inventory Used"))
            self.notes_group.setTitle(_( "Notes"))
            self.bill_group.setTitle(_( "Bill"))
            self.extra_group.setTitle(_( "Additional Charges"))
            self.load_patients()
            self.load_inventory_items()
        except Exception as e:
            logging.exception("Error refreshing language")
            QMessageBox.critical(self.app, self._("Error"), str(e))
