from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QComboBox, QStackedWidget,
    QSizePolicy, QToolButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPainterPath




class SidebarButton(QPushButton):
    def __init__(self, text, icon_path=None, active_icon_path=None, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText("  " + text)
        self.default_icon = QIcon(icon_path) if icon_path else None
        self.active_icon = QIcon(active_icon_path) if active_icon_path else self.default_icon
        if self.default_icon:
            self.setIcon(self.default_icon)
            self.setIconSize(QSize(20, 20))

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 18px;
                background: none;
                border: none;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #255083;
            }
            QPushButton:checked {
                background: #FFB703;
                color: black;
                font-weight: bold;
            }
        """)
        self.toggled.connect(self.update_icon)

    def update_icon(self, checked):
        if checked:
            self.setIcon(self.active_icon)
        else:
            self.setIcon(self.default_icon)


class Sidebar(QFrame):
    def __init__(self, user_name, switch_callback, menu_items):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        self.setStyleSheet("#Sidebar { background: #1B3452; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo = QLabel()
        pix = QPixmap("resources/images/logo.png")
        if not pix.isNull():
            logo.setPixmap(pix)
            logo.setScaledContents(True)
        logo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        logo.setFixedSize(220, 60)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_container = QFrame()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 10)
        logo_layout.addWidget(logo)
        layout.addWidget(logo_container)

        avatar = QLabel()
        av = QPixmap("resources/images/person.png")
        if not av.isNull():
            size = 80
            av_scaled = av.scaled(size, size,
                                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                Qt.TransformationMode.SmoothTransformation)
        mask = QPixmap(size, size)
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, av_scaled)
        painter.end()
        avatar.setPixmap(mask)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar_container = QFrame()
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 10)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(avatar)
        layout.addWidget(avatar_container)

        name_lbl = QLabel(user_name)
        name_lbl.setStyleSheet("color:white; font-size:14px; font-weight:600;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_container = QFrame()
        name_layout = QVBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 10)
        name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_layout.addWidget(name_lbl)
        layout.addWidget(name_container)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self.buttons = {}

        for label, icon, active_icon in menu_items:
            btn = SidebarButton(label, icon, active_icon)
            self._btn_group.addButton(btn)
            btn.clicked.connect(lambda _, lbl=label: switch_callback(lbl))
            layout.addWidget(btn)
            self.buttons[label] = btn

        if self._btn_group.buttons():
            self._btn_group.buttons()[0].setChecked(True)

        layout.addStretch()

        footer = QLabel("© 2025 ACLEDA University of Business")
        footer.setStyleSheet("color:#777; font-size:10px; padding:8px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)


class NotificationButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Notifications")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QToolButton {
                background: none;
                border: 1px solid white;
                border-radius: 4px;
                padding: 0 10px;
                color: white;
                font-size: 14px;
            }
            QToolButton:hover {
                background: #B3B5BB;
                color: black;
            }
        """)


class BaseDashboard(QWidget):
    def __init__(self, user_name="User", menu_items=None, pages=None):
        super().__init__()
        self.setWindowTitle("ACLEDA University Portal")
        self.setMinimumSize(1200, 700)
        self.showFullScreen()

        self.menu_items = menu_items or []
        self.pages = pages or []

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar(user_name, self.switch_form, self.menu_items)
        root.addWidget(self.sidebar)

        right = QFrame()
        right.setStyleSheet("background:#f4f6fa;")
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background: #1B3452;")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(20, 8, 20, 8)
        hlay.setSpacing(12)

        sf = QFrame()
        sf.setFixedHeight(36)
        sf.setFixedWidth(400)
        sf.setStyleSheet("background: #ffffff; border-radius: 18px;")
        sfl = QHBoxLayout(sf)
        sfl.setContentsMargins(15, 0, 12, 0)
        sfl.setSpacing(8)

        search_button = QToolButton()
        icon = QPixmap("resources/icons/search.png")
        if not icon.isNull():
            icon = icon.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            search_button.setIcon(QIcon(icon))
            search_button.setIconSize(icon.size())
        search_button.setStyleSheet("border: none;")
        search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        search_button.clicked.connect(lambda: print("Search clicked"))
        sfl.addWidget(search_button)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search...")
        search_input.setFrame(False)
        search_input.setClearButtonEnabled(True)
        search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                font-size: 14px;
                color: #333;
                background: transparent;
            }
        """)
        sfl.addWidget(search_input, 1)
        hlay.addWidget(sf, 0)
        hlay.addStretch(1)

        notif_btn = NotificationButton()
        hlay.addWidget(notif_btn)

        lang = QComboBox()
        lang.addItems(["English", "ខ្មែរ", "中文"])
        lang.setStyleSheet("""
            QComboBox {
                color: white;
                background: transparent;
                border: 1px solid white;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 14px;
            }
            QComboBox:hover {
                color: black;
                background: #B3B5BB;
            }
            QComboBox QAbstractItemView {
                background: #1B3452;
                color: white;
                outline: none;
                border: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #FFB703;
                color: black;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #FFB703;
                color: black;
            }
        """)
        hlay.addWidget(lang)

        lbtn = QPushButton("Logout")
        lbtn.setFixedHeight(32)
        lbtn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: 1px solid white;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #B3B5BB;
                color: black;
            }
        """)
        lbtn.clicked.connect(self.do_logout)
        hlay.addWidget(lbtn)

        rlay.addWidget(header)
        self.content = QStackedWidget()
        for page in self.pages:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            
            wrapper = QFrame()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(5, 5, 5, 5)
            wrapper_layout.addWidget(page)
            scroll.setWidget(wrapper)
            page.setMinimumHeight(500)
            self.content.addWidget(scroll)

        rlay.addWidget(self.content)


        root.addWidget(right)
        self.setLayout(root)

        if self.pages:
            self.content.setCurrentIndex(0)

    def switch_form(self, name: str):
        for idx, (label, *_rest) in enumerate(self.menu_items):
            if label == name:
                self.content.setCurrentIndex(idx)
                btn = self.sidebar.buttons.get(name)
                if btn:
                    btn.setChecked(True)
                break

    def do_logout(self):
        """
        Close this dashboard and re-open the login window.
        """
        self.close()
        from controllers.login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()