# views/pages/library.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class LibraryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Library (all books) will go here"))
