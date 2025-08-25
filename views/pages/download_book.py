# views/pages/download_book.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QHeaderView, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage, QFont, QCursor
from db_connection import get_connection


class DownloadBookPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download Book PDF")
        self._build_ui()
        self._load_catalog()

    def _build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(10,10,10,10)
        outer.setSpacing(12)

        # ── Left: filter + table + download ──
        left = QVBoxLayout()
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Search:"))
        self.search = QLineEdit(placeholderText="Filter by barcode or title…")
        self.search.textChanged.connect(self._load_catalog)
        filter_row.addWidget(self.search, 1)
        left.addLayout(filter_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["No.","ID","Barcode","Title","Created"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        left.addWidget(self.table, 1)

        dl_row = QHBoxLayout()
        dl_row.addStretch()
        self.btn_download = QPushButton("Download PDF")
        self.btn_download.setEnabled(False)
        self.btn_download.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_download.clicked.connect(self._download)
        dl_row.addWidget(self.btn_download)
        left.addLayout(dl_row)

        outer.addLayout(left, 3)


        # ── Right: Detail pane ──
        detail = QFrame()
        detail.setFrameShape(QFrame.Shape.StyledPanel)
        detail.setFixedWidth(320)
        dlay = QVBoxLayout(detail)
        dlay.setContentsMargins(8,8,8,8)
        dlay.setSpacing(8)

        # Cover
        self.cover_label = QLabel("No cover")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setFixedSize(300,180)
        self.cover_label.setStyleSheet("border:1px solid #CCC;")
        dlay.addWidget(self.cover_label)

        # Metadata form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.lbl_barcode = QLabel("—")
        self.lbl_title   = QLabel("—")
        self.lbl_author  = QLabel("—")
        self.lbl_desc    = QLabel("—")
        self.lbl_desc.setWordWrap(True)
        self.lbl_created = QLabel("—")
        for label, widget in [
            ("Barcode:", self.lbl_barcode),
            ("Title:",   self.lbl_title),
            ("Author:",  self.lbl_author),
            ("Description:", self.lbl_desc),
            ("Created:", self.lbl_created),
        ]:
            form.addRow(label, widget)
        dlay.addLayout(form)

        outer.addWidget(detail, 1)


    def _load_catalog(self):
        term = f"%{self.search.text().lower()}%"
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT book_id, barcode, title, created_at
                  FROM vw_book_info
                 WHERE LOWER(barcode) LIKE :q
                    OR LOWER(title)   LIKE :q
                 ORDER BY title
            """, {"q": term})
            rows = cur.fetchall()
        finally:
            if cur: cur.close()
            conn.close()

        self.table.setRowCount(len(rows))
        for idx, (bid, bc, title, created) in enumerate(rows, start=1):
            r = idx-1
            self.table.setItem(r, 0, QTableWidgetItem(str(idx)))
            self.table.setItem(r, 1, QTableWidgetItem(str(bid)))
            self.table.setItem(r, 2, QTableWidgetItem(bc))
            self.table.setItem(r, 3, QTableWidgetItem(title))
            created_str = created.strftime("%d/%m/%Y %H:%M") if created else "—"
            self.table.setItem(r, 4, QTableWidgetItem(created_str))

        # reset detail
        self._clear_detail()


    def _on_row_selected(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            self._clear_detail()
            return

        row = sel[0].row()
        bid_item = self.table.item(row,1)
        if not bid_item:
            return
        book_id = int(bid_item.text())

        # 1) fetch all LOBs while connection is open
        conn, cur = get_connection(), None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT cover_image,
                       pdf_file,
                       barcode,
                       title,
                       author,
                       description,
                       created_at
                  FROM books
                 WHERE book_id = :id
            """, {"id": book_id})
            result = cur.fetchone()
            if not result:
                # no record
                self._clear_detail()
                return

            cov_lob, pdf_lob, bc, title, author, desc_lob, created = result

            # read LOBs now
            cover_bytes = cov_lob.read() if cov_lob else None
            self._pdf_bytes = pdf_lob.read()   if pdf_lob else None
            desc_text    = desc_lob.read()     if hasattr(desc_lob, "read") else desc_lob or ""
        finally:
            if cur: cur.close()
            conn.close()

        # 2) update UI
        if cover_bytes:
            img = QImage.fromData(cover_bytes)
            pix = QPixmap.fromImage(img).scaled(
                self.cover_label.width(), self.cover_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.cover_label.setPixmap(pix)
        else:
            self.cover_label.setText("No cover")

        self.lbl_barcode.setText(bc or "—")
        self.lbl_title  .setText(title or "—")
        self.lbl_author .setText(author or "—")
        self.lbl_desc   .setText(desc_text or "—")
        self.lbl_created.setText(
            created.strftime("%d/%m/%Y %H:%M") if created else "—"
        )

        self.btn_download.setEnabled(bool(self._pdf_bytes))



    def _clear_detail(self):
        self.cover_label.setText("No cover")
        for lbl in (
            self.lbl_barcode,
            self.lbl_title,
            self.lbl_author,
            self.lbl_desc,
            self.lbl_created
        ):
            lbl.setText("—")
        self.btn_download.setEnabled(False)
        self._pdf_bytes = None


    def _download(self):
        if not getattr(self, "_pdf_bytes", None):
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "book.pdf", "PDF Files (*.pdf)"
        )
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(self._pdf_bytes)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
            else:
                QMessageBox.information(self, "Downloaded", f"Saved to:\n{path}")
