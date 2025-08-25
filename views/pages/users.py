# views/pages/users.py

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from db_connection import get_connection
import oracledb

class ManageUsersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.editing_id = None
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        self.setWindowTitle("Manage Users")
        main = QHBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(12)

        # ── LEFT PANEL: form ────────────────────────────────────
        left = QFrame()
        left.setFrameShape(QFrame.Shape.StyledPanel)
        left.setStyleSheet("""
            QLineEdit, QComboBox {
                height: 20px;
                font-size: 16px;
                padding: 4px 6px;
                margin: 10px;
                border: 1px solid #CCC;
                border-radius: 4px;
                background: #FAFAFA;
            }
            QPushButton {
                height: 20px;
                margin: 10px;
                font-size: 15px;
                background: #255083;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0 12px;
            }
            QPushButton:hover { background: #1B3452; }
            QLabel#hdr {
                background: #1B3452;
                color: white;
                font-weight: bold;
                padding-left: 8px;
            }
        """)
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0,0,0,0)
        left_l.setSpacing(0)

        # header
        hdr = QLabel("Add / Edit User", objectName="hdr")
        hdr.setFixedHeight(30)
        hdr.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        left_l.addWidget(hdr)

        # form
        form = QFormLayout()
        form.setContentsMargins(16,12,16,12)
        self.username_in = QLineEdit(); form.addRow("Username:", self.username_in)
        self.password_in = QLineEdit(); 
        self.password_in.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_in)
        self.role_in = QComboBox()
        self.role_in.addItems(["ADMIN","USER"])
        form.addRow("Role:", self.role_in)
        self.phone_in = QLineEdit(); form.addRow("Phone:", self.phone_in)
        self.address_in = QLineEdit(); form.addRow("Address:", self.address_in)
        self.major_in = QLineEdit(); form.addRow("Major:", self.major_in)

        # action buttons
        btn_h = QHBoxLayout()
        btn_h.addStretch()
        self.btn_submit = QPushButton("Add")
        self.btn_submit.clicked.connect(self.on_submit)
        btn_h.addWidget(self.btn_submit)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_cancel.hide()
        btn_h.addWidget(self.btn_cancel)
        form.addRow(btn_h)

        left_l.addLayout(form)
        main.addWidget(left, 1)

        # ── RIGHT PANEL: table ───────────────────────────────────
        right = QFrame()
        right.setFrameShape(QFrame.Shape.StyledPanel)
        right.setStyleSheet("""
            QHeaderView::section {
                background: #1B3452;
                color: white;
                padding: 4px;
                font-size: 13px;
                border: none;
            }
            QTableWidget {
                background: #FAFAFA;
                border: none;
                font-size: 13px;
            }
            QTableWidget::item:hover {
                background-color: #e8f4ff;
            }
        """)
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0,0,0,0)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "No","ID","Username","Password","Role","Phone","Address","Major","Actions"
        ])
        hdr = self.table.horizontalHeader()
        self.table.verticalHeader().setVisible(False)
        # stretch first eight, last one to contents
        for col in range(8):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        right_l.addWidget(self.table)
        main.addWidget(right, 3)

    def load_users(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, username, password, role, phone, address, major
                  FROM users
                 ORDER BY user_id
            """)
            rows = cur.fetchall()
        finally:
            if cur: cur.close()
            conn.close()

        self.table.setRowCount(len(rows))
        for i, (uid, un, pw, rl, ph, ad, mj) in enumerate(rows):
            self.table.setItem(i,0,QTableWidgetItem(str(i+1)))
            self.table.setItem(i,1,QTableWidgetItem(str(uid)))
            self.table.setItem(i,2,QTableWidgetItem(un))
            self.table.setItem(i,3,QTableWidgetItem(pw))
            self.table.setItem(i,4,QTableWidgetItem(rl))
            self.table.setItem(i,5,QTableWidgetItem(ph or ""))
            self.table.setItem(i,6,QTableWidgetItem(ad or ""))
            self.table.setItem(i,7,QTableWidgetItem(mj or ""))

            # actions
            btn_e = QPushButton("✎"); btn_d = QPushButton("🗑")
            for b in (btn_e, btn_d):
                b.setFixedWidth(28)
            btn_e.clicked.connect(lambda _, u=uid: self.start_edit(u))
            btn_d.clicked.connect(lambda _, u=uid: self.del_user(u))
            ctr = QFrame(); hl = QHBoxLayout(ctr)
            hl.setContentsMargins(0,0,0,0); hl.setSpacing(4)
            hl.addWidget(btn_e); hl.addWidget(btn_d); hl.addStretch()
            self.table.setCellWidget(i,8,ctr)

    def on_submit(self):
        if self.editing_id is None:
            self._add_user()
        else:
            self._update_user()

    def _add_user(self):
        un = self.username_in.text().strip()
        pw = self.password_in.text()
        rl = self.role_in.currentText()
        ph = self.phone_in.text().strip()
        ad = self.address_in.text().strip()
        mj = self.major_in.text().strip()
        if not un or not pw:
            QMessageBox.warning(self, "Input Error", "Username & password required.")
            return
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users(username,password,role,phone,address,major)
                VALUES(:u,:p,:r,:ph,:ad,:mj)
            """, {"u":un,"p":pw,"r":rl,"ph":ph,"ad":ad,"mj":mj})
            conn.commit()
        except oracledb.IntegrityError:
            QMessageBox.critical(self,"Error",f"User '{un}' exists.")
        finally:
            if cur: cur.close()
            conn.close()
        self._reset(); self.load_users()

    def start_edit(self, uid):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT username,password,role,phone,address,major
                  FROM users WHERE user_id=:id
            """, {"id":uid})
            row = cur.fetchone()
        finally:
            if cur: cur.close()
            conn.close()
        if not row:
            return
        un,pw,rl,ph,ad,mj = row
        self.editing_id = uid
        self.username_in.setText(un)
        self.password_in.setText(pw)
        self.role_in.setCurrentText(rl)
        self.phone_in.setText(ph or "")
        self.address_in.setText(ad or "")
        self.major_in.setText(mj or "")
        self.btn_submit.setText("Update")
        self.btn_cancel.show()

    def _update_user(self):
        un = self.username_in.text().strip()
        pw = self.password_in.text()
        rl = self.role_in.currentText()
        ph = self.phone_in.text().strip()
        ad = self.address_in.text().strip()
        mj = self.major_in.text().strip()
        if not un:
            QMessageBox.warning(self, "Input Error", "Username cannot be empty.")
            return
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE users
                   SET username=:u,password=:p,role=:r,
                       phone=:ph,address=:ad,major=:mj
                 WHERE user_id=:id
            """, {"u":un,"p":pw,"r":rl,"ph":ph,"ad":ad,"mj":mj,"id":self.editing_id})
            conn.commit()
        except oracledb.IntegrityError:
            QMessageBox.critical(self,"Error",f"User '{un}' exists.")
        finally:
            if cur: cur.close()
            conn.close()
        QMessageBox.information(self,"Success","User updated.")
        self._reset(); self.load_users()

    def del_user(self, uid):
        row = self.table.currentRow()
        if row < 0:
            return
        un = self.table.item(row,2).text()
        if QMessageBox.question(
            self, "Confirm Delete",
            f"Delete user '{un}'?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE user_id=:id",{"id":uid})
            conn.commit()
        finally:
            if cur: cur.close()
            conn.close()
        if self.editing_id == uid:
            self._reset()
        self.load_users()

    def on_cancel(self):
        self._reset()

    def _reset(self):
        self.editing_id = None
        for w in (self.username_in, self.password_in,
                  self.phone_in, self.address_in, self.major_in):
            w.clear()
        self.btn_submit.setText("Add")
        self.btn_cancel.hide()
