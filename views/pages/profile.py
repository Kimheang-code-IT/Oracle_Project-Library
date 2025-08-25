# views/pages/profile.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Profile information will go here"))
