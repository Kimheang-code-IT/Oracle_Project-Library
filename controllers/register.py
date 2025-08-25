# controllers/register.py

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox,
    QFormLayout, QHBoxLayout, QVBoxLayout
)
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt
from db_connection import get_connection
from controllers.login import LoginWindow

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Library System — Register")
        self.setFixedSize(600, 450)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # ── Left: Banner ──
        img_label = QLabel()
        pixmap = QPixmap("resources/images/register_banner.png")\
                 .scaled(300, 450, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                Qt.TransformationMode.SmoothTransformation)
        img_label.setPixmap(pixmap)
        main_layout.addWidget(img_label)

        # ── Right: Form ──
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(40,20,40,20)
        form_layout.setSpacing(15)

        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:24px;font-weight:bold;")
        desc = QLabel("Please fill in your details to register.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        form_layout.addWidget(title)
        form_layout.addWidget(desc)
        form_layout.addSpacing(20)

        # The actual form
        form = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        form.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        form.addRow("Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm Password")
        form.addRow("Confirm Password:", self.confirm_input)

        # New fields:
        self.major_input = QLineEdit()
        self.major_input.setPlaceholderText("e.g. Computer Science")
        form.addRow("Major:", self.major_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 555-1234")
        form.addRow("Phone:", self.phone_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g. 123 Library St.")
        form.addRow("Address:", self.address_input)

        form_layout.addLayout(form)

        # Register button
        self.register_btn = QPushButton("Register")
        self.register_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.register_btn.setFixedHeight(32)
        form_layout.addWidget(self.register_btn)

        # Login link
        login_label = QLabel('<a href="#">Already have an account? Login</a>')
        login_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        login_label.setOpenExternalLinks(False)
        form_layout.addWidget(login_label)

        main_layout.addWidget(form_widget)

        # ── Signals ──
        self.register_btn.clicked.connect(self.attempt_register)
        self.confirm_input.returnPressed.connect(self.attempt_register)
        login_label.linkActivated.connect(self.open_login)

    def attempt_register(self):
        # gather & trim inputs
        u = self.username_input.text().strip()
        p = self.password_input.text()
        c = self.confirm_input.text()
        mj = self.major_input.text().strip()
        ph = self.phone_input.text().strip()
        ad = self.address_input.text().strip()

        # validate
        if not (u and p and c and mj and ph and ad):
            QMessageBox.warning(self, "Missing Fields", "Please fill in all fields.")
            return
        if p != c:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return

        conn = get_connection()
        cur  = conn.cursor()
        # check for existing username
        cur.execute("SELECT 1 FROM users WHERE LOWER(username)=:u", u=u.lower())
        if cur.fetchone():
            QMessageBox.warning(self, "User Exists", f"Username '{u}' already taken.")
            cur.close(); conn.close()
            return

        # insert into users (including new columns)
        cur.execute("""
            INSERT INTO users(username,password,role,major,phone,address)
            VALUES(:u, :p, 'USER', :mj, :ph, :ad)
        """, u=u.lower(), p=p, mj=mj, ph=ph, ad=ad)
        conn.commit()
        cur.close(); conn.close()

        QMessageBox.information(self, "Registered",
                                "Account created successfully. Please log in.")
        self.open_login()
        self.close()

    def open_login(self):
        self.login_window = LoginWindow()
        self.login_window.show()
