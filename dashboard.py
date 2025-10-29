from datetime import datetime
import logging

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QGroupBox
)
from sqlalchemy import func

from styles import (
    TITLE_STYLE,
    BUTTON_STYLE,
    GROUPBOX_STYLE,
    HEADER_LABEL_STYLE,
    PLACEHOLDER_STYLE
)


class DashboardTab(QtWidgets.QWidget):
    """
    Dashboard tab for Vet Clinic application showing key metrics and navigation.
    """

    REFRESH_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app  # QApplication instance for translations

        # Metric storage
        self._metrics = {
            'patients': 0,
            'appointments': 0,
            'inventory': 0,
            'revenue': 0.0
        }

        self._init_ui()
        self.update_metrics()

        # Schedule auto-refresh
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.update_metrics)
        self._timer.start(self.REFRESH_INTERVAL_MS)

    def _init_ui(self):
        """Initializes UI components and layout."""
        try:
            self.setLayout(QVBoxLayout(margin=15, spacing=20))

            # Title
            self._title_label = QLabel(self.tr("Vet Clinic Dashboard"))
            self._title_label.setAlignment(QtCore.Qt.AlignCenter)
            self._title_label.setStyleSheet(TITLE_STYLE)
            self.layout().addWidget(self._title_label)

            # Navigation
            self._nav_buttons = {}
            nav_layout = QHBoxLayout(spacing=10)
            self._create_navigation_buttons(nav_layout)
            self.layout().addLayout(nav_layout)

            # Metrics group
            metrics_group = QGroupBox(self.tr("Key Metrics"))
            metrics_group.setStyleSheet(GROUPBOX_STYLE)
            metrics_layout = QGridLayout(spacing=20)
            metrics_group.setLayout(metrics_layout)

            # Metric labels
            self._labels = {
                'patients': QLabel('', self),
                'appointments': QLabel('', self),
                'inventory': QLabel('', self),
                'revenue': QLabel('', self)
            }
            for label in self._labels.values():
                label.setStyleSheet(HEADER_LABEL_STYLE)

            metrics_layout.addWidget(self._labels['patients'], 0, 0)
            metrics_layout.addWidget(self._labels['appointments'], 0, 1)
            metrics_layout.addWidget(self._labels['inventory'], 1, 0)
            metrics_layout.addWidget(self._labels['revenue'], 1, 1)
            self.layout().addWidget(metrics_group)

            # Actions
            actions_layout = QHBoxLayout(spacing=10)
            self._refresh_btn = QPushButton(self.tr("Refresh Metrics"))
            self._refresh_btn.setStyleSheet(BUTTON_STYLE)
            self._refresh_btn.setToolTip(self.tr("Refresh dashboard metrics manually"))
            self._refresh_btn.clicked.connect(self.update_metrics)

            self._export_btn = QPushButton(self.tr("Export Dashboard"))
            self._export_btn.setStyleSheet(BUTTON_STYLE)
            self._export_btn.setToolTip(self.tr("Export a screenshot of the dashboard"))
            self._export_btn.clicked.connect(self.export_dashboard)

            actions_layout.addWidget(self._refresh_btn)
            actions_layout.addWidget(self._export_btn)
            self.layout().addLayout(actions_layout)

            # Chart placeholder
            self._chart_placeholder = QLabel(self.tr("Chart/Graph will be displayed here."), self)
            self._chart_placeholder.setAlignment(QtCore.Qt.AlignCenter)
            self._chart_placeholder.setStyleSheet(PLACEHOLDER_STYLE)
            self.layout().addWidget(self._chart_placeholder)

        except Exception as e:
            logging.exception("Failed to initialize Dashboard UI")
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def _create_navigation_buttons(self, layout):
        """Creates navigation buttons to switch application tabs."""
        options = [
            ('Patients', 1),
            ('Inventory', 2),
            ('Billing', 3),
            ('Analytics', 4),
            ('Appointments', 5)
        ]
        for name, idx in options:
            btn = QPushButton(self.tr(name))
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setToolTip(self.tr(f"Go to {name}"))
            btn.clicked.connect(lambda _checked, i=idx: self._navigate(i))
            layout.addWidget(btn)
            self._nav_buttons[name] = btn

    def _navigate(self, index):
        """Switches the main application tab by index."""
        try:
            widget = getattr(self.app, 'tab_widget', None)
            if widget:
                widget.setCurrentIndex(index)
            else:
                raise AttributeError('Tab widget not found')
        except Exception as e:
            logging.exception("Navigation error on DashboardTab")
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def update_metrics(self):
        """Fetches latest metrics from database and updates UI labels."""
        try:
            from main import session_scope, User, Appointment, InventoryItem, BillingRecord
            with session_scope() as session:
                self._metrics['patients'] = session.query(func.count(User.id)).scalar() or 0

                now = datetime.now()
                self._metrics['appointments'] = (
                    session.query(func.count(Appointment.id))
                    .filter(Appointment.appointment_datetime >= now)
                    .scalar() or 0
                )

                self._metrics['inventory'] = session.query(func.count(InventoryItem.id)).scalar() or 0
                self._metrics['revenue'] = session.query(func.sum(BillingRecord.total)).scalar() or 0.0

            self._refresh_labels()
        except Exception as e:
            logging.exception("Error updating Dashboard metrics")
            QMessageBox.critical(self, self.tr("Error updating metrics"), str(e))

    def _refresh_labels(self):
        """Localizes and refreshes metric label texts."""
        self._labels['patients'].setText(
            f"{self.tr('Total Patients:')} {self._metrics['patients']}"
        )
        self._labels['appointments'].setText(
            f"{self.tr('Active Appointments:')} {self._metrics['appointments']}"
        )
        self._labels['inventory'].setText(
            f"{self.tr('Inventory Items:')} {self._metrics['inventory']}"
        )
        self._labels['revenue'].setText(
            f"{self.tr('Total Revenue:')} {self._metrics['revenue']:.2f} {self.tr('LE')}"
        )

    def export_dashboard(self):
        """Exports the dashboard view to an image file."""
        try:
            pixmap = self.grab()
            fname, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Save Dashboard Screenshot"),
                '',
                'PNG (*.png);;JPEG (*.jpg)'
            )
            if fname and pixmap.save(fname):
                QMessageBox.information(
                    self,
                    self.tr("Export Successful"),
                    self.tr("Dashboard exported successfully.")
                )
            elif fname:
                raise IOError(self.tr("Failed to save dashboard image."))
        except Exception as e:
            logging.exception("Error exporting dashboard")
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def refresh_language(self):
        """Refreshes all UI text when the application language changes explicitly."""
        self._title_label.setText(self.tr("Vet Clinic Dashboard"))

        # Update navigation texts
        for name, btn in self._nav_buttons.items():
            btn.setText(self.tr(name))
            btn.setToolTip(self.tr(f"Go to {name}"))

        # Update action buttons
        self._refresh_btn.setText(self.tr("Refresh Metrics"))
        self._refresh_btn.setToolTip(self.tr("Refresh dashboard metrics manually"))
        self._export_btn.setText(self.tr("Export Dashboard"))
        self._export_btn.setToolTip(self.tr("Export a screenshot of the dashboard"))

        # Update metric labels and placeholder
        self._refresh_labels()
        self._chart_placeholder.setText(self.tr("Chart/Graph will be displayed here."))

    def changeEvent(self, event):
        """Handle dynamic language change events."""
        if event.type() == QEvent.LanguageChange:
            self.refresh_language()
        super().changeEvent(event)
