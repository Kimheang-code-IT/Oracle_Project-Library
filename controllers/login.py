import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QCheckBox,
    QPushButton, QMessageBox, QHBoxLayout,
    QVBoxLayout, QFormLayout
)
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt, QSettings,pyqtSignal
from db_connection import get_connection
from models.user import User
from views.admin_dashboard import AdminDashboard
from views.student_dashboard import StudentDashboard


class LoginWindow(QWidget):
    logged_in = pyqtSignal(object) 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Library System — Login")
        self.setFixedSize(900, 500)

        # centralize your settings object
        self.settings = QSettings("MyCompany", "LibraryApp")

        self.setup_ui()
        self._load_remembered_username()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left banner ────────────────────────────────────────
        banner = QLabel()
        banner.setScaledContents(True)

        # build a reliable path to your resource
        img_path = os.path.join(
            os.path.dirname(__file__),
            "..", "resources", "images", "login_banner.png"
        )
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            print(f"⚠️  Failed to load banner image at: {img_path}")
        else:
            banner.setPixmap(pixmap.scaled(
                500, 500,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            ))

        main_layout.addWidget(banner)

        # ── Right form ────────────────────────────────────────
        form_widget = QWidget()
        form_widget.setFixedSize(400, 500)
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(40, 20, 40, 20)
        form_layout.setSpacing(15)

        title = QLabel("Welcome Back!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:24px; font-weight:bold;")
        form_layout.addWidget(title)

        desc = QLabel("Easily manage your library account below.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: gray;")
        form_layout.addWidget(desc)

        form_layout.addSpacing(20)
        form = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        form.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        form.addRow("Password:", self.password_input)

        form_layout.addLayout(form)

        self.remember_cb = QCheckBox("Remember me")
        form_layout.addWidget(self.remember_cb)

        self.login_btn = QPushButton("Log In")
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.login_btn.setFixedHeight(32)
        self.login_btn.setStyleSheet(
            "background-color: #2c3e50; color: white; font-weight: bold;"
        )
        form_layout.addWidget(self.login_btn)

        register_label = QLabel(
            '<a href="#">Don\'t have an account? Register</a>'
        )
        register_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        register_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        register_label.setOpenExternalLinks(False)
        form_layout.addWidget(register_label)

        form_layout.addStretch()
        main_layout.addWidget(form_widget)

        # ── Signals ────────────────────────────────────────────
        self.login_btn.clicked.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        register_label.linkActivated.connect(self.open_register)

    def _load_remembered_username(self):
        u = self.settings.value("username", "")
        if u:
            self.username_input.setText(u)
            self.remember_cb.setChecked(True)

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Credentials",
                                "Please enter both username and password.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, password, role FROM users "
                "WHERE LOWER(username) = :1",
                [username.lower()]
            )
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        if not row:
            QMessageBox.critical(self, "Login Failed",
                                 f"No user '{username}' found.")
            return

        user_id, stored_pw, role = row
        if password != stored_pw:
            QMessageBox.critical(self, "Login Failed",
                                 "Incorrect password.")
            return

        # remember / forget
        if self.remember_cb.isChecked():
            self.settings.setValue("username", username)
        else:
            self.settings.remove("username")

        user = User(user_id=user_id, username=username, role=role.upper())

        if role.upper() == "ADMIN":
            dash = AdminDashboard(user)
        else:
            dash = StudentDashboard(user)

        dash.show()
        self.close()

    def open_register(self):
        from controllers.register import RegisterWindow
        self.register_window = RegisterWindow()
        self.register_window.show()
