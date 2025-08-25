# views/pages/categories.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QFrame,
    QHeaderView, QSizePolicy, QHBoxLayout
)
from PyQt6.QtCore import Qt, QEvent
import datetime
import oracledb
from db_connection import get_connection

class CategoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_id = None
        self.setup_ui()

    def showEvent(self, event):
        if event.type() == QEvent.Type.Show:
            self.load_categories()
        super().showEvent(event)

    def setup_ui(self):
        # Expand in both directions
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5,5,5,5)
        main_layout.setSpacing(20)

        # ─── Left form ────────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0,0,0,0)
        form_layout.setSpacing(12)

        # Header
        header = QLabel("Add / Edit Category")
        header.setFixedHeight(48)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            background-color: #1B3452;
            color: white;
            font-size: 20px;
            font-weight: bold;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        form_layout.addWidget(header)

        # Name label + input
        lbl_name = QLabel("Name:")
        lbl_name.setStyleSheet("padding:4px 8px; font-size:16px; font-weight:600;border: none;")
        form_layout.addWidget(lbl_name)

        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText("Category name")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: #FAFAFA;
                border: 1px solid #CCC;
                border-radius: 4px;
                padding: 4px 8px;
                font-size:16px;
            }
            QLineEdit:focus {
                border-color: #1B3452;
            }
        """)
        form_layout.addWidget(self.name_input)

        # Description label + input
        lbl_desc = QLabel("Description:")
        lbl_desc.setStyleSheet("padding:4px 8px; font-size:16px; font-weight:600;border: none;")
        form_layout.addWidget(lbl_desc)

        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(120)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background: #FAFAFA;
                border: 1px solid #CCC;
                border-radius: 4px;
                padding: 4px 8px;
                font-size:16px;
            }
            QTextEdit:focus {
                border-color: #1B3452;
            }
        """)
        form_layout.addWidget(self.desc_input)

        # Save / Cancel buttons
        self.save_btn = QPushButton("Add Category")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #255083;
                color: white;
                border: none;
                font-size:16px;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QPushButton:hover {
                background: #1B3452;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        form_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #EEE;
                color: #333;
                border: 1px solid #CCC;
                font-size:16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #DDD;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_edit)
        self.cancel_btn.hide()
        form_layout.addWidget(self.cancel_btn)

        form_layout.addStretch()
        main_layout.addWidget(form_frame, 1)

        # ─── Right table ─────────────────────────────────────────────
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10,10,10,10)
        table_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name…")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #FAFAFA;
                border: 1px solid #CCC;
                border-radius: 4px;
                padding: 6px 10px;
                font-size:16px;
            }
            QLineEdit:focus {
                border-color: #1B3452;
            }
        """)
        self.search_input.textChanged.connect(self.load_categories)
        table_layout.addWidget(self.search_input)
        self.table = QTableWidget(0,7)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Expanding)
        self.table.setMouseTracking(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #FAFAFA;
                border: none;
                font-size:16px;
            }
            
            QHeaderView::section {
                background: #1B3452;
                color: white;
                padding: 10px;
                font-size:16px;
                border: none;
            }
            QTableView::item:hover {
                background-color: #d9d9d9; 
            }
        """)
        self.table.setHorizontalHeaderLabels(
            ["No","Name","Description","Count","Created","Updated","Actions"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        # stretch column 2 to fill
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)


        # small columns stay fixed:
        self.table.setColumnWidth(0,  20)   # ID
        self.table.setColumnWidth(1, 100)   # Name
        self.table.setColumnWidth(3,  30)   # Count
        self.table.setColumnWidth(4, 180)   # Created
        self.table.setColumnWidth(5, 180)   # Updated
        self.table.setColumnWidth(6, 100)   # Actions

        # let Description (col 2) stretch to fill all extra space:
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)


        # now add the table to its layout
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_frame, 3)


    def _format_dt(self, ts):
        if isinstance(ts, datetime.datetime):
            return ts.strftime("%d/%m/%Y %H:%M")
        try:
            dt = datetime.datetime.fromisoformat(str(ts))
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return str(ts)[:16]

    def load_categories(self):
        conn = get_connection()
        cur  = conn.cursor()

        # 1) run our join so we never have to GROUP BY the CLOB
        cur.execute("""
            SELECT
              c.category_id,
              c.category_name,
              c.description,
              NVL(bc.book_count, 0) AS book_count,
              c.created_at,
              c.updated_at
            FROM categories c
            LEFT JOIN (
              SELECT category_id, COUNT(*) AS book_count
                FROM books
               GROUP BY category_id
            ) bc ON bc.category_id = c.category_id
            ORDER BY c.category_id
        """)
        raw_rows = cur.fetchall()

        # 2) extract LOB text *before* we close the session
        rows = []
        for cid, name, desc_lob, cnt, created, updated in raw_rows:
            # if it's a LOB locator, read it now
            if hasattr(desc_lob, "read"):
                text = desc_lob.read()
            else:
                text = desc_lob or ""
            rows.append((cid, name, text, str(cnt), created, updated))

        # 3) now it’s safe to tear down
        cur.close()
        conn.close()

        # 4) format and paint
        total = len(rows)
        self.table.setRowCount(total)
        for i, (cid, name, desc, cnt, created, updated) in enumerate(reversed(rows)):
            no = total - i
            self.table.setItem(i, 0, QTableWidgetItem(str(no)))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(desc))
            self.table.setItem(i, 3, QTableWidgetItem(cnt))
            self.table.setItem(i, 4, QTableWidgetItem(self._format_dt(created)))
            self.table.setItem(i, 5, QTableWidgetItem(self._format_dt(updated)))

            # build edit/delete buttons exactly as before…
            btn_edit   = QPushButton("✎")
            btn_delete = QPushButton("🗑")
            for b in (btn_edit, btn_delete):
                b.setFixedWidth(30)
            btn_edit.clicked.connect(lambda _, _id=cid: self.start_edit(_id))
            btn_delete.clicked.connect(lambda _, _id=cid: self._on_delete(_id))

            action_frame = QFrame()
            action_layout = QHBoxLayout(action_frame)
            action_layout.setContentsMargins(0,0,0,0)
            action_layout.setSpacing(4)
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            action_layout.addStretch()
            self.table.setCellWidget(i, 6, action_frame)

        # 5) reapply the name‐filter
        ft = self.search_input.text().lower().strip()
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 1)
            self.table.setRowHidden(r, ft not in (name_item.text().lower() if name_item else ""))


    def _on_save(self):
        self.save_category()
        self.load_categories()

    def _on_delete(self, cid):
        self.delete_category(cid)
        self.load_categories()

    def save_category(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        if not name:
            QMessageBox.warning(self,"Input Error","Name cannot be empty.")
            return

        conn = get_connection(); cur = conn.cursor()
        try:
            if self.current_id is None:
                cur.callproc("category_pkg.add_category",[name,desc])
            else:
                cur.callproc("category_pkg.update_category",
                             [self.current_id,name,desc])
        except oracledb.IntegrityError:
            QMessageBox.critical(self,"Error","Category name must be unique.")
        finally:
            cur.close(); conn.close()

        self.cancel_edit()

    def start_edit(self, category_id):
        conn = get_connection(); cur = conn.cursor()
        p1=cur.var(str); p2=cur.var(str)
        p3=cur.var(int); p4=cur.var(str); p5=cur.var(str)
        cur.callproc("category_pkg.get_category",
                     [category_id,p1,p2,p3,p4,p5])
        cur.close(); conn.close()

        self.current_id=category_id
        self.name_input.setText(p1.getvalue() or "")
        self.desc_input.setPlainText(p2.getvalue() or "")
        self.save_btn.setText("Save Changes")
        self.cancel_btn.show()

    def cancel_edit(self):
        self.current_id=None
        self.name_input.clear()
        self.desc_input.clear()
        self.save_btn.setText("Add Category")
        self.cancel_btn.hide()

    def delete_category(self, category_id):
        ans = QMessageBox.question(self,"Confirm Delete",
                                   "Delete this category?",
                                   QMessageBox.StandardButton.Yes |
                                   QMessageBox.StandardButton.No)
        if ans != QMessageBox.StandardButton.Yes:
            return
        conn = get_connection(); cur = conn.cursor()
        cur.callproc("category_pkg.delete_category",[category_id])
        cur.close(); conn.close()

        if self.current_id==category_id:
            self.cancel_edit()
