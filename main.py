import sys
import os
import os as _os
LOGO_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.png")

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
    QComboBox, QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QTabWidget, QHeaderView, QFileDialog, QSpinBox, QDoubleSpinBox,
    QTextEdit, QGroupBox, QSplitter, QListWidget, QListWidgetItem,
    QStatusBar, QFrame, QAbstractItemView, QTableView, QInputDialog,
    QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QSize, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtGui import QFont, QColor, QIcon, QBrush, QPixmap

# Bağlantı modu: "local" veya "remote"
CONNECTION_MODE = "local"

class _DbProxy:
    """db.xxx çağrılarını CONNECTION_MODE'a göre local veya remote'a yönlendirir."""
    def __getattr__(self, name):
        if CONNECTION_MODE == "remote":
            import api_client
            return getattr(api_client, name)
        return getattr(db, name)

_db = _DbProxy()   # tüm kod db yerine _db kullanır ama mevcut kod db değişkenini kullanıyor,
                   # bu yüzden modül seviyesinde db'yi proxy ile değiştiriyoruz

def _get_db():
    return _db

# Giriş yapmış kullanıcı (global)
CURRENT_USER = {"id": 0, "username": "sistem", "full_name": "Sistem", "role": "admin"}

import database as _local_db
db = _local_db   # başlangıçta yerel; login sonrası proxy ile değiştirilir

GREY   = "#545454"
GREY_D = "#3A3A3A"   # koyu gri (çerçeve, hover)
GREY_L = "#6B6B6B"   # açık gri (hover)

COLORS = {
    "primary":      GREY,
    "primary_light": GREY_L,
    "success": "#2E7D32",
    "danger": "#C62828",
    "warning": "#F57F17",
    "bg": "#F5F5F5",
    "white": "#FFFFFF",
    "border": "#BDBDBD",
    "text": "#212121",
    "subtext": "#757575",
    "row_alt": "#F8F9FA",
    "row_hover": "#EEEEEE",
    "header_bg": GREY,
    "header_fg": "#FFFFFF",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}
QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 16px;
    font-weight: bold;
    min-height: 30px;
}}
QPushButton:hover {{
    background-color: {COLORS['primary_light']};
}}
QPushButton:pressed {{
    background-color: {GREY_D};
}}
QPushButton.success {{
    background-color: {COLORS['success']};
}}
QPushButton.success:hover {{
    background-color: #388E3C;
}}
QPushButton.danger {{
    background-color: {COLORS['danger']};
}}
QPushButton.danger:hover {{
    background-color: #D32F2F;
}}
QPushButton.warning {{
    background-color: {COLORS['warning']};
    color: #212121;
}}
QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px 8px;
    background: white;
    min-height: 28px;
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    border: 2px solid {GREY};
}}
QTableWidget {{
    background: white;
    gridline-color: #E0E0E0;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    selection-background-color: {COLORS['row_hover']};
    selection-color: {COLORS['text']};
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QHeaderView::section {{
    background-color: {COLORS['header_bg']};
    color: {COLORS['header_fg']};
    font-weight: bold;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {GREY_L};
}}
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background: white;
}}
QTabBar::tab {{
    background: #E0E0E0;
    color: {COLORS['text']};
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 100px;
}}
QTabBar::tab:selected {{
    background: {GREY};
    color: white;
    font-weight: bold;
}}
QGroupBox {{
    font-weight: bold;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 6px;
    color: {COLORS['primary']};
}}
QStatusBar {{
    background: #F0F0F0;
    color: #212121;
    font-size: 13px;
    min-height: 28px;
    border-top: 1px solid #BDBDBD;
}}
QLabel.title {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS['primary']};
}}
QLabel.stat {{
    font-size: 15px;
    font-weight: bold;
    color: {COLORS['primary']};
}}
"""


class _MobileAccessDialog(QDialog):
    """WiFi erişim bilgisi."""
    def __init__(self, parent, ip, port):
        super().__init__(parent)
        self.setWindowTitle("Mobil Erişim — WiFi")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        info = QLabel(
            f"<b>WiFi Yerel Erişim Açıldı</b><br><br>"
            f"Aynı WiFi ağındaki telefon / tablet tarayıcısına:<br><br>"
            f"<span style='font-size:18px; color:#545454; font-family:monospace'>"
            f"http://{ip}:{port}</span><br><br>"
            f"<span style='color:#757575; font-size:12px'>"
            f"İnternetten her yerden erişmek için:<br>"
            f"Menü → 📱 Mobil Erişim → İnternetten Erişim Aç (ngrok)</span>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("background:#E3F2FD; padding:16px; border-radius:6px;")
        lay.addWidget(info)

        url = f"http://{ip}:{port}"
        btn_copy = QPushButton("📋 Adresi Kopyala")
        btn_copy.clicked.connect(lambda: (QApplication.clipboard().setText(url),
                                          btn_copy.setText("✓ Kopyalandı!")))
        btn_close = QPushButton("Tamam")
        btn_close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addWidget(btn_copy); row.addWidget(btn_close)
        lay.addLayout(row)


class _NgrokSetupDialog(QDialog):
    """ngrok token kurulum dialog'u."""
    def __init__(self, parent, current_token=""):
        super().__init__(parent)
        self.setWindowTitle("ngrok Token Kurulumu")
        self.setMinimumWidth(480)
        self.token = ""
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        steps = QLabel(
            "<b>Kurulum adımları (sadece bir kez):</b><br><br>"
            "1. <a href='https://ngrok.com/signup'>ngrok.com/signup</a> adresinden <b>ücretsiz hesap</b> açın<br>"
            "2. Giriş yapın → <b>Your Authtoken</b> sayfasına gidin<br>"
            "3. Token'ı kopyalayıp aşağıya yapıştırın<br><br>"
            "<span style='color:#2E7D32'>✓ Ücretsiz — aylık 1GB, sınırsız kullanıcı</span>"
        )
        steps.setWordWrap(True)
        steps.setOpenExternalLinks(True)
        steps.setStyleSheet("background:#FFF8E1; padding:14px; border-radius:6px;")
        lay.addWidget(steps)

        form = QFormLayout()
        self.token_edit = QLineEdit(current_token)
        self.token_edit.setPlaceholderText("2abc123xyz... şeklinde token yapıştırın")
        form.addRow("ngrok Token:", self.token_edit)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _save(self):
        t = self.token_edit.text().strip()
        if len(t) < 10:
            QMessageBox.warning(self, "Hata", "Geçerli bir token giriniz!")
            return
        self.token = t
        self.accept()


