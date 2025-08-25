# views/pages/borrow_book.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QSpinBox,
    QFrame, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from db_connection import get_connection
import oracledb
from datetime import datetime

class BorrowBookPage(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.user = current_user
        self.cart = {}  # barcode -> {"title":…, "qty":…}
        self._build_ui()
        self._load_catalog()
        self._load_summary()
        self._start_countdown()

    def _build_ui(self):
        # Styles
        table_header_style = """
            QHeaderView::section {
                background-color: #005499;
                color: white;
                font-size: 14px;
            }
        """

        main = QHBoxLayout(self)
        main.setContentsMargins(8,8,8,8)
        main.setSpacing(12)

        # ── LEFT ── Catalog + Summary ──
        left = QVBoxLayout()

        # Catalog frame
        cat_frame = QFrame()
        cat_frame.setFrameShape(QFrame.Shape.StyledPanel)
        cf = QVBoxLayout(cat_frame)

        lbl_cat = QLabel("Category")
        lbl_cat.setStyleSheet("font-weight: bold; font-size:14px;")
        cf.addWidget(lbl_cat)

        row = QHBoxLayout()
        self.catalog_search = QLineEdit(placeholderText="Search catalog…")
        self.catalog_search.setFixedHeight(30)
        self.catalog_search.textChanged.connect(self._load_catalog)
        row.addWidget(self.catalog_search, 1)

        add_btn = QPushButton("Add ▶")
        add_btn.setFixedHeight(30)
        add_btn.clicked.connect(self._add_to_cart)
        row.addWidget(add_btn)
        cf.addLayout(row)

        self.tbl_catalog = QTableWidget(0,4)
        self.tbl_catalog.setHorizontalHeaderLabels(
            ["Barcode","Title","Author","Description"]
        )
        self.tbl_catalog.setStyleSheet(table_header_style)
        self._stretch(self.tbl_catalog)
        cf.addWidget(self.tbl_catalog, 2)
        left.addWidget(cat_frame, 2)

        # ── Refresh Button ─────────────────────────────────────────

        # Summary frame
        sum_frame = QFrame()
        sum_frame.setFrameShape(QFrame.Shape.StyledPanel)
        sf = QVBoxLayout(sum_frame)

        lbl_sum = QLabel("Borrowers")
        lbl_sum.setStyleSheet("font-weight: bold; font-size:14px;")
        sf.addWidget(lbl_sum)

        self.tbl_summary = QTableWidget(0,7)
        self.tbl_summary.setHorizontalHeaderLabels([
            "No","Student ID","Total Books",
            "Borrow Date","Due Date","Status","Action"
        ])
        self.tbl_summary.setStyleSheet(table_header_style)
        self._stretch(self.tbl_summary, last_resize="contents")
        self.tbl_summary.itemSelectionChanged.connect(self._on_summary_selected)
        sf.addWidget(self.tbl_summary, 3)
        left.addWidget(sum_frame, 3)

        main.addLayout(left, 3)


        # ── RIGHT ── Student Info, Duration, Cart, Countdown ──
        right = QVBoxLayout()
        right.setSpacing(8)

        # Student Info
        lbl_info = QLabel("Student Information")
        lbl_info.setStyleSheet("""
            background-color: #005499;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 7px;
            margin-bottom: 0px;
        """)
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right.addWidget(lbl_info)

        info = QFrame()
        info.setFrameShape(QFrame.Shape.StyledPanel)
        info.setStyleSheet("""
            QFrame {
                border: 1px solid #D4D4D4;
                border-radius: 4px;
                background: #FFFFFF;
                padding: 7px;
            }
            QLabel { font-size:13px; }
            QLineEdit { font-size:13px; height:28px; border:none; }
        """)
        fi = QFormLayout(info)
        fi.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        fi.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        fi.setVerticalSpacing(4)
        fi.setContentsMargins(0,1,0,1)

        self.inp_sid    = QLineEdit(placeholderText="Enter student ID…")
        self.inp_sid.editingFinished.connect(self._load_student)
        fi.addRow("Student ID:", self.inp_sid)

        self.lbl_name    = QLabel(); fi.addRow("Name:",    self.lbl_name)
        self.lbl_major   = QLabel(); fi.addRow("Major:",   self.lbl_major)
        self.lbl_phone   = QLabel(); fi.addRow("Phone:",   self.lbl_phone)
        self.lbl_address = QLabel(); fi.addRow("Address:", self.lbl_address)
        right.addWidget(info, 2)

        # Duration selector
        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Duration (days):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1,60)
        self.duration_spin.setValue(14)
        dur_row.addWidget(self.duration_spin)
        right.addLayout(dur_row)

        # Cart
        cart_frame = QFrame()
        cart_frame.setFrameShape(QFrame.Shape.StyledPanel)
        cart_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #D4D4D4;
                border-radius: 4px;
                background: #FFFFFF;
            }
        """)
        cart_layout = QVBoxLayout(cart_frame)
        cart_layout.setContentsMargins(8,8,8,8)
        cart_layout.setSpacing(4)

        lbl_cart = QLabel("Cart")
        lbl_cart.setStyleSheet("font-weight:bold; font-size:14px; border:none;")
        cart_layout.addWidget(lbl_cart)

        self.tbl_cart = QTableWidget(0,3)
        self.tbl_cart.setHorizontalHeaderLabels(["Title","Quantity","Act"])
        self.tbl_cart.setStyleSheet(table_header_style)
        hdr = self.tbl_cart.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_cart.verticalHeader().setVisible(False)
        self.tbl_cart.setEditTriggers(self.tbl_cart.EditTrigger.NoEditTriggers)
        self.tbl_cart.setSelectionBehavior(self.tbl_cart.SelectionBehavior.SelectRows)
        cart_layout.addWidget(self.tbl_cart, 2)

        checkout_btn = QPushButton("✔ Checkout Cart")
        checkout_btn.setFixedHeight(30)
        checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-size: 14px;
                padding: 4px 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        checkout_btn.clicked.connect(self._checkout_cart)
        cart_layout.addWidget(checkout_btn)

        right.addWidget(cart_frame, 3)

        # Countdown
        cnt = QFrame()
        cnt.setFrameShape(QFrame.Shape.StyledPanel)
        cnt.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #D4D4D4;
                border-radius: 4px;
            }
        """)
        vc = QVBoxLayout(cnt)
        vc.setContentsMargins(12,12,12,12)
        vc.setSpacing(6)

        lbl_cnt = QLabel("Days Until Next Due")
        lbl_cnt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cnt.setStyleSheet("font-size:14px; font-weight:bold; border:none;")
        vc.addWidget(lbl_cnt)

        self.lbl_count = QLabel("—")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_count.setStyleSheet("font-size:48px; color:#005499;")
        vc.addWidget(self.lbl_count)

        right.addWidget(cnt, 1)

        main.addLayout(right, 1)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(30)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_all)
        right.addWidget(refresh_btn)

    def _refresh_all(self):
        """Reload catalog, summary, and countdown in one go."""
        self._load_catalog()
        self._load_summary()
        self._update_countdown()

    def _stretch(self, tbl, last_resize="stretch"):
        hdr = tbl.horizontalHeader()
        n = tbl.columnCount()
        for i in range(n):
            if (last_resize == "contents" and i >= n-2) or i == n-1:
                mode = QHeaderView.ResizeMode.ResizeToContents
            else:
                mode = QHeaderView.ResizeMode.Stretch
            hdr.setSectionResizeMode(i, mode)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(tbl.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(tbl.SelectionBehavior.SelectRows)

    # ── LOAD CATALOG ──
    def _load_catalog(self):
        conn = get_connection()
        cur = conn.cursor()
        try:
            rc = cur.var(oracledb.DB_TYPE_CURSOR)
            cur.callproc("book_pkg.list_books", [rc])

            books = []
            for book_row in rc.getvalue():
                # Unpack all returned columns (11 expected)
# Unpack first 11 columns only and ignore the rest
                book_id, barcode, category, title, author, desc_lob, total, created, updated, cover_blob, pdf_blob = book_row[:11]


                # Convert LOBs to strings safely
                desc = desc_lob.read() if hasattr(desc_lob, "read") else desc_lob or ""

                # Store minimal required for catalog view
                books.append((book_id, barcode, title, author, desc))

        finally:
            cur.close()
            conn.close()

        term = self.catalog_search.text().lower().strip()
        filtered = [
            (bid, bc, t, a, d)
            for (bid, bc, t, a, d) in books
            if term in bc.lower() or term in t.lower()
        ]

        self.tbl_catalog.setRowCount(len(filtered))
        for i, (_, bc, t, a, d) in enumerate(filtered):
            self.tbl_catalog.setItem(i, 0, QTableWidgetItem(bc))
            self.tbl_catalog.setItem(i, 1, QTableWidgetItem(t))
            self.tbl_catalog.setItem(i, 2, QTableWidgetItem(a))
            self.tbl_catalog.setItem(i, 3, QTableWidgetItem(d))



    # ── ADD SINGLE TO CART ──
    def _add_to_cart(self):
        row = self.tbl_catalog.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Pick a book first")
            return
        bc    = self.tbl_catalog.item(row,0).text()
        title = self.tbl_catalog.item(row,1).text()
        if bc not in self.cart:
            self.cart[bc] = {"title":title, "qty":1}
        else:
            self.cart[bc]["qty"] += 1
        self._refresh_cart()

    def _refresh_cart(self):
        self.tbl_cart.setRowCount(len(self.cart))
        for i,(bc,info) in enumerate(self.cart.items()):
            self.tbl_cart.setItem(i,0, QTableWidgetItem(info["title"]))
            sp = QSpinBox(); sp.setRange(1,99); sp.setValue(info["qty"])
            sp.valueChanged.connect(lambda v,b=bc: self._update_qty(b,v))
            self.tbl_cart.setCellWidget(i,1,sp)
            btn = QPushButton("✖"); btn.setFixedWidth(24)
            btn.clicked.connect(lambda _,b=bc: self._remove_from_cart(b))
            self.tbl_cart.setCellWidget(i,2,btn)

    def _update_qty(self, bc, v):
        self.cart[bc]["qty"] = v

    def _remove_from_cart(self, bc):
        del self.cart[bc]
        self._refresh_cart()

    # ── CHECKOUT ──
    def _checkout_cart(self):
        sid = self.inp_sid.text().strip()
        if not sid.isdigit():
            QMessageBox.warning(self, "Student","Enter valid ID")
            return
        if not self.cart:
            QMessageBox.warning(self, "Cart Empty","Add books first")
            return
        days = self.duration_spin.value()
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            for bc,info in self.cart.items():
                for _ in range(info["qty"]):
                    cur.callproc("borrow_pkg.add_borrow",[int(sid), bc, days])
            conn.commit()
        except oracledb.DatabaseError as e:
            QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.information(self, "Done","Checked out all books")
            self.cart.clear(); self._refresh_cart()
            self._load_summary(); self._update_countdown()
        finally:
            if cur: cur.close()
            conn.close()

    # ── SUMMARY ──
    def _load_summary(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
              SELECT user_id,
                     COUNT(*)      AS total_books,
                     MIN(borrow_date)  AS first_ts,
                     MIN(due_date)     AS next_due,
                     CASE WHEN MAX(
                       CASE WHEN due_date < SYSDATE THEN 1 ELSE 0 END
                     )=1 THEN 'OVERDUE' ELSE 'BORROWED' END AS status
                FROM borrows
               WHERE status<>'RETURNED'
               GROUP BY user_id
               ORDER BY first_ts DESC
            """)
            rows = cur.fetchall()
        finally:
            if cur: cur.close()
            conn.close()

        self.tbl_summary.setRowCount(len(rows))
        for i,(uid,tot,bd,dd,st) in enumerate(rows):
            self.tbl_summary.setItem(i,0, QTableWidgetItem(str(i+1)))
            self.tbl_summary.setItem(i,1, QTableWidgetItem(str(uid)))
            self.tbl_summary.setItem(i,2, QTableWidgetItem(str(tot)))
            self.tbl_summary.setItem(i,3, QTableWidgetItem(bd.strftime("%d/%m/%Y")))
            self.tbl_summary.setItem(i,4, QTableWidgetItem(dd.strftime("%d/%m/%Y")))
            self.tbl_summary.setItem(i,5, QTableWidgetItem(st))

            # Actions
            btn_ret = QPushButton("↩"); btn_ret.setFixedWidth(28)
            btn_del = QPushButton("🗑"); btn_del.setFixedWidth(28)
            btn_ret.clicked.connect(lambda _,u=uid: self._return_all(u))
            btn_del.clicked.connect(lambda _,u=uid: self._delete_all(u))
            c = QFrame(); hl = QHBoxLayout(c); hl.setContentsMargins(0,0,0,0)
            hl.addWidget(btn_ret); hl.addWidget(btn_del); hl.addStretch()
            self.tbl_summary.setCellWidget(i,6,c)

    def _return_all(self, uid):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("SELECT borrow_id FROM borrows WHERE user_id=:u AND status<>'RETURNED'", {"u":uid})
            for (bid,) in cur.fetchall():
                cur.callproc("borrow_pkg.return_book",[bid])
            conn.commit()
        finally:
            if cur: cur.close()
            conn.close()
        self._load_summary(); self._update_countdown()

    def _delete_all(self, uid):
        ans = QMessageBox.question(
            self,
            "Delete?",
            f"Delete all borrow and return records for User {uid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()

            # 1) Delete all entries in RETURNS_LOG tied to this user’s borrows
            cur.execute("""
                DELETE FROM returns_log r
                 WHERE r.borrow_id IN (
                   SELECT b.borrow_id
                     FROM borrows b
                    WHERE b.user_id = :u
                 )
            """, {"u": uid})

            # 2) Now delete the borrows themselves
            cur.execute("""
                DELETE FROM borrows
                 WHERE user_id = :u
            """, {"u": uid})

            conn.commit()

        except oracledb.DatabaseError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        finally:
            if cur:
                cur.close()
            conn.close()

        # Refresh UI
        self._load_summary()
        self._update_countdown()
        QMessageBox.information(
            self,
            "Deleted",
            f"All borrowing (and related returns) for User {uid} have been removed."
        )


    def _on_summary_selected(self):
        sel = self.tbl_summary.selectionModel().selectedRows()
        if not sel: return
        r = sel[0].row()
        uid = self.tbl_summary.item(r,1).text()
        self.inp_sid.setText(uid)
        self._load_student()
        dd = self.tbl_summary.item(r,4).text()
        d  = datetime.strptime(dd,"%d/%m/%Y")
        days = (d - datetime.today()).days
        self.lbl_count.setText(str(days))
        clr = "green" if days>7 else "orange" if days>3 else "red"
        self.lbl_count.setStyleSheet(f"font-size:48px;color:{clr};")

    def _load_student(self):
        sid = self.inp_sid.text().strip()
        if not sid.isdigit(): return
        conn,cur = get_connection(),None
        try:
            cur=conn.cursor()
            cur.execute("SELECT username,major,phone,address FROM users WHERE user_id=:u",{"u":int(sid)})
            row=cur.fetchone()
        finally:
            if cur: cur.close()
            conn.close()
        if row:
            n,m,p,a=row
            self.lbl_name.setText(n)
            self.lbl_major.setText(m or "")
            self.lbl_phone.setText(p or "")
            self.lbl_address.setText(a or "")
        else:
            for lbl in (self.lbl_name,self.lbl_major,self.lbl_phone,self.lbl_address):
                lbl.clear()

    def _start_countdown(self):
        self._update_countdown()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_countdown)
        self._timer.start(60*1000)

    def _update_countdown(self):
        sid = self.inp_sid.text().strip()
        if not sid.isdigit():
            self.lbl_count.setText("—"); return
        conn,cur = get_connection(),None
        try:
            cur=conn.cursor()
            cur.execute("SELECT MIN(due_date-SYSDATE) FROM borrows WHERE user_id=:u AND status<>'RETURNED'",{"u":int(sid)})
            rem=cur.fetchone()[0]
        finally:
            if cur: cur.close()
            conn.close()
        days = int(rem) if rem is not None else 0
        self.lbl_count.setText(str(days))
        clr = "green" if days>7 else "orange" if days>3 else "red"
        self.lbl_count.setStyleSheet(f"font-size:48px;color:{clr};")
