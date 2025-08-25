from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox
from db_connection import get_connection

class BookDetailDialog(QDialog):
    def __init__(self, book_id, user):
        super().__init__()
        self.book_id = book_id
        self.user = user
        self.setWindowTitle("Book Details")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Fetch book details
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, description, pdf_file FROM books WHERE book_id = :bid", {"bid": self.book_id})
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, desc, pdf_data = row
            layout.addWidget(QLabel(f"<h3>{title}</h3>"))
            layout.addWidget(QLabel(desc))

            if pdf_data:
                btn = QPushButton("Download PDF")
                btn.clicked.connect(lambda: self.download_pdf(pdf_data, title))
                layout.addWidget(btn)

    def download_pdf(self, data, title):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"{title}.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(data.read())  # Oracle BLOB
                QMessageBox.information(self, "Download", "PDF downloaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
