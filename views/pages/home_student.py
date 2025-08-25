# views/pages/home_student.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy, QCalendarWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import oracledb
from db_connection import get_connection

class StudentHomePage(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Top Summary Boxes
        self.stat_layout = QHBoxLayout()
        self.stat_layout.setSpacing(12)
        self.add_summary_boxes()
        main_layout.addLayout(self.stat_layout)

        # Chart + Calendar layout
        chart_calendar_layout = QHBoxLayout()
        chart_calendar_layout.setSpacing(20)

        # Chart
        chart_widget = self.create_chart()
        chart_calendar_layout.addWidget(chart_widget, 2)

        # Calendar
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        chart_calendar_layout.addWidget(calendar, 1)

        main_layout.addLayout(chart_calendar_layout)

    def add_summary_boxes(self):
        stats = self.get_statistics()
        for title, count in stats.items():
            box = self.create_box(title, count)
            self.stat_layout.addWidget(box)

    def create_box(self, title, count):
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background-color: #5DADE2;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        box.setFixedHeight(120)
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Arial", 8, QFont.Weight.Normal))
        lbl_title.setStyleSheet("color: white;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_count = QLabel(str(count))
        # Make the number really big and bold
        lbl_count.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_count.setStyleSheet("color: white;")
        lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_count)
        return box
    def create_chart(self):
        stats = self.get_statistics()
        fig = Figure(figsize=(4, 3))
        ax = fig.add_subplot()
        ax.bar(stats.keys(), stats.values(), width=0.4)
        ax.set_title("Library Overview")
        ax.set_ylabel("Count")
        fig.tight_layout()
        return FigureCanvas(fig)

    def get_statistics(self):
        # Pull data from Oracle
        stats = {"Books": 0, "Categories": 0, "Borrows": 0, "Returns": 0}
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books")
            stats["Books"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM categories")
            stats["Categories"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM borrows WHERE status='BORROWED'")
            stats["Borrows"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM borrows WHERE status='RETURNED'")
            stats["Returns"] = cursor.fetchone()[0]

            cursor.close()
            conn.close()
        except Exception as e:
            print("Error fetching stats:", e)
        return stats
