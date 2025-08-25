# views/pages/history.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Read/download/borrow history will go here"))
