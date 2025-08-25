# views/pages/book_dialogs.py

from PyQt6.QtWidgets     import *
from PyQt6.QtCore        import Qt
from PyQt6.QtGui         import QPixmap
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui         import QPainter
import io, barcode, oracledb
from barcode.writer      import ImageWriter
from db_connection       import get_connection


class AddBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Book")
        self.resize(400, 450)

        # these will hold uploaded / existing BLOB bytes
        self.cover_data = None
        self.pdf_data   = None

        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        form = QFormLayout(self)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setSpacing(10)

        # hidden PK field
        self.barcode = QLineEdit()
        self.barcode.setVisible(False)

        # core metadata fields
        self.category = QComboBox();   self.category.setFixedHeight(25)
        self.title    = QLineEdit();   self.title.setFixedHeight(25)
        self.author   = QLineEdit();   self.author.setFixedHeight(25)
        self.desc     = QTextEdit();   self.desc.setFixedHeight(75)
        self.total    = QSpinBox();    self.total.setRange(1, 1_000_000)
        self.total.setFixedHeight(25)

        # image & PDF upload buttons
        self.img_btn = QPushButton("Upload Cover Image")
        self.img_btn.clicked.connect(self._upload_image)
        self.pdf_btn = QPushButton("Upload PDF File")
        self.pdf_btn.clicked.connect(self._upload_pdf)

        # lay everything out
        form.addRow("Category:",    self.category)
        form.addRow("Title:",       self.title)
        form.addRow("Author:",      self.author)
        form.addRow("Description:", self.desc)
        form.addRow("Total Copies:",self.total)
        form.addRow("Cover Image:", self.img_btn)
        form.addRow("PDF File:",    self.pdf_btn)

        btns = QHBoxLayout()
        save   = QPushButton("Save");   save.clicked.connect(self._save)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        btns.addWidget(save); btns.addWidget(cancel)
        form.addRow(btns)

    def _load_categories(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
            for cid, name in cur:
                self.category.addItem(name, cid)
        finally:
            if cur: cur.close()
            conn.close()

    def _upload_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Images (*.png *.jpg *.bmp)")
        if fname:
            with open(fname, "rb") as f:
                self.cover_data = f.read()
            self.img_btn.setText("Cover Loaded")

    def _upload_pdf(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if fname:
            with open(fname, "rb") as f:
                self.pdf_data = f.read()
            self.pdf_btn.setText("PDF Loaded")

    def _save(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.callproc("book_pkg.add_book_full", [
                self.barcode.text().strip(),
                self.category.currentData(),
                self.title.text().strip(),
                self.author.text().strip(),
                self.desc.toPlainText().strip(),
                self.total.value(),
                self.cover_data,
                self.pdf_data
            ])
            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error saving book", str(e))
        finally:
            if cur: cur.close()
            conn.close()
    

class EditBookDialog(AddBookDialog):
    def __init__(self, parent=None, book_id=None):
        # store PK + prepare BLOB slots
        self.book_id    = book_id
        self.cover_data = None
        self.pdf_data   = None
        super().__init__(parent)
        self.setWindowTitle("Edit Book")
        self._load()

    def _load(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()

            # 1) pull down all the VARCHAR/CLOB/NUMBER fields
            p_bar  = cur.var(oracledb.DB_TYPE_VARCHAR, size=64)
            p_cat  = cur.var(oracledb.DB_TYPE_NUMBER)
            p_tit  = cur.var(oracledb.DB_TYPE_VARCHAR, size=256)
            p_aut  = cur.var(oracledb.DB_TYPE_VARCHAR, size=128)
            p_desc = cur.var(oracledb.DB_TYPE_CLOB)
            p_tot  = cur.var(oracledb.DB_TYPE_NUMBER)

            cur.callproc("book_pkg.get_book", [
                self.book_id, p_bar, p_cat, p_tit, p_aut, p_desc, p_tot
            ])

            # populate text controls
            self.barcode.setText(p_bar.getvalue())
            idx = self.category.findData(p_cat.getvalue())
            if idx >= 0:
                self.category.setCurrentIndex(idx)
            self.title.setText(p_tit.getvalue())
            self.author.setText(p_aut.getvalue())

            raw = p_desc.getvalue()
            txt = raw.read() if hasattr(raw, "read") else str(raw)
            self.desc.setPlainText(txt)

            self.total.setValue(p_tot.getvalue())

            # 2) now pull the two BLOB columns
            cur.execute("""
                SELECT cover_image, pdf_file
                  FROM books
                 WHERE book_id = :id
            """, [self.book_id])
            row = cur.fetchone()
            if row:
                cov_lob, pdf_lob = row
                if cov_lob:
                    self.cover_data = cov_lob.read()
                    self.img_btn.setText("Cover Loaded")
                if pdf_lob:
                    self.pdf_data = pdf_lob.read()
                    self.pdf_btn.setText("PDF Loaded")

        except Exception as e:
            QMessageBox.critical(self, "Error loading book", str(e))
        finally:
            if cur: cur.close()
            conn.close()

    def _save(self):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.callproc("book_pkg.update_book_full", [
                self.book_id,
                self.barcode.text().strip(),
                self.category.currentData(),
                self.title.text().strip(),
                self.author.text().strip(),
                self.desc.toPlainText().strip(),
                self.total.value(),
                self.cover_data,
                self.pdf_data
            ])
            conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error saving book", str(e))
        finally:
            if cur: cur.close()
            conn.close()


class BarcodeDialog(QDialog):
    def __init__(self, parent=None, book_id=None):
        super().__init__(parent)
        self.setWindowTitle("Barcode")
        self.resize(340, 250)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(10)

        code = self._fetch_barcode(book_id)
        if not code:
            self.layout.addWidget(QLabel("No barcode found."))
        else:
            self._render_barcode(code)

        btnrow = QHBoxLayout()
        print_btn = QPushButton("Print"); print_btn.clicked.connect(self._print)
        close_btn = QPushButton("Close"); close_btn.clicked.connect(self.accept)
        btnrow.addWidget(print_btn); btnrow.addWidget(close_btn)
        self.layout.addLayout(btnrow)

    def _fetch_barcode(self, book_id):
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("SELECT barcode FROM books WHERE book_id = :id", [book_id])
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            if cur: cur.close()
            conn.close()

    def _render_barcode(self, code):
        buf = io.BytesIO()
        bc = barcode.get_barcode_class("code128")
        bc(code, writer=ImageWriter()).write(buf, {"quiet_zone": 2})
        buf.seek(0)
        pix = QPixmap()
        pix.loadFromData(buf.read(), "PNG")
        lbl = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        lbl.setPixmap(pix.scaled(300,100,Qt.AspectRatioMode.KeepAspectRatio))
        self.layout.addWidget(lbl)
        self.layout.addWidget(QLabel(code, alignment=Qt.AlignmentFlag.AlignCenter))

    def _print(self):
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            painter = QPainter(printer)
            image = self.layout.itemAt(1).widget().pixmap()  # the barcode label
            painter.drawPixmap(0,0, image)
            painter.end()
class AddStockDialog(QDialog):
    def __init__(self, parent=None, book_id=None):
        super().__init__(parent)
        self.book_id = book_id
        self.setWindowTitle("Add Stock")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000)
        self.qty_input.setValue(1)

        form = QFormLayout()
        form.addRow("Quantity to add:", self.qty_input)
        layout.addLayout(form)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")
        btns.addStretch()
        btns.addWidget(add_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        add_btn.clicked.connect(self.add_stock)
        cancel_btn.clicked.connect(self.reject)

    def add_stock(self):
        qty = self.qty_input.value()
        if qty <= 0:
            QMessageBox.warning(self, "Invalid", "Quantity must be greater than 0.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.callproc("book_pkg.add_stock", [self.book_id, qty])
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        finally:
            cur.close()
            conn.close()

        self.accept()

    
