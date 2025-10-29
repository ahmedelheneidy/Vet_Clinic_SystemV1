# analytics.py

import logging
import json
from datetime import date, timedelta, datetime

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Import shared style definitions.
from styles import BUTTON_STYLE, GROUPBOX_STYLE, HEADER_LABEL_STYLE

class AnalyticsTab(QtWidgets.QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        try:
            # Use the translation function from the main app
            self._ = self.app._
        except Exception:
            self._ = lambda s: s
        self.init_ui()

    def init_ui(self):
        try:
            # Set up main layout for the analytics tab.
            self.main_layout = QtWidgets.QVBoxLayout(self)
            self.main_layout.setSpacing(10)
            self.main_layout.setContentsMargins(10, 10, 10, 10)

            # --------- Filter Options Group ---------
            self.filter_group = QtWidgets.QGroupBox(self._("Filter Options"))
            self.filter_group.setStyleSheet(GROUPBOX_STYLE)
            filter_layout = QtWidgets.QHBoxLayout(self.filter_group)

            self.start_date_label = QtWidgets.QLabel(self._("Start Date:"))
            self.start_date_edit = QtWidgets.QDateEdit()
            self.start_date_edit.setCalendarPopup(True)
            self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
            # Set default start date to the first day of current month.
            self.start_date_edit.setDate(date.today().replace(day=1))

            self.end_date_label = QtWidgets.QLabel(self._("End Date:"))
            self.end_date_edit = QtWidgets.QDateEdit()
            self.end_date_edit.setCalendarPopup(True)
            self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
            self.end_date_edit.setDate(date.today())

            self.chart_type_label = QtWidgets.QLabel(self._("Chart Type:"))
            self.chart_type_combo = QtWidgets.QComboBox()
            # Add two chart types and translate the strings.
            self.chart_type_combo.addItems([self._("Line Chart"), self._("Bar Chart")])

            self.apply_filters_button = QtWidgets.QPushButton(self._("Apply Filters"))
            self.apply_filters_button.setStyleSheet(BUTTON_STYLE)
            self.apply_filters_button.clicked.connect(self.update_analytics)

            # Add widgets to filter layout.
            filter_layout.addWidget(self.start_date_label)
            filter_layout.addWidget(self.start_date_edit)
            filter_layout.addWidget(self.end_date_label)
            filter_layout.addWidget(self.end_date_edit)
            filter_layout.addWidget(self.chart_type_label)
            filter_layout.addWidget(self.chart_type_combo)
            filter_layout.addWidget(self.apply_filters_button)
            self.main_layout.addWidget(self.filter_group)

            # --------- Expense Entry Group ---------
            self.expense_group = QtWidgets.QGroupBox(self._("Expense Entry"))
            self.expense_group.setStyleSheet(GROUPBOX_STYLE)
            expense_layout = QtWidgets.QFormLayout(self.expense_group)

            self.expense_category = QtWidgets.QLineEdit()
            self.expense_category.setPlaceholderText(self._("Expense Category (e.g., Rent, Salaries)"))
            self.expense_amount = QtWidgets.QLineEdit()
            self.expense_amount.setPlaceholderText(self._("Amount"))
            self.expense_description = QtWidgets.QLineEdit()
            self.expense_description.setPlaceholderText(self._("Description (optional)"))
            self.add_expense_button = QtWidgets.QPushButton(self._("Add Expense"))
            self.add_expense_button.setStyleSheet(BUTTON_STYLE)
            self.add_expense_button.clicked.connect(self.add_expense)

            expense_layout.addRow(self._("Category:"), self.expense_category)
            expense_layout.addRow(self._("Amount:"), self.expense_amount)
            expense_layout.addRow(self._("Description:"), self.expense_description)
            expense_layout.addRow("", self.add_expense_button)
            self.main_layout.addWidget(self.expense_group)

            # --------- Summary and Chart Section with Export Options ---------
            self.splitter = QtWidgets.QSplitter()
            self.splitter.setOrientation(Qt.Vertical)

            # Analytics Summary Group
            self.summary_group = QtWidgets.QGroupBox(self._("Analytics Summary"))
            self.summary_group.setStyleSheet(GROUPBOX_STYLE)
            summary_layout = QtWidgets.QVBoxLayout(self.summary_group)
            self.results_display = QtWidgets.QTextEdit()
            self.results_display.setReadOnly(True)
            summary_layout.addWidget(self.results_display)

            self.export_report_btn = QtWidgets.QPushButton(self._("Export Report"))
            self.export_report_btn.setStyleSheet(BUTTON_STYLE)
            self.export_report_btn.clicked.connect(self.export_report)
            summary_layout.addWidget(self.export_report_btn)
            self.splitter.addWidget(self.summary_group)

            # Monthly Revenue Chart Group
            self.chart_group = QtWidgets.QGroupBox(self._("Monthly Revenue Chart"))
            self.chart_group.setStyleSheet(GROUPBOX_STYLE)
            chart_layout = QtWidgets.QVBoxLayout(self.chart_group)
            self.figure = Figure(figsize=(6, 4))
            self.canvas = FigureCanvas(self.figure)
            chart_layout.addWidget(self.canvas)

            self.export_chart_btn = QtWidgets.QPushButton(self._("Export Chart"))
            self.export_chart_btn.setStyleSheet(BUTTON_STYLE)
            self.export_chart_btn.clicked.connect(self.export_chart)
            chart_layout.addWidget(self.export_chart_btn)
            self.splitter.addWidget(self.chart_group)

            self.main_layout.addWidget(self.splitter)

            # Refresh language settings (if needed)
            self.refresh_language()

        except Exception as e:
            logging.exception("Error initializing Analytics UI")
            QtWidgets.QMessageBox.critical(self, self._("Error"), str(e))

    def update_analytics(self):
        try:
            # Validate date filter selection
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            if start_date > end_date:
                QtWidgets.QMessageBox.critical(
                    self, self.app._("Error"), self.app._("Start date cannot be after end date.")
                )
                return

            # Query billing, expense, and inventory data
            from main import session_scope, BillingRecord, ExpenseRecord, InventoryItem
            with session_scope() as session:
                bills = session.query(BillingRecord).filter(
                    BillingRecord.date >= start_date,
                    BillingRecord.date <= end_date
                ).all()
                bill_data = [(bill.date, bill.total) for bill in bills]

                services_summary = {}
                for bill in bills:
                    if bill.details:
                        details = json.loads(bill.details)
                        for svc, count in details.get("services", {}).items():
                            services_summary[svc] = services_summary.get(svc, 0) + count

                expenses = session.query(ExpenseRecord).filter(
                    ExpenseRecord.date >= start_date,
                    ExpenseRecord.date <= end_date
                ).all()
                total_expenses = sum(e.amount for e in expenses)

                inventory_items = session.query(InventoryItem).all()
                inventory_list = [
                    (item.item_name, item.stock_count, item.selling_price) for item in inventory_items
                ]

            total_revenue = sum(total for _date, total in bill_data)
            net_profit = total_revenue - total_expenses

            _ = self.app._
            summary = f"{_('Analytics Report')} ({start_date} to {end_date}):\n\n"
            summary += f"{_('Total Revenue:')} LE{total_revenue:.2f}\n"
            summary += f"{_('Total Expenses:')} LE{total_expenses:.2f}\n"
            summary += f"{_('Net Profit:')} LE{net_profit:.2f}\n\n"
            summary += f"{_('Services Sold:')}\n"
            for svc, cnt in services_summary.items():
                summary += f"  {svc}: {cnt}\n"
            summary += f"\n{_('Remaining Inventory:')}\n"
            for name, qty, price in inventory_list:
                summary += f"  {name}: {qty} {_('units')} @ LE{price:.2f} each\n"

            self.results_display.setPlainText(summary)
            self.plot_revenue_chart(start_date, end_date, bill_data)
        except Exception as e:
            logging.exception("Error updating analytics")
            QtWidgets.QMessageBox.critical(self, self.app._("Error"), str(e))

    def plot_revenue_chart(self, start_date, end_date, bill_data):
        try:
            # Aggregate revenue by month.
            revenue_by_month = {}
            current = start_date.replace(day=1)
            while current <= end_date:
                revenue_by_month[current] = 0.0
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            for bill_date, total in bill_data:
                month_start = bill_date.replace(day=1)
                if month_start in revenue_by_month:
                    revenue_by_month[month_start] += total
            months = sorted(revenue_by_month.keys())
            revenues = [revenue_by_month[m] for m in months]

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            chart_type = self.chart_type_combo.currentText()
            if chart_type == self.app._("Bar Chart"):
                ax.bar(months, revenues, width=20)
            else:
                ax.plot(months, revenues, marker="o", linestyle="-")
            _ = self.app._
            ax.set_title(_("Monthly Revenue"))
            ax.set_xlabel(_("Month"))
            ax.set_ylabel(_("Revenue (LE)"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            self.figure.autofmt_xdate()
            self.canvas.draw()
        except Exception as e:
            logging.exception("Error plotting revenue chart")
            QtWidgets.QMessageBox.critical(self, self.app._("Error"), str(e))

    def export_chart(self):
        try:
            fname, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, self.app._("Save Chart"), "", "PNG Files (*.png);;JPEG Files (*.jpg)"
            )
            if fname:
                self.figure.savefig(fname)
                QtWidgets.QMessageBox.information(
                    self, self.app._("Export Chart"), self.app._("Chart exported successfully.")
                )
        except Exception as e:
            logging.exception("Error exporting chart")
            QtWidgets.QMessageBox.critical(self, self.app._("Error"), str(e))

    def export_report(self):
        try:
            fname, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, self.app._("Save Report"), "", "Text Files (*.txt)"
            )
            if fname:
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(self.results_display.toPlainText())
                QtWidgets.QMessageBox.information(
                    self, self.app._("Export Report"), self.app._("Report exported successfully.")
                )
        except Exception as e:
            logging.exception("Error exporting report")
            QtWidgets.QMessageBox.critical(self, self.app._("Error"), str(e))

    def add_expense(self):
        try:
            from main import session_scope, ExpenseRecord
            category = self.expense_category.text().strip()
            try:
                amount = float(self.expense_amount.text().strip())
            except ValueError:
                raise ValueError(self.app._("Invalid expense amount."))
            description = self.expense_description.text().strip()
            if not category or amount <= 0:
                raise ValueError(self.app._("Please provide a valid category and positive amount."))
            with session_scope() as session:
                new_expense = ExpenseRecord(
                    date=date.today(),
                    category=category,
                    amount=amount,
                    description=description
                )
                session.add(new_expense)
            QtWidgets.QMessageBox.information(
                self, self.app._("Success"), self.app._("Expense added successfully.")
            )
            self.expense_category.clear()
            self.expense_amount.clear()
            self.expense_description.clear()
        except Exception as e:
            logging.exception("Error adding expense")
            QtWidgets.QMessageBox.critical(self, self.app._("Error"), str(e))

    def refresh_language(self):
        try:
            _ = self.app._
            self.filter_group.setTitle(_("Filter Options"))
            self.start_date_label.setText(_("Start Date:"))
            self.end_date_label.setText(_("End Date:"))
            self.chart_type_label.setText(_("Chart Type:"))
            self.chart_type_combo.clear()
            self.chart_type_combo.addItems([_("Line Chart"), _("Bar Chart")])
            self.apply_filters_button.setText(_("Apply Filters"))

            self.expense_group.setTitle(_("Expense Entry"))
            self.expense_category.setPlaceholderText(_("Expense Category (e.g., Rent, Salaries)"))
            self.expense_amount.setPlaceholderText(_("Amount"))
            self.expense_description.setPlaceholderText(_("Description (optional)"))
            self.add_expense_button.setText(_("Add Expense"))

            self.summary_group.setTitle(_("Analytics Summary"))
            self.chart_group.setTitle(_("Monthly Revenue Chart"))
            self.export_report_btn.setText(_("Export Report"))
            self.export_chart_btn.setText(_("Export Chart"))
            # Refresh analytics data based on current filters.
            self.update_analytics()
        except Exception as e:
            logging.exception("Error refreshing language in AnalyticsTab")
            QtWidgets.QMessageBox.critical(self, self.app._("Error"), str(e))
