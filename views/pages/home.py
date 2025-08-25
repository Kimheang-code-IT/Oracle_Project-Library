# views/pages/home_page.py

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import oracledb
from db_connection import get_connection

class HomePage(QWidget):
    # signal emitted when one of the cards is clicked:
    # payload is one of 'categories', 'books', 'borrows', 'returns'
    navigate = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()
        self.load_stats()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Top: 4 “cards” side-by-side ───────────────────────
        row = QHBoxLayout()
        row.setSpacing(20)

        # create the four buttons
        self.btn_categories = QPushButton()
        self.btn_books      = QPushButton()
        self.btn_borrows    = QPushButton()
        self.btn_returns    = QPushButton()

        # map keys to buttons for wiring up
        btn_map = {
            "categories": self.btn_categories,
            "books":      self.btn_books,
            "borrows":    self.btn_borrows,
            "returns":    self.btn_returns,
        }

        # shared style and size
        for key, btn in btn_map.items():
            btn.setFixedSize(230, 100)
            btn.setStyleSheet("""
                QPushButton {
                  background: #005499;
                  color: white;
                  font-size: 18px;
                  font-weight: bold;
                  border-radius: 8px;
                }
                QPushButton:hover {
                  background: #007ACC;
                }
            """)
            btn.clicked.connect(lambda _, k=key: self.navigate.emit(k))
            row.addWidget(btn)

        layout.addLayout(row)

        # ── Middle: Stats summary ─────────────────────────────
        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.stats_label)

        # ── Bottom: 3-chart canvas ────────────────────────────
        self.figure = Figure(figsize=(9, 3), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.canvas)

    def load_stats(self):
        # open a connection and cursor
        conn = get_connection()
        cur  = conn.cursor()

        # 1) counts for cards
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM categories")
        total_cats = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM books")
        total_books = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM borrows")
        total_borrows = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM borrows WHERE return_date IS NOT NULL")
        total_returns = cur.fetchone()[0]

        # update each card
        self.btn_categories.setText(f"Users\n{total_users}")
        self.btn_books     .setText(f"Books\n{total_books}")
        self.btn_borrows   .setText(f"Borrows\n{total_borrows}")
        self.btn_returns   .setText(f"Returns\n{total_returns}")

        # 2) borrows per day
        cur.execute("""
            SELECT TRUNC(borrow_date), COUNT(*)
              FROM borrows
             GROUP BY TRUNC(borrow_date)
             ORDER BY 1
        """)
        borrows_by_day = cur.fetchall()

        # 3) returns per day
        cur.execute("""
            SELECT TRUNC(return_date), COUNT(*)
              FROM borrows
             WHERE return_date IS NOT NULL
             GROUP BY TRUNC(return_date)
             ORDER BY 1
        """)
        returns_by_day = cur.fetchall()

        # 4) late returns per day
        cur.execute("""
            SELECT TRUNC(return_date), COUNT(*)
              FROM borrows
             WHERE return_date > due_date
             GROUP BY TRUNC(return_date)
             ORDER BY 1
        """)
        late_by_day = cur.fetchall()

        # clean up
        cur.close()
        conn.close()

        

        # helper to unpack date/count rows
        def unpack(rows):
            if not rows:
                return [], []
            xs, ys = zip(*rows)
            return xs, ys

        days1, cnt1 = unpack(borrows_by_day)
        days2, cnt2 = unpack(returns_by_day)
        days3, cnt3 = unpack(late_by_day)

        # draw 3 side-by-side line charts
        self.figure.clear()

        ax1 = self.figure.add_subplot(1, 3, 1)
        ax1.plot(days1, cnt1, marker='o')
        ax1.set_title("Borrows per Day")
        ax1.tick_params(axis='x', rotation=45)

        ax2 = self.figure.add_subplot(1, 3, 2)
        ax2.plot(days2, cnt2, marker='o')
        ax2.set_title("Returns per Day")
        ax2.tick_params(axis='x', rotation=45)

        ax3 = self.figure.add_subplot(1, 3, 3)
        ax3.plot(days3, cnt3, marker='o')
        ax3.set_title("Late Returns per Day")
        ax3.tick_params(axis='x', rotation=45)

        self.canvas.draw()
