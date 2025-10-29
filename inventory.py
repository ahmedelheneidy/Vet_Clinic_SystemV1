# inventory.py

import logging
from datetime import date, timedelta

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QDateEdit, QCheckBox
)

from styles import BUTTON_STYLE, GROUPBOX_STYLE, HEADER_LABEL_STYLE, LISTSTYLE


class InventoryManagementTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        from main import session_scope, InventoryItem, _, CURRENT_LANG
        self.session_scope = session_scope
        self.InventoryItem = InventoryItem
        self._ = _
        self.rtl = (CURRENT_LANG == "ar")
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Search/filter bar.
        search_layout = QHBoxLayout()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(self._("Search inventory..."))
        self.search_entry.setStyleSheet("font-size: 16px; padding: 5px;")
        self.btn_search = QPushButton(self._("Search"))
        self.btn_search.setStyleSheet(BUTTON_STYLE)
        self.btn_search.clicked.connect(self.search_inventory)
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(self.btn_search)
        self.main_layout.addLayout(search_layout)
        
        # Add Inventory Item Group.
        self.add_group = QGroupBox(self._("Add Inventory Item"))
        self.add_group.setStyleSheet(GROUPBOX_STYLE)
        add_layout = QVBoxLayout(self.add_group)
        self.form_layout = QtWidgets.QGridLayout()

        # Item Name: using QComboBox with editable entries.
        self.inv_item_name = QComboBox()
        self.inv_item_name.setEditable(True)
        # Stock count and prices.
        self.inv_stock = QLineEdit()
        self.inv_purchase = QLineEdit()
        self.inv_selling = QLineEdit()
        # Purchase Date.
        self.inv_purchase_date = QDateEdit()
        self.inv_purchase_date.setDisplayFormat("yyyy-MM-dd")
        self.inv_purchase_date.setCalendarPopup(True)
        self.inv_purchase_date.setDate(QDate.currentDate())
        # Expiry Date: QDateEdit with a checkbox to disable it.
        self.inv_expiry = QDateEdit()
        self.inv_expiry.setDisplayFormat("yyyy-MM-dd")
        self.inv_expiry.setCalendarPopup(True)
        self.inv_expiry.setDate(QDate.currentDate())
        self.chk_no_expiry = QCheckBox(self._("No Expiry Date"))
        self.chk_no_expiry.stateChanged.connect(self.toggle_expiry)

        fields = [
            (self._("Item Name"), self.inv_item_name),
            (self._("Stock Count"), self.inv_stock),
            (self._("Purchase Price"), self.inv_purchase),
            (self._("Selling Price"), self.inv_selling),
            (self._("Purchase Date"), self.inv_purchase_date),
            (self._("Expiry Date"), self.inv_expiry),
        ]
        for idx, (label_txt, widget) in enumerate(fields):
            row, col = divmod(idx, 2)
            label = QLabel(label_txt)
            label.setStyleSheet(HEADER_LABEL_STYLE)
            self.form_layout.addWidget(label, row, col * 2)
            self.form_layout.addWidget(widget, row, col * 2 + 1)
        # Add the "No Expiry Date" checkbox after expiry field.
        self.form_layout.addWidget(self.chk_no_expiry, row + 1, 1)

        add_layout.addLayout(self.form_layout)
        self.btn_save = QPushButton(self._("Save"))
        self.btn_save.setStyleSheet(BUTTON_STYLE)
        self.btn_save.clicked.connect(self.add_inventory_item)
        add_layout.addWidget(self.btn_save, alignment=QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.add_group)

        # Buttons for Bulk Operations and Reminders.
        btn_ops_layout = QHBoxLayout()
        self.btn_bulk_import = QPushButton(self._("Bulk Import"))
        self.btn_bulk_import.setStyleSheet(BUTTON_STYLE)
        self.btn_bulk_import.clicked.connect(self.bulk_import)
        self.btn_bulk_export = QPushButton(self._("Bulk Export"))
        self.btn_bulk_export.setStyleSheet(BUTTON_STYLE)
        self.btn_bulk_export.clicked.connect(self.bulk_export)
        self.btn_email_reminders = QPushButton(self._("Email Reminders"))
        self.btn_email_reminders.setStyleSheet(BUTTON_STYLE)
        self.btn_email_reminders.clicked.connect(self.email_reminders)
        self.btn_modify_item = QPushButton(self._("Modify Item"))
        self.btn_modify_item.setStyleSheet(BUTTON_STYLE)
        self.btn_modify_item.clicked.connect(self.modify_item)
        self.btn_delete_item = QPushButton(self._("Delete Item"))
        self.btn_delete_item.setStyleSheet(BUTTON_STYLE)
        self.btn_delete_item.clicked.connect(self.delete_item)
        btn_ops_layout.addWidget(self.btn_modify_item)
        btn_ops_layout.addWidget(self.btn_delete_item)
        btn_ops_layout.addStretch()
        btn_ops_layout.addWidget(self.btn_bulk_import)
        btn_ops_layout.addWidget(self.btn_bulk_export)
        btn_ops_layout.addWidget(self.btn_email_reminders)
        self.main_layout.addLayout(btn_ops_layout)
        
        # Inventory Table.
        self.table = QTableWidget()
        self.table.setStyleSheet(LISTSTYLE)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "id", self._("Item Name"), self._("Stock Count"), self._("Purchase Price"),
            self._("Selling Price"), self._("Profit"), self._("Purchase Date"), self._("Expiry Date")
        ])
        self.table.hideColumn(0)
        self.table.setSortingEnabled(True)
        self.main_layout.addWidget(self.table)

        self.refresh_inventory_tree()
        self.update_inventory_dropdown()

    def toggle_expiry(self, state):
        """Disable or enable the expiry date widget based on checkbox state."""
        if state == QtCore.Qt.Checked:
            self.inv_expiry.setEnabled(False)
        else:
            self.inv_expiry.setEnabled(True)

    def refresh_language(self):
        _ = self.app._
        self.add_group.setTitle(_( "Add Inventory Item"))
        field_labels = [_( "Item Name"), _( "Stock Count"), _( "Purchase Price"),
                         _( "Selling Price"), _( "Purchase Date"), _( "Expiry Date")]
        for idx in range(self.form_layout.count()):
            item = self.form_layout.itemAt(idx)
            widget = item.widget()
            if isinstance(widget, QLabel):
                index = idx // 2
                if index < len(field_labels):
                    widget.setText(field_labels[index])
        self.btn_save.setText(_( "Save"))
        self.btn_bulk_import.setText(_( "Bulk Import"))
        self.btn_bulk_export.setText(_( "Bulk Export"))
        self.btn_email_reminders.setText(_( "Email Reminders"))
        self.btn_delete_item.setText(_( "Delete Item"))
        self.btn_modify_item.setText(_( "Modify Item"))
        headers = ["id", _( "Item Name"), _( "Stock Count"), _( "Purchase Price"),
                   _( "Selling Price"), _( "Profit"), _( "Purchase Date"), _( "Expiry Date")]
        self.table.setHorizontalHeaderLabels(headers)
        self.update_inventory_dropdown()

    def add_inventory_item(self):
        try:
            item_name_val = self.inv_item_name.currentText().strip()
            if not item_name_val:
                raise ValueError(self._("Item Name cannot be empty."))
            stock_val = int(self.inv_stock.text())
            if stock_val < 0:
                raise ValueError(self._("Stock cannot be negative."))
            purchase_val = float(self.inv_purchase.text())
            selling_val = float(self.inv_selling.text())
            if purchase_val <= 0 or selling_val <= 0:
                raise ValueError(self._("Prices must be positive."))
            if selling_val < purchase_val:
                raise ValueError(self._("Selling price cannot be lower than purchase price."))
            purchase_date_val = self.inv_purchase_date.date().toPyDate()
            # If the "No Expiry Date" checkbox is checked, set expiry to None.
            if self.chk_no_expiry.isChecked():
                expiry_val = None
            else:
                expiry_val = self.inv_expiry.date().toPyDate()
                if expiry_val < date.today():
                    raise ValueError(self._("Expiry date cannot be in the past."))
            from main import session_scope, InventoryItem
            with session_scope() as session:
                new_item = self.InventoryItem(
                    item_name=item_name_val,
                    stock_count=stock_val,
                    purchase_price=purchase_val,
                    selling_price=selling_val,
                    purchase_date=purchase_date_val,
                    expiry_date=expiry_val
                )
                session.add(new_item)
            QMessageBox.information(
                self.app,
                self._("Success"),
                self._("Item '{item}' added successfully.").format(item=item_name_val)
            )
            self.clear_form()
            self.refresh_inventory_tree()
            self.update_inventory_dropdown()
            if hasattr(self.app, 'billing_tab'):
                self.app.billing_tab.load_inventory_items()
        except ValueError as e:
            QMessageBox.critical(self.app, self._("Error"), str(e))
        except Exception as e:
            logging.exception("Error in add_inventory_item")
            QMessageBox.critical(self.app, self._("Error"), str(e))

    def clear_form(self):
        self.inv_item_name.setCurrentIndex(-1)
        self.inv_stock.clear()
        self.inv_purchase.clear()
        self.inv_selling.clear()
        # Reset expiry date widget and checkbox.
        self.inv_expiry.setDate(QDate.currentDate())
        self.chk_no_expiry.setChecked(False)

    def refresh_inventory_tree(self):
        self.table.setRowCount(0)
        low_stock_threshold = 5
        from main import session_scope
        with self.session_scope() as session:
            items = session.query(self.InventoryItem).all()
            for it in items:
                stock = max(it.stock_count, 0)
                profit = (it.selling_price - it.purchase_price) * stock
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(it.id)))
                self.table.setItem(row, 1, QTableWidgetItem(it.item_name))
                self.table.setItem(row, 2, QTableWidgetItem(str(stock)))
                self.table.setItem(row, 3, QTableWidgetItem(str(it.purchase_price)))
                self.table.setItem(row, 4, QTableWidgetItem(str(it.selling_price)))
                self.table.setItem(row, 5, QTableWidgetItem(str(profit)))
                self.table.setItem(row, 6, QTableWidgetItem(it.purchase_date.strftime("%Y-%m-%d")))
                # Show expiry date only if it is not None.
                expiry_text = it.expiry_date.strftime("%Y-%m-%d") if it.expiry_date else ""
                self.table.setItem(row, 7, QTableWidgetItem(expiry_text))
                if it.expiry_date and it.expiry_date == date.today():
                    for col in range(self.table.columnCount()):
                        cell = self.table.item(row, col)
                        if cell:
                            cell.setBackground(QBrush(QColor("red")))
                if it.stock_count < low_stock_threshold:
                    stock_cell = self.table.item(row, 2)
                    if stock_cell:
                        stock_cell.setBackground(QBrush(QColor("yellow")))

    def update_inventory_dropdown(self):
        from main import session_scope
        with self.session_scope() as session:
            items = session.query(self.InventoryItem).all()
            names = [item.item_name for item in items]
        self.inv_item_name.clear()
        self.inv_item_name.addItems(names)

    def search_inventory(self):
        filter_text = self.search_entry.text().strip().lower()
        # Collect needed item data while the session is active.
        item_data = []
        from main import session_scope
        with self.session_scope() as session:
            items = session.query(self.InventoryItem).all()
            for it in items:
                # Extract required attributes now and store in a dictionary.
                item_data.append({
                    "id": it.id,
                    "item_name": it.item_name,
                    "stock_count": it.stock_count,
                    "purchase_price": it.purchase_price,
                    "selling_price": it.selling_price,
                    "purchase_date": it.purchase_date,
                    "expiry_date": it.expiry_date
                })
        
        self.table.setRowCount(0)
        for data in item_data:
            # Now you can safely access data["item_name"] without triggering DB access.
            if filter_text in data["item_name"].lower():
                stock = max(data["stock_count"], 0)
                profit = (data["selling_price"] - data["purchase_price"]) * stock
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(data["id"])))
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(data["item_name"]))
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(stock)))
                self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(data["purchase_price"])))
                self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(data["selling_price"])))
                self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(profit)))
                self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(data["purchase_date"].strftime("%Y-%m-%d")))
                expiry_text = data["expiry_date"].strftime("%Y-%m-%d") if data["expiry_date"] else ""
                self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(expiry_text))
    

    def expiry_reminder(self):
        threshold = date.today() + timedelta(days=30)
        from main import session_scope
        with self.session_scope() as session:
            expiring = session.query(self.InventoryItem).filter(
                self.InventoryItem.expiry_date != None,
                self.InventoryItem.expiry_date <= threshold
            ).all()
            expiring_data = [(item.item_name, item.expiry_date.strftime('%Y-%m-%d')) for item in expiring]
        if not expiring_data:
            QMessageBox.information(self.app, self._("Expiry Reminder"),
                                    self._("No items expiring within the next month."))
        else:
            text = "\n".join(f"{name} (Expires: {exp_date})" for name, exp_date in expiring_data)
            QMessageBox.information(self.app, self._("Expiry Reminder"), text)

    def low_stock_reminder(self):
        threshold = 5
        from main import session_scope
        with self.session_scope() as session:
            low_stock = session.query(self.InventoryItem).filter(
                self.InventoryItem.stock_count < threshold
            ).all()
            low_stock_data = [(item.item_name, item.stock_count) for item in low_stock]
        if not low_stock_data:
            QMessageBox.information(self.app, self._("Low Stock Reminder"),
                                    self._("No items with low stock."))
        else:
            text = "\n".join(f"{name} (Stock: {stock})" for name, stock in low_stock_data)
            QMessageBox.information(self.app, self._("Low Stock Reminder"), text)

    def delete_item(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self.app, self._("Warning"), self._("Please select an item to delete."))
            return
        item_id = self.table.item(selected, 0).text()
        reply = QMessageBox.question(self.app, self._("Confirm"),
                                     self._("Are you sure you want to delete the selected item?"),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            from main import session_scope
            with self.session_scope() as session:
                obj = session.get(self.InventoryItem, item_id)
                if obj:
                    session.delete(obj)
            self.refresh_inventory_tree()
            self.update_inventory_dropdown()
            if hasattr(self.app, 'billing_tab'):
                self.app.billing_tab.load_inventory_items()
            QMessageBox.information(self.app, self._("Success"), self._("Item deleted."))

    def modify_item(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self.app, self._("Warning"), self._("Please select an item to modify."))
            return
        item_id = self.table.item(selected, 0).text()
        from main import session_scope
        with self.session_scope() as session:
            obj = session.get(self.InventoryItem, item_id)
            if not obj:
                QMessageBox.critical(self.app, self._("Error"), self._("Selected item not found."))
                return
            # Store existing values.
            item_name_local = obj.item_name
            stock_local = obj.stock_count
            purchase_local = obj.purchase_price
            selling_local = obj.selling_price
            purchase_date_local = obj.purchase_date
            expiry_date_local = obj.expiry_date  # May be None.
        mod_win = QtWidgets.QDialog(self.app)
        mod_win.setWindowTitle(self._("Modify Item"))
        layout = QtWidgets.QGridLayout(mod_win)
        lbl_name = QLabel(self._("Item Name"))
        e_item_name = QLineEdit()
        e_item_name.setText(str(item_name_local))
        layout.addWidget(lbl_name, 0, 0)
        layout.addWidget(e_item_name, 0, 1)
        lbl_stock = QLabel(self._("Stock Count"))
        e_stock = QLineEdit()
        e_stock.setText(str(stock_local))
        layout.addWidget(lbl_stock, 1, 0)
        layout.addWidget(e_stock, 1, 1)
        lbl_purchase = QLabel(self._("Purchase Price"))
        e_purchase = QLineEdit()
        e_purchase.setText(str(purchase_local))
        layout.addWidget(lbl_purchase, 2, 0)
        layout.addWidget(e_purchase, 2, 1)
        lbl_selling = QLabel(self._("Selling Price"))
        e_selling = QLineEdit()
        e_selling.setText(str(selling_local))
        layout.addWidget(lbl_selling, 3, 0)
        layout.addWidget(e_selling, 3, 1)
        lbl_purchase_date = QLabel(self._("Purchase Date"))
        e_purchase_date = QDateEdit()
        e_purchase_date.setDisplayFormat("yyyy-MM-dd")
        e_purchase_date.setDate(QDate(purchase_date_local.year, purchase_date_local.month, purchase_date_local.day))
        e_purchase_date.setCalendarPopup(True)
        layout.addWidget(lbl_purchase_date, 4, 0)
        layout.addWidget(e_purchase_date, 4, 1)
        lbl_expiry_date = QLabel(self._("Expiry Date"))
        e_expiry_date = QDateEdit()
        e_expiry_date.setDisplayFormat("yyyy-MM-dd")
        if expiry_date_local:
            e_expiry_date.setDate(QDate(expiry_date_local.year, expiry_date_local.month, expiry_date_local.day))
        else:
            e_expiry_date.setDate(QDate.currentDate())
        e_expiry_date.setCalendarPopup(True)
        layout.addWidget(lbl_expiry_date, 5, 0)
        layout.addWidget(e_expiry_date, 5, 1)
        chk_no_expiry_mod = QCheckBox(self._("No Expiry Date"))
        # Pre-set checkbox if expiry_date_local is None.
        if expiry_date_local is None:
            chk_no_expiry_mod.setChecked(True)
            e_expiry_date.setEnabled(False)
        chk_no_expiry_mod.stateChanged.connect(lambda state: e_expiry_date.setEnabled(state != QtCore.Qt.Checked))
        layout.addWidget(chk_no_expiry_mod, 5, 2)
        
        def save_modifications():
            try:
                with self.session_scope() as session:
                    obj2 = session.get(self.InventoryItem, item_id)
                    if not obj2:
                        QMessageBox.critical(mod_win, self._("Error"), self._("Selected item not found."))
                        return
                    obj2.item_name = e_item_name.text().strip()
                    obj2.stock_count = int(e_stock.text())
                    if obj2.stock_count < 0:
                        raise ValueError(self._("Stock cannot be negative."))
                    obj2.purchase_price = float(e_purchase.text())
                    obj2.selling_price = float(e_selling.text())
                    if obj2.purchase_price <= 0 or obj2.selling_price <= 0:
                        raise ValueError(self._("Prices must be positive."))
                    if obj2.selling_price < obj2.purchase_price:
                        raise ValueError(self._("Selling price cannot be lower than purchase price."))
                    obj2.purchase_date = e_purchase_date.date().toPyDate()
                    if chk_no_expiry_mod.isChecked():
                        obj2.expiry_date = None
                    else:
                        obj2.expiry_date = e_expiry_date.date().toPyDate()
                mod_win.accept()
                self.refresh_inventory_tree()
                self.update_inventory_dropdown()
                if hasattr(self.app, 'billing_tab'):
                    self.app.billing_tab.load_inventory_items()
                QMessageBox.information(self.app, self._("Success"), self._("Item details updated."))
            except Exception as ex:
                QMessageBox.critical(mod_win, self._("Error"), str(ex))
        btn_save = QPushButton(self._("Save Changes"))
        btn_save.setStyleSheet(BUTTON_STYLE)
        btn_save.clicked.connect(save_modifications)
        layout.addWidget(btn_save, 6, 0, 1, 2)
        mod_win.exec_()

    def bulk_import(self):
        QMessageBox.information(self.app, self._("Bulk Import"), self._("Bulk import feature is not implemented yet."))

    def bulk_export(self):
        QMessageBox.information(self.app, self._("Bulk Export"), self._("Bulk export feature is not implemented yet."))

    def email_reminders(self):
        QMessageBox.information(self.app, self._("Email Reminders"), self._("Email reminders feature is not implemented yet."))
