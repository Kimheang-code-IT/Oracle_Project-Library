# views/pages/return_book.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QFrame, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from db_connection import get_connection
import oracledb

class ReturnBookPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.user = current_user
        self._build_ui()
        self.load_summary()
        self.load_late_returns()

    def _build_ui(self):
        self.setWindowTitle("Returned Books Dashboard")

        table_header_style = """
            QHeaderView::section {
                background: #005499;
                color: white;
                padding: 4px;
                font-size: 13px;
            }
        """

        main = QHBoxLayout(self)
        main.setContentsMargins(8,8,8,8)
        main.setSpacing(12)

        # ── LEFT PANEL: Summary + Late Returns ──────────────────
        left = QVBoxLayout()

        # Filter + Refresh
        fl = QHBoxLayout()
        self.filter_input = QLineEdit(placeholderText="Filter by student ID…")
        self.filter_input.textChanged.connect(self.load_summary)
        fl.addWidget(self.filter_input, 1)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.load_summary)
        fl.addWidget(btn_refresh)
        left.addLayout(fl)

        # Summary table
        self.tbl_summary = QTableWidget(0, 9)
        self.tbl_summary.setHorizontalHeaderLabels([
            "No", "Student ID", "Total Books",
            "First Borrow", "Last Return", "Last Logged",
            "Total Days", "Remark", "Late Days"
        ])
        self.tbl_summary.verticalHeader().setVisible(False)
        self.tbl_summary.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_summary.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_summary.setStyleSheet(table_header_style)
        hdr = self.tbl_summary.horizontalHeader()
        for c in range(self.tbl_summary.columnCount()):
            hdr.setSectionResizeMode(
                c,
                QHeaderView.ResizeMode.ResizeToContents if c < 2 else
                QHeaderView.ResizeMode.Stretch
            )
        self.tbl_summary.itemSelectionChanged.connect(self._on_summary_selected)
        left.addWidget(self.tbl_summary, 3)

        # All Late Returns
        lbl_late = QLabel("All Late Returns")
        lbl_late.setStyleSheet("font-weight: bold; font-size: 14px;")
        left.addWidget(lbl_late)

        self.tbl_late = QTableWidget(0, 6)
        self.tbl_late.setHorizontalHeaderLabels([
            "No", "Student ID", "Quantity",
            "Book Title", "Return Date", "Days Late"
        ])
        self.tbl_late.verticalHeader().setVisible(False)
        self.tbl_late.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_late.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_late.setStyleSheet("""
            QHeaderView::section {
                background-color: #AA0000;
                color: white;
                padding: 4px;
                font-size: 13px;
            }
        """)
        hdr_late = self.tbl_late.horizontalHeader()
        for col in range(self.tbl_late.columnCount()):
            hdr_late.setSectionResizeMode(
                col,
                QHeaderView.ResizeMode.ResizeToContents if col < 2 else
                QHeaderView.ResizeMode.Stretch
            )
        left.addWidget(self.tbl_late, 2)

        main.addLayout(left, 3)

        # ── RIGHT PANEL: Details + Student Info ────────────────
        right = QVBoxLayout()

        # Details header
        header = QLabel("Books Returned Details")
        header.setStyleSheet("font-size:16px; font-weight:bold;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(header)

        # Details table
        self.tbl_details = QTableWidget(0, 3)
        self.tbl_details.setHorizontalHeaderLabels(["Barcode", "Title", "Qty"])
        self.tbl_details.verticalHeader().setVisible(False)
        self.tbl_details.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_details.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        hdr3 = self.tbl_details.horizontalHeader()
        hdr3.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr3.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr3.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        right.addWidget(self.tbl_details, 2)

        # ── Student Info Frame ─────────────────────────────────
        lbl_info = QLabel("Student Information")
        lbl_info.setStyleSheet("""
            background-color: #005499;
            color: white;
            font-size: 14px;
            font-weight: bold;
            padding: 4px;
        """)
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right.addWidget(lbl_info)

        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                border: none;
                border-radius: 4px;
                background: #FFFFFF;
                padding: 8px;
            }
            QLabel { font-size: 13px; }
        """)
        form = QFormLayout(info_frame)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(4)
        form.setContentsMargins(0,0,0,0)

        self.info_id      = QLabel()
        self.info_name    = QLabel()
        self.info_phone   = QLabel()
        self.info_address = QLabel()
        self.info_major   = QLabel()

        form.addRow("Student ID:", self.info_id)
        form.addRow("Username:",   self.info_name)
        form.addRow("Phone:",      self.info_phone)
        form.addRow("Address:",    self.info_address)
        form.addRow("Major:",      self.info_major)

        right.addWidget(info_frame, 1)

        main.addLayout(right, 2)

    def load_summary(self):
        term = self.filter_input.text().strip()
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                  user_id,
                  COUNT(*)                                             AS total_books,
                  MIN(borrow_date)                                     AS first_borrow,
                  MAX(return_date)                                     AS last_return,
                  MAX(returned_at)                                     AS last_logged,
                  SUM(total_days)                                      AS sum_days,
                  SUM(CASE WHEN days_late>0 THEN days_late ELSE 0 END) AS late_days,
                  CASE WHEN SUM(CASE WHEN days_late>0 THEN days_late ELSE 0 END)>0
                       THEN 'Late' ELSE '' END                        AS remark
                FROM VW_FULL_RETURN_INFO
                GROUP BY user_id
                ORDER BY last_logged DESC
            """)
            summary = cur.fetchall()
        finally:
            if cur: cur.close()
            conn.close()

        # optional client‐side filter by student ID
        if term.isdigit():
            summary = [r for r in summary if str(r[0]) == term]

        self.tbl_summary.setRowCount(len(summary))
        for i, (uid, tot, fb, lr, ll, sd, late_days, remark) in enumerate(summary):
            self.tbl_summary.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.tbl_summary.setItem(i, 1, QTableWidgetItem(str(uid)))
            self.tbl_summary.setItem(i, 2, QTableWidgetItem(str(tot)))
            self.tbl_summary.setItem(i, 3, QTableWidgetItem(fb.strftime("%d/%m/%Y")))
            self.tbl_summary.setItem(i, 4, QTableWidgetItem(lr.strftime("%d/%m/%Y")))
            self.tbl_summary.setItem(i, 5, QTableWidgetItem(ll.strftime("%d/%m/%Y %H:%M")))
            self.tbl_summary.setItem(i, 6, QTableWidgetItem(str(int(sd))))
            self.tbl_summary.setItem(i, 7, QTableWidgetItem(remark))
            self.tbl_summary.setItem(i, 8, QTableWidgetItem(str(int(late_days))))

        # clear the detail & late tables
        self.tbl_details .setRowCount(0)
        self._clear_student_info()
        self.load_late_returns()


    def load_late_returns(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                  return_id,
                  user_id,
                  book_title,
                  return_date,
                  days_late
                FROM VW_LATE_RETURNS
                ORDER BY returned_at DESC
            """)
            late = cur.fetchall()
        finally:
            if cur: cur.close()
            conn.close()

        self.tbl_late.setRowCount(len(late))
        for i, (rid, uid, title, rd, days_late) in enumerate(late):
            self.tbl_late.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.tbl_late.setItem(i, 1, QTableWidgetItem(str(uid)))
            self.tbl_late.setItem(i, 2, QTableWidgetItem("1"))
            self.tbl_late.setItem(i, 3, QTableWidgetItem(title))
            self.tbl_late.setItem(i, 4, QTableWidgetItem(rd.strftime("%d/%m/%Y")))
            self.tbl_late.setItem(i, 5, QTableWidgetItem(str(int(days_late))))


    def _on_summary_selected(self):
        sel = self.tbl_summary.selectionModel().selectedRows()
        if not sel:
            return
        row = sel[0].row()
        uid = int(self.tbl_summary.item(row, 1).text())
        self.load_details(uid)
        self._load_student_info(uid)

    def load_details(self, user_id):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT bo.barcode, bo.title, COUNT(*) AS qty
                  FROM borrows b
                  JOIN books bo       ON bo.book_id = b.book_id
                  JOIN returns_log r  ON r.borrow_id = b.borrow_id
                 WHERE b.user_id = :1
                   AND b.status = 'RETURNED'
                 GROUP BY bo.barcode, bo.title
            """, [user_id])
            books = cur.fetchall()
        finally:
            if cur: cur.close()
            conn.close()

        self.tbl_details.setRowCount(len(books))
        for r, (bc, title, qty) in enumerate(books):
            self.tbl_details.setItem(r, 0, QTableWidgetItem(bc))
            self.tbl_details.setItem(r, 1, QTableWidgetItem(title))
            self.tbl_details.setItem(r, 2, QTableWidgetItem(str(qty)))

    def _load_student_info(self, user_id):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT username, phone, address, major
                  FROM users
                 WHERE user_id = :1
            """, [user_id])
            row = cur.fetchone()
        finally:
            if cur: cur.close()
            conn.close()

        if row:
            username, phone, address, major = row
            self.info_id     .setText(str(user_id))
            self.info_name   .setText(username)
            self.info_phone  .setText(phone or "")
            self.info_address.setText(address or "")
            self.info_major  .setText(major  or "")
        else:
            self._clear_student_info()

    def _clear_student_info(self):
        for lbl in (self.info_id, self.info_name,
                    self.info_phone, self.info_address,
                    self.info_major):
            lbl.clear()
