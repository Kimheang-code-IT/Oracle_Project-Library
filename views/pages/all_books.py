from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QCursor
import datetime, oracledb
from db_connection import get_connection


class AllBooksPage(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()

    def setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(12)

        # ── Top bar ──
        top = QHBoxLayout(); top.setSpacing(8)
        self.search = QLineEdit(placeholderText="Search books…")
        self.search.textChanged.connect(self.load_books)
        top.addWidget(self.search, 1)
        add_btn = QPushButton("＋ Add Book")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self.open_add_dialog)
        top.addWidget(add_btn)
        layout.addLayout(top)

        # ── Table ──
        self.table = QTableWidget(0, 14)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
          QHeaderView::section { background:#1B3452; color:white; height:30px; }
          QTableWidget { background:#FAFAFA; font:13px; }
          QTableWidget::item:hover { background:#d9d9d9; }
        """)
        headers = [
          "No","Cover","Barcode","Category","Title","Author","Description",
          "Tot","Add","Bor","Ava","Created","Updated","Actions"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        hdr = self.table.horizontalHeader()
        widths = [20, 50, 100, 100, 150, 120, 150, 50, 50, 50, 50, 140, 140, 120]
        modes  = [
          QHeaderView.ResizeMode.ResizeToContents,  # No
          QHeaderView.ResizeMode.Interactive,       # Cover
          QHeaderView.ResizeMode.Interactive,       # Barcode
          QHeaderView.ResizeMode.Stretch,           # Category
          QHeaderView.ResizeMode.Interactive,       # Title
          QHeaderView.ResizeMode.Stretch,           # Author
          QHeaderView.ResizeMode.Interactive,       # Description ← INTERACTIVE so user can still resize
          QHeaderView.ResizeMode.ResizeToContents,  # Tot
          QHeaderView.ResizeMode.ResizeToContents,  # Add
          QHeaderView.ResizeMode.ResizeToContents,  # Bor
          QHeaderView.ResizeMode.ResizeToContents,  # Ava
          QHeaderView.ResizeMode.ResizeToContents,  # Created
          QHeaderView.ResizeMode.ResizeToContents,  # Updated
          QHeaderView.ResizeMode.ResizeToContents   # Actions
        ]
        for i,(w,m) in enumerate(zip(widths,modes)):
            hdr.setSectionResizeMode(i, m)
            self.table.setColumnWidth(i, w)

        layout.addWidget(self.table, 1)
        self.setLayout(layout)

    def showEvent(self, ev: QEvent):
        if ev.type() == QEvent.Type.Show:
            self.load_books()
        super().showEvent(ev)

    def _format_dt(self, ts):
        try:
            if isinstance(ts, str):
                ts = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            return ts.strftime("%d/%m/%Y %H:%M")
        except:
            return "—"


    def load_books(self):
        conn = get_connection(); cur = conn.cursor()
        try:
            rc = cur.var(oracledb.DB_TYPE_CURSOR)
            cur.callproc("book_pkg.list_books", [rc])
            rows = []
            for row in rc.getvalue():
                bid, bc, cat, t, a, desc_lob, tot, added, borrowed, cdt_lob, udt_lob, cover_blob, pdf_blob = row[:13]

                desc = desc_lob.read() if hasattr(desc_lob, "read") else (desc_lob or "")
                cover_data = cover_blob.read() if hasattr(cover_blob, "read") else None

                def _read(val):
                    return val.read() if hasattr(val, "read") else val

                # read all numeric LOBs
                tot      = _read(tot) or 0
                added    = _read(added) or 0
                borrowed = _read(borrowed) or 0

                # read & format timestamps
                raw_cdt = _read(cdt_lob)
                raw_udt = _read(udt_lob)
                cdt     = self._format_dt(raw_cdt)
                udt     = self._format_dt(raw_udt)

                ava = int(tot) - int(borrowed)

                rows.append((
                    bid, bc, cat, t, a, desc,
                    str(tot), str(added), str(borrowed), str(ava),
                    cdt, udt,
                    cover_data
                ))

        finally:
            cur.close(); conn.close()

        rows.reverse()
        self.table.setRowCount(len(rows))
        total = len(rows)

        for i, (bid, bc, cat, t, a, desc, tot, added, borrowed, ava, cdt, udt, cover_blob) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(total - i)))

            cover_lbl = QLabel()
            cover_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cover_data = cover_blob
            if cover_data:
                from PyQt6.QtGui import QPixmap, QImage
                image = QImage.fromData(cover_data)
                pixmap = QPixmap.fromImage(image).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
                cover_lbl.setPixmap(pixmap)
            else:
                cover_lbl.setText("—")
            self.table.setCellWidget(i, 1, cover_lbl)

            self.table.setItem(i, 2, QTableWidgetItem(bc))
            self.table.setItem(i, 3, QTableWidgetItem(cat))
            self.table.setItem(i, 4, QTableWidgetItem(t))
            self.table.setItem(i, 5, QTableWidgetItem(a))
            # force the Description column (index 6) to 200 px
            # in setup_ui(), after creating hdr:
            self.table.setItem(i, 6, QTableWidgetItem(desc))
            self.table.setItem(i, 7, QTableWidgetItem(tot))
            self.table.setItem(i, 8, QTableWidgetItem(added))
            self.table.setItem(i, 9, QTableWidgetItem(borrowed))
            self.table.setItem(i,10, QTableWidgetItem(ava))
            self.table.setItem(i,11, QTableWidgetItem(cdt))
            self.table.setItem(i,12, QTableWidgetItem(udt))


            # Actions – FIXED: must be in loop
            container = QFrame()
            hl = QHBoxLayout(container)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(4)

            icons = ("✎", "🗑", "🖨", "📦")
            actions = [
                lambda _, x=bid: self.open_edit_dialog(x),
                lambda _, x=bid: self._on_delete(x),
                lambda _, x=bid: self.view_barcode(x),
                lambda _, x=bid: self.open_stock_dialog(x),
            ]

            for icon, action in zip(icons, actions):
                btn = QPushButton(icon)
                btn.setFixedWidth(28)
                btn.clicked.connect(action)
                hl.addWidget(btn)

            hl.addStretch()
            self.table.setCellWidget(i, 13, container)

        # Live filter
        term = self.search.text().lower().strip()
        for r in range(total):
            cat = self.table.item(r, 3).text().lower()
            tit = self.table.item(r, 4).text().lower()
            aut = self.table.item(r, 5).text().lower()
            self.table.setRowHidden(r, not (term in cat or term in tit or term in aut))

    def open_add_dialog(self):
        from views.pages.book_dialogs import AddBookDialog
        dlg = AddBookDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success","Book added")
            self.load_books()

    def open_edit_dialog(self, book_id):
        from views.pages.book_dialogs import EditBookDialog
        dlg = EditBookDialog(self, book_id=book_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success","Book updated")
            self.load_books()

    def _on_delete(self, book_id):
        # Confirm
        reply = QMessageBox.question(
            self, "Delete Book?", 
            "Are you sure you want to delete this book?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()

            # 1) check for active borrows
            cur.execute("""
                SELECT COUNT(*) 
                  FROM borrows 
                 WHERE book_id = :b 
                   AND status <> 'RETURNED'
            """, {"b": book_id})
            active = cur.fetchone()[0]
            if active > 0:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"There are {active} active borrow(s) for this book.\n"
                    "Please return or delete those first."
                )
                return

            # 2) safe to delete
            cur.callproc("book_pkg.delete_book", [book_id])
            conn.commit()
            QMessageBox.information(self, "Deleted", "Book successfully deleted.")

        except oracledb.IntegrityError:
            QMessageBox.critical(
                self, "Delete Error",
                "This book cannot be deleted due to existing references."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            if cur: cur.close()
            conn.close()

        # refresh table
        self.load_books()


    def view_barcode(self, book_id):
        from views.pages.book_dialogs import BarcodeDialog
        BarcodeDialog(self, book_id).exec()

    def open_stock_dialog(self, book_id):
        from views.pages.book_dialogs import AddStockDialog
        dlg = AddStockDialog(self, book_id=book_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Success","Stock added")
            self.load_books()