class _NgrokActiveDialog(QDialog):
    """ngrok aktif — URL ve QR göster."""
    def __init__(self, parent, url):
        super().__init__(parent)
        self.setWindowTitle("İnternetten Erişim Açıldı 🌍")
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        # HTTPS URL göster
        info = QLabel(
            f"<b>🌍 İnternetten erişim AÇIK</b><br><br>"
            f"Herhangi bir telefon veya bilgisayar tarayıcısından:<br><br>"
            f"<span style='font-size:16px; color:#545454; font-family:monospace'>{url}</span><br><br>"
            f"<span style='color:#757575; font-size:12px'>"
            f"⚠ Program kapatılınca veya durdurulunca erişim kapanır.<br>"
            f"Her açılışta URL değişebilir.</span>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("background:#E8F5E9; padding:16px; border-radius:6px;")
        lay.addWidget(info)

        # QR kod (online servis üzerinden)
        try:
            from PyQt6.QtNetwork import QNetworkAccessManager
        except Exception:
            pass

        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={url}"
        # QR kodu indirip göster
        try:
            import urllib.request
            data = urllib.request.urlopen(qr_url, timeout=5).read()
            pix = QPixmap()
            pix.loadFromData(data)
            qr_label.setPixmap(pix)
            qr_label.setToolTip("Telefon kamerasıyla tarayın")
        except Exception:
            qr_label.setText("(QR kod için internet gerekli)")
        lay.addWidget(qr_label)

        btn_copy = QPushButton("📋 Adresi Kopyala")
        btn_copy.clicked.connect(lambda: (QApplication.clipboard().setText(url),
                                          btn_copy.setText("✓ Kopyalandı!")))
        btn_close = QPushButton("Tamam")
        btn_close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addWidget(btn_copy); row.addWidget(btn_close)
        lay.addLayout(row)


class CustomerManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Müşteri Yönetimi")
        self.setMinimumSize(680, 460)
        self._build_ui(); self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # Arama
        top = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Müşteri adı, kodu, telefon...")
        self.search.textChanged.connect(lambda: self._load(self.search.text()))
        top.addWidget(QLabel("Ara:")); top.addWidget(self.search); top.addStretch()
        lay.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Müşteri Adı", "Kodu", "Telefon", "Adres", "Durum"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1,2,3,4): hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_add   = QPushButton("+ Yeni Müşteri");  btn_add.clicked.connect(self._add)
        btn_edit  = QPushButton("✎ Düzenle");        btn_edit.clicked.connect(self._edit)
        btn_del   = QPushButton("✕ Sil")
        btn_del.setStyleSheet("background:#757575;color:white;border-radius:4px;padding:6px 14px;")
        btn_del.clicked.connect(self._delete)
        btn_excel = QPushButton("📥 Excel'den İçe Aktar")
        btn_excel.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;border-radius:4px;padding:6px 14px;")
        btn_excel.clicked.connect(self._import_excel)
        btn_close = QPushButton("Kapat"); btn_close.clicked.connect(self.accept)
        for b in (btn_add, btn_edit, btn_del, btn_excel):
            btn_row.addWidget(b)
        btn_row.addStretch(); btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

    def _load(self, search=""):
        rows = db.get_all_customers(search=search, active_only=False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            name_item = QTableWidgetItem(r["name"] or "")
            name_item.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, QTableWidgetItem(r["code"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r["phone"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(r["address"] or ""))
            s = QTableWidgetItem("✅ Aktif" if r["active"] else "⛔ Pasif")
            s.setForeground(QBrush(QColor("#2E7D32" if r["active"] else "#C62828")))
            self.table.setItem(i, 4, s)
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self,"Bilgi","Müşteri seçin."); return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _customer_dialog(self, c=None):
        dlg = QDialog(self); dlg.setWindowTitle("Müşteri" + (" Düzenle" if c else " Ekle"))
        dlg.setMinimumWidth(360); lay = QVBoxLayout(dlg); form = QFormLayout(); form.setSpacing(8)
        dlg.name  = QLineEdit(c["name"]    if c else "")
        dlg.code  = QLineEdit(c["code"]    if c else "")
        dlg.phone = QLineEdit(c["phone"]   if c else "")
        dlg.addr  = QLineEdit(c["address"] if c else "")
        form.addRow("Müşteri Adı *:", dlg.name)
        form.addRow("Kodu:",          dlg.code)
        form.addRow("Telefon:",       dlg.phone)
        form.addRow("Adres:",         dlg.addr)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        return dlg

    def _add(self):
        dlg = self._customer_dialog()
        if dlg.exec():
            if not dlg.name.text().strip():
                return QMessageBox.warning(self,"Hata","Müşteri adı zorunlu!")
            db.add_customer(dlg.name.text(), dlg.code.text(), dlg.phone.text(), dlg.addr.text())
            self._load(self.search.text())

    def _edit(self):
        cid = self._selected_id()
        if not cid: return
        c = db.get_customer(cid)
        dlg = self._customer_dialog(c)
        if dlg.exec():
            db.update_customer(cid, dlg.name.text(), dlg.code.text(),
                               dlg.phone.text(), dlg.addr.text())
            self._load(self.search.text())

    def _delete(self):
        cid = self._selected_id()
        if not cid: return
        if QMessageBox.question(self,"Sil","Müşteri silinsin mi?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            db.delete_customer(cid); self._load(self.search.text())

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self,"Müşteri Excel Dosyası","","Excel (*.xlsx *.xls)")
        if not path: return
        try:
            import pandas as pd
            df = pd.read_excel(path)
            df.columns = [str(c).strip().lower() for c in df.columns]

            # Sütun eşleştirme — esnek
            col_map = {}
            for col in df.columns:
                if any(k in col for k in ["ad","isim","müşteri","musteri","name"]): col_map.setdefault("name", col)
                elif any(k in col for k in ["kod","code"]): col_map.setdefault("code", col)
                elif any(k in col for k in ["tel","phone","gsm","cep"]): col_map.setdefault("phone", col)
                elif any(k in col for k in ["adres","address"]): col_map.setdefault("address", col)

            if "name" not in col_map:
                return QMessageBox.warning(self,"Hata",
                    f"'Müşteri Adı' sütunu bulunamadı.\nMevcut sütunlar: {', '.join(df.columns)}")

            records = []
            for _, row in df.iterrows():
                name = str(row.get(col_map["name"],"")).strip()
                if not name or name.lower() == "nan": continue
                records.append({
                    "name":    name,
                    "code":    str(row.get(col_map.get("code","_"),"")).strip() if "code" in col_map else "",
                    "phone":   str(row.get(col_map.get("phone","_"),"")).strip() if "phone" in col_map else "",
                    "address": str(row.get(col_map.get("address","_"),"")).strip() if "address" in col_map else "",
                })

            db.import_customers_bulk(records)
            self._load(self.search.text())
            QMessageBox.information(self,"Başarılı",f"{len(records)} müşteri içe aktarıldı.")
        except Exception as e:
            QMessageBox.critical(self,"Hata",f"İçe aktarma hatası:\n{e}")


class LocationManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Raf / Lokasyon Tanımlamaları")
        self.setMinimumSize(640, 480)
        self._build_ui()
        self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Lokasyon Adı", "Grup", "Açıklama", "Durum", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_add  = QPushButton("+ Yeni Lokasyon"); btn_add.clicked.connect(self._add)
        btn_edit = QPushButton("✎ Düzenle");       btn_edit.clicked.connect(self._edit)
        btn_del  = QPushButton("✕ Sil")
        btn_del.setStyleSheet("background:#757575;color:white;border-radius:4px;padding:6px 14px;")
        btn_del.clicked.connect(self._delete)
        btn_sync = QPushButton("🔄 Stoktan Senkronize Et")
        btn_sync.setStyleSheet("background:#37474F;color:white;border-radius:4px;padding:6px 14px;")
        btn_sync.clicked.connect(self._sync)
        btn_close = QPushButton("Kapat"); btn_close.clicked.connect(self.accept)
        for b in (btn_add, btn_edit, btn_del, btn_sync):
            btn_row.addWidget(b)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

    def _load(self):
        rows = db.get_all_locations()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            name_item = QTableWidgetItem(r["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.table.setItem(i, 0, name_item)
            grp_item = QTableWidgetItem(r["group_name"])
            grp_item.setForeground(QBrush(QColor("#545454") if r["group_name"] == "DEPO" else QColor("#545454")))
            grp_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(i, 1, grp_item)
            self.table.setItem(i, 2, QTableWidgetItem(r["description"] or ""))
            status = QTableWidgetItem("✅ Aktif" if r["active"] else "⛔ Pasif")
            status.setForeground(QBrush(QColor("#2E7D32") if r["active"] else QColor("#C62828")))
            self.table.setItem(i, 3, status)
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Bir lokasyon seçin.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _add(self):
        dlg = self._loc_dialog()
        if dlg.exec():
            name, grp, desc = dlg._get()
            if not name:
                return QMessageBox.warning(self, "Hata", "Lokasyon adı boş olamaz!")
            try:
                db.add_location(name, grp, desc)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Eklenemedi:\n{e}")

    def _edit(self):
        lid = self._selected_id()
        if not lid: return
        rows = db.get_all_locations()
        loc = next((r for r in rows if r["id"] == lid), None)
        if not loc: return
        dlg = self._loc_dialog(loc)
        if dlg.exec():
            name, grp, desc = dlg._get()
            active = dlg.active_cb.isChecked()
            db.update_location(lid, name, grp, desc, active)
            self._load()

    def _delete(self):
        lid = self._selected_id()
        if not lid: return
        loc = next((r for r in db.get_all_locations() if r["id"] == lid), None)
        if not loc: return

        # Lokasyonda aktif stok varsa silme — stoklar hiçbir şekilde silinmez
        fabrics = db.get_all_fabrics(location=loc["name"])
        if fabrics:
            toplam_mt = sum((f["meter"] or 0) for f in fabrics)
            QMessageBox.warning(
                self, "Lokasyon Silinemez",
                f"<b>{loc['name']}</b> lokasyonunda <b>{len(fabrics)} stok kaydı</b> var "
                f"({toplam_mt:,.0f} mt).<br><br>"
                f"Stoklar silinemez — önce bu kayıtları çıkış/transfer ile "
                f"<b>başka lokasyona taşıyın</b>, sonra lokasyonu silebilirsiniz.")
            return

        if QMessageBox.question(self, "Sil", f"<b>{loc['name']}</b> lokasyonu silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                db.delete_location(lid)
            except Exception as e:
                QMessageBox.critical(self, "Silinemedi", str(e))
            self._load()

    def _sync(self):
        db.sync_locations()
        self._load()
        QMessageBox.information(self, "Tamam", "Stok lokasyonları senkronize edildi.")

    def _loc_dialog(self, loc=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Lokasyon Ekle" if not loc else "Lokasyon Düzenle")
        dlg.setMinimumWidth(340)
        lay = QVBoxLayout(dlg)
        form = QFormLayout(); form.setSpacing(8)
        dlg.name_edit = QLineEdit(loc["name"] if loc else "")
        dlg.grp_cb = QComboBox()
        dlg.grp_cb.addItems(["DEPO", "DIŞ DEPO"])
        if loc:
            idx = dlg.grp_cb.findText(loc["group_name"])
            if idx >= 0: dlg.grp_cb.setCurrentIndex(idx)
        dlg.desc_edit = QLineEdit(loc["description"] if loc else "")
        dlg.active_cb = QCheckBox("Aktif")
        dlg.active_cb.setChecked(loc["active"] if loc else True)
        form.addRow("Lokasyon Adı *:", dlg.name_edit)
        form.addRow("Grup:", dlg.grp_cb)
        form.addRow("Açıklama:", dlg.desc_edit)
        form.addRow("", dlg.active_cb)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        dlg._get = lambda: (dlg.name_edit.text().strip(), dlg.grp_cb.currentText(), dlg.desc_edit.text().strip())
        return dlg


class EmailSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("E-posta Rapor Ayarları")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # Gmail notu
        note = QLabel(
            "<b>Gmail kullanıyorsanız:</b> Normal şifre değil, "
            "<a href='https://myaccount.google.com/apppasswords'>Google Uygulama Şifresi</a> gereklidir.<br>"
            "Google Hesabım → Güvenlik → 2 Adımlı Doğrulama → Uygulama Şifreleri"
        )
        note.setWordWrap(True)
        note.setOpenExternalLinks(True)
        note.setStyleSheet("background:#FFF8E1;padding:10px;border-radius:6px;font-size:12px;")
        lay.addWidget(note)

        form = QFormLayout(); form.setSpacing(8)

        self.smtp_host = QLineEdit()
        self.smtp_port = QLineEdit()
        self.smtp_user = QLineEdit(); self.smtp_user.setPlaceholderText("gönderen@gmail.com")
        self.smtp_pass = QLineEdit(); self.smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_pass.setPlaceholderText("Uygulama şifresi (16 karakter)")
        self.from_addr = QLineEdit(); self.from_addr.setPlaceholderText("gönderen@gmail.com (boş = smtp_user)")
        self.to_addrs  = QLineEdit(); self.to_addrs.setPlaceholderText("alici@gmail.com, diger@gmail.com")

        self.send_hour = QComboBox()
        for h in range(24):
            self.send_hour.addItem(f"{h:02d}:00", h)

        self.send_enabled = QCheckBox("Her gün otomatik rapor gönder")

        form.addRow("SMTP Sunucu:", self.smtp_host)
        form.addRow("SMTP Port:", self.smtp_port)
        form.addRow("Kullanıcı Adı:", self.smtp_user)
        form.addRow("Şifre:", self.smtp_pass)
        form.addRow("Gönderen:", self.from_addr)
        form.addRow("Alıcılar:", self.to_addrs)
        form.addRow("Gönderim Saati:", self.send_hour)
        form.addRow("", self.send_enabled)
        lay.addLayout(form)

        btn_row = QHBoxLayout()
        btn_test = QPushButton("📤 Şimdi Test Gönder")
        btn_test.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;border-radius:4px;padding:7px 14px;")
        btn_test.clicked.connect(self._test_send)
        btn_save = QPushButton("Kaydet")
        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("background:#757575;color:white;border-radius:4px;padding:7px 14px;")
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_test); btn_row.addStretch()
        btn_row.addWidget(btn_save); btn_row.addWidget(btn_cancel)
        lay.addLayout(btn_row)

    def _load(self):
        import email_report as er
        cfg = er.get_email_config()
        self.smtp_host.setText(cfg["smtp_host"])
        self.smtp_port.setText(str(cfg["smtp_port"]))
        self.smtp_user.setText(cfg["smtp_user"])
        self.smtp_pass.setText(cfg["smtp_pass"])
        self.from_addr.setText(cfg["from_addr"])
        self.to_addrs.setText(cfg["to_addrs"])
        idx = self.send_hour.findData(cfg["send_hour"])
        if idx >= 0: self.send_hour.setCurrentIndex(idx)
        self.send_enabled.setChecked(cfg["send_enabled"])

    def _save(self):
        import email_report as er
        er.save_email_config(
            smtp_host    = self.smtp_host.text().strip(),
            smtp_port    = self.smtp_port.text().strip() or "587",
            smtp_user    = self.smtp_user.text().strip(),
            smtp_pass    = self.smtp_pass.text(),
            from_addr    = self.from_addr.text().strip(),
            to_addrs     = self.to_addrs.text().strip(),
            send_hour    = self.send_hour.currentData(),
            send_enabled = self.send_enabled.isChecked(),
        )
        QMessageBox.information(self, "Kaydedildi", "E-posta ayarları kaydedildi.")
        self.accept()

    def _test_send(self):
        self._save_silent()
        import email_report as er
        try:
            n = er.send_report(test=True)
            QMessageBox.information(self, "Gönderildi ✓",
                f"Test raporu {n} alıcıya gönderildi!\nGelen kutunuzu kontrol edin.")
        except Exception as e:
            QMessageBox.critical(self, "Gönderilemedi", str(e))

    def _save_silent(self):
        import email_report as er
        er.save_email_config(
            smtp_host    = self.smtp_host.text().strip(),
            smtp_port    = self.smtp_port.text().strip() or "587",
            smtp_user    = self.smtp_user.text().strip(),
            smtp_pass    = self.smtp_pass.text(),
            from_addr    = self.from_addr.text().strip(),
            to_addrs     = self.to_addrs.text().strip(),
            send_hour    = self.send_hour.currentData(),
            send_enabled = self.send_enabled.isChecked(),
        )


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Giriş Yap")
        self.setMinimumWidth(360)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._build_ui()
        self._load_server_setting()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if _os.path.exists(LOGO_PATH):
            logo = QLabel()
            pix  = QPixmap(LOGO_PATH)
            logo.setPixmap(pix.scaledToWidth(220, Qt.TransformationMode.SmoothTransformation))
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)

        title = QLabel("Depo Takip Sistemine Giriş")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#545454;")
        layout.addWidget(title)

        # ── Bağlantı modu ──────────────────────────────────────
        conn_box = QGroupBox("Bağlantı")
        conn_lay = QVBoxLayout(conn_box)
        conn_lay.setSpacing(6)

        self.rb_local  = QPushButton("💻 Bu Bilgisayar (yerel)")
        self.rb_remote = QPushButton("🌐 Sunucuya Bağlan")
        self.rb_local.setCheckable(True);  self.rb_local.setChecked(True)
        self.rb_remote.setCheckable(True); self.rb_remote.setChecked(False)
        self.rb_local.setMinimumHeight(36)
        self.rb_remote.setMinimumHeight(36)
        self.rb_local.clicked.connect(lambda: self._set_mode("local"))
        self.rb_remote.clicked.connect(lambda: self._set_mode("remote"))

        self.server_url = QLineEdit()
        self.server_url.setPlaceholderText("http://192.168.1.x:5060")
        self.server_url.setVisible(False)

        conn_lay.addWidget(self.rb_local)
        conn_lay.addWidget(self.rb_remote)
        conn_lay.addWidget(self.server_url)
        layout.addWidget(conn_box)
        # Başlangıç stilleri — server_url tanımlandıktan sonra
        self._set_mode("local")

        # ── Giriş formu ────────────────────────────────────────
        form = QFormLayout(); form.setSpacing(8)
        self.username = QLineEdit(); self.username.setPlaceholderText("Kullanıcı adı")
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Şifre")
        form.addRow("Kullanıcı:", self.username)
        form.addRow("Şifre:",     self.password)
        layout.addLayout(form)

        self.err_label = QLabel("")
        self.err_label.setStyleSheet("color:#C62828; font-size:12px;")
        self.err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.err_label)

        btn = QPushButton("Giriş Yap")
        btn.setMinimumHeight(38)
        btn.clicked.connect(self._login)
        layout.addWidget(btn)

        self.password.returnPressed.connect(self._login)
        self.username.returnPressed.connect(lambda: self.password.setFocus())

    def _set_mode(self, mode):
        self.rb_local.setChecked(mode == "local")
        self.rb_remote.setChecked(mode == "remote")
        self.server_url.setVisible(mode == "remote")
        ACTIVE   = "background:#545454; color:white; font-weight:bold; text-align:left; padding:8px 12px; border-radius:4px;"
        INACTIVE = "background:white; color:#545454; font-weight:normal; text-align:left; padding:8px 12px; border-radius:4px; border:1px solid #BDBDBD;"
        if mode == "local":
            self.rb_local.setStyleSheet(ACTIVE)
            self.rb_remote.setStyleSheet(INACTIVE)
        else:
            self.rb_remote.setStyleSheet(ACTIVE)
            self.rb_local.setStyleSheet(INACTIVE)

    def _load_server_setting(self):
        """Daha önce kullanılan sunucu adresini yükle."""
        try:
            import json
            cfg_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "config.json")
            cfg = json.load(open(cfg_path)) if _os.path.exists(cfg_path) else {}
            saved_url = cfg.get("server_url", "")
            if saved_url:
                self.server_url.setText(saved_url)
                self._set_mode("remote")
        except Exception:
            pass

    def _save_server_setting(self, url):
        try:
            import json
            cfg_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "config.json")
            cfg = json.load(open(cfg_path)) if _os.path.exists(cfg_path) else {}
            cfg["server_url"] = url
            with open(cfg_path, "w") as f: json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _login(self):
        global CURRENT_USER, CONNECTION_MODE
        self.err_label.setText("")

        if self.rb_remote.isChecked():
            # ── Sunucuya bağlan ─────────────────────────────────
            url = self.server_url.text().strip()
            if not url:
                self.err_label.setText("Sunucu adresi giriniz!")
                return
            import api_client
            api_client.configure(url)
            self.err_label.setText("Bağlanıyor...")
            QApplication.processEvents()
            if not api_client.ping():
                self.err_label.setText(f"Sunucuya bağlanılamadı:\n{url}\n\nAdres ve sunucunun açık olduğundan emin olun.")
                return
            try:
                user = api_client.login(self.username.text().strip(), self.password.text())
                CONNECTION_MODE = "remote"
                CURRENT_USER.update(user)
                # db'yi proxy'ye çevir — __main__ modülünü kullan (import main değil!)
                import sys
                _mod = sys.modules['__main__']
                _mod.db = _mod._db
                self._save_server_setting(url)
                self.accept()
            except Exception as e:
                self.err_label.setText(str(e))
                self.password.clear(); self.password.setFocus()
        else:
            # ── Yerel bağlantı ──────────────────────────────────
            user = db.authenticate(self.username.text().strip(), self.password.text())
            if user:
                CONNECTION_MODE = "local"
                CURRENT_USER.update(user)
                self._save_server_setting("")  # yerel ise kayıtlı URL'yi temizle
                self.accept()
            else:
                self.err_label.setText("Kullanıcı adı veya şifre hatalı!")
                self.password.clear(); self.password.setFocus()


class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kullanıcı Yönetimi")
        self.setMinimumSize(580, 400)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Kullanıcı Adı", "Ad Soyad", "Rol", "Durum", "Kayıt Tarihi"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Butonlar
        btn_row = QHBoxLayout()
        btn_add  = QPushButton("+ Yeni Kullanıcı"); btn_add.clicked.connect(self._add)
        btn_pw   = QPushButton("🔑 Şifre Değiştir"); btn_pw.clicked.connect(self._change_pw)
        btn_tog  = QPushButton("⏸ Aktif/Pasif");    btn_tog.clicked.connect(self._toggle)
        btn_del  = QPushButton("✕ Sil")
        btn_del.setStyleSheet("background:#757575; color:white; border-radius:4px; padding:6px 14px;")
        btn_del.clicked.connect(self._delete)
        for b in (btn_add, btn_pw, btn_tog, btn_del):
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load(self):
        users = db.get_all_users()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            uname_item = QTableWidgetItem(u["username"])
            uname_item.setData(Qt.ItemDataRole.UserRole, u["id"])
            self.table.setItem(i, 0, uname_item)
            self.table.setItem(i, 1, QTableWidgetItem(u["full_name"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(u["role"]))
            status = QTableWidgetItem("✅ Aktif" if u["active"] else "⛔ Pasif")
            status.setForeground(QBrush(QColor("#2E7D32") if u["active"] else QColor("#C62828")))
            self.table.setItem(i, 3, status)
            self.table.setItem(i, 4, QTableWidgetItem(str(u["created_at"])[:10]))
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Kullanıcı seçin.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _add(self):
        dlg = QDialog(self); dlg.setWindowTitle("Yeni Kullanıcı"); dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg); form = QFormLayout(); form.setSpacing(8)
        uname = QLineEdit(); fname = QLineEdit()
        pw1 = QLineEdit(); pw1.setEchoMode(QLineEdit.EchoMode.Password)
        pw2 = QLineEdit(); pw2.setEchoMode(QLineEdit.EchoMode.Password)
        role_cb = QComboBox(); role_cb.addItems(["kullanici", "admin"])
        form.addRow("Kullanıcı Adı *:", uname)
        form.addRow("Ad Soyad:", fname)
        form.addRow("Şifre *:", pw1)
        form.addRow("Şifre (tekrar):", pw2)
        form.addRow("Rol:", role_cb)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec():
            if not uname.text().strip():
                return QMessageBox.warning(self, "Hata", "Kullanıcı adı boş olamaz!")
            if pw1.text() != pw2.text():
                return QMessageBox.warning(self, "Hata", "Şifreler eşleşmiyor!")
            if len(pw1.text()) < 4:
                return QMessageBox.warning(self, "Hata", "Şifre en az 4 karakter olmalı!")
            try:
                db.add_user(uname.text(), fname.text(), pw1.text(), role_cb.currentText())
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcı eklenemedi:\n{e}")

    def _change_pw(self):
        uid = self._selected_id()
        if not uid: return
        pw, ok = QInputDialog.getText(self, "Şifre Değiştir", "Yeni şifre:", QLineEdit.EchoMode.Password)
        if ok and pw:
            if len(pw) < 4:
                return QMessageBox.warning(self, "Hata", "Şifre en az 4 karakter!")
            db.update_user_password(uid, pw)
            QMessageBox.information(self, "Tamam", "Şifre güncellendi.")

    def _toggle(self):
        uid = self._selected_id()
        if not uid: return
        if uid == CURRENT_USER.get("id"):
            return QMessageBox.warning(self, "Uyarı", "Kendi hesabınızı pasif yapamazsınız!")
        db.toggle_user_active(uid); self._load()

    def _delete(self):
        uid = self._selected_id()
        if not uid: return
        if uid == CURRENT_USER.get("id"):
            return QMessageBox.warning(self, "Uyarı", "Kendi hesabınızı silemezsiniz!")
        if QMessageBox.question(self, "Sil", "Kullanıcı silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            db.delete_user(uid); self._load()


class FabricDialog(QDialog):
    def __init__(self, parent=None, fabric=None):
        super().__init__(parent)
        self.fabric = fabric
        self.setWindowTitle("Kumaş Ekle" if not fabric else "Kumaş Düzenle")
        self.setMinimumWidth(480)
        self._build_ui()
        if fabric:
            self._populate(fabric)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.product_code = QLineEdit()
        self.product_name = QLineEdit()
        self.color = QLineEdit()

        # Lokasyon — iki kademeli: önce depo (DEPO / dış depolar), DEPO seçilirse raf
        self.depo = QComboBox()
        self.depo.setEditable(False)
        self.raf = QComboBox()
        self.raf.setEditable(False)
        self.raf_label = QLabel("Raf *:")
        self._load_locations()
        self.depo.currentIndexChanged.connect(self._on_depo_change)

        self.meter = QDoubleSpinBox()
        self.meter.setRange(0, 999999)
        self.meter.setDecimals(2)
        self.kg = QDoubleSpinBox()
        self.kg.setRange(0, 999999)
        self.kg.setDecimals(2)
        self.piece_count = QLineEdit()

        self.birim_fiyat = QDoubleSpinBox()
        self.birim_fiyat.setRange(0, 9999999)
        self.birim_fiyat.setDecimals(2)
        self.birim_fiyat.setSuffix(" $")
        self.birim_fiyat.setStyleSheet("border: 1px solid #BDBDBD;")

        # Kumaş tipi — zorunlu
        self.fabric_type = QComboBox()
        self.fabric_type.addItem("— Seçiniz —", "")
        for t in ["HAM", "PFD", "BOYALI", "BASKILI"]:
            self.fabric_type.addItem(t, t)
        self.fabric_type.setStyleSheet("border: 1px solid #BDBDBD;")

        self.lot = QLineEdit()
        self.lot.setPlaceholderText("Boş bırakılırsa otomatik verilir (LOT-20260610-001)")

        self.description = QTextEdit()
        self.description.setMaximumHeight(70)

        form.addRow("Ürün Kodu *:", self.product_code)
        form.addRow("Ürün Bilgisi:", self.product_name)
        form.addRow("Renk:", self.color)
        form.addRow("Lokasyon *:", self.depo)
        form.addRow(self.raf_label, self.raf)
        self.raf_label.setVisible(False)
        self.raf.setVisible(False)

        # Giriş lokasyonu — köken takibi (taşınsa bile değişmez)
        self.entry_loc = QComboBox()
        self.entry_loc.addItem("— Lokasyon ile aynı —", "")
        for name in self._depo_rafs:
            self.entry_loc.addItem(name, name)
        for i in range(self.depo.count()):
            d = self.depo.itemData(i)
            if d and d != "__DEPO__":
                self.entry_loc.addItem(d, d)
        form.addRow("Giriş Lokasyonu:", self.entry_loc)
        form.addRow("Kumaş Tipi *:", self.fabric_type)
        form.addRow("Lot:", self.lot)
        form.addRow("Metre:", self.meter)
        form.addRow("Kilo:", self.kg)
        form.addRow("Top/Adet:", self.piece_count)
        form.addRow("Birim Fiyat ($/mt):", self.birim_fiyat)
        form.addRow("Açıklama:", self.description)

        layout.addLayout(form)

        # Zorunlu alan notu
        note = QLabel("* işaretli alanlar zorunludur")
        note.setStyleSheet("color:#9E9E9E; font-size:11px;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_locations(self):
        """İlk kademe: DEPO + dış depolar. İkinci kademe: DEPO'nun rafları."""
        locs = db.get_active_locations()
        self._depo_rafs = sorted(l["name"] for l in locs if l["group_name"] == "DEPO")
        dis_depolar    = sorted(l["name"] for l in locs if l["group_name"] != "DEPO")

        self.depo.clear()
        self.depo.addItem("— Seçiniz —", "")
        self.depo.addItem("DEPO", "__DEPO__")
        for name in dis_depolar:
            self.depo.addItem(name, name)

        self.raf.clear()
        self.raf.addItem("— Raf Seçiniz —", "")
        for name in self._depo_rafs:
            self.raf.addItem(name, name)

    def _on_depo_change(self, idx):
        is_depo = self.depo.currentData() == "__DEPO__"
        self.raf_label.setVisible(is_depo)
        self.raf.setVisible(is_depo)
        if not is_depo:
            self.raf.setCurrentIndex(0)

    def _selected_location(self):
        d = self.depo.currentData() or ""
        if d == "__DEPO__":
            return self.raf.currentData() or ""
        return d

    def _populate(self, f):
        self.product_code.setText(f["product_code"] or "")
        self.product_name.setText(f["product_name"] or "")
        self.color.setText(f["color"] or "")
        # Lokasyonu seç — raf ise DEPO + raf, değilse doğrudan
        loc_val = f["location"] or ""
        if loc_val in self._depo_rafs:
            self.depo.setCurrentIndex(self.depo.findData("__DEPO__"))
            self.raf.setCurrentIndex(self.raf.findData(loc_val))
        elif loc_val:
            idx = self.depo.findData(loc_val)
            if idx < 0:   # listede olmayan eski lokasyon — kaybolmasın
                self.depo.addItem(loc_val, loc_val)
                idx = self.depo.count() - 1
            self.depo.setCurrentIndex(idx)
        entry = dict(f).get("entry_location") or ""
        if entry:
            i = self.entry_loc.findData(entry)
            if i < 0:
                self.entry_loc.addItem(entry, entry)
                i = self.entry_loc.count() - 1
            self.entry_loc.setCurrentIndex(i)
        self.meter.setValue(f["meter"] or 0)
        self.kg.setValue(f["kg"] or 0)
        self.piece_count.setText(f["piece_count"] or "")
        self.birim_fiyat.setValue(f["birim_fiyat"] or 0)
        ft_idx = self.fabric_type.findData(f["fabric_type"] or "")
        if ft_idx >= 0:
            self.fabric_type.setCurrentIndex(ft_idx)
        self.lot.setText(f["lot"] or "")
        self.description.setPlainText(f["description"] or "")

    def _validate(self):
        errors = []
        if not self.product_code.text().strip():
            errors.append("• Ürün kodu zorunludur")
        if not self.depo.currentData():
            errors.append("• Lokasyon seçilmelidir")
        elif self.depo.currentData() == "__DEPO__" and not self.raf.currentData():
            errors.append("• Raf seçilmelidir")
        if not self.fabric_type.currentData():
            errors.append("• Kumaş tipi seçilmelidir (Ham / PFD / Boyalı / Baskılı)")
            self.fabric_type.setStyleSheet("border: 2px solid #C62828; border-radius:4px;")
        else:
            self.fabric_type.setStyleSheet("")
        if errors:
            QMessageBox.warning(self, "Eksik Bilgi", "\n".join(errors))
            return
        self.accept()

    def get_data(self):
        return {
            "product_code": self.product_code.text().strip().upper(),
            "product_name": self.product_name.text().strip(),
            "color": self.color.text().strip().upper(),
            "location": self._selected_location(),
            "entry_location": self.entry_loc.currentData() or self._selected_location(),
            "fabric_type": self.fabric_type.currentData() or "",
            "lot": self.lot.text().strip(),
            "meter": self.meter.value(),
            "kg": self.kg.value(),
            "piece_count": self.piece_count.text().strip(),
            "birim_fiyat": self.birim_fiyat.value(),
            "description": self.description.toPlainText().strip(),
        }


class CellEditDialog(QDialog):
    """Tek bir alanı düzenleyen küçük pencere — çift tıklamayla açılır.
    count > 1 ise toplu düzenleme: aynı değer seçili tüm kayıtlara yazılır."""
    def __init__(self, parent, fabric, field, label, count=1):
        super().__init__(parent)
        self.fabric = fabric
        self.field = field
        self.setWindowTitle(f"{label} Düzenle" if count == 1 else f"{label} — Toplu Düzenle")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        if count > 1:
            info = QLabel(f"⚠ <b>{count} kayıt</b> birden güncellenecek — "
                          f"girilen değer seçili tüm satırlara yazılır.")
            info.setStyleSheet("background:#FFF3E0; padding:6px; border-radius:4px; color:#E65100;")
        else:
            info = QLabel(f"<b>{fabric['product_code']}</b> — {fabric['color']}  "
                          f"<span style='color:#555'>({fabric['location']})</span>")
            info.setStyleSheet("background:#FFF8E1; padding:6px; border-radius:4px;")
        layout.addWidget(info)

        form = QFormLayout()
        cur = fabric[field]

        if field == "fabric_type":
            self.widget = QComboBox()
            self.widget.addItem("— Seçiniz —", "")
            for t in ["HAM", "PFD", "BOYALI", "BASKILI"]:
                self.widget.addItem(t, t)
            idx = self.widget.findData(cur or "")
            if idx >= 0:
                self.widget.setCurrentIndex(idx)
        elif field == "location":
            locs = db.get_active_locations()
            self._rafs = sorted(l["name"] for l in locs if l["group_name"] == "DEPO")
            dis = sorted(l["name"] for l in locs if l["group_name"] != "DEPO")
            self.depo = QComboBox()
            self.depo.addItem("— Seçiniz —", "")
            self.depo.addItem("DEPO", "__DEPO__")
            for n in dis:
                self.depo.addItem(n, n)
            self.raf = QComboBox()
            self.raf.addItem("— Raf Seçiniz —", "")
            for n in self._rafs:
                self.raf.addItem(n, n)
            self.raf_label = QLabel("Raf:")
            cur_loc = cur or ""
            if cur_loc in self._rafs:
                self.depo.setCurrentIndex(self.depo.findData("__DEPO__"))
                self.raf.setCurrentIndex(self.raf.findData(cur_loc))
            elif cur_loc:
                i = self.depo.findData(cur_loc)
                if i < 0:
                    self.depo.addItem(cur_loc, cur_loc)
                    i = self.depo.count() - 1
                self.depo.setCurrentIndex(i)
            self.depo.currentIndexChanged.connect(self._on_depo_change)
            self.widget = self.depo
        elif field == "entry_location":
            self.widget = QComboBox()
            locs = db.get_active_locations()
            for l in sorted(locs, key=lambda x: (x["group_name"] != "DEPO", x["name"])):
                self.widget.addItem(l["name"], l["name"])
            idx = self.widget.findData(cur or "")
            if idx < 0 and cur:
                self.widget.addItem(cur, cur)
                idx = self.widget.count() - 1
            if idx >= 0:
                self.widget.setCurrentIndex(idx)
        elif field in ("meter", "kg", "birim_fiyat"):
            self.widget = QDoubleSpinBox()
            self.widget.setRange(0, 9999999)
            self.widget.setDecimals(2)
            if field == "birim_fiyat":
                self.widget.setSuffix(" $")
            self.widget.setValue(cur or 0)
        else:
            self.widget = QLineEdit(str(cur or ""))

        form.addRow(f"{label}:", self.widget)
        if field == "location":
            form.addRow(self.raf_label, self.raf)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if field == "location":
            self._on_depo_change(0)
        self.widget.setFocus()

    def _on_depo_change(self, idx):
        is_depo = self.depo.currentData() == "__DEPO__"
        self.raf_label.setVisible(is_depo)
        self.raf.setVisible(is_depo)

    def _validate(self):
        v = self.value()
        if self.field == "product_code" and not str(v).strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Ürün kodu boş olamaz.")
            return
        if self.field == "location" and not v:
            QMessageBox.warning(self, "Eksik Bilgi", "Lokasyon (DEPO ise raf) seçilmelidir.")
            return
        if self.field == "fabric_type" and not v:
            QMessageBox.warning(self, "Eksik Bilgi", "Kumaş tipi seçilmelidir.")
            return
        self.accept()

    def value(self):
        if self.field in ("fabric_type", "entry_location"):
            return self.widget.currentData() or ""
        if self.field == "location":
            d = self.depo.currentData() or ""
            return (self.raf.currentData() or "") if d == "__DEPO__" else d
        if self.field in ("meter", "kg", "birim_fiyat"):
            return self.widget.value()
        text = self.widget.text().strip()
        if self.field in ("product_code", "color"):
            return text.upper()
        return text


class MovementDialog(QDialog):
    def __init__(self, parent, fabric, movement_type):
        super().__init__(parent)
        self.fabric = fabric
        self.movement_type = movement_type
        self._manual_pct = None   # fire oranı elle girildiyse yüzdesi
        self._skip_fire = False   # kullanıcı fire takibi istemedi
        label = "GİRİŞ" if movement_type == "GİRİŞ" else "ÇIKIŞ"
        self.setWindowTitle(f"Stok {label} — {fabric['product_code']} / {fabric['color']}")
        self.setMinimumWidth(440)
        self._build_ui(fabric)

    def _build_ui(self, fabric):
        layout = QVBoxLayout(self)

        bg = "#E3F2FD" if self.movement_type == "GİRİŞ" else "#FFEBEE"
        pieces = dict(fabric).get("piece_count") or "-"
        info = QLabel(f"<b>{fabric['product_name'] or fabric['product_code']}</b>  |  "
                      f"Renk: {fabric['color']}  |  Lokasyon: {fabric['location']}<br>"
                      f"Mevcut: <b>{fabric['meter']:.2f} mt</b>  /  <b>{fabric['kg']:.2f} kg</b>"
                      f"  /  <b>{pieces} top</b>")
        info.setStyleSheet(f"background:{bg}; padding:8px; border-radius:4px;")
        layout.addWidget(info)

        form = QFormLayout(); form.setSpacing(10)

        self.meter = QDoubleSpinBox(); self.meter.setRange(0, 999999); self.meter.setDecimals(2)
        self.kg    = QDoubleSpinBox(); self.kg.setRange(0, 999999);    self.kg.setDecimals(2)
        self.piece_count = QLineEdit()
        self.notes = QLineEdit()

        # Dış depodan müşteriye sevk = boyahane fire takibi
        self._is_dis_depo = False
        if self.movement_type == "ÇIKIŞ":
            dis = {l["name"] for l in db.get_active_locations() if l["group_name"] != "DEPO"}
            self._is_dis_depo = (fabric["location"] or "") in dis

        if self._is_dis_depo:
            self.pre_meter = QDoubleSpinBox(); self.pre_meter.setRange(0, 999999); self.pre_meter.setDecimals(2)
            self.pre_kg    = QDoubleSpinBox(); self.pre_kg.setRange(0, 999999);    self.pre_kg.setDecimals(2)
            self.lbl_pre_m = QLabel("Çıkış Öncesi:")
            self.lbl_pre_k = QLabel("Çıkış Öncesi:")

            mrow = QWidget(); ml = QHBoxLayout(mrow); ml.setContentsMargins(0, 0, 0, 0)
            ml.addWidget(self.meter, 1); ml.addWidget(self.lbl_pre_m); ml.addWidget(self.pre_meter, 1)
            krow = QWidget(); kl = QHBoxLayout(krow); kl.setContentsMargins(0, 0, 0, 0)
            kl.addWidget(self.kg, 1); kl.addWidget(self.lbl_pre_k); kl.addWidget(self.pre_kg, 1)
            form.addRow("Metre:", mrow)
            form.addRow("Kilo:", krow)

            self.lbl_fire = QLabel("Fire:")
            self.fire_label = QLabel("—")
            self.fire_label.setStyleSheet("color:#C62828; font-weight:bold;")
            form.addRow(self.lbl_fire, self.fire_label)

            for w in (self.meter, self.kg, self.pre_meter, self.pre_kg):
                w.valueChanged.connect(self._update_fire_label)
        else:
            form.addRow("Metre:", self.meter)
            form.addRow("Kilo:", self.kg)

        form.addRow("Top/Adet:", self.piece_count)

        # Çıkışta renk / lab / parti bilgileri
        if self.movement_type == "ÇIKIŞ":
            self.out_color = QLineEdit()
            self.lab_no = QLineEdit()
            self.parti_no = QLineEdit()
            form.addRow("Renk:", self.out_color)
            form.addRow("Lab No:", self.lab_no)
            form.addRow("Parti No:", self.parti_no)

        form.addRow("Not:", self.notes)

        # Çıkış ise hedef seçimi
        if self.movement_type == "ÇIKIŞ":
            self.dest_type = QComboBox()
            self.dest_type.addItems(["Müşteri", "Lokasyon", "Diğer"])
            self.dest_type.currentIndexChanged.connect(self._on_dest_type_change)

            self.dest_customer = QComboBox()
            self.lbl_customer = QLabel("Müşteri:")
            self._load_customers()

            # Lokasyon — iki kademeli: DEPO / dış depolar, DEPO seçilirse raf
            self.dest_depo = QComboBox()
            self.lbl_depo = QLabel("Lokasyon:")
            self.dest_raf = QComboBox()
            self.lbl_raf = QLabel("Raf:")
            self._load_locations()
            self.dest_depo.currentIndexChanged.connect(self._on_dest_depo_change)

            self.dest_other = QLineEdit()
            self.dest_other.setPlaceholderText("Hedef açıklayınız...")
            self.lbl_other = QLabel("Diğer:")

            form.addRow("Çıkış Hedefi:", self.dest_type)
            form.addRow(self.lbl_customer, self.dest_customer)
            form.addRow(self.lbl_depo, self.dest_depo)
            form.addRow(self.lbl_raf, self.dest_raf)
            form.addRow(self.lbl_other, self.dest_other)
            self._on_dest_type_change(0)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if self._is_dis_depo:
            self._update_fire_visibility()

    def _fire_active(self):
        """Fire takibi: dış depodan yapılan her çıkışta (hedef ne olursa olsun)."""
        return self._is_dis_depo and self.movement_type == "ÇIKIŞ"

    def _update_fire_visibility(self):
        on = self._fire_active()
        for w in (self.lbl_pre_m, self.pre_meter, self.lbl_pre_k, self.pre_kg,
                  self.lbl_fire, self.fire_label):
            w.setVisible(on)

    def _update_fire_label(self):
        if not self._is_dis_depo:
            return
        pre_m, m = self.pre_meter.value(), self.meter.value()
        pre_k, k = self.pre_kg.value(), self.kg.value()
        parts = []
        if pre_m > 0:
            if pre_m < m:
                self.fire_label.setText("⚠ Çıkış öncesi metre, çıkış metresinden küçük olamaz")
                return
            parts.append(f"{pre_m - m:,.2f} mt (%{(pre_m - m) / pre_m * 100:.1f})")
        if pre_k > 0:
            if pre_k < k:
                self.fire_label.setText("⚠ Çıkış öncesi kilo, çıkış kilosundan küçük olamaz")
                return
            parts.append(f"{pre_k - k:,.2f} kg (%{(pre_k - k) / pre_k * 100:.1f})")
        self.fire_label.setText("  |  ".join(parts) if parts else "—")

    def _on_ok(self):
        if self._fire_active() and not self._skip_fire:
            pre_m, pre_k = self.pre_meter.value(), self.pre_kg.value()
            m, k = self.meter.value(), self.kg.value()
            if pre_m <= 0 and pre_k <= 0:
                reply = QMessageBox.question(
                    self, "Fire Oranı",
                    "Çıkış öncesi metre/kilo girilmedi.\n\nFire oranını elle girmek ister misiniz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    from PyQt6.QtWidgets import QInputDialog
                    pct, ok = QInputDialog.getDouble(
                        self, "Fire Oranı", "Fire oranı (%):", 0, 0, 99.9, 1)
                    if not ok:
                        return
                    factor = 1 - pct / 100
                    if m > 0:
                        self.pre_meter.setValue(m / factor)
                    if k > 0:
                        self.pre_kg.setValue(k / factor)
                    self._manual_pct = pct
                    style = "color:#C62828; font-weight:bold; border:1px solid #C62828; border-radius:3px;"
                    self.pre_meter.setStyleSheet(style)
                    self.pre_kg.setStyleSheet(style)
                    self._update_fire_label()
                    return   # hesaplananı göster, kullanıcı tekrar OK'a basınca kaydedilir
                else:
                    self._skip_fire = True   # fire takibi olmadan normal çıkış
            elif (m > 0 and pre_m > 0 and pre_m < m) or (k > 0 and pre_k > 0 and pre_k < k):
                QMessageBox.warning(self, "Hatalı Değer",
                                    "Çıkış öncesi miktar, çıkış miktarından küçük olamaz.")
                return
        self.accept()

    def _load_customers(self):
        self.dest_customer.clear()
        self.dest_customer.addItem("— Seçiniz —", "")
        for c in db.get_all_customers():
            label = c["name"] + (f" ({c['code']})" if c["code"] else "")
            self.dest_customer.addItem(label, str(c["id"]))

    def _load_locations(self):
        locs = db.get_active_locations()
        rafs        = sorted(l["name"] for l in locs if l["group_name"] == "DEPO")
        dis_depolar = sorted(l["name"] for l in locs if l["group_name"] != "DEPO")

        self.dest_depo.clear()
        self.dest_depo.addItem("— Seçiniz —", "")
        self.dest_depo.addItem("DEPO", "__DEPO__")
        for name in dis_depolar:
            self.dest_depo.addItem(name, name)

        self.dest_raf.clear()
        self.dest_raf.addItem("— Raf Seçiniz —", "")
        for name in rafs:
            self.dest_raf.addItem(name, name)

    def _on_dest_type_change(self, idx):
        t = self.dest_type.currentText()
        for w in (self.lbl_customer, self.dest_customer):
            w.setVisible(t == "Müşteri")
        for w in (self.lbl_depo, self.dest_depo):
            w.setVisible(t == "Lokasyon")
        for w in (self.lbl_other, self.dest_other):
            w.setVisible(t == "Diğer")
        self._on_dest_depo_change(0)
        if self._is_dis_depo:
            self._update_fire_visibility()

    def _on_dest_depo_change(self, idx):
        show_raf = (self.dest_type.currentText() == "Lokasyon"
                    and self.dest_depo.currentData() == "__DEPO__")
        self.lbl_raf.setVisible(show_raf)
        self.dest_raf.setVisible(show_raf)
        if not show_raf:
            self.dest_raf.setCurrentIndex(0)

    def get_data(self):
        d = {
            "meter":       self.meter.value(),
            "kg":          self.kg.value(),
            "piece_count": self.piece_count.text().strip(),
            "notes":       self.notes.text().strip(),
            "destination": "", "destination_type": "",
            "fire_active": False, "pre_meter": 0.0, "pre_kg": 0.0,
            "fire_pct": 0.0, "fire_manual": False,
            "out_color": "", "lab_no": "", "parti_no": "",
        }
        if self.movement_type == "ÇIKIŞ":
            d["out_color"] = self.out_color.text().strip().upper()
            d["lab_no"] = self.lab_no.text().strip()
            d["parti_no"] = self.parti_no.text().strip()
            t = self.dest_type.currentText()
            d["destination_type"] = t
            if t == "Müşteri":
                d["destination"] = self.dest_customer.currentText() if self.dest_customer.currentData() else ""
            elif t == "Lokasyon":
                depo = self.dest_depo.currentData() or ""
                d["destination"] = (self.dest_raf.currentData() or "") if depo == "__DEPO__" else depo
            else:
                d["destination"] = self.dest_other.text().strip()

            if self._fire_active() and not self._skip_fire:
                pre_m, pre_k = self.pre_meter.value(), self.pre_kg.value()
                if pre_m > 0 or pre_k > 0:
                    d["fire_active"] = True
                    d["pre_meter"] = pre_m
                    d["pre_kg"] = pre_k
                    base = pre_m if pre_m > 0 else pre_k
                    out  = d["meter"] if pre_m > 0 else d["kg"]
                    d["fire_pct"] = max(0.0, (base - out) / base * 100) if base > 0 else 0.0
                    d["fire_manual"] = self._manual_pct is not None
        return d


TYPE_COLORS = {"GİRİŞ": "#2E7D32", "ÇIKIŞ": "#C62828", "SİLME": "#880E4F"}


def _fill_movement_table(table, movements, show_product=False):
    """Hareket tablosunu doldur. show_product=True ise ürün sütunu eklenir."""
    if show_product:
        cols = ["Tarih", "Tür", "Ürün Kodu", "Renk", "Lokasyon", "Metre", "Kilo", "Top/Adet", "Hedef", "Kullanıcı", "Not"]
    else:
        cols = ["Tarih", "Tür", "Metre", "Kilo", "Top/Adet", "Hedef", "Kullanıcı", "Not"]

    table.setColumnCount(len(cols))
    table.setHorizontalHeaderLabels(cols)
    hdr = table.horizontalHeader()
    hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    hdr.setSectionResizeMode(len(cols) - 1, QHeaderView.ResizeMode.Stretch)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setRowCount(len(movements))

    for i, m in enumerate(movements):
        m = dict(m)   # sqlite3.Row'da .get yok; dict'e çevirince iki kaynak da çalışır
        col = 0
        def _set(val, align=None, color=None, bold=False):
            nonlocal col
            item = QTableWidgetItem(str(val) if val else "")
            if align:
                item.setTextAlignment(align)
            if color:
                item.setForeground(QBrush(QColor(color)))
            if bold:
                item.setFont(QFont("", -1, QFont.Weight.Bold))
            table.setItem(i, col, item)
            col += 1

        _set(str(m["movement_date"])[:16])
        t = m["movement_type"]
        _set(t, color=TYPE_COLORS.get(t, "#333"), bold=True)
        if show_product:
            _set(m["product_code"] or "")
            _set(m["color"] or "")
            _set(m["location"] or "")
        _set(f"{m['meter']:,.2f}" if m["meter"] else "")
        _set(f"{m['kg']:,.2f}" if m["kg"] else "")
        _set(m["piece_count"] or "")
        dest = m.get("destination") or ""
        dest_type = m.get("destination_type") or ""
        dest_label = f"{dest_type}: {dest}" if dest and dest_type else dest
        _set(dest_label, color="#1565C0" if dest else None)
        _set(m["user_name"] or "")
        extra = []
        if m.get("out_color") and m.get("out_color") != m.get("color"):
            extra.append(f"Renk: {m['out_color']}")
        if m.get("lab_no"):
            extra.append(f"Lab: {m['lab_no']}")
        if m.get("parti_no"):
            extra.append(f"Parti: {m['parti_no']}")
        notes = m["notes"] or ""
        if extra:
            notes = (notes + "  |  " if notes else "") + "  ".join(extra)
        _set(notes)


class MovementsDialog(QDialog):
    """Tek ürünün tüm hareketleri."""
    def __init__(self, parent, fabric):
        super().__init__(parent)
        self.setWindowTitle(f"Tüm Hareketler — {fabric['product_code']} / {fabric['color']}")
        self.setMinimumSize(750, 480)
        layout = QVBoxLayout(self)

        info = QLabel(
            f"<b>{fabric['product_name'] or ''} {fabric['product_code']}</b>"
            f" — {fabric['color']} — <span style='color:#545454'>{fabric['location']}</span>"
        )
        info.setStyleSheet("font-size:14px; padding:6px; background:#E3F2FD; border-radius:4px;")
        layout.addWidget(info)

        table = QTableWidget()
        movements = db.get_movements(fabric["id"])
        _fill_movement_table(table, movements, show_product=False)
        layout.addWidget(table)

        row = QHBoxLayout()
        lbl = QLabel(f"<span style='color:#555'>{len(movements)} hareket kaydı</span>")
        btn = QPushButton("Kapat"); btn.clicked.connect(self.accept)
        row.addWidget(lbl); row.addStretch(); row.addWidget(btn)
        layout.addLayout(row)


class DailyMovementsDialog(QDialog):
    """Tarih aralığındaki tüm hareketler — seçili satır yokken açılır."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Hareketler")
        self.setMinimumSize(950, 540)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate

        # Hazır aralık butonları
        presets = QHBoxLayout()
        for label, days in [("Bugün", 0), ("Son 7 Gün", 7), ("Son 15 Gün", 15), ("Son 30 Gün", 30)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _, d=days: self._set_preset(d))
            presets.addWidget(b)
        presets.addStretch()
        layout.addLayout(presets)

        # Tarih aralığı seçici
        top = QHBoxLayout()
        top.addWidget(QLabel("Başlangıç:"))
        self.start_edit = QDateEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDate(QDate.currentDate())
        self.start_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_edit.dateChanged.connect(self._load)
        top.addWidget(self.start_edit)
        top.addWidget(QLabel("Bitiş:"))
        self.end_edit = QDateEdit()
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDate(QDate.currentDate())
        self.end_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_edit.dateChanged.connect(self._load)
        top.addWidget(self.end_edit)
        top.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#555; font-size:12px;")
        top.addWidget(self.count_lbl)
        layout.addLayout(top)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        btn = QPushButton("Kapat"); btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def _set_preset(self, days):
        from PyQt6.QtCore import QDate
        today = QDate.currentDate()
        # Sinyalleri kapat, iki tarihi birden ayarla, tek seferde yükle
        self.start_edit.blockSignals(True)
        self.end_edit.blockSignals(True)
        self.start_edit.setDate(today.addDays(-days))
        self.end_edit.setDate(today)
        self.start_edit.blockSignals(False)
        self.end_edit.blockSignals(False)
        self._load()

    def _load(self):
        start = self.start_edit.date().toString("yyyy-MM-dd")
        end = self.end_edit.date().toString("yyyy-MM-dd")
        if start > end:
            start, end = end, start
        movements = db.get_movements_by_range(start, end)
        _fill_movement_table(self.table, movements, show_product=True)
        if movements:
            in_m = sum(m["meter"] or 0 for m in movements if m["movement_type"] == "GİRİŞ")
            out_m = sum(m["meter"] or 0 for m in movements if m["movement_type"] == "ÇIKIŞ")
            self.count_lbl.setText(
                f"{len(movements)} hareket — Giriş: {in_m:,.0f} mt, Çıkış: {out_m:,.0f} mt"
            )
        else:
            self.count_lbl.setText("Bu tarih aralığında hareket yok")


COLS = ["#", "Ürün Kodu", "Ürün Bilgisi", "Renk", "Lokasyon", "Tip", "Lot", "Metre", "Kilo", "Top/Adet", "Birim Fiyat $", "Toplam Değer $", "Son Güncelleme", "Giriş Lok.", "Açıklama"]
_GREEN = QColor("#1B5E20")
_GREY  = QColor("#BDBDBD")
_ALT   = QColor("#F0F4FF")


def _export_table_to_excel(parent, model, table_view, title="Stok Raporu"):
    """Model verilerini sütun sırasına göre (görsel sıra dahil) Excel'e aktar."""
    path, _ = QFileDialog.getSaveFileName(
        parent, "Excel'e Aktar", f"{title}.xlsx", "Excel (*.xlsx)"
    )
    if not path:
        return
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from datetime import datetime

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title[:31]

        # Görsel sütun sırası (kullanıcı sütunları taşımış olabilir)
        hdr = table_view.horizontalHeader()
        col_count = model.columnCount()
        visual_order = [hdr.logicalIndex(vi) for vi in range(col_count)]

        # Başlık satırı
        headers = [model.headerData(li, Qt.Orientation.Horizontal) or "" for li in visual_order]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", start_color="1565C0")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 18

        # Veri satırları
        for row_i in range(model.rowCount()):
            row_data = []
            for li in visual_order:
                idx = model.index(row_i, li)
                val = model.data(idx, Qt.ItemDataRole.DisplayRole) or ""
                # Sayısal değerler için float'a çevir
                if li in (7, 8, 10, 11):
                    try:
                        val = float(str(val).replace(" $", "").replace(",", ""))
                    except Exception:
                        pass
                row_data.append(val)
            ws.append(row_data)

        # Sütun genişlikleri
        for i, col in enumerate(ws.columns, 1):
            max_len = max((len(str(c.value or "")) for c in col), default=8)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 40)

        # Footer notu
        ws.append([])
        ws.append([f"Dışa aktarıldı: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  {model.rowCount()} kayıt"])

        wb.save(path)
        QMessageBox.information(parent, "Başarılı", f"{model.rowCount()} kayıt dışa aktarıldı:\n{path}")
    except Exception as e:
        QMessageBox.critical(parent, "Hata", f"Dışa aktarma hatası:\n{e}")


def _export_widget_table_to_excel(parent, table_widget, title="Rapor"):
    """QTableWidget içeriğini Excel'e aktar (Lokasyon görünümü için)."""
    path, _ = QFileDialog.getSaveFileName(
        parent, "Excel'e Aktar", f"{title}.xlsx", "Excel (*.xlsx)"
    )
    if not path:
        return
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from datetime import datetime

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title[:31]

        hdr = table_widget.horizontalHeader()
        col_count = table_widget.columnCount()
        visual_order = [hdr.logicalIndex(vi) for vi in range(col_count)]

        headers = [table_widget.horizontalHeaderItem(li).text()
                   if table_widget.horizontalHeaderItem(li) else "" for li in visual_order]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", start_color="1565C0")
            cell.alignment = Alignment(horizontal="center")

        for row_i in range(table_widget.rowCount()):
            row_data = []
            for li in visual_order:
                item = table_widget.item(row_i, li)
                row_data.append(item.text() if item else "")
            ws.append(row_data)

        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=8)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 40)

        ws.append([])
        ws.append([f"Dışa aktarıldı: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  {table_widget.rowCount()} kayıt"])

        wb.save(path)
        QMessageBox.information(parent, "Başarılı", f"{table_widget.rowCount()} kayıt dışa aktarıldı:\n{path}")
    except Exception as e:
        QMessageBox.critical(parent, "Hata", f"Dışa aktarma hatası:\n{e}")


import re
_AUTO_LOT = re.compile(r"^LOT-\d{8}-\d+$")   # otomatik üretilen lot formatı


class FabricModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._rows = []
        self._ids  = []

    # tuple: 0=id,1=code,2=name,3=color,4=loc,5=tip,6=lot,7=mt,8=kg,9=piece,10=fiyat,11=deger,12=date,13=girisLok,14=desc
    def load(self, rows):
        self.beginResetModel()
        self._rows = []
        for r in rows:
            mt    = r["meter"] or 0.0
            kg    = r["kg"] or 0.0
            fiy   = r["birim_fiyat"] or 0.0
            deger = mt * fiy if mt > 0 else (kg * fiy if kg > 0 else 0.0)
            self._rows.append((
                r["id"],
                r["product_code"] or "",
                r["product_name"] or "",
                r["color"] or "",
                r["location"] or "",
                r["fabric_type"] or "",
                r["lot"] or "",
                mt,
                kg,
                r["piece_count"] or "",
                fiy,
                deger,
                str(r["updated_at"] or "")[:16],
                dict(r).get("entry_location") or "",
                r["description"] or "",
            ))
        self._ids = [r[0] for r in self._rows]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COLS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLS[section]
        if role == Qt.ItemDataRole.FontRole and orientation == Qt.Orientation.Horizontal:
            f = QFont(); f.setBold(True); return f
        return None

    def sort(self, col, order=Qt.SortOrder.AscendingOrder):
        if col == 0:   # # sütunu — sıralama yapma
            return
        self.layoutAboutToBeChanged.emit()
        reverse = (order == Qt.SortOrder.DescendingOrder)
        # Sayısal sütunlar: 7=mt, 8=kg, 10=fiyat, 11=değer
        numeric = {7, 8, 10, 11}
        def key(r):
            v = r[col]
            if col in numeric:
                return v if isinstance(v, (int, float)) else 0
            return str(v).lower()
        self._rows.sort(key=key, reverse=reverse)
        self._ids = [r[0] for r in self._rows]
        self.layoutChanged.emit()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        r = self._rows[row]

        # col: 0=#,1=code,2=name,3=color,4=loc,5=tip,6=lot,7=mt,8=kg,9=piece,10=fiyat,11=deger,12=date,13=girisLok,14=desc
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(row + 1)
            val = r[col]
            if col in (7, 8): return f"{val:.2f}"
            if col == 10: return f"{val:,.2f} $" if val else "—"
            if col == 11: return f"{val:,.2f} $" if val else "—"
            return str(val)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (7, 8, 10, 11):
                return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col in (7, 8):
                return QBrush(_GREY if r[col] == 0 else _GREEN)
            if col == 11 and r[11] > 0:
                return QBrush(QColor("#1A237E"))
            if col == 5:
                return QBrush({"HAM": QColor("#5D4037"),
                                "PFD": QColor("#00695C"),
                                "BOYALI": QColor("#545454"),
                                "BASKILI": QColor("#6A1B9A")}.get(r[5], QColor("#333")))
            if col == 6 and _AUTO_LOT.match(r[6]):
                return QBrush(QColor("#78909C"))

        if role == Qt.ItemDataRole.FontRole:
            if col == 6 and _AUTO_LOT.match(r[6]):
                f = QFont(); f.setItalic(True); return f

        if role == Qt.ItemDataRole.BackgroundRole:
            if row % 2 == 1:
                return QBrush(_ALT)

        if role == Qt.ItemDataRole.ToolTipRole:
            val = r[col]
            if col == 0: return str(row + 1)
            if col in (7, 8): return f"{val:.2f}"
            if col == 10: return f"{val:,.2f} $" if val else "Fiyat girilmemiş"
            if col == 11: return f"{val:,.2f} $" if val else "—"
            if col == 6 and _AUTO_LOT.match(r[6]):
                return f"{val}\n(Otomatik verilen lot numarası)"
            return str(val) if val else ""

        return None

    def id_at(self, row):
        if 0 <= row < len(self._ids):
            return self._ids[row]
        return None


class StockTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._model = FabricModel()
        self._build_ui()
        QTimer.singleShot(0, self._first_load)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        toolbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ürün kodu, adı, renk ile ara...")
        self.search_box.setMinimumWidth(280)
        self.search_box.textChanged.connect(self._on_search_change)

        self.location_filter = QComboBox()
        self.location_filter.setMinimumWidth(130)
        self.location_filter.currentIndexChanged.connect(self.refresh)

        self.type_filter = QComboBox()
        self.type_filter.setMinimumWidth(100)
        self.type_filter.addItem("Tüm Tipler", "")
        for t in ["HAM", "PFD", "BOYALI", "BASKILI"]:
            self.type_filter.addItem(t, t)
        self.type_filter.currentIndexChanged.connect(self.refresh)

        btn_add   = QPushButton("+ Yeni Kumaş"); btn_add.clicked.connect(self._add)
        btn_giris = QPushButton("↑ Giriş");      btn_giris.clicked.connect(self._giris)
        btn_cikis = QPushButton("↓ Çıkış");      btn_cikis.clicked.connect(self._cikis)
        btn_edit  = QPushButton("✎ Düzenle");    btn_edit.clicked.connect(self._edit)
        btn_del   = QPushButton("✕ Sil");        btn_del.clicked.connect(self._delete)
        btn_hist  = QPushButton("☰ Hareketler"); btn_hist.clicked.connect(self._history)
        btn_hist.setToolTip("Satır seçiliyse: o ürünün tüm hareketleri\nSeçili satır yoksa: tarih aralığına göre hareketler")

        btn_giris.setStyleSheet(f"background:{COLORS['success']}; color:white; font-weight:bold; border-radius:4px; padding:7px 14px;")
        btn_cikis.setStyleSheet(f"background:{COLORS['danger']}; color:white; font-weight:bold; border-radius:4px; padding:7px 14px;")
        btn_edit.setStyleSheet("background:#F57F17; color:white; font-weight:bold; border-radius:4px; padding:7px 14px;")
        btn_del.setStyleSheet("background:#757575; color:white; font-weight:bold; border-radius:4px; padding:7px 14px;")

        toolbar.addWidget(QLabel("Ara:")); toolbar.addWidget(self.search_box)
        toolbar.addWidget(QLabel("Lokasyon:")); toolbar.addWidget(self.location_filter)
        toolbar.addWidget(QLabel("Tip:")); toolbar.addWidget(self.type_filter)
        toolbar.addStretch()
        for b in (btn_add, btn_giris, btn_cikis, btn_edit, btn_del, btn_hist):
            toolbar.addWidget(b)
        layout.addLayout(toolbar)

        # QTableView — sadece görünen satırları render eder
        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.PenStyle.SolidLine)
        self.table.doubleClicked.connect(self._cell_edit)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.setMouseTracking(True)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.setMinimumSectionSize(40)
        hdr.setSectionsMovable(True)   # sütun sürükle-bırak

        # Başlangıç genişlikleri
        col_widths = [36, 100, 130, 110, 90, 70, 90, 72, 65, 80, 110, 120, 130, 220]
        for i, w in enumerate(col_widths):
            self.table.setColumnWidth(i, w)

        layout.addWidget(self.table)

        # ── Toplam Barı ──
        self._totals_bar = QFrame()
        self._totals_bar.setStyleSheet(
            "QFrame { background:#545454; border-radius:6px;"
            "border: 2px solid #3A3A3A; padding:0; }"
        )
        self._totals_bar.setFixedHeight(56)
        bar_layout = QHBoxLayout(self._totals_bar)
        bar_layout.setContentsMargins(20, 4, 20, 4)
        bar_layout.setSpacing(0)

        def _stat_widget(label):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            wl = QVBoxLayout(w); wl.setSpacing(2); wl.setContentsMargins(16, 2, 16, 2)
            lbl = QLabel(label)
            lbl.setStyleSheet("color:rgba(255,255,255,.7); font-size:10px; background:transparent;")
            val = QLabel("—")
            val.setStyleSheet("color:white; font-size:15px; font-weight:bold; background:transparent;")
            wl.addWidget(lbl); wl.addWidget(val)
            return w, val

        def sep():
            f = QFrame()
            f.setFrameShape(QFrame.Shape.VLine)
            f.setFixedWidth(1)
            f.setStyleSheet("background:rgba(255,255,255,.3); margin:8px 4px;")
            return f

        w1, self._tot_items  = _stat_widget("Kalem Sayısı")
        w2, self._tot_meter  = _stat_widget("Toplam Metre")
        w3, self._tot_kg     = _stat_widget("Toplam Kilo")
        w4, self._tot_value  = _stat_widget("Toplam Değer")

        for w in (w1, sep(), w2, sep(), w3, sep(), w4):
            bar_layout.addWidget(w)
        bar_layout.addStretch()

        self._filter_lbl = QLabel()
        self._filter_lbl.setStyleSheet(
            "color:#212121; font-size:11px; font-style:italic; background:transparent;")
        bar_layout.addWidget(self._filter_lbl)

        layout.addWidget(self._totals_bar)

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self.refresh)

    def _on_search_change(self):
        self._search_timer.start(250)

    def _first_load(self):
        self._reload_locations()
        self._fill_table()
        self._loaded = True

    def refresh(self):
        if not self._loaded:
            return
        self._fill_table()

    def refresh_with_locations(self):
        self._reload_locations()
        self._fill_table()

    def _reload_locations(self):
        current_loc = self.location_filter.currentData()
        self.location_filter.blockSignals(True)
        self.location_filter.clear()
        self.location_filter.addItem("Tüm Lokasyonlar", "")

        all_locs = db.get_active_locations()
        from collections import defaultdict
        groups = defaultdict(list)
        for l in all_locs:
            groups[l["group_name"]].append(l["name"])

        for grp in sorted(groups.keys()):
            if grp == "DEPO":
                # DEPO → tek seçenek, tümünü getirir
                self.location_filter.addItem("DEPO", "__GRP_DEPO__")
            else:
                # Diğer gruplar → tek tek lokasyon olarak listele
                for name in sorted(groups[grp]):
                    self.location_filter.addItem(name, name)

        if current_loc:
            idx = self.location_filter.findData(current_loc)
            if idx >= 0:
                self.location_filter.setCurrentIndex(idx)
        self.location_filter.blockSignals(False)

    def _fill_table(self):
        search  = self.search_box.text().strip()
        loc     = self.location_filter.currentData() or ""
        ftype   = self.type_filter.currentData() or ""

        if loc.startswith("__GRP_"):
            grp_name = loc[len("__GRP_"):-2]
            grp_locs = [l["name"] for l in db.get_active_locations()
                        if l["group_name"] == grp_name]
            rows = []
            for gl in grp_locs:
                rows.extend(db.get_all_fabrics(search, gl, ftype))
        else:
            rows = db.get_all_fabrics(search, loc, ftype)

        # Mevcut sıralama, seçim ve kaydırma konumunu koru
        hdr = self.table.horizontalHeader()
        sort_col = hdr.sortIndicatorSection()
        sort_ord = hdr.sortIndicatorOrder()
        idx = self.table.selectionModel().currentIndex() if self.table.selectionModel() else None
        sel_id = self._model.id_at(idx.row()) if idx is not None and idx.isValid() else None
        scroll = self.table.verticalScrollBar().value()

        self._model.load(rows)
        if sort_col > 0:
            self._model.sort(sort_col, sort_ord)

        if sel_id is not None:
            for row in range(self._model.rowCount()):
                if self._model.id_at(row) == sel_id:
                    self.table.selectRow(row)
                    break
        self.table.verticalScrollBar().setValue(scroll)

        self._update_totals(rows)

        summary = db.get_summary()
        if hasattr(self.parent(), "update_status"):
            self.parent().update_status(len(rows), summary)

    def _update_totals(self, rows):
        total_mt  = sum(r["meter"] or 0 for r in rows)
        total_kg  = sum(r["kg"] or 0 for r in rows)
        total_val = sum(
            ((r["meter"] or 0) * (r["birim_fiyat"] or 0)) if (r["meter"] or 0) > 0
            else ((r["kg"] or 0) * (r["birim_fiyat"] or 0))
            for r in rows
        )
        self._tot_items.setText(f"{len(rows):,}")
        self._tot_meter.setText(f"{total_mt:,.2f} mt")
        self._tot_kg.setText(f"{total_kg:,.2f} kg")
        self._tot_value.setText(f"{total_val:,.2f} $" if total_val else "—")

        loc = self.location_filter.currentData() or ""
        search = self.search_box.text().strip()
        parts = []
        if loc and not loc.startswith("__"):
            parts.append(f"Lokasyon: {self.location_filter.currentText().strip()}")
        elif loc.startswith("__ALL_"):
            parts.append(f"Lokasyon: {self.location_filter.currentText().strip()}")
        if search:
            parts.append(f'Arama: "{search}"')
        self._filter_lbl.setText("  |  " + "  ·  ".join(parts) if parts else "")

    def _selected_row(self):
        idx = self.table.selectionModel().currentIndex()
        if not idx.isValid():
            QMessageBox.information(self, "Bilgi", "Lütfen bir kayıt seçin.")
            return -1
        return idx.row()

    def _selected_id(self):
        row = self._selected_row()
        if row < 0:
            return None
        fid = self._model.id_at(row)
        if fid is None:
            QMessageBox.information(self, "Bilgi", "Lütfen bir kayıt seçin.")
        return fid

    def _add(self):
        dlg = FabricDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            fid = db.add_fabric(**d, user_name=CURRENT_USER["full_name"])
            self.refresh_with_locations()

    def _edit(self):
        fid = self._selected_id()
        if not fid:
            return
        fabric = db.get_fabric(fid)
        dlg = FabricDialog(self, fabric)
        if dlg.exec():
            d = dlg.get_data()
            db.update_fabric(fid, **d)
            self.refresh()

    def _delete(self):
        fid = self._selected_id()
        if not fid:
            return
        fabric = db.get_fabric(fid)
        reply = QMessageBox.question(
            self, "Stoktan Sil",
            f"<b>{fabric['product_code']}</b> ({fabric['color']}) stoktan silinsin mi?<br><br>"
            f"<span style='color:#555'>Hareket geçmişi korunacak, stok listesinden kaldırılacak.</span>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.soft_delete_fabric(fid, user_name=CURRENT_USER["full_name"])
            self.refresh_with_locations()

    def _giris(self):
        fid = self._selected_id()
        if not fid:
            return
        fabric = db.get_fabric(fid)
        dlg = MovementDialog(self, fabric, "GİRİŞ")
        if dlg.exec():
            d = dlg.get_data()
            db.add_movement(fid, "GİRİŞ", d["meter"], d["kg"], d["piece_count"],
                            d["notes"], user_name=CURRENT_USER["full_name"])
            self.refresh()

    def _cikis(self):
        fid = self._selected_id()
        if not fid:
            return
        fabric = db.get_fabric(fid)
        dlg = MovementDialog(self, fabric, "ÇIKIŞ")
        if dlg.exec():
            d = dlg.get_data()
            notes = d["notes"]
            deduct_m = deduct_k = None
            if d["fire_active"]:
                # Depodan çıkış öncesi miktar düşülür (fire dahil)
                deduct_m, deduct_k = d["pre_meter"] or None, d["pre_kg"] or None
                fire_note = f"Fire: %{d['fire_pct']:.1f}" + (" (elle)" if d["fire_manual"] else "")
                notes = f"{notes} | {fire_note}" if notes else fire_note
            mid = db.add_movement(fid, "ÇIKIŞ", d["meter"], d["kg"], d["piece_count"],
                                  notes, user_name=CURRENT_USER["full_name"],
                                  destination=d.get("destination",""),
                                  destination_type=d.get("destination_type",""),
                                  deduct_meter=deduct_m, deduct_kg=deduct_k,
                                  out_color=d["out_color"], lab_no=d["lab_no"],
                                  parti_no=d["parti_no"])
            if d["fire_active"]:
                db.add_fire_record(
                    fid, mid, fabric["product_code"], fabric["color"] or "",
                    fabric["lot"] or "", fabric["location"] or "", d["destination"],
                    d["pre_meter"], d["pre_kg"], d["meter"], d["kg"], d["fire_pct"],
                    manual_pct=d["fire_manual"], user_name=CURRENT_USER["full_name"],
                    out_color=d["out_color"], lab_no=d["lab_no"], parti_no=d["parti_no"])
                if db.finalize_lot_if_consumed(fid, CURRENT_USER["full_name"]):
                    QMessageBox.information(
                        self, "Lot Tükendi",
                        f"<b>{fabric['product_code']} / {fabric['lot'] or '-'}</b> lotu tükendi.<br>"
                        f"Toplam fire 'Boyahane Fire Oranları' sekmesine işlendi.")
            self.refresh()

    # Çift tıklanabilen sütunlar → veritabanı alanı
    CELL_FIELDS = {1: "product_code", 2: "product_name", 3: "color", 4: "location",
                   5: "fabric_type", 6: "lot", 7: "meter", 8: "kg",
                   9: "piece_count", 10: "birim_fiyat", 13: "entry_location",
                   14: "description"}

    def _cell_edit(self, index):
        if not index.isValid():
            return
        field = self.CELL_FIELDS.get(index.column())
        if not field:   # #, Toplam Değer, Son Güncelleme — düzenlenemez
            return
        fid = self._model.id_at(index.row())
        if not fid:
            return
        fabric = db.get_fabric(fid)
        dlg = CellEditDialog(self, fabric, field, COLS[index.column()])
        if dlg.exec():
            d = {k: dict(fabric).get(k) for k in
                 ("product_name", "product_code", "color", "location", "meter", "kg",
                  "piece_count", "birim_fiyat", "fabric_type", "lot", "description")}
            d[field] = dlg.value()
            db.update_fabric(fid, **d)
            self.refresh_with_locations()

    def _history(self):
        idx = self.table.selectionModel().currentIndex()
        if idx.isValid():
            fid = self._model.id_at(idx.row())
            if fid:
                fabric = db.get_fabric(fid)
                MovementsDialog(self, fabric).exec()
                return
        DailyMovementsDialog(self).exec()

    def _context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        # Çok satır seçiliyse: tıklanan sütunu toplu düzenle
        act_bulk = None
        idx = self.table.indexAt(pos)
        sel_rows = self.table.selectionModel().selectedRows()
        field = self.CELL_FIELDS.get(idx.column()) if idx.isValid() else None
        if field and len(sel_rows) > 1:
            act_bulk = menu.addAction(f"✎ {COLS[idx.column()]} — {len(sel_rows)} satırı toplu düzenle")
            menu.addSeparator()

        act_export = menu.addAction("📥 Excel'e Aktar (görünen liste)")
        act_export_all = menu.addAction("📥 Excel'e Aktar (tüm stok)")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if act_bulk and action == act_bulk:
            self._bulk_cell_edit(idx.column(), field, sel_rows)
        elif action == act_export:
            self._export_visible()
        elif action == act_export_all:
            self._export_all()

    def _bulk_cell_edit(self, col, field, sel_rows):
        fids = [self._model.id_at(r.row()) for r in sel_rows]
        fids = [f for f in fids if f]
        if not fids:
            return
        first = db.get_fabric(fids[0])
        dlg = CellEditDialog(self, first, field, COLS[col], count=len(fids))
        if dlg.exec():
            val = dlg.value()
            keys = ("product_name", "product_code", "color", "location", "meter", "kg",
                    "piece_count", "birim_fiyat", "fabric_type", "lot", "description")
            for fid in fids:
                fabric = db.get_fabric(fid)
                d = {k: dict(fabric).get(k) for k in keys}
                d[field] = val
                db.update_fabric(fid, **d)
            self.refresh_with_locations()

    def _export_visible(self):
        """Tabloda şu an görünen satırları dışa aktar."""
        _export_table_to_excel(self, self._model, self.table)

    def _export_all(self):
        """Filtresiz tüm stoğu dışa aktar."""
        all_rows = db.get_all_fabrics()
        import tempfile
        tmp_model = FabricModel()
        tmp_model.load(all_rows)
        _export_table_to_excel(self, tmp_model, self.table, title="Tüm Stok")


class _FireSortItem(QTableWidgetItem):
    """Sayısal sütunlar için doğru sıralama: UserRole'daki değere göre karşılaştırır."""
    def __lt__(self, other):
        a = self.data(Qt.ItemDataRole.UserRole)
        b = other.data(Qt.ItemDataRole.UserRole)
        if a is not None and b is not None:
            return a < b
        return super().__lt__(other)


class FireView(QWidget):
    """Boyahane fire oranları — dış depodan müşteriye sevklerin fire kayıtları."""
    COLS = ["Tarih", "Boyahane", "Ürün Kodu", "Renk", "Lot", "Lab No", "Parti No", "Hedef",
            "Öncesi mt", "Çıkış mt", "Fire mt", "Fire mt %",
            "Öncesi kg", "Çıkış kg", "Fire kg", "Fire kg %", "Tür"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Ara:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ürün, renk, lot, lab, parti, hedef...")
        self.search_box.setMaximumWidth(260)
        self.search_box.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_box)

        toolbar.addWidget(QLabel("Boyahane:"))
        self.boyahane_filter = QComboBox()
        self.boyahane_filter.addItem("Tümü", "")
        self.boyahane_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.boyahane_filter)

        toolbar.addWidget(QLabel("Tür:"))
        self.type_filter = QComboBox()
        for t in ["Tümü", "ÇIKIŞ", "LOT TOPLAMI"]:
            self.type_filter.addItem(t, "" if t == "Tümü" else t)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.type_filter)

        toolbar.addStretch()
        btn_reset = QPushButton("🔄 Lot Sıfırla")
        btn_reset.setToolTip("Seçili satırın lotunu kapatır: dış depoda kalan stok fire yazılır,\n"
                             "lotun toplam firesi ayrı satır olarak eklenir.")
        btn_reset.clicked.connect(self._reset_lot)
        btn_refresh = QPushButton("⟳ Yenile")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_reset)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        info = QLabel("Dış depolardan yapılan çıkışların fire kayıtları. "
                      "<i>(elle)</i> işaretli oranlar elle girilmiştir; "
                      "<b>LOT TOPLAMI</b> satırları kapanan lotların toplam firesidir.")
        info.setStyleSheet("color:#555; font-size:11px;")
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)   # elle genişlik ayarı
        hdr.setStretchLastSection(True)
        self._cols_sized = False   # ilk veri yüklemesinde bir kez otomatik boyutlandır
        layout.addWidget(self.table)

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#555; font-size:12px;")
        layout.addWidget(self.count_lbl)

    def refresh(self):
        all_rows = [dict(r) for r in db.get_fire_records()]

        # Boyahane filtresini doldur (seçim korunur)
        cur_b = self.boyahane_filter.currentData() or ""
        names = sorted({r["boyahane"] for r in all_rows if r["boyahane"]})
        self.boyahane_filter.blockSignals(True)
        self.boyahane_filter.clear()
        self.boyahane_filter.addItem("Tümü", "")
        for n in names:
            self.boyahane_filter.addItem(n, n)
        idx = self.boyahane_filter.findData(cur_b)
        if idx >= 0:
            self.boyahane_filter.setCurrentIndex(idx)
        self.boyahane_filter.blockSignals(False)

        # Filtrele
        q = self.search_box.text().strip().lower()
        b = self.boyahane_filter.currentData() or ""
        t = self.type_filter.currentData() or ""
        rows = []
        for r in all_rows:
            if b and r["boyahane"] != b:
                continue
            if t and r["record_type"] != t:
                continue
            if q:
                hay = " ".join(str(r.get(k) or "") for k in
                               ("boyahane", "product_code", "color", "out_color",
                                "lot", "lab_no", "parti_no", "customer")).lower()
                if q not in hay:
                    continue
            rows.append(r)

        self._rows = rows
        self.table.setSortingEnabled(False)   # doldururken sıralamayı kapat
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            is_total = r["record_type"] == "LOT TOPLAMI"
            elle = " (elle)" if r["manual_pct"] else ""
            pre_m, out_m = r["pre_meter"] or 0, r["out_meter"] or 0
            pre_k, out_k = r["pre_kg"] or 0, r["out_kg"] or 0
            fire_m, fire_k = max(0, pre_m - out_m), max(0, pre_k - out_k)
            pct_m = (fire_m / pre_m * 100) if pre_m > 0 else 0
            pct_k = (fire_k / pre_k * 100) if pre_k > 0 else 0
            vals = [
                str(r["created_at"] or "")[:16],
                r["boyahane"] or "",
                r["product_code"] or "",
                r.get("out_color") or r["color"] or "",
                r["lot"] or "",
                r.get("lab_no") or "",
                r.get("parti_no") or "",
                r["customer"] or "",
                f"{pre_m:,.2f}" if pre_m else "",
                f"{out_m:,.2f}" if out_m else "",
                f"{fire_m:,.2f}" if pre_m else "",
                f"%{pct_m:.1f}{elle}" if pre_m else "",
                f"{pre_k:,.2f}" if pre_k else "",
                f"{out_k:,.2f}" if out_k else "",
                f"{fire_k:,.2f}" if pre_k else "",
                f"%{pct_k:.1f}{elle}" if pre_k else "",
                r["record_type"],
            ]
            sort_keys = {8: pre_m, 9: out_m, 10: fire_m, 11: pct_m,
                         12: pre_k, 13: out_k, 14: fire_k, 15: pct_k}
            for j, v in enumerate(vals):
                item = _FireSortItem(v)
                if j in sort_keys:
                    item.setData(Qt.ItemDataRole.UserRole, sort_keys[j])
                if j == 0:   # sıralamadan bağımsız kayıt eşlemesi için id sakla
                    item.setData(Qt.ItemDataRole.UserRole + 1, r["id"])
                if 8 <= j <= 15:
                    item.setTextAlignment(int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight))
                if j in (10, 11, 14, 15):   # fire sütunları — kırmızı, elle girilenler turuncu
                    item.setForeground(QBrush(QColor("#E65100" if r["manual_pct"] else "#C62828")))
                    f = QFont(); f.setBold(True); item.setFont(f)
                if is_total:
                    f = QFont(); f.setBold(True); item.setFont(f)
                    item.setBackground(QBrush(QColor("#FFF8E1")))
                self.table.setItem(i, j, item)
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar, mevcut sıralamayı uygular
        if rows and not self._cols_sized:
            self.table.resizeColumnsToContents()   # ilk yüklemede makul genişlikler
            self._cols_sized = True
        self.count_lbl.setText(f"{len(rows)} kayıt" + (f" / toplam {len(all_rows)}" if len(rows) != len(all_rows) else ""))

    def _reset_lot(self):
        row = self.table.currentRow()
        item0 = self.table.item(row, 0) if row >= 0 else None
        rid = item0.data(Qt.ItemDataRole.UserRole + 1) if item0 else None
        r = next((x for x in self._rows if x["id"] == rid), None)
        if r is None:
            QMessageBox.information(self, "Bilgi", "Önce tablodan sıfırlanacak lota ait bir satır seçin.")
            return
        if r["record_type"] == "LOT TOPLAMI":
            QMessageBox.information(self, "Bilgi", "Bu lot zaten kapatılmış (LOT TOPLAMI satırı).")
            return
        if db.lot_total_exists(r["product_code"], r["color"], r["lot"], r["boyahane"]):
            QMessageBox.warning(self, "Lot Sıfırlama",
                                f"<b>{r['product_code']} / {r['lot'] or '-'}</b> — {r['boyahane']}<br><br>"
                                f"Bu lot daha önce sıfırlanmıştır.")
            return
        fabric = db.get_fabric(r["fabric_id"]) if r["fabric_id"] else None
        if not fabric:
            QMessageBox.warning(self, "Hata", "Lota ait stok kaydı bulunamadı.")
            return
        rem_m, rem_k = fabric["meter"] or 0, fabric["kg"] or 0
        reply = QMessageBox.question(
            self, "Lot Sıfırlama",
            f"<b>{r['product_code']} / {r['lot'] or '-'}</b> — {r['boyahane']}<br><br>"
            f"Kalan stok: <b>{rem_m:,.2f} mt / {rem_k:,.2f} kg</b><br><br>"
            f"Lot kapatılsın mı? Kalan stok <span style='color:#C62828'>fire olarak yazılacak</span> "
            f"ve toplam fire ayrı satır olarak eklenecek.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        db.reset_lot_fire(r["fabric_id"], CURRENT_USER["full_name"])
        self.refresh()
        QMessageBox.information(self, "Tamamlandı",
                                "Lot kapatıldı, toplam fire satırı eklendi.")


class LocationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: location list
        left = QGroupBox("Lokasyonlar")
        left_layout = QVBoxLayout(left)
        self.loc_list = QListWidget()
        self.loc_list.currentItemChanged.connect(self._on_loc_change)
        left_layout.addWidget(self.loc_list)
        left.setMaximumWidth(180)
        splitter.addWidget(left)

        # Right: fabric table
        right = QGroupBox("Kumaşlar")
        right_layout = QVBoxLayout(right)
        self.table = QTableWidget()
        cols = ["Ürün Kodu", "Ürün Bilgisi", "Renk", "Metre", "Kilo", "Top/Adet", "Açıklama"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setMouseTracking(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.setMinimumSectionSize(50)
        hdr.setSectionsMovable(True)
        for i, w in enumerate([100, 130, 100, 75, 65, 80, 250]):
            self.table.setColumnWidth(i, w)
        right_layout.addWidget(self.table)

        # Alt toplam barı
        self._loc_bar = QFrame()
        self._loc_bar.setStyleSheet(
            "QFrame { background:#545454; border-radius:6px;"
            "border: 2px solid #3A3A3A; padding:0; }"
        )
        self._loc_bar.setFixedHeight(56)
        loc_bar_layout = QHBoxLayout(self._loc_bar)
        loc_bar_layout.setContentsMargins(20, 4, 20, 4)
        loc_bar_layout.setSpacing(0)

        def _lstat(label):
            w = QWidget(); w.setStyleSheet("background:transparent;")
            wl = QVBoxLayout(w); wl.setSpacing(2); wl.setContentsMargins(16,2,16,2)
            lbl = QLabel(label)
            lbl.setStyleSheet("color:rgba(255,255,255,.7); font-size:10px; background:transparent;")
            val = QLabel("—")
            val.setStyleSheet("color:white; font-size:15px; font-weight:bold; background:transparent;")
            wl.addWidget(lbl); wl.addWidget(val)
            return w, val

        def _lsep():
            f = QFrame(); f.setFrameShape(QFrame.Shape.VLine); f.setFixedWidth(1)
            f.setStyleSheet("background:rgba(255,255,255,.3); margin:8px 4px;")
            return f

        bw1, self._lbl_loc   = _lstat("Lokasyon")
        bw2, self._lbl_items = _lstat("Kalem Sayısı")
        bw3, self._lbl_meter = _lstat("Toplam Metre")
        bw4, self._lbl_kg    = _lstat("Toplam Kilo")
        bw5, self._lbl_val   = _lstat("Toplam Değer")

        for w in (bw1, _lsep(), bw2, _lsep(), bw3, _lsep(), bw4, _lsep(), bw5):
            loc_bar_layout.addWidget(w)
        loc_bar_layout.addStretch()

        right_layout.addWidget(self._loc_bar)
        splitter.addWidget(right)
        splitter.setSizes([160, 640])
        layout.addWidget(splitter)

    def refresh(self):
        current = self.loc_list.currentItem()
        current_data = current.data(Qt.ItemDataRole.UserRole) if current else None

        # Listeyi sadece lokasyon sayısı değişmişse yeniden oluştur
        new_locs = db.get_active_locations()
        new_sig  = tuple(l["name"] for l in new_locs)
        if hasattr(self, "_loc_sig") and self._loc_sig == new_sig and self.loc_list.count() > 0:
            return   # değişmemiş, listeyi yeniden çizme
        self._loc_sig = new_sig

        self.loc_list.clear()

        all_locs = db.get_active_locations()
        from collections import defaultdict
        groups = defaultdict(list)
        for l in all_locs:
            groups[l["group_name"]].append(l["name"])

        for grp in sorted(groups.keys()):
            if grp == "DEPO":
                # DEPO → tek tıklanabilir satır, tüm rafları getirir
                item = QListWidgetItem("DEPO")
                item.setData(Qt.ItemDataRole.UserRole, "__GRP_DEPO__")
                self.loc_list.addItem(item)
            else:
                # Diğer grup → başlık yok, lokasyonlar kendi isimleriyle
                for name in sorted(groups[grp]):
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, name)
                    self.loc_list.addItem(item)

        # Önceki seçimi koru
        if current_data:
            for i in range(self.loc_list.count()):
                it = self.loc_list.item(i)
                if it.data(Qt.ItemDataRole.UserRole) == current_data:
                    self.loc_list.setCurrentItem(it)
                    break

    def _on_loc_change(self, item):
        if not item:
            return
        loc_data = item.data(Qt.ItemDataRole.UserRole)
        if not loc_data:
            return

        if loc_data == "__GRP_DEPO__":
            rows = db.get_all_fabrics()   # tek sorgu — tümünü çek, sonra filtrele
            depo_locs = {l["name"] for l in db.get_active_locations()
                         if l["group_name"] == "DEPO"}
            rows = [r for r in rows if (r["location"] or "") in depo_locs]
            label = "DEPO"
        else:
            rows = db.get_all_fabrics(location=loc_data)
            label = loc_data

        R_ALIGN = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        total_m = total_kg = total_val = 0.0

        self.table.setSortingEnabled(False)   # veri yüklenirken sıralamayı kapat
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            mt  = r["meter"] or 0
            kg  = r["kg"] or 0
            fiy = r["birim_fiyat"] or 0
            val = mt * fiy if mt > 0 else kg * fiy
            vals = [r["product_code"] or "", r["product_name"] or "", r["color"] or "",
                    f"{mt:,.2f}", f"{kg:,.2f}", r["piece_count"] or "", r["description"] or ""]
            for j, v in enumerate(vals):
                cell = QTableWidgetItem(v)
                cell.setToolTip(v)
                if j in (3, 4):
                    cell.setTextAlignment(R_ALIGN)
                self.table.setItem(i, j, cell)
            total_m += mt; total_kg += kg; total_val += val
        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)   # veri yüklendi, sıralamayı aç

        self._lbl_loc.setText(label)
        self._lbl_items.setText(f"{len(rows):,}")
        self._lbl_meter.setText(f"{total_m:,.2f} mt")
        self._lbl_kg.setText(f"{total_kg:,.2f} kg")
        self._lbl_val.setText(f"{total_val:,.0f} $" if total_val else "—")

    def _context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        cur = self.loc_list.currentItem()
        label = cur.text().strip() if cur else "Lokasyon"
        menu = QMenu(self)
        act = menu.addAction(f"📥 Excel'e Aktar ({label})")
        if menu.exec(self.table.viewport().mapToGlobal(pos)) == act:
            _export_widget_table_to_excel(self, self.table, title=label)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.setSpacing(16)
        header_row.setContentsMargins(12, 8, 12, 8)

        # Logo — yüksek çözünürlük, sola yasla
        logo_label = QLabel()
        if _os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH)
            logo_label.setPixmap(
                pix.scaledToHeight(100, Qt.TransformationMode.SmoothTransformation)
            )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # Başlık
        title = QLabel("DEPO TAKİP SİSTEMİ")
        title.setStyleSheet("font-size:20px; font-weight:bold; color:#545454; letter-spacing:1px;")
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        header_row.addWidget(logo_label)
        header_row.addWidget(title)
        header_row.addStretch()

        btn_users = QPushButton("👤 Kullanıcı Yönetimi")
        btn_users.setStyleSheet(
            "background:#37474F; color:white; font-weight:bold; border-radius:4px; padding:8px 16px;"
        )
        btn_users.clicked.connect(self._open_user_mgmt)
        header_row.addWidget(btn_users)

        header_frame = QFrame()
        header_frame.setLayout(header_row)
        header_frame.setStyleSheet("background:white; border-radius:6px;")
        header_frame.setFixedHeight(116)
        layout.addWidget(header_frame)

        def _make_card(icon, label, color, small=False):
            box = QGroupBox()
            bl  = QVBoxLayout(box); bl.setSpacing(2)
            li  = QLabel(icon); li.setAlignment(Qt.AlignmentFlag.AlignCenter)
            li.setStyleSheet("font-size:18px;")
            val = QLabel("—"); val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fs  = "14px" if small else "18px"
            val.setStyleSheet(f"color:{color}; font-size:{fs}; font-weight:bold;")
            lbl = QLabel(label); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color:#757575; font-size:10px;")
            bl.addWidget(li); bl.addWidget(val); bl.addWidget(lbl)
            box.setMinimumHeight(90)
            return box, val

        # Satır 1 — Genel özet
        self.stat_items = QLabel("0")
        self.stat_meter = QLabel("0 mt")
        self.stat_kg    = QLabel("0 kg")
        self.stat_value = QLabel("0 $")
        row1 = QHBoxLayout()
        for icon, lbl, color, wgt in [
            ("📦","Toplam Kalem","#545454", self.stat_items),
            ("📏","Toplam Metre","#2E7D32", self.stat_meter),
            ("⚖️","Toplam Kilo","#6A1B9A",  self.stat_kg),
            ("💰","Stok Değeri","#B71C1C",   self.stat_value),
        ]:
            box, val = _make_card(icon, lbl, color)
            val.setText = wgt.setText  # yönlendir — kullanmayacağız, ayrı set edeceğiz
            # Ortak widget referansı için kutuya ekleyelim
            # val zaten dışarıda tanımlı, sadece stili ata
            val.setStyleSheet(f"color:{color}; font-size:18px; font-weight:bold;")
            # Box içindeki ikinci widget val — bunu değiştir
            box.layout().itemAt(1).widget().deleteLater()
            box.layout().insertWidget(1, wgt)
            wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wgt.setStyleSheet(f"color:{color}; font-size:18px; font-weight:bold;")
            row1.addWidget(box)
        layout.addLayout(row1)

        # Satır 2 — Tip dağılımı
        self.stat_ham    = QLabel("—")
        self.stat_pfd    = QLabel("—")
        self.stat_boyali = QLabel("—")
        self.stat_baskili= QLabel("—")
        row2 = QHBoxLayout()
        for icon, lbl, color, wgt in [
            ("🟫","HAM (Metre)","#5D4037",   self.stat_ham),
            ("🟩","PFD (Metre)","#00695C",   self.stat_pfd),
            ("🟦","BOYALI (Metre)","#1565C0", self.stat_boyali),
            ("🟪","BASKILI (Metre)","#6A1B9A",self.stat_baskili),
        ]:
            box2 = QGroupBox(); bl2 = QVBoxLayout(box2); bl2.setSpacing(2)
            li2  = QLabel(icon); li2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            li2.setStyleSheet("font-size:16px;")
            wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wgt.setStyleSheet(f"color:{color}; font-size:16px; font-weight:bold;")
            lbl2 = QLabel(lbl); lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl2.setStyleSheet("color:#757575; font-size:10px;")
            bl2.addWidget(li2); bl2.addWidget(wgt); bl2.addWidget(lbl2)
            box2.setMinimumHeight(80)
            row2.addWidget(box2)
        layout.addLayout(row2)

        # Location summary table
        loc_group = QGroupBox("Depo / Lokasyon Özeti")
        loc_layout = QVBoxLayout(loc_group)
        self.loc_table = QTableWidget()
        self.loc_table.setColumnCount(5)
        self.loc_table.setHorizontalHeaderLabels(["Depo / Lokasyon", "Kalem", "Toplam Metre", "Toplam Kilo", "Toplam Değer $"])
        self.loc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.loc_table.verticalHeader().setVisible(False)
        hdr = self.loc_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        loc_layout.addWidget(self.loc_table)
        layout.addWidget(loc_group)

    def _open_user_mgmt(self):
        if CURRENT_USER.get("role") != "admin":
            QMessageBox.warning(self, "Yetki", "Bu işlem için yönetici yetkisi gereklidir.")
            return
        UserManagementDialog(self).exec()

    DEPO_LOCS = {"DEPO", "M11", "M7", "OFİS", "OFIS"}

    @classmethod
    def _loc_group(cls, loc):
        import re
        u = loc.strip().upper()
        if u in cls.DEPO_LOCS or re.match(r"^(RAF|PALET|P\d|H\d|HP|H-P)", u):
            return "DEPO"
        return u

    def refresh(self):
        import re
        summary = db.get_summary()
        self.stat_items.setText(str(summary["total_items"] or 0))
        self.stat_meter.setText(f"{summary['total_meter'] or 0:,.0f} mt")
        self.stat_kg.setText(f"{summary['total_kg'] or 0:,.0f} kg")
        val = summary["total_value"] or 0
        priced = summary["priced_items"] or 0
        total  = summary["total_items"] or 1
        self.stat_value.setText(f"{val:,.0f} $")
        if priced < total:
            self.stat_value.setToolTip(f"Not: {total - priced} kalemin fiyatı girilmemiş")

        # ── Kumaş Tipi Özet Kartları ─────────────────────────────
        all_rows = db.get_all_fabrics()
        tip_mt = {"HAM": 0.0, "PFD": 0.0, "BOYALI": 0.0, "BASKILI": 0.0}
        for r in all_rows:
            t = r["fabric_type"] or ""
            if t in tip_mt:
                tip_mt[t] += r["meter"] or 0
        self.stat_ham.setText(f"{tip_mt['HAM']:,.0f} mt")
        self.stat_pfd.setText(f"{tip_mt['PFD']:,.0f} mt")
        self.stat_boyali.setText(f"{tip_mt['BOYALI']:,.0f} mt")
        self.stat_baskili.setText(f"{tip_mt['BASKILI']:,.0f} mt")

        locs = db.get_locations()

        # Build grouped data: {group: {loc: (count, meter, kg)}}
        from collections import defaultdict
        groups = defaultdict(dict)
        for loc in locs:
            rows = db.get_all_fabrics(location=loc)
            total_m   = sum(r["meter"] or 0 for r in rows)
            total_kg  = sum(r["kg"] or 0 for r in rows)
            total_val = sum(
                ((r["meter"] or 0) * (r["birim_fiyat"] or 0)) if (r["meter"] or 0) > 0
                else ((r["kg"] or 0) * (r["birim_fiyat"] or 0))
                for r in rows
            )
            group = self._loc_group(loc)
            groups[group][loc] = (len(rows), total_m, total_kg, total_val)

        table_rows = []
        for group in sorted(groups.keys()):
            locs_in_group = groups[group]
            g_count = sum(v[0] for v in locs_in_group.values())
            g_meter = sum(v[1] for v in locs_in_group.values())
            g_kg    = sum(v[2] for v in locs_in_group.values())
            g_val   = sum(v[3] for v in locs_in_group.values())
            table_rows.append((group, g_count, g_meter, g_kg, g_val))

        self.loc_table.setRowCount(len(table_rows))

        for i, (group, count, meter, kg, val) in enumerate(table_rows):
            bg = QColor("#545454") if group == "DEPO" else QColor("#545454")
            fg = QColor("#FFFFFF")
            val_str = f"{val:,.0f} $" if val else "—"
            vals = [group, str(count), f"{meter:,.2f} mt", f"{kg:,.2f} kg", val_str]

            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setBackground(QBrush(bg))
                item.setForeground(QBrush(fg))
                item.setFont(QFont("", -1, QFont.Weight.Bold))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |
                    (Qt.AlignmentFlag.AlignRight if j >= 1 else Qt.AlignmentFlag.AlignLeft))
                self.loc_table.setItem(i, j, item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bursa Knitted Depo Takip Sistemi")
        self.setMinimumSize(1100, 700)
        if _os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.dashboard = DashboardWidget()
        self.stock_table = StockTable(self)
        self.location_view = LocationView()
        self.fire_view = FireView()

        # Dashboard sadece admin'e göster
        if CURRENT_USER.get("role") == "admin":
            self.tabs.addTab(self.dashboard, "📊 Dashboard")
        self.tabs.addTab(self.stock_table, "📦 Stok Listesi")
        self.tabs.addTab(self.location_view, "🗂 Lokasyon Görünümü")
        self.tabs.addTab(self.fire_view, "🔥 Boyahane Fire Oranları")
        self.tabs.currentChanged.connect(self._on_tab_change)
        layout.addWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._user_label = QLabel()
        self._user_label.setStyleSheet("color:#212121; font-weight:bold; font-size:12px; padding:0 12px;")
        self.status.addPermanentWidget(self._user_label)
        self._update_user_label()

        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Dosya")
        file_menu.addAction("Excel'den İçe Aktar...").triggered.connect(self._import)
        file_menu.addAction("Excel'e Dışa Aktar...").triggered.connect(self._export)
        file_menu.addSeparator()
        file_menu.addAction("Çıkış").triggered.connect(self.close)

        sys_menu = menubar.addMenu("🛡 Sistem")
        sys_menu.addAction("Yedek Durumu ve Yönetimi...").triggered.connect(self._backup_dialog)
        sys_menu.addAction("Şimdi Yedek Al").triggered.connect(self._backup_now)

        cust_menu = menubar.addMenu("👥 Müşteriler")
        cust_menu.addAction("Müşteri Listesi...").triggered.connect(
            lambda: CustomerManagementDialog(self).exec())

        loc_menu = menubar.addMenu("🗄 Lokasyonlar")
        loc_menu.addAction("Raf / Lokasyon Tanımlamaları...").triggered.connect(
            lambda: LocationManagementDialog(self).exec())

        user_menu = menubar.addMenu("👤 Kullanıcılar")
        user_menu.addAction("Kullanıcı Yönetimi").triggered.connect(self._user_mgmt)
        user_menu.addSeparator()
        user_menu.addAction("Oturumu Kapat").triggered.connect(self._logout)

        mail_menu = menubar.addMenu("📧 E-posta Rapor")
        mail_menu.addAction("Ayarlar ve Zamanlama...").triggered.connect(
            lambda: EmailSettingsDialog(self).exec())
        mail_menu.addAction("Şimdi Rapor Gönder").triggered.connect(self._send_now)

        web_menu = menubar.addMenu("📱 Mobil Erişim")
        self._web_action = web_menu.addAction("WiFi Sunucusunu Başlat (yerel)")
        self._web_action.triggered.connect(self._toggle_web)
        web_menu.addSeparator()
        self._ngrok_action = web_menu.addAction("İnternetten Erişim Aç (ngrok)")
        self._ngrok_action.triggered.connect(self._toggle_ngrok)
        web_menu.addSeparator()
        web_menu.addAction("ngrok Token Ayarla...").triggered.connect(self._set_ngrok_token)

        self._web_label = QLabel("  📱 Mobil: Kapalı  ")
        self._web_label.setStyleSheet("color:#212121; font-size:12px; padding:0 10px;")
        self.status.addPermanentWidget(self._web_label)

        self._backup_lbl = QLabel("  🛡 Yedek: —  ")
        self._backup_lbl.setStyleSheet("color:#212121; font-size:12px; padding:0 10px;")
        self._backup_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self._backup_lbl.mousePressEvent = lambda e: self._backup_dialog()
        self.status.addPermanentWidget(self._backup_lbl)
        QTimer.singleShot(2000, self._refresh_backup_indicator)

    def _update_user_label(self):
        role_icon = "👑" if CURRENT_USER.get("role") == "admin" else "👤"
        self._user_label.setText(f"{role_icon} {CURRENT_USER.get('full_name', '')}")

    def _user_mgmt(self):
        if CURRENT_USER.get("role") != "admin":
            QMessageBox.warning(self, "Yetki", "Bu işlem için yönetici yetkisi gereklidir.")
            return
        UserManagementDialog(self).exec()

    def _logout(self):
        reply = QMessageBox.question(self, "Çıkış", "Oturumu kapatıp yeniden giriş yapılsın mı?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            dlg = LoginDialog(self)
            dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
            if dlg.exec():
                self._update_user_label()
                self._rebuild_tabs()
            else:
                self.close()

    def _rebuild_tabs(self):
        """Oturum değişince tabları role göre yeniden oluştur."""
        while self.tabs.count():
            self.tabs.removeTab(0)
        if CURRENT_USER.get("role") == "admin":
            self.tabs.addTab(self.dashboard, "📊 Dashboard")
        self.tabs.addTab(self.stock_table, "📦 Stok Listesi")
        self.tabs.addTab(self.location_view, "🗂 Lokasyon Görünümü")
        self.tabs.addTab(self.fire_view, "🔥 Boyahane Fire Oranları")
        self.stock_table.refresh_with_locations()

    def _toggle_web(self):
        import web_server as ws
        if ws.is_running():
            ws.stop()
            self._web_action.setText("Mobil Sunucuyu Başlat")
            self._web_label.setText("  📱 Kapalı  ")
            self._web_label.setStyleSheet("color:#212121; font-size:12px; padding:0 8px;")
        else:
            ip, port = ws.start()
            self._web_action.setText("Mobil Sunucuyu Durdur")
            self._web_label.setText(f"  📱 {ip}:{port}  ")
            self._web_label.setStyleSheet("color:#2E7D32; font-weight:bold; font-size:12px; padding:0 8px;")
            # Bilgi dialogu
            dlg = _MobileAccessDialog(self, ip, port)
            dlg.exec()

    def _toggle_ngrok(self):
        import web_server as ws
        if ws.ngrok_running():
            ws.stop_ngrok()
            self._ngrok_action.setText("İnternetten Erişim Aç (ngrok)")
            self._web_label.setText(
                f"  📱 {ws.get_local_ip()}:{ws.PORT}  " if ws.is_running() else "  📱 Kapalı  "
            )
        else:
            # Token kontrolü
            token = ws.get_ngrok_token()
            if not token:
                dlg = _NgrokSetupDialog(self)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                token = dlg.token
                ws.set_ngrok_token(token)

            # Loading mesajı
            self.status.showMessage("  ngrok bağlantısı kuruluyor...")
            QApplication.processEvents()
            try:
                url = ws.start_ngrok()
                self._ngrok_action.setText("İnternetten Erişimi Kapat")
                self._web_label.setText(f"  🌍 İnternette Açık  ")
                self._web_label.setStyleSheet("color:#FFD54F; font-weight:bold; font-size:12px; padding:0 8px;")
                dlg = _NgrokActiveDialog(self, url)
                dlg.exec()
            except Exception as e:
                QMessageBox.critical(self, "ngrok Hatası",
                    f"Bağlantı kurulamadı:\n{e}\n\nToken'ı kontrol edin: Menü → Mobil Erişim → ngrok Token Ayarla")

    def _send_now(self):
        import email_report as er
        try:
            self.status.showMessage("  Rapor gönderiliyor...")
            QApplication.processEvents()
            n = er.send_report(test=True)
            self.status.showMessage(f"  ✓ Rapor {n} alıcıya gönderildi.")
        except Exception as e:
            QMessageBox.critical(self, "Gönderilemedi",
                f"{e}\n\nMenü → 📧 E-posta Rapor → Ayarlar'dan yapılandırın.")

    def _backup_now(self):
        import backup as bk
        self.status.showMessage("  Yedek alınıyor...")
        QApplication.processEvents()
        ok, msg = bk.take_backup(force=True)
        if ok:
            self.status.showMessage(f"  ✓ {msg}")
            self._refresh_backup_indicator()
        else:
            QMessageBox.critical(self, "Yedekleme Hatası", msg)

    def _backup_dialog(self):
        import backup as bk, glob, os
        s = bk.get_backup_status()
        dlg = QDialog(self)
        dlg.setWindowTitle("Yedek Yönetimi")
        dlg.setMinimumSize(580, 420)
        lay = QVBoxLayout(dlg)

        status_color = "#2E7D32" if s["is_today"] else "#C62828"
        status_text  = "✅ Bugün alındı" if s["is_today"] else "⚠️ Bugün alınmadı!"
        info = QLabel(
            f"<b>Yedek Durumu:</b> <span style='color:{status_color}'>{status_text}</span><br>"
            f"Son yedek: <b>{s['last_backup'] or 'Hiç alınmamış'}</b><br>"
            f"Kayıtlı yedek sayısı: <b>{s['backup_count']}</b>  |  "
            f"Toplam boyut: <b>{s['backup_size_mb']} MB</b><br>"
            f"Klasör: <span style='color:#555;font-size:11px'>{s['backup_dir']}</span>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("background:#F5F5F5; padding:12px; border-radius:6px;")
        lay.addWidget(info)

        # Yedek listesi
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Dosya Adı", "Tarih", "Boyut"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        files = sorted(glob.glob(os.path.join(s["backup_dir"], "stok_*.db")), reverse=True)
        table.setRowCount(len(files))
        for i, f in enumerate(files):
            name = os.path.basename(f)
            size = f"{os.path.getsize(f)/1024/1024:.1f} MB"
            mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%d.%m.%Y %H:%M")
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(mtime))
            table.setItem(i, 2, QTableWidgetItem(size))
        lay.addWidget(table)

        btn_row = QHBoxLayout()
        btn_now = QPushButton("🗂 Şimdi Yedek Al")
        btn_now.setStyleSheet("background:#2E7D32; color:white; font-weight:bold; border-radius:4px; padding:7px 14px;")

        btn_restore = QPushButton("↩ Seçili Yedeği Geri Yükle")
        btn_restore.setStyleSheet("background:#C62828; color:white; font-weight:bold; border-radius:4px; padding:7px 14px;")

        btn_close = QPushButton("Kapat")

        def _now():
            ok, msg = bk.take_backup(force=True)
            if ok:
                dlg.accept()
                self._backup_now()
            else:
                QMessageBox.critical(dlg, "Hata", msg)

        def _restore():
            row = table.currentRow()
            if row < 0:
                return QMessageBox.information(dlg, "Bilgi", "Geri yüklenecek yedeği seçin.")
            f = files[row]
            reply = QMessageBox.question(dlg, "Geri Yükle",
                f"<b>{os.path.basename(f)}</b> yedeğine dönülsün mü?<br><br>"
                f"<span style='color:#C62828'>Mevcut tüm veriler bu yedekle değiştirilir!</span>",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    safe = bk.restore_backup(f)
                    QMessageBox.information(dlg, "Başarılı",
                        f"Yedek geri yüklendi.\nEski veriler şuraya kaydedildi:\n{os.path.basename(safe)}\n\nProgram yeniden başlatılıyor...")
                    dlg.accept()
                    import subprocess, sys
                    subprocess.Popen([sys.executable] + sys.argv)
                    QApplication.quit()
                except Exception as e:
                    QMessageBox.critical(dlg, "Hata", str(e))

        btn_now.clicked.connect(_now)
        btn_restore.clicked.connect(_restore)
        btn_close.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_now); btn_row.addWidget(btn_restore)
        btn_row.addStretch(); btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)
        dlg.exec()

    def _refresh_backup_indicator(self):
        import backup as bk
        s = bk.get_backup_status()
        if hasattr(self, "_backup_lbl"):
            if s["is_today"]:
                self._backup_lbl.setText(f"  🛡 Yedek: {s['last_backup']}  ")
                self._backup_lbl.setStyleSheet("color:#2E7D32; font-size:12px; padding:0 10px;")
            else:
                self._backup_lbl.setText("  ⚠️ Yedek alınmadı  ")
                self._backup_lbl.setStyleSheet("color:#E65100; font-size:11px; font-weight:bold; padding:0 6px;")

    def _set_ngrok_token(self):
        import web_server as ws
        current = ws.get_ngrok_token()
        dlg = _NgrokSetupDialog(self, current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ws.set_ngrok_token(dlg.token)
            QMessageBox.information(self, "Kaydedildi", "ngrok token kaydedildi.\nArtık 'İnternetten Erişim Aç' butonunu kullanabilirsiniz.")

    def _check_updates(self):
        """Arka planda güncelleme kontrolü — program açılınca çağrılır."""
        import updater
        def _on_result(var_mi, mesaj):
            if var_mi:
                # Ana thread'de bildirim göster
                QTimer.singleShot(0, lambda: self._show_update_notice(mesaj))
        updater.check_in_background(_on_result)

    def _show_update_notice(self, mesaj):
        reply = QMessageBox.question(self, "🔄 Güncelleme Mevcut",
            f"{mesaj}\n\nŞimdi güncellensin mi?\n(Program yeniden başlayacak)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            import updater
            ok, msg = updater.apply_update()
            if ok:
                QMessageBox.information(self, "Güncellendi", msg)
                updater.restart()
            else:
                QMessageBox.critical(self, "Güncelleme Hatası", msg)

    def _on_tab_change(self, idx):
        w = self.tabs.widget(idx)
        if w is not None and hasattr(w, "refresh"):
            w.refresh()

    def update_status(self, count, summary):
        if not hasattr(self, "status"):
            return
        self.status.showMessage(
            f"  {count} kayıt gösteriliyor  |  Toplam: {summary['total_items'] or 0} kalem  |  "
            f"{summary['total_meter'] or 0:.2f} mt  |  {summary['total_kg'] or 0:.2f} kg"
        )

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Excel Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls)"
        )
        if not path:
            return

        reply = QMessageBox.question(
            self, "İçe Aktarma",
            "Hangi sayfaları içe aktarmak istersiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )

        from importer import import_from_excel, import_from_main_sheet
        try:
            if reply == QMessageBox.StandardButton.Yes:
                records = import_from_main_sheet(path)
                source = "STOK RAPORU sayfası"
            elif reply == QMessageBox.StandardButton.No:
                records = import_from_excel(path)
                source = "Raf/Lokasyon sayfaları"
            else:
                return

            if not records:
                QMessageBox.warning(self, "Uyarı", "Hiç kayıt bulunamadı!")
                return

            confirm = QMessageBox.question(
                self, "Onay",
                f"{source}'ndan <b>{len(records)}</b> kayıt bulundu.\nİçe aktarılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                db.import_fabrics_bulk(records)
                self.stock_table.refresh()
                self.location_view.refresh()
                self.dashboard.refresh()
                QMessageBox.information(self, "Başarılı", f"{len(records)} kayıt içe aktarıldı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İçe aktarma hatası:\n{e}")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Dışa Aktar", "stok_raporu.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "STOK RAPORU"

            # Header
            headers = ["#", "Ürün Kodu", "Ürün Bilgisi", "Renk", "Lokasyon", "Metre", "Kilo", "Top/Adet", "Açıklama", "Son Güncelleme"]
            ws.append(headers)
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", start_color="1565C0")
                cell.alignment = Alignment(horizontal="center")

            rows = db.get_all_fabrics()
            for i, r in enumerate(rows, 1):
                ws.append([
                    i,
                    r["product_code"] or "",
                    r["product_name"] or "",
                    r["color"] or "",
                    r["location"] or "",
                    r["meter"] or 0,
                    r["kg"] or 0,
                    r["piece_count"] or "",
                    r["description"] or "",
                    str(r["updated_at"] or "")[:16],
                ])

            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

            wb.save(path)
            QMessageBox.information(self, "Başarılı", f"Dışa aktarıldı:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma hatası:\n{e}")


def main():
    db.init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Bursa Knitted Depo Takip Sistemi")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Giriş ekranı
    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # Günlük yedek al (arka planda)
    import threading, backup as bk
    def _do_backup():
        ok, msg = bk.take_backup()
        print(f"[Yedek] {msg}")
    threading.Thread(target=_do_backup, daemon=True).start()

    # Günlük mail zamanlayıcısını başlat
    import email_report as er
    er.start_scheduler()

    window = MainWindow()
    window.show()
    # 3 saniye sonra arka planda güncelleme kontrol et
    QTimer.singleShot(3000, window._check_updates)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
