# views/pages/library_student.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel,
    QScrollArea, QGridLayout, QFrame, QMessageBox, QFileDialog, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage, QCursor
import oracledb
from db_connection import get_connection


class LibraryPage(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.books = []       # holds tuples: (book_id, barcode, category, title, author, desc, image_bytes, pdf_bytes)
        self.per_page = 8
        self.current_page = 0
        self.setup_ui()
        self.load_categories()
        self.load_books()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ── Control bar ──
        control_bar = QHBoxLayout()
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        control_bar.addWidget(self.category_filter)

        self.search_input = QLineEdit(placeholderText="Search books…")
        control_bar.addWidget(self.search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.load_books)
        control_bar.addWidget(search_btn)

        main_layout.addLayout(control_bar)

        # ── Scrollable cards ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.card_container = QWidget()
        self.card_layout = QGridLayout(self.card_container)
        self.card_layout.setSpacing(15)
        self.scroll_area.setWidget(self.card_container)
        main_layout.addWidget(self.scroll_area)

        # ── Pagination ──
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addStretch()
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)
        main_layout.addLayout(pagination_layout)

    def load_categories(self):
        conn = get_connection(); cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT category FROM vw_book_info ORDER BY category")
            for (cat,) in cur:
                self.category_filter.addItem(cat)
        finally:
            cur.close(); conn.close()

    def load_books(self):
        term = self.search_input.text().lower()
        sel_cat = self.category_filter.currentText()

        conn = get_connection(); cur = conn.cursor()
        try:
            cur.execute("""
                SELECT book_id, barcode, category, title, author, description, cover_image, pdf_file
                  FROM vw_book_info
                 WHERE (:cat = 'All Categories' OR category = :cat)
                   AND (LOWER(title) LIKE :q OR LOWER(barcode) LIKE :q)
                 ORDER BY title
            """, {"cat": sel_cat, "q": f"%{term}%"})
            self.books = []
            for bid, bc, cat, title, author, desc_lob, img_blob, pdf_blob in cur:
                desc = desc_lob.read() if hasattr(desc_lob, "read") else desc_lob or ""
                img_bytes = img_blob.read() if hasattr(img_blob, "read") else None
                pdf_bytes = pdf_blob.read() if hasattr(pdf_blob, "read") else None
                self.books.append((bid, bc, cat, title, author, desc, img_bytes, pdf_bytes))
            self.current_page = 0
            self.render_cards()
        finally:
            cur.close(); conn.close()

    def render_cards(self):
        # clear
        for i in reversed(range(self.card_layout.count())):
            w = self.card_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        row = col = 0
        start = self.current_page * self.per_page
        end = start + self.per_page
        for book in self.books[start:end]:
            card = self.create_book_card(*book)
            self.card_layout.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_cards()

    def next_page(self):
        if (self.current_page + 1) * self.per_page < len(self.books):
            self.current_page += 1
            self.render_cards()

    def create_book_card(self, book_id, barcode, category, title, author, desc, img_bytes, pdf_bytes):
        frame = QFrame()
        frame.setFixedSize(200, 220)
        frame.setStyleSheet(
            "QFrame { background: #F2F3F4; border:1px solid #D5D8DC; border-radius:8px; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4,4,4,4)
        layout.setSpacing(4)

        # cover
        cover = QLabel()
        cover.setFixedHeight(100)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if img_bytes:
            qimg = QImage.fromData(img_bytes)
            pix = QPixmap.fromImage(qimg).scaled(200,100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            cover.setPixmap(pix)
        else:
            cover.setText("No Image")
        layout.addWidget(cover)

        # title
        tl = QLabel(title)
        tl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        tl.setWordWrap(True)
        tl.setStyleSheet("border:none;")
        layout.addWidget(tl)

        # author
        auth = QLabel(f"By {author}")
        auth.setFont(QFont("Arial", 9))
        auth.setStyleSheet("border:none;")
        layout.addWidget(auth)

        # download button on card
        btn = QPushButton("Details ▶")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda _, b=book_id: self.show_book_detail(b))
        layout.addWidget(btn)

        return frame

    def show_book_detail(self, book_id):
        # find the tuple
        for bid, bc, cat, title, author, desc, img_bytes, pdf_bytes in self.books:
            if bid == book_id:
                dlg = QDialog(self)
                dlg.setWindowTitle("Book Detail")
                dlg.resize(400, 500)
                form = QFormLayout(dlg)

                # barcode, title, ...
                form.addRow("Barcode:", QLabel(bc))
                form.addRow("Category:", QLabel(cat))
                form.addRow("Title:", QLabel(title))
                form.addRow("Author:", QLabel(author))
                desc_lbl = QLabel(desc)
                desc_lbl.setWordWrap(True)
                form.addRow("Description:", desc_lbl)

                # cover preview
                cov = QLabel()
                cov.setFixedHeight(150)
                if img_bytes:
                    qimg = QImage.fromData(img_bytes)
                    cov.setPixmap(QPixmap.fromImage(qimg).scaledToHeight(150, Qt.TransformationMode.SmoothTransformation))
                else:
                    cov.setText("No cover")
                form.addRow("Cover:", cov)

                # download PDF
                download = QPushButton("📥 Download PDF")
                download.clicked.connect(lambda _, p=pdf_bytes: self._download_pdf(p, title))
                form.addRow(download)

                dlg.exec()
                break

    def _download_pdf(self, pdf_bytes, title):
        if not pdf_bytes:
            QMessageBox.warning(self, "No PDF", "This book has no PDF attached.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"{title}.pdf", "PDF Files (*.pdf)")
        if path:
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            QMessageBox.information(self, "Saved", f"PDF saved to:\n{path}")
