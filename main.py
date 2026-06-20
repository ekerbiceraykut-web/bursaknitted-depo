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
    QCheckBox, QCompleter, QDateEdit, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QSize, QAbstractTableModel, QModelIndex, QVariant, QDate
from PyQt6.QtGui import QFont, QColor, QIcon, QBrush, QPixmap


def _excepthook(exctype, value, tb):
    """PyQt6 varsayılan davranışı: bir slot içinde yakalanmayan hata oluşunca
    qFatal() çağrılır ve tüm program anında kapanır (SIGABRT) — kullanıcı sadece
    "program kapandı" görür. Bu hook hatayı gösterir ve programı açık tutar."""
    import traceback
    traceback.print_exception(exctype, value, tb)
    try:
        QMessageBox.critical(QApplication.activeWindow(), "Beklenmeyen Hata",
            f"Bir hata oluştu, son işlem tamamlanmamış olabilir:\n\n{value}")
    except Exception:
        pass


sys.excepthook = _excepthook

# Bağlantı modu: "local" veya "remote"
CONNECTION_MODE = "local"

# Liste döndüren api_client fonksiyonları: uzak çağrı hata verirse _load() metotlarının
# `len(rows)`/`for r in rows` ile çökmemesi için boş liste döndürülür.
_LIST_FUNCS = {
    "get_all_fabrics", "get_all_customers", "get_all_suppliers",
    "get_all_products", "get_all_locations", "get_active_locations",
    "get_locations", "get_all_users", "get_fire_records",
    "get_movements", "get_all_movements", "get_movements_by_range",
    "get_all_orders", "get_all_purchase_orders",
    "get_pending_approval_orders", "get_shippable_orders",
    "get_order_shipments", "get_po_receipts", "get_boyahane_queue",
    "get_po_items_for_order",
}

_REAUTH_IN_PROGRESS = False

def _reauthenticate(parent):
    """Oturum geçersiz hale geldiğinde (sunucu yeniden başlamış olabilir) yeniden
    giriş ister. Başarılı olursa sekmeleri yeniler ve True döner."""
    global _REAUTH_IN_PROGRESS
    if _REAUTH_IN_PROGRESS:
        return False
    _REAUTH_IN_PROGRESS = True
    try:
        dlg = LoginDialog(parent)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.err_label.setText("Oturum sona erdi (sunucu yeniden başlamış olabilir).\nLütfen yeniden giriş yapın.")
        dlg.username.setText(CURRENT_USER.get("username", ""))
        dlg.password.setFocus()
        if dlg.exec():
            for w in QApplication.topLevelWidgets():
                if isinstance(w, MainWindow):
                    w._update_user_label()
                    w._rebuild_tabs()
            return True
        return False
    finally:
        _REAUTH_IN_PROGRESS = False

class _DbProxy:
    """db.xxx çağrılarını CONNECTION_MODE'a göre local veya remote'a yönlendirir.
    Uzak moddaki hatalar burada yakalanır, kullanıcıya gösterilir ve uygulamanın
    çökmesi yerine güvenli bir varsayılan değer döndürülür. Oturum süresi dolmuşsa
    (401) yeniden giriş istenir ve işlem otomatik tekrar denenir — kullanıcı az önce
    girdiği veriyi yeniden girmek zorunda kalmaz."""
    def __getattr__(self, name):
        if CONNECTION_MODE != "remote":
            return getattr(db, name)
        import api_client
        attr = getattr(api_client, name)
        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            try:
                return attr(*args, **kwargs)
            except Exception as e:
                parent = QApplication.activeWindow()
                if "Yetkisiz" in str(e) and _reauthenticate(parent):
                    try:
                        return attr(*args, **kwargs)   # yeni token ile tekrar dene
                    except Exception as e2:
                        e = e2
                if "Yetkisiz" not in str(e):
                    QMessageBox.critical(parent, "Bağlantı Hatası",
                        f"Sunucu ile iletişim kurulamadı:\n\n{e}")
                return [] if name in _LIST_FUNCS else None
        return wrapper

_db = _DbProxy()   # tüm kod db yerine _db kullanır ama mevcut kod db değişkenini kullanıyor,
                   # bu yüzden modül seviyesinde db'yi proxy ile değiştiriyoruz

def _get_db():
    return _db

# Giriş yapmış kullanıcı (global)
CURRENT_USER = {"id": 0, "username": "sistem", "full_name": "Sistem", "role": "admin"}

import database as _local_db
db = _local_db   # başlangıçta yerel; login sonrası proxy ile değiştirilir

import order_pdf
from order_pdf import CURRENCY_SYMBOLS

CURRENCY_OPTIONS = ["USD", "EUR", "GBP", "TRY"]

FABRIC_TYPE_COLORS = {"HAM": QColor("#5D4037"), "PFD": QColor("#00695C"),
                      "BOYALI": QColor("#545454"), "İPLİĞİ BOYALI": QColor("#EF6C00"),
                      "BASKILI": QColor("#6A1B9A")}

PRINT_TYPES = ["RONJAN", "ROTASYON", "DİJİTAL", "FLOK", "VARAK", "GLITTER"]

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


# ── Excel sütun eşleştirme ───────────────────────────────────────

# (alan_anahtarı, etiket, zorunlu_mu)
CUSTOMER_FIELDS = [
    ("name",    "Müşteri Adı", True),
    ("code",    "Kodu",        False),
    ("phone",   "Telefon",     False),
    ("address", "Adres",       False),
    ("tax_no",  "Vergi No",    False),
]
CUSTOMER_AUTO = {
    "name":    ["ad","isim","müşteri","musteri","name","unvan","firma"],
    "code":    ["kod","code"],
    "phone":   ["tel","phone","gsm","cep"],
    "address": ["adres","address"],
    "tax_no":  ["vergi","tax"],
}

SUPPLIER_FIELDS = [
    ("name",    "Tedarikçi Adı", True),
    ("code",    "Kodu",          False),
    ("phone",   "Telefon",       False),
    ("address", "Adres",         False),
    ("tax_no",  "Vergi No",      False),
]
SUPPLIER_AUTO = {
    "name":    ["ad","isim","tedarikçi","tedarikci","müşteri","musteri","name","unvan","firma"],
    "code":    ["kod","code"],
    "phone":   ["tel","phone","gsm","cep"],
    "address": ["adres","address"],
    "tax_no":  ["vergi","tax"],
}

PRODUCT_FIELDS = [
    ("product_code",   "Ürün Kodu",          True),
    ("reference_code", "Kumaş Kodu",         False),
    ("product_name",   "Ürün Adı/Bilgisi",   False),
    ("composition",    "Kompozisyon",        False),
    ("width",          "En",                 False),
    ("gramaj",         "Gramaj",             False),
    ("shrinkage",      "Çekme",              False),
    ("price",          "Fiyat",              False),
    ("supplier",       "Tedarikçi/Fason",    False),
]
PRODUCT_AUTO = {
    "product_code":   ["kumas","ürün kodu","urun kodu","product_code","kod"],
    "reference_code": ["kumas_kodu","kumaş kodu","kumas kodu","referans"],
    "product_name":   ["kumas_on_adi","kumas_adi","ürün adı","urun adi","ürün bilgisi","product_name","ad"],
    "composition":    ["kumas_bilesimi","bilesim","bileşim","kompozisyon","composition"],
    "width":          ["kumas_en","en","width"],
    "gramaj":         ["kumas_gramaj","gramaj","gsm"],
    "shrinkage":      ["kumas_cekme","cekme","çekme","shrinkage"],
    "price":          ["kumas_fiy","fiyat","price","birim_fiyat"],
    "supplier":       ["kumas_fason_id","fason","tedarikci","tedarikçi","supplier"],
}


def _excel_val_to_str(val):
    import pandas as pd
    if val is None or (hasattr(pd, "isna") and pd.isna(val)):
        return ""
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return str(val)
    return str(val).strip()


def _customer_tax_no(customer_id):
    customer = db.get_customer(customer_id)
    return dict(customer).get("tax_no", "") if customer else ""


def _wire_header_persistence(table, key, default_fn=None):
    """Sütun sırası ve genişliği kalıcı: kapatıp açınca aynı kalır.
    default_fn: kayıtlı durum yoksa (ilk çalıştırma) uygulanacak varsayılan
    sütun genişlikleri; verilmezse table.resizeColumnsToContents() kullanılır."""
    if table.property("hdr_wired"):
        return
    from PyQt6.QtCore import QSettings
    hdr = table.header() if isinstance(table, QTreeWidget) else table.horizontalHeader()
    settings = QSettings("BursaKnitted", "DepoTakip")
    st = settings.value(key)
    restored = False
    if st is not None:
        restored = hdr.restoreState(st)
    if not restored:
        if default_fn:
            default_fn()
        elif isinstance(table, QTreeWidget):
            for col in range(table.columnCount()):
                table.resizeColumnToContents(col)
        else:
            table.resizeColumnsToContents()
    # sectionResized, sürükleyerek yeniden boyutlandırma sırasında (mouseMoveEvent
    # içinden) art arda tetiklenir; o anda hdr.saveState() çağırmak macOS'ta
    # QHeaderView::resizeSection içinde yeniden girilebilirlik (reentrancy) sorunu
    # yaratıp SIGSEGV'e yol açabiliyor. Kayıt işlemini QTimer ile geciktirip
    # event-loop'a döndükten sonra yapıyoruz.
    save_timer = QTimer(table)
    save_timer.setSingleShot(True)
    save_timer.setInterval(300)
    def _save_hdr():
        QSettings("BursaKnitted", "DepoTakip").setValue(key, hdr.saveState())
    save_timer.timeout.connect(_save_hdr)
    hdr.sectionMoved.connect(lambda *a: save_timer.start())
    hdr.sectionResized.connect(lambda *a: save_timer.start())
    table.setProperty("hdr_wired", True)


class ExcelColumnMapDialog(QDialog):
    """Excel dosyasından sütun eşleştirmesi yapıp kayıt listesi üretir.
    fields: [(alan_anahtarı, etiket, zorunlu_mu), ...]
    auto_keywords: {alan_anahtarı: [başlık eşleştirme anahtar kelimeleri]}
    Kabul edildikten sonra self.records doldurulur."""

    def __init__(self, path, fields, auto_keywords=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Excel Sütun Eşleştirme")
        self.setMinimumSize(760, 540)
        self.path = path
        self.fields = fields
        self.auto_keywords = auto_keywords or {}
        self.df = None
        self.records = []
        self._build_ui()
        self._load_preview()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        self.chk_header = QCheckBox("İlk satır sütun başlığı içeriyor")
        self.chk_header.setChecked(True)
        self.chk_header.toggled.connect(self._load_preview)
        lay.addWidget(self.chk_header)

        lay.addWidget(QLabel("Önizleme (ilk 5 satır):"))
        self.preview = QTableWidget()
        self.preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview.verticalHeader().setVisible(False)
        self.preview.setMaximumHeight(170)
        lay.addWidget(self.preview)

        lay.addWidget(QLabel("Hangi sütun hangi alana karşılık geliyor?"))
        form = QFormLayout(); form.setSpacing(6)
        self.combos = {}
        for key, label, required in self.fields:
            combo = QComboBox()
            form.addRow((label + " *:") if required else (label + ":"), combo)
            self.combos[key] = combo
        lay.addLayout(form)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color:#757575;")
        lay.addWidget(self.info_label)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load_preview(self):
        import pandas as pd
        header = 0 if self.chk_header.isChecked() else None
        try:
            df = pd.read_excel(self.path, header=header)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel okunamadı:\n{e}")
            return

        if header is None:
            df.columns = [f"Sütun {i+1}" for i in range(len(df.columns))]
        else:
            df.columns = [str(c).strip() for c in df.columns]
        self.df = df
        cols = list(df.columns)

        # Önizleme tablosu
        self.preview.setColumnCount(len(cols))
        self.preview.setHorizontalHeaderLabels([str(c) for c in cols])
        n = min(5, len(df))
        self.preview.setRowCount(n)
        for r in range(n):
            for c in range(len(cols)):
                self.preview.setItem(r, c, QTableWidgetItem(_excel_val_to_str(df.iat[r, c])))
        self.preview.resizeColumnsToContents()

        # Eşleştirme kutularını doldur
        for combo in self.combos.values():
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("— Kullanılmıyor —", "")
            for c in cols:
                combo.addItem(str(c), c)
            combo.blockSignals(False)

        # Otomatik eşleştirme: önce tam eşleşme, sonra anahtar kelime içeriği
        if header == 0:
            used = set()
            lower_cols = {c: str(c).strip().lower() for c in cols}
            for pass_exact in (True, False):
                for key, combo in self.combos.items():
                    if combo.currentData():
                        continue
                    for kw in self.auto_keywords.get(key, []):
                        match = None
                        for c, lc in lower_cols.items():
                            if c in used:
                                continue
                            if (pass_exact and lc == kw) or (not pass_exact and kw in lc):
                                match = c; break
                        if match:
                            idx = combo.findData(match)
                            if idx >= 0:
                                combo.setCurrentIndex(idx)
                                used.add(match)
                            break

        self.info_label.setText(f"Toplam {len(df)} satır bulundu.")

    def _on_accept(self):
        if self.df is None:
            return self.reject()
        mapping = {}
        for key, label, required in self.fields:
            col = self.combos[key].currentData()
            if required and not col:
                return QMessageBox.warning(self, "Hata", f"'{label}' sütunu seçilmelidir.")
            mapping[key] = col

        records = []
        for _, row in self.df.iterrows():
            rec = {key: (_excel_val_to_str(row.get(col, "")) if col else "") for key, col in mapping.items()}
            if all(rec.get(key) for key, label, required in self.fields if required):
                records.append(rec)
        self.records = records
        self.accept()


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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Müşteri Adı", "Kodu", "Telefon", "Adres", "Vergi No", "Durum"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1,2,3,4,5): hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
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
            self.table.setItem(i, 4, QTableWidgetItem(r["tax_no"] or ""))
            s = QTableWidgetItem("✅ Aktif" if r["active"] else "⛔ Pasif")
            s.setForeground(QBrush(QColor("#2E7D32" if r["active"] else "#C62828")))
            self.table.setItem(i, 5, s)
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self,"Bilgi","Müşteri seçin."); return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _customer_dialog(self, c=None):
        dlg = QDialog(self); dlg.setWindowTitle("Müşteri" + (" Düzenle" if c else " Ekle"))
        dlg.setMinimumWidth(360); lay = QVBoxLayout(dlg); form = QFormLayout(); form.setSpacing(8)
        dlg.name   = QLineEdit(c["name"]    if c else "")
        dlg.code   = QLineEdit(c["code"]    if c else "")
        dlg.phone  = QLineEdit(c["phone"]   if c else "")
        dlg.addr   = QLineEdit(c["address"] if c else "")
        dlg.tax_no = QLineEdit(c["tax_no"]  if c else "")
        form.addRow("Müşteri Adı *:", dlg.name)
        form.addRow("Kodu:",          dlg.code)
        form.addRow("Telefon:",       dlg.phone)
        form.addRow("Adres:",         dlg.addr)
        form.addRow("Vergi No:",      dlg.tax_no)
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
            db.add_customer(dlg.name.text(), dlg.code.text(), dlg.phone.text(), dlg.addr.text(), dlg.tax_no.text())
            self._load(self.search.text())

    def _edit(self):
        cid = self._selected_id()
        if not cid: return
        c = db.get_customer(cid)
        dlg = self._customer_dialog(c)
        if dlg.exec():
            db.update_customer(cid, dlg.name.text(), dlg.code.text(),
                               dlg.phone.text(), dlg.addr.text(), dlg.tax_no.text())
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
            dlg = ExcelColumnMapDialog(path, CUSTOMER_FIELDS, CUSTOMER_AUTO, self)
            if not dlg.exec():
                return
            records = dlg.records
            if not records:
                return QMessageBox.warning(self,"Hata","Eşleştirilen sütunda geçerli veri bulunamadı.")
            db.import_customers_bulk(records)
            self._load(self.search.text())
            QMessageBox.information(self,"Başarılı",f"{len(records)} müşteri içe aktarıldı.")
        except Exception as e:
            QMessageBox.critical(self,"Hata",f"İçe aktarma hatası:\n{e}")


class SupplierManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tedarikçi Yönetimi")
        self.setMinimumSize(680, 460)
        self._build_ui(); self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # Arama
        top = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Tedarikçi adı, kodu, telefon...")
        self.search.textChanged.connect(lambda: self._load(self.search.text()))
        top.addWidget(QLabel("Ara:")); top.addWidget(self.search); top.addStretch()
        lay.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Tedarikçi Adı", "Kodu", "Telefon", "Adres", "Vergi No", "E-posta", "Durum"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1,2,3,4,5,6): hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_add   = QPushButton("+ Yeni Tedarikçi");  btn_add.clicked.connect(self._add)
        btn_edit  = QPushButton("✎ Düzenle");          btn_edit.clicked.connect(self._edit)
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
        rows = db.get_all_suppliers(search=search, active_only=False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            name_item = QTableWidgetItem(r["name"] or "")
            name_item.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, QTableWidgetItem(r["code"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r["phone"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(r["address"] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(r["tax_no"] or ""))
            self.table.setItem(i, 5, QTableWidgetItem(dict(r).get("email") or ""))
            s = QTableWidgetItem("✅ Aktif" if r["active"] else "⛔ Pasif")
            s.setForeground(QBrush(QColor("#2E7D32" if r["active"] else "#C62828")))
            self.table.setItem(i, 6, s)
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self,"Bilgi","Tedarikçi seçin."); return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _supplier_dialog(self, s=None):
        dlg = QDialog(self); dlg.setWindowTitle("Tedarikçi" + (" Düzenle" if s else " Ekle"))
        dlg.setMinimumWidth(360); lay = QVBoxLayout(dlg); form = QFormLayout(); form.setSpacing(8)
        dlg.name   = QLineEdit(s["name"]    if s else "")
        dlg.code   = QLineEdit(s["code"]    if s else "")
        dlg.phone  = QLineEdit(s["phone"]   if s else "")
        dlg.addr   = QLineEdit(s["address"] if s else "")
        dlg.tax_no = QLineEdit(s["tax_no"]  if s else "")
        dlg.email  = QLineEdit(dict(s).get("email", "") if s else "")
        form.addRow("Tedarikçi Adı *:", dlg.name)
        form.addRow("Kodu:",            dlg.code)
        form.addRow("Telefon:",         dlg.phone)
        form.addRow("Adres:",           dlg.addr)
        form.addRow("Vergi No:",        dlg.tax_no)
        form.addRow("E-posta:",         dlg.email)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        return dlg

    def _add(self):
        dlg = self._supplier_dialog()
        if dlg.exec():
            if not dlg.name.text().strip():
                return QMessageBox.warning(self,"Hata","Tedarikçi adı zorunlu!")
            db.add_supplier(dlg.name.text(), dlg.code.text(), dlg.phone.text(), dlg.addr.text(),
                            dlg.tax_no.text(), dlg.email.text().strip())
            self._load(self.search.text())

    def _edit(self):
        sid = self._selected_id()
        if not sid: return
        s = db.get_supplier(sid)
        dlg = self._supplier_dialog(s)
        if dlg.exec():
            db.update_supplier(sid, dlg.name.text(), dlg.code.text(),
                               dlg.phone.text(), dlg.addr.text(), dlg.tax_no.text(),
                               email=dlg.email.text().strip())
            self._load(self.search.text())

    def _delete(self):
        sid = self._selected_id()
        if not sid: return
        if QMessageBox.question(self,"Sil","Tedarikçi silinsin mi?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            db.delete_supplier(sid); self._load(self.search.text())

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self,"Tedarikçi Excel Dosyası","","Excel (*.xlsx *.xls)")
        if not path: return
        try:
            dlg = ExcelColumnMapDialog(path, SUPPLIER_FIELDS, SUPPLIER_AUTO, self)
            if not dlg.exec():
                return
            records = dlg.records
            if not records:
                return QMessageBox.warning(self,"Hata","Eşleştirilen sütunda geçerli veri bulunamadı.")
            db.import_suppliers_bulk(records)
            self._load(self.search.text())
            QMessageBox.information(self,"Başarılı",f"{len(records)} tedarikçi içe aktarıldı.")
        except Exception as e:
            QMessageBox.critical(self,"Hata",f"İçe aktarma hatası:\n{e}")


class ProductManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ürün Kataloğu Yönetimi")
        self.setMinimumSize(920, 520)
        self._build_ui(); self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Ürün kodu veya adı...")
        self.search.textChanged.connect(lambda: self._load(self.search.text()))
        top.addWidget(QLabel("Ara:")); top.addWidget(self.search); top.addStretch()
        lay.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Kodu", "Kumaş Kodu", "Ürün Adı/Bilgisi", "Kompozisyon", "En", "Gramaj", "Fiyat", "Tedarikçi/Fason", "Durum"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)   # elle genişlik
        hdr.setStretchLastSection(False)
        hdr.setSectionsMovable(True)   # sütun sürükle-bırak
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_add   = QPushButton("+ Yeni Ürün");  btn_add.clicked.connect(self._add)
        btn_edit  = QPushButton("✎ Düzenle");     btn_edit.clicked.connect(self._edit)
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
        rows = db.get_all_products(search=search, active_only=False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            code_item = QTableWidgetItem(r["product_code"] or "")
            code_item.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.table.setItem(i, 0, code_item)
            self.table.setItem(i, 1, QTableWidgetItem(r["reference_code"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r["product_name"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(r["composition"] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(r["width"] or ""))
            self.table.setItem(i, 5, QTableWidgetItem(r["gramaj"] or ""))
            price = r["price"] or 0
            price_item = _FireSortItem(f"{price:,.2f}" if price else "")
            price_item.setData(Qt.ItemDataRole.UserRole, price)
            self.table.setItem(i, 6, price_item)
            self.table.setItem(i, 7, QTableWidgetItem(r["supplier"] or ""))
            s = QTableWidgetItem("✅ Aktif" if r["active"] else "⛔ Pasif")
            s.setForeground(QBrush(QColor("#2E7D32" if r["active"] else "#C62828")))
            self.table.setItem(i, 8, s)
            for col in range(self.table.columnCount()):
                cell = self.table.item(i, col)
                if cell and cell.text():
                    cell.setToolTip(cell.text())   # sığmayan yazılar üzerine gelince okunur
        self.table.setSortingEnabled(True)   # başlığa tıklayınca sıralar
        _wire_header_persistence(self.table, "products_header")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self,"Bilgi","Ürün seçin."); return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _product_dialog(self, p=None):
        dlg = QDialog(self); dlg.setWindowTitle("Ürün" + (" Düzenle" if p else " Ekle"))
        dlg.setMinimumWidth(380); lay = QVBoxLayout(dlg); form = QFormLayout(); form.setSpacing(8)
        dlg.code     = QLineEdit(p["product_code"] if p else "")
        dlg.ref      = QLineEdit(p["reference_code"] if p else "")
        dlg.name     = QLineEdit(p["product_name"] if p else "")
        dlg.comp     = QLineEdit(p["composition"] if p else "")
        dlg.width    = QLineEdit(p["width"] if p else "")
        dlg.gramaj   = QLineEdit(p["gramaj"] if p else "")
        dlg.shrink   = QLineEdit(p["shrinkage"] if p else "")
        dlg.price    = QDoubleSpinBox(); dlg.price.setRange(0, 999999); dlg.price.setDecimals(2)
        dlg.price.setValue(p["price"] if (p and p["price"]) else 0)
        dlg.supplier = QLineEdit(p["supplier"] if p else "")
        form.addRow("Ürün Kodu *:", dlg.code)
        form.addRow("Kumaş Kodu:", dlg.ref)
        form.addRow("Ürün Adı/Bilgisi:", dlg.name)
        form.addRow("Kompozisyon:", dlg.comp)
        form.addRow("En:", dlg.width)
        form.addRow("Gramaj:", dlg.gramaj)
        form.addRow("Çekme:", dlg.shrink)
        form.addRow("Fiyat:", dlg.price)
        form.addRow("Tedarikçi/Fason:", dlg.supplier)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        return dlg

    def _add(self):
        dlg = self._product_dialog()
        if dlg.exec():
            code = dlg.code.text().strip()
            if not code:
                return QMessageBox.warning(self,"Hata","Ürün kodu zorunlu!")
            try:
                db.add_product(code, dlg.name.text(), dlg.comp.text(), dlg.width.text(),
                               dlg.gramaj.text(), dlg.shrink.text(), dlg.price.value(), dlg.supplier.text(),
                               reference_code=dlg.ref.text())
                self._load(self.search.text())
            except Exception as e:
                QMessageBox.critical(self,"Hata",f"Eklenemedi:\n{e}")

    def _edit(self):
        pid = self._selected_id()
        if not pid: return
        p = db.get_product(pid)
        dlg = self._product_dialog(p)
        if dlg.exec():
            code = dlg.code.text().strip()
            if not code:
                return QMessageBox.warning(self,"Hata","Ürün kodu zorunlu!")
            db.update_product(pid, code, dlg.name.text(), dlg.comp.text(), dlg.width.text(),
                              dlg.gramaj.text(), dlg.shrink.text(), dlg.price.value(), dlg.supplier.text(),
                              p["active"], reference_code=dlg.ref.text())
            self._load(self.search.text())

    def _delete(self):
        pid = self._selected_id()
        if not pid: return
        if QMessageBox.question(self,"Sil","Ürün silinsin mi?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            db.delete_product(pid); self._load(self.search.text())

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self,"Ürün Excel Dosyası","","Excel (*.xlsx *.xls)")
        if not path: return
        try:
            dlg = ExcelColumnMapDialog(path, PRODUCT_FIELDS, PRODUCT_AUTO, self)
            if not dlg.exec():
                return
            records = dlg.records
            if not records:
                return QMessageBox.warning(self,"Hata","Eşleştirilen sütunda geçerli veri bulunamadı.")
            n = db.import_products_bulk(records)
            self._load(self.search.text())
            QMessageBox.information(self,"Başarılı",f"{n} ürün içe aktarıldı/güncellendi.")
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


class CompanySettingsDialog(QDialog):
    """Sipariş formlarında kullanılan firma/banka bilgileri ve varsayılan
    sözleşme şartnamesi metni — settings tablosunda saklanır."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Şirket / Banka Ayarları")
        self.setMinimumSize(560, 600)
        self._build_ui()
        self._load()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        form = QFormLayout(); form.setSpacing(8)
        self.company_name = QLineEdit()
        self.company_address = QLineEdit()
        self.company_phone = QLineEdit()
        self.company_tax = QLineEdit()
        self.company_origin = QLineEdit()
        self.company_website = QLineEdit()
        self.company_email_info = QLineEdit()
        self.company_email_planlama = QLineEdit()
        form.addRow("Firma Unvanı:", self.company_name)
        form.addRow("Adres:", self.company_address)
        form.addRow("Telefon:", self.company_phone)
        form.addRow("Vergi Numarası:", self.company_tax)
        form.addRow("Menşei:", self.company_origin)
        form.addRow("Web Sitesi:", self.company_website)
        form.addRow("E-posta (Info):", self.company_email_info)
        form.addRow("E-posta (Planlama):", self.company_email_planlama)
        lay.addLayout(form)

        lay.addWidget(QLabel("Banka Bilgileri:"))
        self.bank_info = QTextEdit()
        self.bank_info.setMinimumHeight(140)
        lay.addWidget(self.bank_info)

        lay.addWidget(QLabel("Varsayılan Sözleşme Şartnamesi:"))
        self.contract_template = QTextEdit()
        self.contract_template.setMinimumHeight(220)
        lay.addWidget(self.contract_template)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("Kaydet")
        btn_save.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;border-radius:4px;padding:7px 14px;")
        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("background:#757575;color:white;border-radius:4px;padding:7px 14px;")
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(btn_save); btn_row.addWidget(btn_cancel)
        lay.addLayout(btn_row)

    def _load(self):
        cfg = db.get_company_settings() or {}
        self.company_name.setText(cfg.get("name", ""))
        self.company_address.setText(cfg.get("address", ""))
        self.company_phone.setText(cfg.get("phone", ""))
        self.company_tax.setText(cfg.get("tax", ""))
        self.company_origin.setText(cfg.get("origin", ""))
        self.company_website.setText(cfg.get("website", ""))
        self.company_email_info.setText(cfg.get("email_info", ""))
        self.company_email_planlama.setText(cfg.get("email_planlama", ""))
        self.bank_info.setPlainText(cfg.get("bank_info", ""))
        self.contract_template.setPlainText(cfg.get("contract_template", ""))

    def _save(self):
        db.save_company_settings(
            name=self.company_name.text().strip(),
            address=self.company_address.text().strip(),
            phone=self.company_phone.text().strip(),
            tax=self.company_tax.text().strip(),
            origin=self.company_origin.text().strip(),
            website=self.company_website.text().strip(),
            email_info=self.company_email_info.text().strip(),
            email_planlama=self.company_email_planlama.text().strip(),
            bank_info=self.bank_info.toPlainText(),
            contract_template=self.contract_template.toPlainText(),
        )
        QMessageBox.information(self, "Kaydedildi", "Şirket / banka ayarları kaydedildi.")
        self.accept()


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
        btn_edit = QPushButton("✏ Düzenle");         btn_edit.clicked.connect(self._edit)
        btn_pw   = QPushButton("🔑 Şifre Değiştir"); btn_pw.clicked.connect(self._change_pw)
        btn_tog  = QPushButton("⏸ Aktif/Pasif");    btn_tog.clicked.connect(self._toggle)
        btn_del  = QPushButton("✕ Sil")
        btn_del.setStyleSheet("background:#757575; color:white; border-radius:4px; padding:6px 14px;")
        btn_del.clicked.connect(self._delete)
        for b in (btn_add, btn_edit, btn_pw, btn_tog, btn_del):
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
        role_cb = QComboBox()
        role_cb.addItems(["kullanici", "admin", "planlama", "satışçı", "depo-sevkiyat"])
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

    def _edit(self):
        uid = self._selected_id()
        if not uid:
            return
        row = self.table.currentRow()
        cur_fname = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        cur_role  = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        cur_uname = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        dlg = QDialog(self); dlg.setWindowTitle(f"Kullanıcı Düzenle — {cur_uname}")
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg); form = QFormLayout(); form.setSpacing(8)
        fname = QLineEdit(cur_fname)
        role_cb = QComboBox()
        role_cb.addItems(["kullanici", "admin", "planlama", "satışçı", "depo-sevkiyat"])
        idx = role_cb.findText(cur_role)
        if idx >= 0:
            role_cb.setCurrentIndex(idx)
        form.addRow("Ad Soyad:", fname)
        form.addRow("Rol:", role_cb)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec():
            db.update_user(uid, fname.text().strip(), role_cb.currentText())
            self._load()

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

        # Ürün kodu — katalogdan sadece seçim (aranabilir, serbest metin kabul edilmez)
        self.product_code = QComboBox()
        self.product_code.setEditable(True)
        self.product_code.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = self.product_code.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.product_code.currentIndexChanged.connect(self._on_product_change)

        # Ürün açıklaması — serbest metin, elle girilir
        self.product_name = QLineEdit()

        self.color = QLineEdit()
        self.lab_no = QLineEdit()
        self.lab_no.setPlaceholderText("Lab dip onay numarası (opsiyonel)")
        self._load_products()

        # Lokasyon — tek kademeli düz liste (tüm aktif lokasyonlar)
        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        self.location_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        _lc = self.location_combo.completer()
        _lc.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        _lc.setFilterMode(Qt.MatchFlag.MatchContains)
        _lc.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Satın alma lokasyonu — müşteri listesinden seçim
        self.entry_loc = QComboBox()
        self.entry_loc.setEditable(True)
        self.entry_loc.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        _ec = self.entry_loc.completer()
        _ec.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        _ec.setFilterMode(Qt.MatchFlag.MatchContains)
        _ec.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._load_locations()
        self._load_entry_customers()

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
        for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]:
            self.fabric_type.addItem(t, t)
        self.fabric_type.setStyleSheet("border: 1px solid #BDBDBD;")

        # Baskı tipi — sadece Kumaş Tipi = BASKILI iken görünür
        self.print_type = QComboBox()
        self.print_type.addItem("— Seçiniz —", "")
        for t in PRINT_TYPES:
            self.print_type.addItem(t, t)
        self.print_type.setStyleSheet("border: 1px solid #BDBDBD;")

        self.zemin_rengi = QLineEdit()
        self.baski_desen_no = QLineEdit()

        self.fabric_type.currentIndexChanged.connect(self._update_print_fields)
        self.print_type.currentIndexChanged.connect(self._update_print_fields)

        self.lot = QLineEdit()
        self.lot.setPlaceholderText("Boş bırakılırsa otomatik verilir (LOT-20260610-001)")

        self.description = QTextEdit()
        self.description.setMaximumHeight(70)

        form.addRow("Ürün Kodu *:", self.product_code)
        form.addRow("Ürün Açıklaması:", self.product_name)
        form.addRow("Kumaş Tipi *:", self.fabric_type)
        form.addRow("Baskı Tipi *:", self.print_type)
        form.addRow("Renk:", self.color)
        form.addRow("Zemin Rengi:", self.zemin_rengi)
        form.addRow("Lab No:", self.lab_no)
        form.addRow("Baskı Desen No:", self.baski_desen_no)

        form.addRow("Satın Alma Lokasyonu:", self.entry_loc)

        form.addRow("Hedef Lokasyon *:", self.location_combo)
        form.addRow("Lot:", self.lot)
        form.addRow("Metre:", self.meter)
        form.addRow("Kilo:", self.kg)
        form.addRow("Top/Adet:", self.piece_count)
        form.addRow("Birim Fiyat ($/mt):", self.birim_fiyat)
        form.addRow("Açıklama:", self.description)

        layout.addLayout(form)
        self._form = form
        self._update_print_fields()

        # Zorunlu alan notu
        note = QLabel("* işaretli alanlar zorunludur")
        note.setStyleSheet("color:#9E9E9E; font-size:11px;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_products(self, select_code="", select_name=""):
        """Ürün kodu kombosunu kataloğa göre doldurur. select_code katalogda
        yoksa (eski kayıt), kaybolmaması için listeye eklenir."""
        self._products = {}
        self.product_code.blockSignals(True)
        self.product_code.clear()
        self.product_code.addItem("— Seçiniz —", "")
        self.product_code.addItem("➕ Yeni ürün ekle...", "__NEW__")
        for r in db.get_all_products(active_only=True):
            code = r["product_code"]
            name = r["product_name"] or ""
            self._products[code] = name
            self.product_code.addItem(f"{code} — {name}" if name else code, code)
        if select_code:
            idx = self.product_code.findData(select_code)
            if idx < 0:
                self._products[select_code] = select_name
                label = f"{select_code} — {select_name}" if select_name else select_code
                self.product_code.addItem(label, select_code)
                idx = self.product_code.count() - 1
            self.product_code.setCurrentIndex(idx)
        self.product_code.blockSignals(False)
        self._on_product_change()

    def _on_product_change(self, idx=None):
        code = self.product_code.currentData()
        if code == "__NEW__":
            self._add_new_product()
            return

    def _add_new_product(self):
        """Katalogda olmayan bir ürün kodu için hızlı ekleme."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Yeni Ürün Ekle")
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg)
        form = QFormLayout(); form.setSpacing(8)
        code_edit = QLineEdit()
        name_edit = QLineEdit()
        form.addRow("Ürün Kodu *:", code_edit)
        form.addRow("Ürün Adı/Bilgisi:", name_edit)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec():
            code = code_edit.text().strip().upper()
            if not code:
                QMessageBox.warning(self, "Hata", "Ürün kodu zorunlu!")
                self.product_code.setCurrentIndex(0)
                return
            try:
                db.add_product(code, name_edit.text().strip())
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün eklenemedi:\n{e}")
                self.product_code.setCurrentIndex(0)
                return
            self._load_products(select_code=code)
        else:
            self.product_code.setCurrentIndex(0)

    def _load_locations(self):
        locs = db.get_active_locations()
        sorted_locs = sorted(locs, key=lambda x: (x["group_name"] or "", x["name"] or ""))

        self.location_combo.clear()
        self.location_combo.addItem("— Seçiniz —", "")
        for l in sorted_locs:
            grp = l["group_name"] or ""
            label = f"[{grp}] {l['name']}" if grp else l["name"]
            self.location_combo.addItem(label, l["name"])

    def _load_entry_customers(self):
        self.entry_loc.clear()
        self.entry_loc.addItem("— Seçiniz —", "")
        for c in db.get_all_customers():
            label = c["name"] + (f" ({c['code']})" if c.get("code") else "")
            self.entry_loc.addItem(label, c["name"])

    def _selected_location(self):
        return self.location_combo.currentData() or ""

    def _update_print_fields(self):
        """BASKILI / Baskı Tipi seçimine göre Renk, Zemin Rengi, Lab No,
        Baskı Tipi ve Baskı Desen No alanlarının görünürlüğünü ayarlar."""
        is_baskili = self.fabric_type.currentData() == "BASKILI"
        pt = self.print_type.currentData() if is_baskili else ""
        is_ronjan = pt == "RONJAN"
        for widget, visible in (
            (self.print_type, is_baskili),
            (self.color, not is_baskili),
            (self.zemin_rengi, is_ronjan),
            (self.lab_no, (not is_baskili) or is_ronjan),
            (self.baski_desen_no, is_baskili and bool(pt)),
        ):
            label = self._form.labelForField(widget)
            if label:
                label.setVisible(visible)
            widget.setVisible(visible)

    def _populate(self, f):
        self._load_products(select_code=f["product_code"] or "", select_name=f["product_name"] or "")
        self.product_name.setText(f["product_name"] or "")
        self.color.setText(f["color"] or "")
        self.lab_no.setText(dict(f).get("lab_no") or "")
        loc_val = f["location"] or ""
        if loc_val:
            idx = self.location_combo.findData(loc_val)
            if idx < 0:
                self.location_combo.addItem(loc_val, loc_val)
                idx = self.location_combo.count() - 1
            self.location_combo.setCurrentIndex(idx)
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
        pt_idx = self.print_type.findData(dict(f).get("print_type") or "")
        if pt_idx >= 0:
            self.print_type.setCurrentIndex(pt_idx)
        self.zemin_rengi.setText(dict(f).get("zemin_rengi") or "")
        self.baski_desen_no.setText(dict(f).get("baski_desen_no") or "")
        self.lot.setText(f["lot"] or "")
        self.description.setPlainText(f["description"] or "")
        self._update_print_fields()

    def _validate(self):
        errors = []
        if not self.product_code.currentData():
            errors.append("• Ürün kodu katalogdan seçilmelidir")
        if not self.location_combo.currentData():
            errors.append("• Hedef lokasyon seçilmelidir")
        if not self.fabric_type.currentData():
            errors.append("• Kumaş tipi seçilmelidir (Ham / PFD / Boyalı / İpliği Boyalı / Baskılı)")
            self.fabric_type.setStyleSheet("border: 2px solid #C62828; border-radius:4px;")
        else:
            self.fabric_type.setStyleSheet("")
        if self.fabric_type.currentData() == "BASKILI" and not self.print_type.currentData():
            errors.append("• Baskı tipi seçilmelidir (Ronjan / Rotasyon / Dijital / Flok / Varak / Glitter)")
            self.print_type.setStyleSheet("border: 2px solid #C62828; border-radius:4px;")
        else:
            self.print_type.setStyleSheet("border: 1px solid #BDBDBD;")
        if errors:
            QMessageBox.warning(self, "Eksik Bilgi", "\n".join(errors))
            return
        self.accept()

    def get_data(self):
        fabric_type = self.fabric_type.currentData() or ""
        is_baskili = fabric_type == "BASKILI"
        print_type = (self.print_type.currentData() or "") if is_baskili else ""
        is_ronjan = print_type == "RONJAN"
        return {
            "product_code": (self.product_code.currentData() or "").strip().upper(),
            "product_name": self.product_name.text().strip(),
            "color": self.color.text().strip().upper() if not is_baskili else "",
            "lab_no": self.lab_no.text().strip() if ((not is_baskili) or is_ronjan) else "",
            "location": self._selected_location(),
            "entry_location": self.entry_loc.currentData() or self._selected_location(),
            "fabric_type": fabric_type,
            "print_type": print_type,
            "zemin_rengi": self.zemin_rengi.text().strip().upper() if is_ronjan else "",
            "baski_desen_no": self.baski_desen_no.text().strip() if (is_baskili and print_type) else "",
            "lot": self.lot.text().strip(),
            "meter": self.meter.value(),
            "kg": self.kg.value(),
            "piece_count": self.piece_count.text().strip(),
            "birim_fiyat": self.birim_fiyat.value(),
            "description": self.description.toPlainText().strip(),
        }


class OrderItemDialog(QDialog):
    """Sipariş kalemi ekle/düzenle — tek bir ürün/renk/kumaş tipi satırı."""

    FABRIC_TYPES = ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]

    def __init__(self, parent=None, item=None, currency="USD"):
        super().__init__(parent)
        self.currency = currency
        self.setWindowTitle("Sipariş Kalemi Ekle" if not item else "Sipariş Kalemini Düzenle")
        self.setMinimumSize(460, 540)
        self._build_ui()
        if item:
            self._populate(item)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.product_code = QComboBox()
        self.product_code.setEditable(True)
        self.product_code.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = self.product_code.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._load_products()
        self.product_code.currentIndexChanged.connect(self._on_product_change)
        form.addRow("Ürün Kodu *:", self.product_code)

        self.composition = QLineEdit()
        self.width = QLineEdit()
        self.gramaj = QLineEdit()
        form.addRow("Kompozisyon:", self.composition)
        form.addRow("En:", self.width)
        form.addRow("Gramaj:", self.gramaj)

        self.fabric_type = QComboBox()
        self.fabric_type.addItem("— Seçiniz —", "")
        for t in self.FABRIC_TYPES:
            self.fabric_type.addItem(t, t)
        self.fabric_type.setStyleSheet("border: 1px solid #BDBDBD;")
        form.addRow("Kumaş Tipi *:", self.fabric_type)

        # Baskı tipi — sadece Kumaş Tipi = BASKILI iken görünür
        self.print_type = QComboBox()
        self.print_type.addItem("— Seçiniz —", "")
        for t in PRINT_TYPES:
            self.print_type.addItem(t, t)
        self.print_type.setStyleSheet("border: 1px solid #BDBDBD;")
        form.addRow("Baskı Tipi *:", self.print_type)

        self.color = QLineEdit()
        self.zemin_rengi = QLineEdit()
        self.lab_no = QLineEdit()
        self.baski_desen_no = QLineEdit()
        form.addRow("Renk:", self.color)
        form.addRow("Zemin Rengi:", self.zemin_rengi)
        form.addRow("Lab No:", self.lab_no)
        form.addRow("Baskı Desen No:", self.baski_desen_no)

        self.fabric_type.currentIndexChanged.connect(self._update_print_fields)
        self.print_type.currentIndexChanged.connect(self._update_print_fields)

        self.description = QLineEdit()
        self.description.setPlaceholderText("Opsiyonel not (örn. numune ile aynı ton)")
        form.addRow("Açıklama:", self.description)

        self.meter = QDoubleSpinBox()
        self.meter.setRange(0, 999999)
        self.meter.setDecimals(2)
        self.meter.valueChanged.connect(self._update_total)
        form.addRow("Metre:", self.meter)

        kg_row = QWidget()
        kg_lay = QHBoxLayout(kg_row)
        kg_lay.setContentsMargins(0, 0, 0, 0)
        self.kg = QDoubleSpinBox()
        self.kg.setRange(0, 999999)
        self.kg.setDecimals(2)
        btn_calc_kg = QPushButton("🧮 Hesapla")
        btn_calc_kg.setToolTip("Kilo = Gramaj × (En / 100) × Metre / 1000")
        btn_calc_kg.clicked.connect(self._calc_kg)
        kg_lay.addWidget(self.kg, 1)
        kg_lay.addWidget(btn_calc_kg)
        form.addRow("Kilo:", kg_row)

        symbol = CURRENCY_SYMBOLS.get(self.currency, "$")
        self.sale_price = QDoubleSpinBox()
        self.sale_price.setRange(0, 9999999)
        self.sale_price.setDecimals(2)
        self.sale_price.setSuffix(f" {symbol}")
        self.sale_price.setStyleSheet("border: 1px solid #BDBDBD;")
        self.sale_price.valueChanged.connect(self._update_total)
        form.addRow(f"Satış Fiyatı ({symbol}/mt):", self.sale_price)

        self.total_lbl = QLabel(f"0.00 {symbol}")
        self.total_lbl.setStyleSheet("font-weight:bold; color:#1A237E;")
        form.addRow("Tutar:", self.total_lbl)

        layout.addLayout(form)
        self._form = form
        self._update_print_fields()

        note = QLabel("* işaretli alanlar zorunludur")
        note.setStyleSheet("color:#9E9E9E; font-size:11px;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Ürün ─────────────────────────────────────────────────────
    def _load_products(self, select_code="", select_name=""):
        self._products = {}
        self.product_code.blockSignals(True)
        self.product_code.clear()
        self.product_code.addItem("— Seçiniz —", "")
        self.product_code.addItem("➕ Yeni ürün ekle...", "__NEW__")
        for r in db.get_all_products(active_only=True):
            code = r["product_code"]
            name = r["product_name"] or ""
            self._products[code] = name
            self.product_code.addItem(f"{code} — {name}" if name else code, code)
        if select_code:
            idx = self.product_code.findData(select_code)
            if idx < 0:
                self._products[select_code] = select_name
                label = f"{select_code} — {select_name}" if select_name else select_code
                self.product_code.addItem(label, select_code)
                idx = self.product_code.count() - 1
            self.product_code.setCurrentIndex(idx)
        self.product_code.blockSignals(False)
        self._on_product_change()

    def _on_product_change(self, idx=None):
        code = self.product_code.currentData()
        if code == "__NEW__":
            self._add_new_product()
            return
        if code:
            product = db.get_product_by_code(code)
            if product:
                p = dict(product)
                self.composition.setText(p.get("composition") or "")
                self.width.setText(p.get("width") or "")
                self.gramaj.setText(p.get("gramaj") or "")

    def _add_new_product(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Yeni Ürün Ekle")
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg)
        form = QFormLayout(); form.setSpacing(8)
        code_edit = QLineEdit()
        name_edit = QLineEdit()
        form.addRow("Ürün Kodu *:", code_edit)
        form.addRow("Ürün Adı/Bilgisi:", name_edit)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec():
            code = code_edit.text().strip().upper()
            if not code:
                QMessageBox.warning(self, "Hata", "Ürün kodu zorunlu!")
                self.product_code.setCurrentIndex(0)
                return
            try:
                db.add_product(code, name_edit.text().strip())
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün eklenemedi:\n{e}")
                self.product_code.setCurrentIndex(0)
                return
            self._load_products(select_code=code)
        else:
            self.product_code.setCurrentIndex(0)

    # ── Hesaplamalar ─────────────────────────────────────────────
    def _calc_kg(self):
        try:
            gramaj = float(str(self.gramaj.text()).replace(",", ".").strip())
            en = float(str(self.width.text()).replace(",", ".").strip())
            metre = self.meter.value()
            kg = gramaj * (en / 100) * metre / 1000
            self.kg.setValue(round(kg, 2))
        except ValueError:
            QMessageBox.warning(self, "Hesaplanamadı",
                "Kilo hesaplamak için Gramaj, En ve Metre alanları sayısal olmalıdır.")

    def _update_total(self):
        symbol = CURRENCY_SYMBOLS.get(self.currency, "$")
        total = self.meter.value() * self.sale_price.value()
        self.total_lbl.setText(f"{total:,.2f} {symbol}")

    def _update_print_fields(self):
        """BASKILI / Baskı Tipi seçimine göre Renk, Zemin Rengi, Lab No,
        Baskı Tipi ve Baskı Desen No alanlarının görünürlüğünü ayarlar."""
        is_baskili = self.fabric_type.currentData() == "BASKILI"
        pt = self.print_type.currentData() if is_baskili else ""
        is_ronjan = pt == "RONJAN"
        for widget, visible in (
            (self.print_type, is_baskili),
            (self.color, not is_baskili),
            (self.zemin_rengi, is_ronjan),
            (self.lab_no, (not is_baskili) or is_ronjan),
            (self.baski_desen_no, is_baskili and bool(pt)),
        ):
            label = self._form.labelForField(widget)
            if label:
                label.setVisible(visible)
            widget.setVisible(visible)

    def _populate(self, item):
        self._load_products(select_code=item.get("product_code") or "", select_name=item.get("product_name") or "")
        self.composition.setText(item.get("composition") or "")
        self.width.setText(item.get("width") or "")
        self.gramaj.setText(item.get("gramaj") or "")
        ft_idx = self.fabric_type.findData(item.get("fabric_type") or "")
        if ft_idx >= 0:
            self.fabric_type.setCurrentIndex(ft_idx)
        pt_idx = self.print_type.findData(item.get("print_type") or "")
        if pt_idx >= 0:
            self.print_type.setCurrentIndex(pt_idx)
        self.color.setText(item.get("color") or "")
        self.zemin_rengi.setText(item.get("zemin_rengi") or "")
        self.lab_no.setText(item.get("lab_no") or "")
        self.baski_desen_no.setText(item.get("baski_desen_no") or "")
        self.description.setText(item.get("description") or "")
        self.meter.setValue(item.get("meter") or 0)
        self.kg.setValue(item.get("kg") or 0)
        self.sale_price.setValue(item.get("sale_price") or 0)
        self._update_total()
        self._update_print_fields()

    def _validate(self):
        errors = []
        code = self.product_code.currentData()
        if not code or code == "__NEW__":
            errors.append("• Ürün kodu seçilmelidir")
        if not self.fabric_type.currentData():
            errors.append("• Kumaş tipi seçilmelidir (Ham / PFD / Boyalı / İpliği Boyalı / Baskılı)")
            self.fabric_type.setStyleSheet("border: 2px solid #C62828; border-radius:4px;")
        else:
            self.fabric_type.setStyleSheet("border: 1px solid #BDBDBD;")
        if self.fabric_type.currentData() == "BASKILI" and not self.print_type.currentData():
            errors.append("• Baskı tipi seçilmelidir (Ronjan / Rotasyon / Dijital / Flok / Varak / Glitter)")
            self.print_type.setStyleSheet("border: 2px solid #C62828; border-radius:4px;")
        else:
            self.print_type.setStyleSheet("border: 1px solid #BDBDBD;")
        if errors:
            QMessageBox.warning(self, "Eksik Bilgi", "\n".join(errors))
            return
        self.accept()

    def get_data(self):
        fabric_type = self.fabric_type.currentData() or ""
        is_baskili = fabric_type == "BASKILI"
        print_type = (self.print_type.currentData() or "") if is_baskili else ""
        is_ronjan = print_type == "RONJAN"
        return {
            "product_code": (self.product_code.currentData() or "").strip().upper(),
            "product_name": self._products.get(self.product_code.currentData(), ""),
            "composition": self.composition.text().strip(),
            "width": self.width.text().strip(),
            "gramaj": self.gramaj.text().strip(),
            "fabric_type": fabric_type,
            "color": self.color.text().strip().upper() if not is_baskili else "",
            "lab_no": self.lab_no.text().strip() if ((not is_baskili) or is_ronjan) else "",
            "print_type": print_type,
            "zemin_rengi": self.zemin_rengi.text().strip().upper() if is_ronjan else "",
            "baski_desen_no": self.baski_desen_no.text().strip() if (is_baskili and print_type) else "",
            "description": self.description.text().strip(),
            "meter": self.meter.value(),
            "kg": self.kg.value(),
            "sale_price": self.sale_price.value(),
        }


class OrderDialog(QDialog):
    """Satış siparişi açma/düzenleme — 3 sekme: sipariş bilgileri, sipariş
    kalemleri (çoklu ürün/renk/kumaş tipi), sözleşme şartnamesi. Kaydedilince
    status='PLANLAMA BEKLİYOR' ile orders tablosuna yazılır."""

    PAYMENT_METHODS = ["Peşin", "Havale/EFT", "30 Gün Vade", "60 Gün Vade",
                       "90 Gün Vade", "120 Gün Vade", "Akreditif (L/C)", "Diğer"]
    DELIVERY_TERMS = ["FOB", "CIF", "EXW", "DAP", "Diğer"]

    ITEM_COLS = ["Ürün Kodu", "Kompozisyon", "En", "Gramaj", "Kumaş Tipi", "Renk",
                 "Lab No", "Açıklama", "Metre", "Kilo", "Birim Fiyat", "Tutar",
                 "Baskı Tipi", "Zemin Rengi", "Baskı Desen No"]

    def __init__(self, parent=None, order=None):
        super().__init__(parent)
        self.order = order
        self._items = list(order.get("items", [])) if order else []
        self.setWindowTitle("Yeni Sipariş" if not order else f"Sipariş Düzenle — {order['order_no']}")
        self.setMinimumSize(740, 660)
        self._build_ui()
        if order:
            self._populate(order)
        else:
            self.order_date.setDate(QDate.currentDate())
            self.delivery_date.setDate(QDate.currentDate().addDays(30))
            self._refresh_items_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ── Sekme 1: Sipariş Bilgileri ──────────────────────────────
        tab1 = QWidget()
        form1 = QFormLayout(tab1)
        form1.setSpacing(10)

        self.customer = QComboBox()
        self._load_customers()
        self.customer.currentIndexChanged.connect(self._on_customer_change)
        form1.addRow("Müşteri *:", self.customer)

        self.customer_ref = QLineEdit()
        self.customer_ref.setPlaceholderText("Müşterinin kendi sipariş/PO numarası (opsiyonel)")
        form1.addRow("Müşteri Referans:", self.customer_ref)

        self.order_no_edit = QLineEdit()
        self.order_no_edit.setReadOnly(True)
        self.order_no_edit.setText("Kaydedince atanacak")
        self.order_no_edit.setStyleSheet("color:#757575;")
        form1.addRow("Sipariş No:", self.order_no_edit)

        self.order_date = QDateEdit()
        self.order_date.setCalendarPopup(True)
        self.order_date.setDisplayFormat("dd.MM.yyyy")
        form1.addRow("Sipariş Tarihi:", self.order_date)

        self.delivery_date = QDateEdit()
        self.delivery_date.setCalendarPopup(True)
        self.delivery_date.setDisplayFormat("dd.MM.yyyy")
        form1.addRow("Termin *:", self.delivery_date)

        self.currency = QComboBox()
        for code in CURRENCY_OPTIONS:
            self.currency.addItem(f"{code} ({CURRENCY_SYMBOLS[code]})", code)
        form1.addRow("Para Birimi *:", self.currency)

        self.payment_method = QComboBox()
        self.payment_method.setEditable(True)
        self.payment_method.addItem("")
        for p in self.PAYMENT_METHODS:
            self.payment_method.addItem(p)
        form1.addRow("Ödeme Şekli:", self.payment_method)

        self.delivery_terms = QComboBox()
        self.delivery_terms.setEditable(True)
        self.delivery_terms.addItem("")
        for d in self.DELIVERY_TERMS:
            self.delivery_terms.addItem(d)
        form1.addRow("Teslimat Şartları:", self.delivery_terms)

        self.delivery_address = QLineEdit()
        form1.addRow("Teslimat Adresi:", self.delivery_address)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(70)
        form1.addRow("Notlar:", self.notes)

        self.tabs.addTab(tab1, "📋 Sipariş Bilgileri")

        # ── Sekme 2: Sipariş Kalemleri ───────────────────────────────
        tab2 = QWidget()
        lay2 = QVBoxLayout(tab2)

        toolbar2 = QHBoxLayout()
        btn_add_item = QPushButton("+ Kalem Ekle")
        btn_add_item.setStyleSheet("background:#2E7D32; color:white; font-weight:bold; border-radius:4px; padding:6px 14px;")
        btn_add_item.clicked.connect(self._add_item)
        btn_edit_item = QPushButton("✎ Düzenle")
        btn_edit_item.clicked.connect(self._edit_item)
        btn_del_item = QPushButton("✕ Kaldır")
        btn_del_item.setStyleSheet("background:#757575; color:white; border-radius:4px; padding:6px 14px;")
        btn_del_item.clicked.connect(self._remove_item)
        toolbar2.addWidget(btn_add_item)
        toolbar2.addWidget(btn_edit_item)
        toolbar2.addWidget(btn_del_item)
        toolbar2.addStretch()
        lay2.addLayout(toolbar2)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(len(self.ITEM_COLS))
        self.items_table.setHorizontalHeaderLabels(self.ITEM_COLS)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.items_table.verticalHeader().setVisible(False)
        hdr = self.items_table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        self.items_table.doubleClicked.connect(self._edit_item)
        lay2.addWidget(self.items_table)

        self.items_total_lbl = QLabel("Genel Toplam: 0.00 $")
        self.items_total_lbl.setStyleSheet("font-weight:bold; color:#1A237E; font-size:13px;")
        self.items_total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay2.addWidget(self.items_total_lbl)

        self.tabs.addTab(tab2, "📦 Sipariş Kalemleri")

        # Para birimi değişince kalemler tablosu yeniden formatlanır —
        # items_table oluşturulduktan sonra bağlanır (erken tetiklenmesin)
        self.currency.currentIndexChanged.connect(self._refresh_items_table)

        note = QLabel("* işaretli alanlar zorunludur")
        note.setStyleSheet("color:#9E9E9E; font-size:11px;")
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        if self.order:
            btn_pdf = QPushButton("📄 PDF Al")
            btn_pdf.clicked.connect(self._export_pdf)
            btn_row.addWidget(btn_pdf)
        btn_row.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        btn_row.addWidget(buttons)
        layout.addLayout(btn_row)

    # ── Para Birimi / Kalemler ───────────────────────────────────
    def _current_currency(self):
        return self.currency.currentData() or "USD"

    def _refresh_items_table(self):
        symbol = CURRENCY_SYMBOLS.get(self._current_currency(), "$")
        self.items_table.setRowCount(len(self._items))
        grand_total = 0.0
        for i, it in enumerate(self._items):
            meter = it.get("meter") or 0
            sale_price = it.get("sale_price") or 0
            total = meter * sale_price
            grand_total += total
            values = [
                it.get("product_code") or "",
                it.get("composition") or "",
                it.get("width") or "",
                it.get("gramaj") or "",
                it.get("fabric_type") or "",
                it.get("color") or "",
                it.get("lab_no") or "",
                it.get("description") or "",
                f"{meter:,.2f}",
                f"{(it.get('kg') or 0):,.2f}",
                f"{sale_price:,.2f} {symbol}",
                f"{total:,.2f} {symbol}",
                it.get("print_type") or "",
                it.get("zemin_rengi") or "",
                it.get("baski_desen_no") or "",
            ]
            for j, v in enumerate(values):
                cell = QTableWidgetItem(v)
                if 8 <= j <= 11:
                    cell.setTextAlignment(int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight))
                if j == 4:
                    cell.setForeground(QBrush(FABRIC_TYPE_COLORS.get(it.get("fabric_type", ""), QColor("#333333"))))
                self.items_table.setItem(i, j, cell)
        self.items_total_lbl.setText(f"Genel Toplam: {grand_total:,.2f} {symbol}")

    def _add_item(self):
        dlg = OrderItemDialog(self, currency=self._current_currency())
        if dlg.exec():
            self._items.append(dlg.get_data())
            self._refresh_items_table()

    def _edit_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir kalem seçin.")
            return
        dlg = OrderItemDialog(self, item=self._items[row], currency=self._current_currency())
        if dlg.exec():
            self._items[row] = dlg.get_data()
            self._refresh_items_table()

    def _remove_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir kalem seçin.")
            return
        if QMessageBox.question(self, "Kaldır", "Bu kalem kaldırılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            del self._items[row]
            self._refresh_items_table()

    # ── PDF ──────────────────────────────────────────────────────
    def _export_pdf(self):
        company = db.get_company_settings()
        data = self.get_data()
        order = {**data, "order_no": self.order.get("order_no", ""),
                 "customer_tax_no": _customer_tax_no(data.get("customer_id"))}
        default_name = f"{order['order_no']}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Sipariş Sözleşmesi PDF", default_name, "PDF (*.pdf)")
        if not path:
            return
        try:
            order_pdf.generate_order_pdf(order, company, path)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturulamadı:\n{e}")
            return
        QMessageBox.information(self, "PDF Oluşturuldu", f"Kaydedildi:\n{path}")

    # ── Müşteri ──────────────────────────────────────────────────
    def _load_customers(self, select_id=None):
        self._customers = {}
        self.customer.blockSignals(True)
        self.customer.clear()
        self.customer.addItem("— Seçiniz —", "")
        self.customer.addItem("➕ Yeni müşteri ekle...", "__NEW__")
        for c in db.get_all_customers():
            cid = str(c["id"])
            self._customers[cid] = c["name"]
            label = c["name"] + (f" ({c['code']})" if c["code"] else "")
            self.customer.addItem(label, cid)
        if select_id is not None:
            sid = str(select_id)
            idx = self.customer.findData(sid)
            if idx < 0:
                c = db.get_customer(select_id)
                if c:
                    self._customers[sid] = c["name"]
                    label = c["name"] + (f" ({c['code']})" if c["code"] else "")
                    self.customer.addItem(label, sid)
                    idx = self.customer.count() - 1
            if idx >= 0:
                self.customer.setCurrentIndex(idx)
        self.customer.blockSignals(False)

    def _on_customer_change(self, idx=None):
        if self.customer.currentData() == "__NEW__":
            self._add_new_customer()

    def _add_new_customer(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Yeni Müşteri Ekle")
        dlg.setMinimumWidth(320)
        lay = QVBoxLayout(dlg)
        form = QFormLayout(); form.setSpacing(8)
        name_edit = QLineEdit()
        code_edit = QLineEdit()
        form.addRow("Müşteri Adı *:", name_edit)
        form.addRow("Kodu:", code_edit)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Hata", "Müşteri adı zorunlu!")
                self.customer.setCurrentIndex(0)
                return
            try:
                cid = db.add_customer(name, code_edit.text().strip())
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Müşteri eklenemedi:\n{e}")
                self.customer.setCurrentIndex(0)
                return
            self._load_customers(select_id=cid)
        else:
            self.customer.setCurrentIndex(0)

    # ── Doldurma / Doğrulama / Veri ─────────────────────────────────
    def _populate(self, o):
        self._load_customers(select_id=o.get("customer_id"))
        self.customer_ref.setText(o.get("customer_ref") or "")
        self.order_no_edit.setText(o.get("order_no") or "")

        d = QDate.fromString(str(o.get("order_date") or ""), "yyyy-MM-dd")
        self.order_date.setDate(d if d.isValid() else QDate.currentDate())

        d = QDate.fromString(str(o.get("delivery_date") or ""), "yyyy-MM-dd")
        self.delivery_date.setDate(d if d.isValid() else QDate.currentDate().addDays(30))

        cur_idx = self.currency.findData(o.get("currency") or "USD")
        self.currency.setCurrentIndex(cur_idx if cur_idx >= 0 else 0)

        idx = self.payment_method.findText(o.get("payment_method") or "")
        if idx >= 0:
            self.payment_method.setCurrentIndex(idx)
        else:
            self.payment_method.setEditText(o.get("payment_method") or "")

        idx = self.delivery_terms.findText(o.get("delivery_terms") or "")
        if idx >= 0:
            self.delivery_terms.setCurrentIndex(idx)
        else:
            self.delivery_terms.setEditText(o.get("delivery_terms") or "")

        self.delivery_address.setText(o.get("delivery_address") or "")
        self.notes.setPlainText(o.get("notes") or "")
        self._refresh_items_table()

    def _validate(self):
        errors = []
        cust = self.customer.currentData()
        if not cust or cust == "__NEW__":
            errors.append("• Müşteri seçilmelidir")
        if not self._items:
            errors.append("• En az bir sipariş kalemi eklenmelidir")
        if errors:
            QMessageBox.warning(self, "Eksik Bilgi", "\n".join(errors))
            return
        self.accept()

    def get_data(self):
        customer_id = self.customer.currentData()
        return {
            "customer_id": int(customer_id) if customer_id and customer_id != "__NEW__" else None,
            "customer_name": self._customers.get(customer_id, ""),
            "customer_ref": self.customer_ref.text().strip(),
            "currency": self.currency.currentData() or "USD",
            "payment_method": self.payment_method.currentText().strip(),
            "delivery_terms": self.delivery_terms.currentText().strip(),
            "delivery_address": self.delivery_address.text().strip(),
            "delivery_date": self.delivery_date.date().toString("yyyy-MM-dd"),
            "order_date": self.order_date.date().toString("yyyy-MM-dd"),
            "notes": self.notes.toPlainText().strip(),
            "items": self._items,
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
            for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]:
                self.widget.addItem(t, t)
            idx = self.widget.findData(cur or "")
            if idx >= 0:
                self.widget.setCurrentIndex(idx)
        elif field == "print_type":
            self.widget = QComboBox()
            self.widget.addItem("— Seçiniz —", "")
            for t in PRINT_TYPES:
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
        if self.field in ("fabric_type", "entry_location", "print_type"):
            return self.widget.currentData() or ""
        if self.field == "location":
            d = self.depo.currentData() or ""
            return (self.raf.currentData() or "") if d == "__DEPO__" else d
        if self.field in ("meter", "kg", "birim_fiyat"):
            return self.widget.value()
        text = self.widget.text().strip()
        if self.field in ("product_code", "color", "zemin_rengi"):
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
        self._form = form

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

        # Çıkışta kumaş tipi / baskı / renk / lab / parti bilgileri
        if self.movement_type == "ÇIKIŞ":
            self.out_fabric_type = QComboBox()
            self.out_fabric_type.addItem("— Seçiniz —", "")
            for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]:
                self.out_fabric_type.addItem(t, t)
            ft_idx = self.out_fabric_type.findData(fabric["fabric_type"] or "")
            if ft_idx >= 0:
                self.out_fabric_type.setCurrentIndex(ft_idx)

            self.out_print_type = QComboBox()
            self.out_print_type.addItem("— Seçiniz —", "")
            for t in PRINT_TYPES:
                self.out_print_type.addItem(t, t)
            pt_idx = self.out_print_type.findData(dict(fabric).get("print_type") or "")
            if pt_idx >= 0:
                self.out_print_type.setCurrentIndex(pt_idx)

            self.out_color = QLineEdit()
            self.lab_no = QLineEdit()
            self.out_zemin_rengi = QLineEdit()
            self.out_zemin_rengi.setText(dict(fabric).get("zemin_rengi") or "")
            self.out_baski_desen_no = QLineEdit()
            self.out_baski_desen_no.setText(dict(fabric).get("baski_desen_no") or "")
            self.parti_no = QLineEdit()

            form.addRow("Kumaş Tipi:", self.out_fabric_type)
            form.addRow("Baskı Tipi:", self.out_print_type)
            form.addRow("Renk:", self.out_color)
            form.addRow("Zemin Rengi:", self.out_zemin_rengi)
            form.addRow("Lab No:", self.lab_no)
            form.addRow("Baskı Desen No:", self.out_baski_desen_no)
            form.addRow("Parti No:", self.parti_no)

            self.out_fabric_type.currentIndexChanged.connect(self._update_out_print_fields)
            self.out_print_type.currentIndexChanged.connect(self._update_out_print_fields)

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
            self._update_out_print_fields()

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

    def _update_out_print_fields(self):
        """BASKILI / Baskı Tipi seçimine göre Renk, Zemin Rengi, Lab No,
        Baskı Tipi ve Baskı Desen No alanlarının görünürlüğünü ayarlar."""
        is_baskili = self.out_fabric_type.currentData() == "BASKILI"
        pt = self.out_print_type.currentData() if is_baskili else ""
        is_ronjan = pt == "RONJAN"
        for widget, visible in (
            (self.out_print_type, is_baskili),
            (self.out_color, not is_baskili),
            (self.out_zemin_rengi, is_ronjan),
            (self.lab_no, (not is_baskili) or is_ronjan),
            (self.out_baski_desen_no, is_baskili and bool(pt)),
        ):
            label = self._form.labelForField(widget)
            if label:
                label.setVisible(visible)
            widget.setVisible(visible)

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
            "out_fabric_type": "", "out_print_type": "",
            "out_zemin_rengi": "", "out_baski_desen_no": "",
        }
        if self.movement_type == "ÇIKIŞ":
            fabric_type = self.out_fabric_type.currentData() or ""
            is_baskili = fabric_type == "BASKILI"
            print_type = (self.out_print_type.currentData() or "") if is_baskili else ""
            is_ronjan = print_type == "RONJAN"
            d["out_fabric_type"] = fabric_type
            d["out_print_type"] = print_type
            d["out_color"] = self.out_color.text().strip().upper() if not is_baskili else ""
            d["out_zemin_rengi"] = self.out_zemin_rengi.text().strip().upper() if is_ronjan else ""
            d["lab_no"] = self.lab_no.text().strip() if ((not is_baskili) or is_ronjan) else ""
            d["out_baski_desen_no"] = self.out_baski_desen_no.text().strip() if (is_baskili and print_type) else ""
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


TYPE_COLORS = {"GİRİŞ": "#2E7D32", "SATINALMA GİRİŞİ": "#1565C0",
               "ÇIKIŞ": "#C62828", "SİLME": "#880E4F"}


def _fill_movement_table(table, movements, show_product=False):
    """Hareket tablosunu doldur. show_product=True ise ürün sütunu eklenir.
    Sütunlar elle ayarlanabilir, başlıklar taşınabilir, tıklayınca sıralanır."""
    if show_product:
        cols = ["Tarih", "Tür", "Ürün Kodu", "Renk", "Satın Alma Lok.", "Lokasyon", "Metre", "Kilo", "Top/Adet", "Hedef", "Kullanıcı", "Not"]
    else:
        cols = ["Tarih", "Tür", "Metre", "Kilo", "Top/Adet", "Hedef", "Kullanıcı", "Not"]

    table.setColumnCount(len(cols))
    table.setHorizontalHeaderLabels(cols)
    hdr = table.horizontalHeader()
    hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)   # elle genişlik
    hdr.setStretchLastSection(True)
    hdr.setSectionsMovable(True)   # başlıklar sürüklenerek yer değiştirir
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setSortingEnabled(False)   # doldururken kapalı
    table.setRowCount(len(movements))

    for i, m in enumerate(movements):
        m = dict(m)   # sqlite3.Row'da .get yok; dict'e çevirince iki kaynak da çalışır
        col = 0
        def _set(val, align=None, color=None, bold=False, sort_key=None):
            nonlocal col
            text = str(val) if val else ""
            item = _FireSortItem(text)
            if sort_key is not None:
                item.setData(Qt.ItemDataRole.UserRole, sort_key)
            if text:
                item.setToolTip(text)   # sığmayan yazılar üzerine gelince okunur
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
            _set(m.get("entry_location") or "", color="#00695C")   # köken
            # Hareketin yapıldığı lokasyon; eski kayıtlarda kumaşın güncel lokasyonu
            _set(m.get("location") or m.get("fabric_location") or "")
        _set(f"{m['meter']:,.2f}" if m["meter"] else "", sort_key=m["meter"] or 0)
        _set(f"{m['kg']:,.2f}" if m["kg"] else "", sort_key=m["kg"] or 0)
        try:
            piece_key = int(str(m["piece_count"]).strip())
        except (ValueError, TypeError):
            piece_key = -1
        _set(m["piece_count"] or "", sort_key=piece_key)
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

    table.setSortingEnabled(True)   # başlığa tıklayınca sıralar

    # Sütun düzeni (sıra + genişlik) kalıcı: kapatıp açınca aynı kalır
    if not table.property("hdr_wired"):
        from PyQt6.QtCore import QSettings
        key = "mv_header_p" if show_product else "mv_header_s"
        settings = QSettings("BursaKnitted", "DepoTakip")
        st = settings.value(key)
        restored = False
        if st is not None:
            restored = hdr.restoreState(st)
        if not restored:
            table.resizeColumnsToContents()   # kayıt yoksa makul genişlik
        def _save_hdr(*a):
            QSettings("BursaKnitted", "DepoTakip").setValue(key, hdr.saveState())
        hdr.sectionMoved.connect(_save_hdr)
        hdr.sectionResized.connect(_save_hdr)
        table.setProperty("hdr_wired", True)


class MovementsDialog(QDialog):
    """Tek ürünün tüm hareketleri."""
    def __init__(self, parent, fabric):
        super().__init__(parent)
        self.setWindowTitle(f"Tüm Hareketler — {fabric['product_code']} / {fabric['color']}")
        self.setMinimumSize(750, 480)
        layout = QVBoxLayout(self)

        entry = dict(fabric).get("entry_location") or ""
        entry_html = f" — <span style='color:#00695C'>Satın Alma Lok: {entry}</span>" if entry else ""
        info = QLabel(
            f"<b>{fabric['product_name'] or ''} {fabric['product_code']}</b>"
            f" — {fabric['color']} — <span style='color:#545454'>{fabric['location']}</span>"
            f"{entry_html}"
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

        # Hazır aralık butonları (Tümü = kalitenin girişten tükenişe tüm geçmişi)
        presets = QHBoxLayout()
        for label, days in [("Bugün", 0), ("Son 7 Gün", 7), ("Son 15 Gün", 15),
                            ("Son 30 Gün", 30), ("Tümü", None)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _, d=days: self._set_preset(d))
            presets.addWidget(b)
        presets.addStretch()
        layout.addLayout(presets)

        # Filtreler — ürün/lokasyon/tip/tür
        filt = QHBoxLayout()
        filt.addWidget(QLabel("Ara:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Ürün kodu, renk, lot, not, hedef...")
        self.search_box.setMinimumWidth(200)
        self.search_box.textChanged.connect(self._load)
        filt.addWidget(self.search_box)

        filt.addWidget(QLabel("Lokasyon:"))
        self.loc_filter = QComboBox()
        self.loc_filter.addItem("Tümü", "")
        for l in db.get_active_locations():
            self.loc_filter.addItem(l["name"], l["name"])
        self.loc_filter.currentIndexChanged.connect(self._load)
        filt.addWidget(self.loc_filter)

        filt.addWidget(QLabel("Tip:"))
        self.tip_filter = QComboBox()
        self.tip_filter.addItem("Tümü", "")
        for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]:
            self.tip_filter.addItem(t, t)
        self.tip_filter.currentIndexChanged.connect(self._load)
        filt.addWidget(self.tip_filter)

        filt.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", "")
        for t in ["GİRİŞ", "SATINALMA GİRİŞİ", "ÇIKIŞ", "SİLME"]:
            self.tur_filter.addItem(t, t)
        self.tur_filter.currentIndexChanged.connect(self._load)
        filt.addWidget(self.tur_filter)
        filt.addStretch()
        layout.addLayout(filt)

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
        if days is None:   # Tümü — geçmişin tamamı
            self.start_edit.setDate(QDate(2000, 1, 1))
        else:
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
        all_mv = db.get_movements_by_range(start, end)

        # Filtreler
        q   = self.search_box.text().strip().lower()
        loc = self.loc_filter.currentData() or ""
        tip = self.tip_filter.currentData() or ""
        tur = self.tur_filter.currentData() or ""
        movements = []
        for m in all_mv:
            md = dict(m)
            if tur and md["movement_type"] != tur:
                continue
            if loc and (md.get("location") or md.get("fabric_location") or "") != loc:
                continue
            if tip and (md.get("fabric_type") or "") != tip:
                continue
            if q:
                hay = " ".join(str(md.get(k) or "") for k in
                               ("product_code", "product_name", "color", "out_color",
                                "lot", "notes", "destination", "lab_no", "parti_no",
                                "user_name", "entry_location")).lower()
                if q not in hay:
                    continue
            movements.append(m)

        _fill_movement_table(self.table, movements, show_product=True)
        if movements:
            in_m = sum(m["meter"] or 0 for m in movements
                       if m["movement_type"] in ("GİRİŞ", "SATINALMA GİRİŞİ"))
            out_m = sum(m["meter"] or 0 for m in movements if m["movement_type"] == "ÇIKIŞ")
            suffix = f" / toplam {len(all_mv)}" if len(movements) != len(all_mv) else ""
            self.count_lbl.setText(
                f"{len(movements)} hareket{suffix} — Giriş: {in_m:,.0f} mt, Çıkış: {out_m:,.0f} mt"
            )
        else:
            self.count_lbl.setText("Bu kriterlere uyan hareket yok")


COLS = ["#", "Ürün Kodu", "Ürün Açıklaması", "Açıklama", "Renk", "Lokasyon", "Tip", "Lot", "Metre", "Kilo", "Top/Adet", "Birim Fiyat $", "Toplam Değer $", "Son Güncelleme", "Satın Alma Lok.", "Lab No", "Baskı Tipi", "Zemin Rengi", "Baskı Desen No"]
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

    # tuple: 0=id,1=code,2=name,3=desc,4=color,5=loc,6=tip,7=lot,8=mt,9=kg,10=piece,11=fiyat,12=deger,13=date,14=girisLok,15=labNo,16=printType,17=zeminRengi,18=baskiDesenNo
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
                r["description"] or "",
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
                dict(r).get("lab_no") or "",
                dict(r).get("print_type") or "",
                dict(r).get("zemin_rengi") or "",
                dict(r).get("baski_desen_no") or "",
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
        # Sayısal sütunlar: 8=mt, 9=kg, 11=fiyat, 12=değer
        numeric = {8, 9, 11, 12}
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

        # col: 0=#,1=code,2=name,3=desc,4=color,5=loc,6=tip,7=lot,8=mt,9=kg,10=piece,11=fiyat,12=deger,13=date,14=girisLok,15=labNo,16=printType,17=zeminRengi,18=baskiDesenNo
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(row + 1)
            val = r[col]
            if col in (8, 9): return f"{val:.2f}"
            if col == 11: return f"{val:,.2f} $" if val else "—"
            if col == 12: return f"{val:,.2f} $" if val else "—"
            return str(val)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (8, 9, 11, 12):
                return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col in (8, 9):
                return QBrush(_GREY if r[col] == 0 else _GREEN)
            if col == 12 and r[12] > 0:
                return QBrush(QColor("#1A237E"))
            if col == 6:
                return QBrush({"HAM": QColor("#5D4037"),
                                "PFD": QColor("#00695C"),
                                "BOYALI": QColor("#545454"),
                                "İPLİĞİ BOYALI": QColor("#EF6C00"),
                                "BASKILI": QColor("#6A1B9A")}.get(r[6], QColor("#333")))
            if col == 7 and _AUTO_LOT.match(r[7]):
                return QBrush(QColor("#78909C"))

        if role == Qt.ItemDataRole.FontRole:
            if col == 7 and _AUTO_LOT.match(r[7]):
                f = QFont(); f.setItalic(True); return f

        if role == Qt.ItemDataRole.BackgroundRole:
            if row % 2 == 1:
                return QBrush(_ALT)

        if role == Qt.ItemDataRole.ToolTipRole:
            val = r[col]
            if col == 0: return str(row + 1)
            if col in (8, 9): return f"{val:.2f}"
            if col == 11: return f"{val:,.2f} $" if val else "Fiyat girilmemiş"
            if col == 12: return f"{val:,.2f} $" if val else "—"
            if col == 7 and _AUTO_LOT.match(r[7]):
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
        for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]:
            self.type_filter.addItem(t, t)
        self.type_filter.currentIndexChanged.connect(self.refresh)

        btn_add   = QPushButton("+ Yeni Kumaş"); btn_add.clicked.connect(self._add)
        btn_giris = QPushButton("↑ Giriş");      btn_giris.clicked.connect(self._giris)
        btn_cikis = QPushButton("↓ Çıkış");      btn_cikis.clicked.connect(self._cikis)
        btn_edit  = QPushButton("✎ Düzenle");    btn_edit.clicked.connect(self._edit)
        btn_del   = QPushButton("✕ Sil");        btn_del.clicked.connect(self._delete)
        btn_hist  = QPushButton("☰ Hareketler"); btn_hist.clicked.connect(self._history)
        btn_hist.setToolTip("Tüm hareketler — tarih aralığı ve filtrelerle\nSatır seçiliyse o ürünün geçmişi hazır gelir")

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

        # Başlangıç genişlikleri (kayıtlı sütun düzeni yoksa kullanılır)
        col_widths = [36, 100, 130, 160, 110, 90, 70, 90, 72, 65, 80, 110, 120, 130, 220, 90, 90, 90, 100]
        def _default_widths():
            for i, w in enumerate(col_widths):
                self.table.setColumnWidth(i, w)
        _wire_header_persistence(self.table, "stock_header", _default_widths)

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

        # ── Seçili Satırın Ürün Bilgisi (katalogdan) ──
        self._product_info_bar = QFrame()
        self._product_info_bar.setStyleSheet(
            "QFrame { background:#E3F2FD; border-radius:6px;"
            "border: 1px solid #BBDEFB; padding:0; }"
        )
        self._product_info_bar.setFixedHeight(34)
        pi_layout = QHBoxLayout(self._product_info_bar)
        pi_layout.setContentsMargins(16, 2, 16, 2)
        self._product_info_lbl = QLabel("Ürün bilgisi için bir satır seçin")
        self._product_info_lbl.setStyleSheet("color:#1565C0; font-size:12px;")
        pi_layout.addWidget(self._product_info_lbl)
        pi_layout.addStretch()
        layout.addWidget(self._product_info_bar)

        self.table.selectionModel().currentRowChanged.connect(self._on_row_selected)

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

    def _on_row_selected(self, current, previous):
        if not current.isValid() or current.row() >= len(self._model._rows):
            self._product_info_lbl.setText("Ürün bilgisi için bir satır seçin")
            return
        code = self._model._rows[current.row()][1]
        product = db.get_product_by_code(code)
        if not product:
            self._product_info_lbl.setText(f"{code}   —   (katalogda kayıt bulunamadı)")
            return
        p = dict(product)
        parts = [
            code,
            p.get('composition') or '—',
            p.get('width') or '—',
            p.get('gramaj') or '—',
            p.get('reference_code') or '—',
            p.get('supplier') or '—',
        ]
        self._product_info_lbl.setText("   |   ".join(parts))

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
        if db.is_fabric_linked_to_order(fid):
            QMessageBox.warning(self, "Düzenlenemez",
                "Bu kumaş bir sipariş satınalmasına bağlıdır.\n"
                "Stok listesinden düzenlenemez; değişiklik için planlama ekranını kullanın.")
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
        if db.is_fabric_linked_to_order(fid):
            QMessageBox.warning(self, "Silinemez",
                "Bu kumaş bir sipariş satınalmasına bağlıdır.\n"
                "Stok listesinden silinemez; işlem için planlama ekranını kullanın.")
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
                                  parti_no=d["parti_no"],
                                  out_fabric_type=d["out_fabric_type"],
                                  out_print_type=d["out_print_type"],
                                  out_zemin_rengi=d["out_zemin_rengi"],
                                  out_baski_desen_no=d["out_baski_desen_no"])
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
    CELL_FIELDS = {1: "product_code", 2: "product_name", 3: "description", 4: "color",
                   5: "location", 6: "fabric_type", 7: "lot", 8: "meter", 9: "kg",
                   10: "piece_count", 11: "birim_fiyat", 14: "entry_location", 15: "lab_no",
                   16: "print_type", 17: "zemin_rengi", 18: "baski_desen_no"}

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
                  "piece_count", "birim_fiyat", "fabric_type", "lot", "description", "lab_no",
                  "print_type", "zemin_rengi", "baski_desen_no")}
            d[field] = dlg.value()
            db.update_fabric(fid, **d)
            self.refresh_with_locations()

    def _history(self):
        dlg = DailyMovementsDialog(self)
        idx = self.table.selectionModel().currentIndex()
        if idx.isValid():
            fid = self._model.id_at(idx.row())
            if fid:
                fabric = db.get_fabric(fid)
                # Seçili ürünün tüm geçmişi hazır gelsin; filtreler değiştirilebilir
                dlg.search_box.setText(fabric["product_code"] or "")
                dlg._set_preset(None)
        dlg.exec()

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
                    "piece_count", "birim_fiyat", "fabric_type", "lot", "description", "lab_no",
                    "print_type", "zemin_rengi", "baski_desen_no")
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


class OrdersView(QWidget):
    """Satış siparişleri listesi — yeni sipariş açıldığında
    status='PLANLAMA BEKLİYOR' ile kaydedilir (planlama ekranı sonraki aşama)."""

    COLS = ["Sipariş No", "Sip. Tarihi", "Müşteri", "Müşteri Referans", "Kalem",
            "Para Birimi", "Toplam Tutar", "Termin", "Ödeme Şekli",
            "Teslimat Şartları", "Durum", "Oluşturan",
            "Baskı Tipi", "Zemin Rengi", "Baskı Desen No",
            "Teslimat Adresi", "Notlar"]

    # Kalem (alt) satırları, üst satırla aynı sütunları farklı anlamlarla
    # kullanır — her siparişin kalemlerinden önce bu etiket satırı gösterilir.
    ITEM_COL_LABELS = ["Ürün Kodu", "Kompozisyon", "En", "Gramaj", "Kumaş Tipi", "Renk",
                       "Lab No", "Açıklama", "Metre", "Kilo", "Birim Fiyat", "Tutar",
                       "Baskı Tipi", "Zemin Rengi", "Baskı Desen No", "", ""]

    STATUS_OPTIONS = [
        "ONAYDA", "ONAYLANDI - PLANLAMADA", "PLANLAMA - GÖRDÜ", "PLANLANDI",
        "BOYAHANAYA SEVKLER BAŞLADI", "TÜM KUMAŞLAR BOYAHANEDE",
        "MÜŞTERİYE SEVKLER BAŞLADI", "SİPARİŞ TAMAMLANDI", "İPTAL",
    ]

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
        self.search_box.setPlaceholderText("Sipariş no, ürün kodu, müşteri, renk...")
        self.search_box.setMaximumWidth(260)
        self.search_box.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_box)

        toolbar.addWidget(QLabel("Durum:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tümü", "")
        for s in self.STATUS_OPTIONS:
            self.status_filter.addItem(s, s)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        toolbar.addStretch()
        btn_new = QPushButton("+ Yeni Sipariş")
        btn_new.setStyleSheet("background:#2E7D32;color:white;font-weight:bold;border-radius:4px;padding:6px 14px;")
        btn_new.clicked.connect(self._new_order)
        btn_del = QPushButton("✕ Sil")
        btn_del.setStyleSheet("background:#757575;color:white;border-radius:4px;padding:6px 14px;")
        btn_del.clicked.connect(self._delete_order)
        btn_pdf = QPushButton("📄 PDF Al")
        btn_pdf.clicked.connect(self._export_pdf)
        btn_refresh = QPushButton("⟳ Yenile")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_new)
        if CURRENT_USER.get("role") == "admin":
            btn_settings = QPushButton("🏦 Şirket/Banka Ayarları")
            btn_settings.clicked.connect(self._company_settings)
            toolbar.addWidget(btn_settings)
        toolbar.addWidget(btn_del)
        toolbar.addWidget(btn_pdf)
        toolbar.addWidget(btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTreeWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHeaderLabels(self.COLS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setRootIsDecorated(True)
        self.table.setExpandsOnDoubleClick(False)
        hdr = self.table.header()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        hdr.setSectionsMovable(True)
        self.table.doubleClicked.connect(self._edit_order)
        self.table.setStyleSheet(
            "QTreeWidget::item { border: 1px solid #E0E0E0; padding: 3px; }"
            "QTreeWidget::item:has-children { background-color: #E8EAF6; font-weight: bold;"
            " border-top: 2px solid #9FA8DA; padding-top: 5px; padding-bottom: 5px; }"
            "QTreeWidget::item:selected { background-color: #BBDEFB; color: #212121; }"
            "QTreeWidget::item:selected:has-children { background-color: #9FA8DA; color: #212121; }"
        )

        layout.addWidget(self.table)
        _wire_header_persistence(self.table, "orders_columns")

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#555; font-size:12px;")
        layout.addWidget(self.count_lbl)

    def refresh(self):
        search = self.search_box.text().strip()
        status = self.status_filter.currentData() or ""
        rows = [dict(r) for r in db.get_all_orders(search=search, status=status)]
        self._rows = rows
        self.table.clear()
        for r in rows:
            currency = r.get("currency") or "USD"
            symbol = CURRENCY_SYMBOLS.get(currency, "$")
            item_count = r.get("item_count") or 0
            total_amount = r.get("total_amount") or 0
            vals = [
                r.get("order_no") or "",
                str(r.get("order_date") or "")[:10],
                r.get("customer_name") or "",
                r.get("customer_ref") or "",
                f"{item_count} kalem",
                currency,
                f"{total_amount:,.2f} {symbol}",
                str(r.get("delivery_date") or "")[:10],
                r.get("payment_method") or "",
                r.get("delivery_terms") or "",
                r.get("status") or "",
                r.get("created_by") or "",
                "", "", "",
                r.get("delivery_address") or "",
                (r.get("notes") or "").replace("\n", " "),
            ]
            order_item = QTreeWidgetItem([str(v) for v in vals])
            order_item.setData(0, Qt.ItemDataRole.UserRole, r["id"])
            order_item.setTextAlignment(4, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight))
            order_item.setTextAlignment(6, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight))
            self.table.addTopLevelItem(order_item)

            items = r.get("items") or []
            if items:
                legend = QTreeWidgetItem([str(v) for v in self.ITEM_COL_LABELS])
                legend.setFlags(legend.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                legend_font = QFont(); legend_font.setItalic(True); legend_font.setPointSize(8)
                for col in range(len(self.ITEM_COL_LABELS)):
                    legend.setFont(col, legend_font)
                    legend.setForeground(col, QBrush(QColor("#9E9E9E")))
                order_item.addChild(legend)

            for it in items:
                meter = it.get("meter") or 0
                kg = it.get("kg") or 0
                sale_price = it.get("sale_price") or 0
                total = meter * sale_price
                child_vals = [
                    it.get("product_code") or "",
                    it.get("composition") or "",
                    it.get("width") or "",
                    it.get("gramaj") or "",
                    it.get("fabric_type") or "",
                    it.get("color") or "",
                    it.get("lab_no") or "",
                    it.get("description") or "",
                    f"{meter:,.2f}",
                    f"{kg:,.2f}",
                    f"{sale_price:,.2f} {symbol}",
                    f"{total:,.2f} {symbol}",
                    it.get("print_type") or "",
                    it.get("zemin_rengi") or "",
                    it.get("baski_desen_no") or "",
                    "", "",
                ]
                child = QTreeWidgetItem([str(v) for v in child_vals])
                for col in (8, 9, 10, 11):
                    child.setTextAlignment(col, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight))
                order_item.addChild(child)

        self.table.expandAll()
        self.count_lbl.setText(f"{len(rows)} sipariş")

    def _new_order(self):
        dlg = OrderDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            oid, order_no = db.add_order(**data, created_by=CURRENT_USER["full_name"])
            self.refresh()
            QMessageBox.information(self, "Sipariş Oluşturuldu",
                f"Sipariş kaydedildi.\n\nSipariş No: {order_no}\nDurum: ONAYDA\n\nAdmin onayı bekleniyor.")

    def _selected_id(self):
        item = self.table.currentItem()
        oid = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if oid is None and item is not None and item.parent() is not None:
            oid = item.parent().data(0, Qt.ItemDataRole.UserRole)
        if oid is None:
            QMessageBox.information(self, "Bilgi", "Önce bir sipariş seçin.")
            return None
        return oid

    def _edit_order(self):
        oid = self._selected_id()
        if not oid:
            return
        order = db.get_order(oid)
        if not order:
            return
        dlg = OrderDialog(self, order=order)
        if dlg.exec():
            data = dlg.get_data()
            db.update_order(oid, **data)
            self.refresh()

    def _delete_order(self):
        if CURRENT_USER.get("role") != "admin":
            QMessageBox.warning(self, "Yetersiz Yetki",
                "Sipariş silme işlemi yalnızca admin tarafından yapılabilir.")
            return
        oid = self._selected_id()
        if not oid:
            return
        order = db.get_order(oid)
        if not order:
            return
        status = order.get("status","")
        if status not in ("ONAYDA", "İPTAL"):
            QMessageBox.warning(self, "Silinemez",
                f"Bu sipariş şu an '{status}' durumunda.\n\n"
                "Silebilmek için siparişin önce İPTAL edilmesi gerekir.")
            return
        if QMessageBox.question(self, "Sil",
                f"{order.get('order_no','')} numaralı sipariş kalıcı olarak silinsin mi?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            db.delete_order(oid)
            self.refresh()

    def _export_pdf(self):
        oid = self._selected_id()
        if not oid:
            return
        order = db.get_order(oid)
        if not order:
            return
        order = {**order, "customer_tax_no": _customer_tax_no(order.get("customer_id"))}
        company = db.get_company_settings()
        default_name = f"{order['order_no']}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Sipariş Sözleşmesi PDF", default_name, "PDF (*.pdf)")
        if not path:
            return
        try:
            order_pdf.generate_order_pdf(order, company, path)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturulamadı:\n{e}")
            return
        QMessageBox.information(self, "PDF Oluşturuldu", f"Kaydedildi:\n{path}")

    def _company_settings(self):
        if CURRENT_USER.get("role") != "admin":
            QMessageBox.warning(self, "Yetki", "Bu işlem için yönetici yetkisi gereklidir.")
            return
        CompanySettingsDialog(self).exec()


PO_STATUS_OPTIONS = ["BEKLEMEDE", "GÖNDERİLDİ", "KISMİ GELDİ", "TAMAMLANDI", "İPTAL"]


class PurchaseOrderDialog(QDialog):
    """Kalem bazında tedarikçi + kumaş tipi seçimli PO oluşturma."""
    FABRIC_TYPES = ["HAM", "PFD", "Boyalı", "Baskılı", "Mamül", "Diğer"]
    PAYMENT_METHODS = ["Peşin", "Havale/EFT", "30 Gün Vade", "60 Gün Vade",
                       "90 Gün Vade", "120 Gün Vade", "Akreditif (L/C)", "Diğer"]
    # col: 0=Ürün Kodu, 1=Ürün Adı, 2=Kumaş Tipi(w), 3=Tedarikçi(w),
    #      4=Para Birimi(w), 5=Sip.Mt(ro), 6=Ham Sip.Mt(+%20),
    #      7=Sip.Kg(ro), 8=Ham Kg(+%20), 9=Birim Fiyat,
    #      10=Toplam(ro), 11=Ödeme Şekli(w), 12=Teslimat Şekli,
    #      13=Termin, 14=Notlar, 15=Açıklama
    ITEM_COLS = [
        "Ürün Kodu", "Ürün Adı", "Kumaş Tipi", "Tedarikçi", "Para Birimi",
        "Sip. Mt", "Ham Sip. Mt (+%20)", "Sip. Kg", "Ham Kg (+%20)",
        "Birim Fiyat", "Toplam", "Ödeme Şekli",
        "Teslimat Şekli", "Termin", "Notlar", "Açıklama",
    ]
    _READONLY_COLS = {5, 7, 10}  # Sip.Mt, Sip.Kg, Toplam

    def __init__(self, parent=None, missing_items=None, po=None):
        super().__init__(parent)
        self.setWindowTitle("Satınalma Siparişi Oluştur")
        self.setMinimumSize(1400, 520)
        self._suppliers = []
        self._build_ui()
        self._reload_suppliers()
        if missing_items:
            self._fill_items(missing_items)

    def _build_ui(self):
        lay = QVBoxLayout(self)

        hint = QLabel(
            "<i>Her kalem için kumaş tipi, tedarikçi ve para birimi ayrı seçilebilir. "
            "Aynı tedarikçiye ait kalemler otomatik aynı PO'ya eklenir. "
            "Sip. Mt/Kg referans; Ham değerler %20 artışlı önerilen miktardır.</i>"
        )
        hint.setStyleSheet("color:#757575;font-size:11px;"); hint.setWordWrap(True)
        lay.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.ITEM_COLS))
        self.table.setHorizontalHeaderLabels(self.ITEM_COLS)
        self.table.verticalHeader().setVisible(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.cellChanged.connect(self._on_cell_changed)
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        b_add = QPushButton("+ Kalem Ekle"); b_add.clicked.connect(self._copy_row)
        b_del = QPushButton("✕ Kalem Kaldır"); b_del.clicked.connect(self._del_row)
        btn_row.addWidget(b_add); btn_row.addWidget(b_del)
        btn_row.addStretch()
        self._subtotal_lbl = QLabel()
        self._subtotal_lbl.setStyleSheet("font-weight:bold;color:#1565C0;")
        btn_row.addWidget(self._subtotal_lbl)
        lay.addLayout(btn_row)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _reload_suppliers(self):
        self._suppliers = db.get_all_suppliers()
        for row in range(self.table.rowCount()):
            sup_cb = self.table.cellWidget(row, 3)
            if isinstance(sup_cb, QComboBox):
                prev = sup_cb.currentData()
                self._fill_supplier_combo(sup_cb, select_data=prev)

    def _fill_supplier_combo(self, cb, select_data=None):
        cb.blockSignals(True)
        cb.clear()
        cb.addItem("— Tedarikçi —", None)
        for s in self._suppliers:
            label = s["name"] + (f" ({s['code']})" if s.get("code") else "")
            cb.addItem(label, (s["id"], s["name"]))
        if select_data:
            for i in range(cb.count()):
                if cb.itemData(i) == select_data:
                    cb.setCurrentIndex(i); break
        cb.blockSignals(False)

    def _fill_items(self, items):
        self.table.setRowCount(0)
        for item in items:
            self._insert_row(item)

    def _insert_row(self, item=None):
        item = item or {}
        row = self.table.rowCount()
        self.table.blockSignals(True)
        self.table.insertRow(row)

        # col 2: Kumaş Tipi combo
        ft_cb = QComboBox()
        for ft in self.FABRIC_TYPES:
            ft_cb.addItem(ft, ft)
        idx = ft_cb.findData(item.get("fabric_type", "HAM") or "HAM")
        if idx >= 0: ft_cb.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, ft_cb)

        # col 3: Tedarikçi combo
        sup_cb = QComboBox()
        self._fill_supplier_combo(sup_cb, select_data=item.get("_supplier_data"))
        self.table.setCellWidget(row, 3, sup_cb)

        # col 4: Para Birimi combo
        cur_cb = QComboBox()
        for code in CURRENCY_OPTIONS:
            cur_cb.addItem(f"{code} ({CURRENCY_SYMBOLS[code]})", code)
        preset_cur = item.get("currency") or "USD"
        ci = cur_cb.findData(preset_cur)
        if ci >= 0: cur_cb.setCurrentIndex(ci)
        cur_cb.currentIndexChanged.connect(lambda _, r=row: self._recalc_row(r))
        self.table.setCellWidget(row, 4, cur_cb)

        # col 11: Ödeme Şekli combo
        pay_cb = QComboBox()
        pay_cb.setEditable(True)
        pay_cb.addItem("")
        for p in self.PAYMENT_METHODS:
            pay_cb.addItem(p)
        preset_pay = item.get("payment_method", "")
        pi = pay_cb.findText(preset_pay)
        if pi >= 0: pay_cb.setCurrentIndex(pi)
        else: pay_cb.setEditText(preset_pay)
        self.table.setCellWidget(row, 11, pay_cb)

        orig_meter = float(item.get("meter") or 0)
        orig_kg    = float(item.get("kg") or 0)
        ham_meter  = item.get("ham_meter")
        ham_kg     = item.get("ham_kg")
        if ham_meter is None: ham_meter = round(orig_meter * 1.20, 2)
        if ham_kg    is None: ham_kg    = round(orig_kg    * 1.20, 2)
        termin = item.get("termin") or QDate.currentDate().addDays(30).toString("dd.MM.yyyy")

        text_vals = {
            0:  str(item.get("product_code", "")),
            1:  str(item.get("product_name", "")),
            5:  str(orig_meter),   # Sip. Mt  (readonly)
            6:  str(ham_meter),    # Ham Sip. Mt
            7:  str(orig_kg),      # Sip. Kg  (readonly)
            8:  str(ham_kg),       # Ham Kg
            9:  str(item.get("unit_price") or "0"),
            10: "0.00",            # Toplam   (readonly, calculated)
            12: str(item.get("delivery_terms", "")),
            13: termin,
            14: str(item.get("notes", "")),
            15: str(item.get("description", "")),
        }
        for col, val in text_vals.items():
            cell = QTableWidgetItem(str(val))
            if col in self._READONLY_COLS:
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                cell.setBackground(QBrush(QColor("#F5F5F5")))
            self.table.setItem(row, col, cell)

        self.table.blockSignals(False)
        self._recalc_row(row)
        self._update_subtotal()

    def _recalc_row(self, row):
        try:
            m  = float((self.table.item(row, 6) or QTableWidgetItem("0")).text() or 0)
            up = float((self.table.item(row, 9) or QTableWidgetItem("0")).text() or 0)
            total = m * up
        except (ValueError, AttributeError):
            total = 0.0
        cur_cb = self.table.cellWidget(row, 4)
        sym = ""
        if isinstance(cur_cb, QComboBox):
            sym = CURRENCY_SYMBOLS.get(cur_cb.currentData(), "")
        self.table.blockSignals(True)
        cell = self.table.item(row, 10)
        if not cell:
            cell = QTableWidgetItem()
            cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            cell.setBackground(QBrush(QColor("#F5F5F5")))
            self.table.setItem(row, 10, cell)
        cell.setText(f"{sym}{total:,.2f}")
        self.table.blockSignals(False)
        self._update_subtotal()

    def _update_subtotal(self):
        total_mt = 0.0; total_kg = 0.0
        for r in range(self.table.rowCount()):
            try: total_mt += float((self.table.item(r, 6) or QTableWidgetItem("0")).text() or 0)
            except ValueError: pass
            try: total_kg += float((self.table.item(r, 8) or QTableWidgetItem("0")).text() or 0)
            except ValueError: pass
        self._subtotal_lbl.setText(
            f"Alt Toplam:  {total_mt:,.2f} mt  |  {total_kg:,.2f} kg")

    def _on_cell_changed(self, row, col):
        if col in (6, 8, 9):
            self._recalc_row(row)
        if col in (6, 8):
            self._update_subtotal()

    def _copy_row(self):
        """Seçili satırı kopyala; seçili satır yoksa son satırı kopyala."""
        src = self.table.currentRow()
        if src < 0:
            src = self.table.rowCount() - 1
        if src < 0:
            self._insert_row()
            return

        def _txt(c):
            it = self.table.item(src, c)
            return it.text() if it else ""

        ft_cb  = self.table.cellWidget(src, 2)
        sup_cb = self.table.cellWidget(src, 3)
        cur_cb = self.table.cellWidget(src, 4)
        pay_cb = self.table.cellWidget(src, 11)
        item = {
            "product_code":   _txt(0),
            "product_name":   _txt(1),
            "fabric_type":    ft_cb.currentData()  if isinstance(ft_cb, QComboBox)  else "HAM",
            "_supplier_data": sup_cb.currentData() if isinstance(sup_cb, QComboBox) else None,
            "currency":       cur_cb.currentData() if isinstance(cur_cb, QComboBox) else "USD",
            "meter":          float(_txt(5) or 0),
            "ham_meter":      _txt(6),
            "kg":             float(_txt(7) or 0),
            "ham_kg":         _txt(8),
            "unit_price":     _txt(9),
            "payment_method": pay_cb.currentText() if isinstance(pay_cb, QComboBox) else _txt(11),
            "delivery_terms": _txt(12),
            "termin":         _txt(13),
            "notes":          _txt(14),
            "description":    _txt(15),
        }
        self._insert_row(item)

    def _del_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _validate(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Eksik Bilgi", "En az bir kalem eklenmelidir.")
            return
        for row in range(self.table.rowCount()):
            sup_cb = self.table.cellWidget(row, 3)
            if not isinstance(sup_cb, QComboBox) or not isinstance(sup_cb.currentData(), tuple):
                QMessageBox.warning(self, "Eksik Bilgi",
                    f"Kalem {row+1} için tedarikçi seçilmelidir.")
                return
            try:
                it = self.table.item(row, 6)  # Ham Sip. Mt
                if float(it.text() if it else "0") <= 0:
                    QMessageBox.warning(self, "Eksik Bilgi",
                        f"Kalem {row+1} için geçerli Ham Sip. Metresi girilmelidir.")
                    return
            except ValueError:
                QMessageBox.warning(self, "Geçersiz Değer",
                    f"Kalem {row+1} için sayısal metre giriniz.")
                return
        self.accept()

    def get_data(self):
        """Tedarikçiye göre gruplu PO listesi döner."""
        def _cell(row, col):
            it = self.table.item(row, col)
            return it.text().strip() if it else ""
        def _num(row, col):
            try: return float(_cell(row, col) or 0)
            except ValueError: return 0.0

        items_by_supplier = {}
        headers_by_supplier = {}
        for row in range(self.table.rowCount()):
            sup_cb = self.table.cellWidget(row, 3)
            ft_cb  = self.table.cellWidget(row, 2)
            cur_cb = self.table.cellWidget(row, 4)
            pay_cb = self.table.cellWidget(row, 11)
            sup_data = sup_cb.currentData() if isinstance(sup_cb, QComboBox) else None
            if not isinstance(sup_data, tuple):
                continue
            sid, sname = sup_data
            ft       = ft_cb.currentData()  if isinstance(ft_cb,  QComboBox) else "HAM"
            currency = cur_cb.currentData() if isinstance(cur_cb, QComboBox) else "USD"
            pay_meth = pay_cb.currentText() if isinstance(pay_cb, QComboBox) else _cell(row, 11)

            # Termin: dd.MM.yyyy → yyyy-MM-dd
            termin_raw = _cell(row, 13)
            try:
                from datetime import datetime as _dtt
                termin = _dtt.strptime(termin_raw, "%d.%m.%Y").strftime("%Y-%m-%d")
            except Exception:
                termin = termin_raw

            key = (sid, sname)
            if key not in headers_by_supplier:
                headers_by_supplier[key] = {
                    "currency":          currency,
                    "payment_method":    pay_meth,
                    "delivery_terms":    _cell(row, 12),
                    "expected_delivery": termin,
                    "notes":             _cell(row, 14),
                }
            if key not in items_by_supplier:
                items_by_supplier[key] = []
            items_by_supplier[key].append({
                "product_code": _cell(row, 0),
                "product_name": _cell(row, 1),
                "fabric_type":  ft,
                "meter":        _num(row, 6),   # Ham Sip. Mt
                "kg":           _num(row, 8),   # Ham Kg
                "unit_price":   _num(row, 9),
                "description":  _cell(row, 15),
                "composition":  "",
                "width":        "",
                "gramaj":       "",
            })
        return {
            "po_groups": [
                {
                    "supplier_id":   k[0],
                    "supplier_name": k[1],
                    "items":         items_by_supplier[k],
                    **headers_by_supplier.get(k, {}),
                }
                for k in items_by_supplier
            ],
        }


class ItemReceiptDialog(QDialog):
    """Tek PO kalemine mal girişi: metre, kilo, lot, lokasyon."""
    def __init__(self, parent=None, po_item=None):
        super().__init__(parent)
        self.po_item = po_item or {}
        it = self.po_item
        self.setWindowTitle(
            f"Mal Girişi — {it.get('product_code','')} / {it.get('fabric_type','')}")
        self.setMinimumWidth(440)
        self._build_ui()

    def _build_ui(self):
        import datetime as _dt
        lay = QVBoxLayout(self)
        it = self.po_item
        remaining = max(0.0, (it.get("meter") or 0) - (it.get("received_meter") or 0))
        info_lbl = QLabel(
            f"<b>Ürün Kodu:</b> {it.get('product_code','')}  "
            f"<b>Kumaş:</b> {it.get('fabric_type','')}  |  "
            f"<b>Sipariş:</b> {it.get('meter',0):.2f} mt / {it.get('kg',0):.2f} kg  |  "
            f"<b>Kalan:</b> {remaining:.2f} mt"
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("background:#F5F5F5;padding:6px;border-radius:4px;")
        lay.addWidget(info_lbl)

        form = QFormLayout(); form.setSpacing(10)
        self.metre = QDoubleSpinBox()
        self.metre.setRange(0, 9_999_999); self.metre.setDecimals(2)
        self.metre.setSuffix(" mt"); self.metre.setValue(remaining)
        self.kilo = QDoubleSpinBox()
        self.kilo.setRange(0, 9_999_999); self.kilo.setDecimals(2)
        self.kilo.setSuffix(" kg")

        ft_short = (it.get("fabric_type") or "HAM").split()[0][:3].upper()
        date_str = _dt.date.today().strftime("%Y%m%d")
        self.lot = QLineEdit()
        self.lot.setPlaceholderText(f"Boş bırakılırsa otomatik: {ft_short}-{date_str}-001")

        self.location = QComboBox()
        self.location.addItem("— Lokasyon Seçiniz —", ("", ""))
        for loc in db.get_active_locations():
            grp = loc.get("group_name","")
            self.location.addItem(f"[{grp}]  {loc['name']}", (loc["name"], grp))
        self._routing_lbl = QLabel()
        self._routing_lbl.setStyleSheet("color:#1565C0;font-style:italic;font-size:11px;")
        self.location.currentIndexChanged.connect(self._update_routing)

        form.addRow("Gelen Metre:", self.metre)
        form.addRow("Gelen Kilo:", self.kilo)
        form.addRow("Lot No:", self.lot)
        form.addRow("Lokasyon:", self.location)
        form.addRow("", self._routing_lbl)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _update_routing(self):
        data = self.location.currentData()
        if not data or not data[0]:
            self._routing_lbl.setText(""); return
        _, grp = data
        if grp == "DEPO":
            self._routing_lbl.setText("→ Ana depoya giriş (Boyahane planlamasına gelmez)")
        else:
            self._routing_lbl.setText("→ Dış depoya giriş — Boyahane planlama ekranına düşecek")

    def _validate(self):
        data = self.location.currentData()
        if not data or not data[0]:
            QMessageBox.warning(self, "Eksik", "Lokasyon seçilmelidir."); return
        if self.metre.value() <= 0 and self.kilo.value() <= 0:
            QMessageBox.warning(self, "Eksik", "Gelen metre veya kilo girilmelidir."); return
        self.accept()

    def get_data(self):
        loc_name, grp = self.location.currentData()
        return {"metre": self.metre.value(), "kilo": self.kilo.value(),
                "lot": self.lot.text().strip(),
                "location": loc_name, "location_group": grp}


class GoodsReceiptDialog(QDialog):
    def __init__(self, parent=None, po=None):
        super().__init__(parent)
        self.po = po
        self.setWindowTitle(f"Mal Girişi — {po.get('po_no','')}")
        self.resize(780, 400)
        self._item_ids = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        items = self.po.get("items", [])

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Kodu", "Kumaş Tipi", "Sipariş Mt", "Sipariş Kg",
             "Gelen Metre", "Gelen Kilo"])
        self.table.setRowCount(len(items))
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        hdr = self.table.horizontalHeader()
        hdr.setSectionsMovable(True)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        for row, it in enumerate(items):
            self._item_ids.append(it["id"])
            for col, val in enumerate([
                it.get("product_code",""), it.get("fabric_type","HAM"),
                f"{it.get('meter',0):.2f}", f"{it.get('kg',0):.2f}",
                "0", "0",
            ]):
                cell = QTableWidgetItem(val)
                if col < 4:
                    cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    cell.setBackground(QBrush(QColor("#F5F5F5")))
                self.table.setItem(row, col, cell)
        lay.addWidget(self.table)

        form = QFormLayout(); form.setSpacing(8)
        self.location = QComboBox()
        self.location.addItem("— Lokasyon Seçiniz —", "")
        for loc in db.get_active_locations():
            if loc["group_name"] == "DEPO":
                self.location.addItem(loc["name"], loc["name"])
        form.addRow("DEPO Lokasyonu *:", self.location)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.location.currentData():
            QMessageBox.warning(self, "Eksik Bilgi", "DEPO lokasyonu seçilmelidir.")
            return
        self.accept()

    def get_data(self):
        results = []
        for row in range(self.table.rowCount()):
            try:
                m = float(self.table.item(row, 4).text() or 0)
            except (ValueError, AttributeError):
                m = 0.0
            try:
                k = float(self.table.item(row, 5).text() or 0)
            except (ValueError, AttributeError):
                k = 0.0
            results.append({"item_id": self._item_ids[row], "meter": m, "kg": k})
        return {"location": self.location.currentData(), "items": results}


class PlanningView(QWidget):
    _PLANNING_STATUSES = [
        "ONAYDA", "ONAYLANDI - PLANLAMADA", "PLANLAMA - GÖRDÜ",
        "PLANLANDI", "BOYAHANAYA SEVKLER BAŞLADI", "TÜM KUMAŞLAR BOYAHANEDE",
    ]
    _STATUS_COLORS = {
        "ONAYDA":                    "#B71C1C",
        "ONAYLANDI - PLANLAMADA":    "#E65100",
        "PLANLAMA - GÖRDÜ":          "#F57F17",
        "PLANLANDI":                 "#1565C0",
        "BOYAHANAYA SEVKLER BAŞLADI":"#6A1B9A",
        "TÜM KUMAŞLAR BOYAHANEDE":  "#2E7D32",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_order_id = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("<b>📌 Planlama Modülü</b>"))
        top.addStretch()
        btn_ref = QPushButton("🔄 Yenile"); btn_ref.clicked.connect(self.refresh)
        top.addWidget(btn_ref)
        lay.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(splitter)

        # ── Sol: Kuyruk ──────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 4, 0)
        ll.addWidget(QLabel("<b>Aktif Planlamalar</b>"))
        self._pending_lbl = QLabel()
        self._pending_lbl.setStyleSheet(
            "background:#B71C1C;color:white;font-weight:bold;"
            "padding:4px 8px;border-radius:4px;")
        self._pending_lbl.setVisible(False)
        ll.addWidget(self._pending_lbl)
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(
            ["Sipariş No", "Müşteri", "Termin", "Ürün Kodu", "Durum"])
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setSortingEnabled(True)
        qhdr = self.queue_table.horizontalHeader()
        qhdr.setSectionsMovable(True)
        qhdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        qhdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        qhdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        qhdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        qhdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.itemSelectionChanged.connect(self._on_queue_select)
        ll.addWidget(self.queue_table)

        # Admin onay butonu
        self._btn_approve = QPushButton("✅ Seçili Siparişi Onayla")
        self._btn_approve.setStyleSheet(
            "background:#1B5E20;color:white;font-weight:bold;"
            "border-radius:4px;padding:5px 10px;")
        self._btn_approve.clicked.connect(self._approve_order)
        self._btn_approve.setVisible(CURRENT_USER.get("role") == "admin")
        ll.addWidget(self._btn_approve)
        splitter.addWidget(left)

        # ── Sağ: Detay (scroll) ──────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(4, 0, 0, 8)
        scroll.setWidget(right)

        # Sipariş bilgileri
        self._order_group = QGroupBox("📋 Sipariş Bilgileri")
        self._order_group.setVisible(False)
        og = QGridLayout(self._order_group); og.setSpacing(6)
        self._info = {}
        fields = [
            ("order_no", "Sipariş No"), ("order_date", "Sipariş Tarihi"),
            ("customer_name", "Müşteri"), ("customer_ref", "Müşteri Ref."),
            ("currency", "Para Birimi"), ("payment_method", "Ödeme Şekli"),
            ("delivery_terms", "Teslimat Şartları"), ("delivery_date", "Termin"),
            ("delivery_address", "Teslimat Adresi"), ("notes", "Notlar"),
            ("status", "Durum"),
        ]
        for i, (key, lbl) in enumerate(fields):
            col_base = (i % 2) * 2
            row_g = i // 2
            og.addWidget(QLabel(f"<b>{lbl}:</b>"), row_g, col_base)
            val_lbl = QLabel()
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            og.addWidget(val_lbl, row_g, col_base + 1)
            self._info[key] = val_lbl
        og.setColumnStretch(1, 1)
        og.setColumnStretch(3, 1)
        rl.addWidget(self._order_group)

        # Ham dokuma ihtiyaç tablosu
        rl.addWidget(QLabel("<b>Ham Dokuma İhtiyaç Tablosu</b>"))
        self.need_table = QTableWidget()
        _NEED_COLS = [
            "Seç", "Ürün Kodu", "Ürün Adı", "Kumaş Tipi", "Renk",
            "Kompozisyon", "En", "Gramaj", "Lab No", "Baskı Tipi",
            "Zemin Rengi", "Baskı Desen No", "Sip. Mt", "Sip. Kg",
            "Satış Fiyatı", "Açıklama", "DEPO HAM (mt)", "Eksik (mt)"]
        self.need_table.setColumnCount(len(_NEED_COLS))
        self.need_table.setHorizontalHeaderLabels(_NEED_COLS)
        self.need_table.verticalHeader().setVisible(False)
        self.need_table.setSortingEnabled(True)
        nhdr = self.need_table.horizontalHeader()
        nhdr.setSectionsMovable(True)
        nhdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in range(len(_NEED_COLS)):
            if i != 2:
                nhdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.need_table.setMaximumHeight(200)
        rl.addWidget(self.need_table)

        btn_po = QPushButton("+ Satınalma Siparişi Oluştur (Seçili Kalemler)")
        btn_po.setStyleSheet("background:#1565C0;color:white;font-weight:bold;"
                             "border-radius:4px;padding:6px 14px;")
        btn_po.clicked.connect(self._create_po)
        rl.addWidget(btn_po)

        rl.addWidget(QLabel("<b>Satınalma Kalemleri</b> (çift tıklayarak mal girişi yapabilirsiniz)"))
        self.po_table = QTableWidget()
        self.po_table.setColumnCount(12)
        self.po_table.setHorizontalHeaderLabels([
            "PO No", "Tedarikçi", "Ürün Kodu", "Kumaş Tipi",
            "Ham Sip.Mt", "Ham Sip.Kg", "Gelen Mt", "Kalan Mt",
            "Gelen Kg", "Kalan Kg", "Birim Fiyat", "Durum"])
        self.po_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.po_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.po_table.verticalHeader().setVisible(False)
        self.po_table.setSortingEnabled(True)
        phdr = self.po_table.horizontalHeader()
        phdr.setSectionsMovable(True)
        phdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        phdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in (0, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            phdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.po_table.setMaximumHeight(200)
        self.po_table.itemSelectionChanged.connect(self._on_po_item_select)
        self.po_table.cellDoubleClicked.connect(self._po_item_dbl_click)
        rl.addWidget(self.po_table)

        po_btns = QHBoxLayout()
        for lbl, slot in [("📄 PDF Al", self._po_pdf),
                           ("📧 Mail Gönder", self._po_mail),
                           ("📝 Durum Değiştir", self._po_change_status),
                           ("🗑 Sil", self._po_delete)]:
            b = QPushButton(lbl); b.clicked.connect(slot); po_btns.addWidget(b)
        po_btns.addStretch()
        rl.addLayout(po_btns)

        rl.addWidget(QLabel("<b>Mal Giriş Kayıtları</b> (her giriş ayrı satır)"))
        self.po_receipts_table = QTableWidget()
        self.po_receipts_table.setColumnCount(7)
        self.po_receipts_table.setHorizontalHeaderLabels([
            "Tarih", "Ürün Kodu", "Kumaş Tipi", "Lot", "Metre", "Kilo", "Lokasyon"])
        self.po_receipts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.po_receipts_table.verticalHeader().setVisible(False)
        self.po_receipts_table.setSortingEnabled(True)
        rrhdr = self.po_receipts_table.horizontalHeader()
        rrhdr.setSectionsMovable(True)
        rrhdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        for i in (0, 1, 2, 3, 4, 5):
            rrhdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.po_receipts_table.setMaximumHeight(160)
        rl.addWidget(self.po_receipts_table)

        receipt_btns = QHBoxLayout()
        b_rec_edit = QPushButton("✏ Girişi Düzenle")
        b_rec_edit.clicked.connect(self._edit_po_receipt)
        b_rec_del  = QPushButton("🗑 Girişi Sil")
        b_rec_del.clicked.connect(self._delete_po_receipt)
        b_rec_del.setStyleSheet("color:#C62828;")
        receipt_btns.addWidget(b_rec_edit)
        receipt_btns.addWidget(b_rec_del)
        receipt_btns.addStretch()
        rl.addLayout(receipt_btns)

        rl.addStretch()
        splitter.addWidget(scroll)
        splitter.setSizes([300, 700])
        self._right_scroll = scroll
        self._right_scroll.setVisible(False)

    # ── Yenile ───────────────────────────────────────────────────
    def refresh(self):
        self._refresh_queue()
        if self._current_order_id:
            self._show_detail(self._current_order_id)

    def _refresh_queue(self):
        from datetime import datetime
        all_orders = db.get_all_orders()
        rows = [r for r in all_orders if r.get("status") in self._PLANNING_STATUSES]
        pending_count = sum(1 for r in rows if r.get("status") == "ONAYDA")
        if pending_count:
            self._pending_lbl.setText(f"⚠ {pending_count} yeni sipariş onay bekliyor!")
            self._pending_lbl.setVisible(True)
        else:
            self._pending_lbl.setVisible(False)
        self.queue_table.blockSignals(True)
        self.queue_table.setSortingEnabled(False)
        self.queue_table.setRowCount(0)
        for r in rows:
            row = self.queue_table.rowCount()
            self.queue_table.insertRow(row)
            item0 = QTableWidgetItem(r.get("order_no","") or "")
            item0.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.queue_table.setItem(row, 0, item0)
            self.queue_table.setItem(row, 1, QTableWidgetItem(r.get("customer_name","") or ""))
            td = r.get("delivery_date","") or ""
            try:
                td = datetime.strptime(td[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                pass
            self.queue_table.setItem(row, 2, QTableWidgetItem(td))
            # Ürün kodları
            codes = list(dict.fromkeys(
                it.get("product_code","") for it in (r.get("items") or [])
                if it.get("product_code")))
            self.queue_table.setItem(row, 3, QTableWidgetItem(", ".join(codes)))
            st = r.get("status","")
            st_item = QTableWidgetItem(st)
            color = self._STATUS_COLORS.get(st, "#212121")
            st_item.setForeground(QBrush(QColor(color)))
            self.queue_table.setItem(row, 4, st_item)
            if r["id"] == self._current_order_id:
                self.queue_table.selectRow(row)
        self.queue_table.setSortingEnabled(True)
        self.queue_table.blockSignals(False)

    # ── Sipariş seçildi ──────────────────────────────────────────
    def _on_queue_select(self):
        row = self.queue_table.currentRow()
        if row < 0:
            return
        item = self.queue_table.item(row, 0)
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        order = db.get_order(oid)
        if not order:
            return
        st = order.get("status","")
        if st == "ONAYDA":
            QMessageBox.warning(self, "Onay Gerekli",
                "Bu sipariş henüz admin tarafından onaylanmamış.\n"
                "Planlama başlatmak için önce onaylanması gerekiyor.")
            return
        if st == "ONAYLANDI - PLANLAMADA":
            db.update_order_status(oid, "PLANLAMA - GÖRDÜ")
        self._current_order_id = oid
        self._refresh_queue()
        self._show_detail(oid)

    def _approve_order(self):
        row = self.queue_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir sipariş seçin.")
            return
        item = self.queue_table.item(row, 0)
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        order = db.get_order(oid)
        if not order:
            return
        if order.get("status") != "ONAYDA":
            QMessageBox.information(self, "Bilgi",
                f"Bu sipariş zaten '{order.get('status')}' durumunda.")
            return
        reply = QMessageBox.question(self, "Onay",
            f"{order.get('order_no','')} numaralı sipariş onaylansın mı?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.approve_order(oid, CURRENT_USER["full_name"])
            self._refresh_queue()
            QMessageBox.information(self, "Onaylandı",
                "Sipariş onaylandı. Planlama ekibine hazır.")

    # ── PO kalemi seçildi → makbuzları göster ───────────────────
    def _on_po_item_select(self):
        row = self.po_table.currentRow()
        if row < 0:
            self.po_receipts_table.setRowCount(0)
            return
        item = self.po_table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        po_id = data[0] if isinstance(data, tuple) else data
        if po_id:
            self._refresh_receipts_table(po_id)

    def _refresh_receipts_table(self, po_id):
        from datetime import datetime
        receipts = db.get_po_receipts(po_id)
        self.po_receipts_table.setSortingEnabled(False)
        self.po_receipts_table.setRowCount(0)
        for r in receipts:
            row = self.po_receipts_table.rowCount()
            self.po_receipts_table.insertRow(row)
            dt = r.get("received_at","") or ""
            try:
                dt = datetime.strptime(dt[:16], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass
            m = float(r.get("meter",0) or 0)
            k = float(r.get("kg",0) or 0)
            grp = r.get("location_group","")
            for col, val in enumerate([
                dt,
                r.get("product_code",""),
                r.get("fabric_type",""),
                r.get("lot","") or "",
                f"{m:.2f}",
                f"{k:.2f}",
                f"{r.get('location','')} [{grp}]",
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setData(Qt.ItemDataRole.UserRole, r.get("id"))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 6 and grp != "DEPO":
                    cell.setForeground(QBrush(QColor("#E65100")))
                self.po_receipts_table.setItem(row, col, cell)
        self.po_receipts_table.setSortingEnabled(True)

    # ── Çift tıklama mal girişi (po_table satırına) ──────────────
    def _po_item_dbl_click(self, row, _col):
        cell = self.po_table.item(row, 0)
        if not cell:
            return
        data = cell.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, tuple):
            return
        po_id, po_item_id = data
        if not po_item_id:
            return
        po = db.get_purchase_order(po_id)
        if not po:
            return
        po_item = next((i for i in (po.get("items") or []) if i.get("id") == po_item_id), None)
        if not po_item:
            return
        dlg = ItemReceiptDialog(self, po_item=po_item)
        if dlg.exec():
            d = dlg.get_data()
            try:
                db.receive_purchase_order_item(
                    po_item_id, d["metre"], d["kilo"],
                    d["location"], user_name=CURRENT_USER["full_name"],
                    location_group=d["location_group"], lot=d["lot"])
                self._refresh_po_table()
                self._refresh_receipts_table(po_id)
                if self._current_order_id:
                    self._show_detail(self._current_order_id)
                grp_msg = ("Ana depoya kaydedildi." if d["location_group"] == "DEPO"
                           else "Dış depoya kaydedildi — Boyahane planlama ekranına düşecek.")
                QMessageBox.information(self, "Kaydedildi",
                    f"Mal girişi tamamlandı.\n{grp_msg}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Mal girişi kaydedilemedi:\n{e}")

    def _selected_po_id_silent(self):
        row = self.po_table.currentRow()
        if row < 0:
            return None
        item = self.po_table.item(row, 0)
        if not item:
            return None
        data = item.data(Qt.ItemDataRole.UserRole)
        return data[0] if isinstance(data, tuple) else data

    # ── Detay paneli ─────────────────────────────────────────────
    def _show_detail(self, order_id):
        from datetime import datetime
        order = db.get_order(order_id)
        if not order:
            return

        def _fmt(key):
            val = order.get(key,"") or ""
            if key in ("delivery_date","order_date") and val:
                try: val = datetime.strptime(val[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
                except Exception: pass
            return str(val)

        for key, lbl_w in self._info.items():
            lbl_w.setText(_fmt(key))
        self._order_group.setVisible(True)

        items = order.get("items", [])
        self.need_table.setSortingEnabled(False)
        self.need_table.setRowCount(0)
        for it in items:
            pc = it.get("product_code","")
            fabric_type = it.get("fabric_type","") or ""
            stock = db.get_fabric_stock_in_depo(pc, fabric_type if fabric_type == "HAM" else "HAM") or {"meter": 0}
            depo_m = float(stock.get("meter", 0) or 0)
            order_m = float(it.get("meter") or 0)
            order_kg = float(it.get("kg") or 0)
            missing = max(0.0, order_m - depo_m)

            row = self.need_table.rowCount()
            self.need_table.insertRow(row)

            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if missing > 0 else Qt.CheckState.Unchecked)
            chk.setData(Qt.ItemDataRole.UserRole, dict(it))
            self.need_table.setItem(row, 0, chk)

            sp = it.get("sale_price") or 0
            row_vals = [
                pc,                             # 1 Ürün Kodu
                it.get("product_name",""),       # 2 Ürün Adı
                fabric_type,                    # 3 Kumaş Tipi
                it.get("color",""),             # 4 Renk
                it.get("composition",""),        # 5 Kompozisyon
                it.get("width",""),             # 6 En
                it.get("gramaj",""),            # 7 Gramaj
                it.get("lab_no",""),            # 8 Lab No
                it.get("print_type",""),        # 9 Baskı Tipi
                it.get("zemin_rengi",""),       # 10 Zemin Rengi
                it.get("baski_desen_no",""),    # 11 Baskı Desen No
                f"{order_m:.2f}",              # 12 Sip. Mt
                f"{order_kg:.2f}",             # 13 Sip. Kg
                f"{sp:.2f}" if sp else "",     # 14 Satış Fiyatı
                it.get("description",""),       # 15 Açıklama
                f"{depo_m:.2f}",              # 16 DEPO HAM (mt)
                f"{missing:.2f}",             # 17 Eksik (mt)
            ]
            for col, val in enumerate(row_vals, start=1):
                cell = QTableWidgetItem(str(val))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 17:
                    if missing > 0:
                        cell.setText(f"{missing:.2f}  ⚠ Eksik")
                        cell.setForeground(QBrush(QColor("#C62828")))
                    else:
                        cell.setText("✅ Yeterli")
                        cell.setForeground(QBrush(QColor("#2E7D32")))
                self.need_table.setItem(row, col, cell)
        self.need_table.setSortingEnabled(True)

        self._refresh_po_table(order_id)
        self._right_scroll.setVisible(True)

    def _refresh_po_table(self, order_id=None):
        oid = order_id or self._current_order_id
        if not oid:
            return
        items = db.get_po_items_for_order(oid)
        self.po_table.blockSignals(True)
        self.po_table.setSortingEnabled(False)
        self.po_table.setRowCount(0)
        for it in items:
            row = self.po_table.rowCount()
            self.po_table.insertRow(row)
            po_id = it.get("po_id") or it.get("po_id_ref")
            item_id = it.get("id")
            om = float(it.get("meter",0) or 0)
            ok = float(it.get("kg",0) or 0)
            rm = float(it.get("received_meter",0) or 0)
            rk = float(it.get("received_kg",0) or 0)
            kalan_m = max(0.0, om - rm)
            kalan_k = max(0.0, ok - rk)
            up = float(it.get("unit_price",0) or 0)
            po_status = it.get("po_status","") or ""

            item0 = QTableWidgetItem(it.get("po_no",""))
            item0.setData(Qt.ItemDataRole.UserRole, (po_id, item_id))
            item0.setFlags(item0.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.po_table.setItem(row, 0, item0)

            vals = [
                it.get("supplier_name","") or "",        # 1 Tedarikçi
                it.get("product_code","") or "",          # 2 Ürün Kodu
                it.get("fabric_type","") or "",           # 3 Kumaş Tipi
                f"{om:.2f}",                              # 4 Ham Sip.Mt
                f"{ok:.2f}",                              # 5 Ham Sip.Kg
                f"{rm:.2f}",                              # 6 Gelen Mt
                f"{kalan_m:.2f}",                         # 7 Kalan Mt
                f"{rk:.2f}",                              # 8 Gelen Kg
                f"{kalan_k:.2f}",                         # 9 Kalan Kg
                f"{up:.4f}" if up else "—",               # 10 Birim Fiyat
                po_status,                                # 11 Durum
            ]
            for col, val in enumerate(vals, start=1):
                cell = QTableWidgetItem(str(val))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 6:  # Gelen Mt
                    cell.setForeground(QBrush(QColor("#2E7D32" if rm >= om else "#C62828")))
                if col == 7 and kalan_m > 0:  # Kalan Mt
                    cell.setForeground(QBrush(QColor("#E65100")))
                if col == 11:
                    sc = {"TAMAMLANDI": "#2E7D32", "GÖNDERİLDİ": "#1565C0",
                          "KISMİ GELDİ": "#E65100", "İPTAL": "#757575"}.get(po_status)
                    if sc:
                        cell.setForeground(QBrush(QColor(sc)))
                self.po_table.setItem(row, col, cell)
        self.po_table.setSortingEnabled(True)
        self.po_table.blockSignals(False)
        self.po_receipts_table.setRowCount(0)

    def _selected_po_id(self):
        row = self.po_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir satınalma kalemi seçin.")
            return None
        item = self.po_table.item(row, 0)
        if not item:
            return None
        data = item.data(Qt.ItemDataRole.UserRole)
        return data[0] if isinstance(data, tuple) else data

    # ── PO Oluştur ───────────────────────────────────────────────
    def _create_po(self):
        if not self._current_order_id:
            return
        order = db.get_order(self._current_order_id)
        if not order:
            return
        missing_items = []
        for row in range(self.need_table.rowCount()):
            chk = self.need_table.item(row, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                it = chk.data(Qt.ItemDataRole.UserRole)
                pc = it.get("product_code","")
                stock = db.get_fabric_stock_in_depo(pc, "HAM") or {"meter": 0}
                depo_m = float(stock.get("meter", 0) or 0)
                order_m = float(it.get("meter") or 0)
                missing = max(0.0, order_m - depo_m)
                if missing > 0:
                    missing_items.append({
                        "product_code": pc,
                        "product_name": it.get("product_name",""),
                        "composition":  it.get("composition",""),
                        "width":        it.get("width",""),
                        "gramaj":       it.get("gramaj",""),
                        "fabric_type":  "HAM",
                        "meter":        missing, "kg": 0, "unit_price": 0,
                        "description":  f"{order.get('order_no','')} için ham dokuma",
                    })
        if not missing_items:
            QMessageBox.information(self, "Bilgi", "Eksik kalem seçilmedi veya tüm stok yeterli.")
            return
        dlg = PurchaseOrderDialog(self, missing_items=missing_items)
        if dlg.exec():
            d = dlg.get_data()
            try:
                created_po_nos = []
                for grp in d["po_groups"]:
                    _, po_no = db.add_purchase_order(
                        supplier_id=grp["supplier_id"],
                        supplier_name=grp["supplier_name"],
                        order_id=self._current_order_id,
                        order_no=order.get("order_no",""),
                        currency=grp.get("currency",""),
                        payment_method=grp.get("payment_method",""),
                        delivery_terms=grp.get("delivery_terms",""),
                        expected_delivery=grp.get("expected_delivery",""),
                        notes=grp.get("notes",""),
                        items=grp["items"],
                        created_by=CURRENT_USER["full_name"])
                    created_po_nos.append(po_no)
                cur_st = order.get("status","")
                if cur_st in ("PLANLAMA - GÖRDÜ", "ONAYLANDI - PLANLAMADA"):
                    db.update_order_status(self._current_order_id, "PLANLANDI")
                self._refresh_po_table()
                if self._current_order_id:
                    self._show_detail(self._current_order_id)
                po_list = "\n".join(f"  • {n}" for n in created_po_nos)
                QMessageBox.information(self, "Oluşturuldu",
                    f"{len(created_po_nos)} adet satınalma siparişi oluşturuldu:\n{po_list}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"PO oluşturulamadı:\n{e}")

    # ── PDF ──────────────────────────────────────────────────────
    def _po_pdf(self):
        po_id = self._selected_po_id()
        if not po_id:
            return
        po = db.get_purchase_order(po_id)
        if not po:
            return
        company = db.get_company_settings()
        path, _ = QFileDialog.getSaveFileName(
            self, "PO PDF Kaydet", f"{po['po_no']}.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            import purchase_order_pdf as pop
            pop.generate_purchase_order_pdf(po, company, path)
            QMessageBox.information(self, "PDF Oluşturuldu", f"Kaydedildi:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF oluşturulamadı:\n{e}")

    # ── Mail ─────────────────────────────────────────────────────
    def _po_mail(self):
        po_id = self._selected_po_id()
        if not po_id:
            return
        po = db.get_purchase_order(po_id)
        if not po:
            return
        sup = db.get_supplier(po.get("supplier_id")) if po.get("supplier_id") else None
        email_addr = (dict(sup).get("email","") if sup else "") or ""
        if not email_addr:
            QMessageBox.warning(self, "E-posta Yok",
                f"Tedarikçi '{po.get('supplier_name','')}' için e-posta adresi tanımlı değil.\n"
                "Tedarikçiler menüsünden e-posta ekleyiniz.")
            return
        import tempfile, os as _os2
        tmp = tempfile.mktemp(suffix=".pdf")
        try:
            import purchase_order_pdf as pop
            company = db.get_company_settings()
            pop.generate_purchase_order_pdf(po, company, tmp)
            import email_report as er
            er.send_email_with_attachment(
                email_addr,
                subject=f"Satınalma Siparişi {po['po_no']}",
                body_text=(f"Sayın {po.get('supplier_name','')} Yetkilileri,\n\n"
                           f"Ek'te {po['po_no']} numaralı satınalma sipariş formumuzu "
                           f"bulabilirsiniz.\n\nİyi çalışmalar,\nBursa Knitted"),
                attachment_path=tmp,
            )
            db.update_purchase_order_status(po_id, "GÖNDERİLDİ")
            self._refresh_po_table()
            QMessageBox.information(self, "Gönderildi",
                f"E-posta {email_addr} adresine gönderildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"E-posta gönderilemedi:\n{e}")
        finally:
            try:
                _os2.unlink(tmp)
            except Exception:
                pass

    # ── Mal Girişi ───────────────────────────────────────────────
    # _po_receive yerine _po_item_dbl_click kullanılıyor (kalem satırına çift tıklama)

    # ── Durum Değiştir ───────────────────────────────────────────
    def _po_change_status(self):
        po_id = self._selected_po_id()
        if not po_id:
            return
        row = self.po_table.currentRow()
        current_status = self.po_table.item(row, 11).text() if row >= 0 else ""
        dlg = QDialog(self); dlg.setWindowTitle("PO Durumu Değiştir")
        form = QFormLayout(dlg)
        combo = QComboBox()
        for s in PO_STATUS_OPTIONS:
            combo.addItem(s)
        idx = combo.findText(current_status)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        form.addRow("Yeni Durum:", combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec():
            db.update_purchase_order_status(po_id, combo.currentText())
            self._refresh_po_table()

    # ── Sil ──────────────────────────────────────────────────────
    def _po_delete(self):
        po_id = self._selected_po_id()
        if not po_id:
            return
        row = self.po_table.currentRow()
        po_no = self.po_table.item(row, 0).text() if row >= 0 else str(po_id)
        current_status = self.po_table.item(row, 11).text() if row >= 0 else ""
        if current_status not in ("TAMAMLANDI", "İPTAL"):
            QMessageBox.warning(self, "Silinemez",
                f"'{po_no}' PO'su şu an '{current_status}' durumunda.\n\n"
                "Silebilmek için önce 'Durum Değiştir' butonu ile\n"
                "TAMAMLANDI veya İPTAL durumuna getiriniz.")
            return
        if QMessageBox.question(
            self, "Sil", f"{po_no} satınalma siparişi kalıcı olarak silinsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            db.delete_purchase_order(po_id)
            self._refresh_po_table()

    # ── Mal Girişi Düzenle / Sil ─────────────────────────────────
    def _selected_receipt_id(self):
        row = self.po_receipts_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir mal girişi satırı seçin.")
            return None
        cell = self.po_receipts_table.item(row, 0)
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def _edit_po_receipt(self):
        role = CURRENT_USER.get("role","")
        if role not in ("admin", "planlama"):
            QMessageBox.warning(self, "Yetersiz Yetki",
                "Mal girişi düzenleme yalnızca planlamacı veya admin tarafından yapılabilir.")
            return
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return
        row = self.po_receipts_table.currentRow()
        def _txt(c): return self.po_receipts_table.item(row, c).text() \
                     if self.po_receipts_table.item(row, c) else ""

        dlg = QDialog(self); dlg.setWindowTitle("Mal Girişi Düzenle"); dlg.setMinimumWidth(420)
        form = QFormLayout(dlg)
        metre_sb = QDoubleSpinBox(); metre_sb.setRange(0, 9_999_999); metre_sb.setDecimals(2)
        metre_sb.setSuffix(" mt")
        try: metre_sb.setValue(float(_txt(4)))
        except ValueError: pass
        kilo_sb = QDoubleSpinBox(); kilo_sb.setRange(0, 9_999_999); kilo_sb.setDecimals(2)
        kilo_sb.setSuffix(" kg")
        try: kilo_sb.setValue(float(_txt(5)))
        except ValueError: pass
        lot_e = QLineEdit(_txt(3))
        loc_cb = QComboBox()
        loc_cb.addItem("— Lokasyon Seçiniz —", ("", ""))
        for loc in db.get_active_locations():
            grp = loc.get("group_name","")
            loc_cb.addItem(f"[{grp}]  {loc['name']}", (loc["name"], grp))
        cur_loc = _txt(6).split(" [")[0]  # strip " [GRP]"
        for i in range(loc_cb.count()):
            d = loc_cb.itemData(i)
            if isinstance(d, tuple) and d[0] == cur_loc:
                loc_cb.setCurrentIndex(i); break
        form.addRow("Metre:", metre_sb); form.addRow("Kilo:", kilo_sb)
        form.addRow("Lot No:", lot_e);   form.addRow("Lokasyon:", loc_cb)
        btns2 = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns2.accepted.connect(dlg.accept); btns2.rejected.connect(dlg.reject)
        form.addRow(btns2)
        if dlg.exec():
            loc_data = loc_cb.currentData()
            loc_name, grp = loc_data if isinstance(loc_data, tuple) else ("", "")
            if not loc_name:
                QMessageBox.warning(self, "Eksik", "Lokasyon seçilmelidir."); return
            try:
                db.update_boyahane_receipt(
                    receipt_id, meter=metre_sb.value(), kg=kilo_sb.value(),
                    lot=lot_e.text().strip(), location=loc_name, location_group=grp,
                    user_name=CURRENT_USER["full_name"])
                po_id = self._selected_po_id_silent()
                self._refresh_po_table()
                if po_id: self._refresh_receipts_table(po_id)
                if self._current_order_id: self._show_detail(self._current_order_id)
                QMessageBox.information(self, "Güncellendi",
                    "Mal girişi ve bağlı stok kaydı güncellendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncellenemedi:\n{e}")

    def _delete_po_receipt(self):
        role = CURRENT_USER.get("role","")
        if role not in ("admin", "planlama"):
            QMessageBox.warning(self, "Yetersiz Yetki",
                "Mal girişi silme yalnızca planlamacı veya admin tarafından yapılabilir.")
            return
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return
        row = self.po_receipts_table.currentRow()
        pc = self.po_receipts_table.item(row, 1).text() \
             if self.po_receipts_table.item(row, 1) else ""
        reply = QMessageBox.question(
            self, "Mal Girişini Sil",
            f"<b>{pc}</b> mal giriş kaydı silinsin mi?<br><br>"
            f"<span style='color:#C62828'>Bağlı stok kaydı silinir ve "
            f"sipariş miktarları güncellenir.</span>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                po_id = self._selected_po_id_silent()
                db.delete_boyahane_receipt(receipt_id, user_name=CURRENT_USER["full_name"])
                self._refresh_po_table()
                if po_id: self._refresh_receipts_table(po_id)
                if self._current_order_id: self._show_detail(self._current_order_id)
                QMessageBox.information(self, "Silindi",
                    "Mal girişi ve bağlı stok kaydı silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silinemedi:\n{e}")


BOYAHANE_STATUS_OPTIONS = ["BEKLEMEDE", "İŞLEMDE", "TAMAMLANDI", "İPTAL"]


class BoyahanePlanningView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("<b>🧶 Boyahane Planlama</b>"))
        top.addStretch()
        # Durum filtresi
        self._status_filter = QComboBox()
        self._status_filter.addItem("Tüm Durumlar", "")
        for s in BOYAHANE_STATUS_OPTIONS:
            self._status_filter.addItem(s, s)
        self._status_filter.currentIndexChanged.connect(self.refresh)
        top.addWidget(QLabel("Durum:"))
        top.addWidget(self._status_filter)
        btn_ref = QPushButton("🔄 Yenile"); btn_ref.clicked.connect(self.refresh)
        top.addWidget(btn_ref)
        lay.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Tarih", "PO No", "Sipariş No", "Ürün Kodu", "Kumaş Tipi",
            "Metre", "Kilo", "Birim Fiyat", "Toplam", "Lokasyon",
            "Tedarikçi", "Durum"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        hdr = self.table.horizontalHeader()
        hdr.setSectionsMovable(True)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for i in (0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.table)

        btn_row = QHBoxLayout()
        b_status = QPushButton("📝 Durum Değiştir")
        b_status.clicked.connect(self._change_status)
        b_edit = QPushButton("✏ Düzenle")
        b_edit.clicked.connect(self._edit_receipt)
        b_del = QPushButton("🗑 Sil")
        b_del.clicked.connect(self._delete_receipt)
        b_del.setStyleSheet("color:#C62828;")
        btn_row.addWidget(b_status)
        btn_row.addWidget(b_edit)
        btn_row.addWidget(b_del)
        btn_row.addStretch()

        # Özet
        self._summary_lbl = QLabel()
        self._summary_lbl.setStyleSheet("color:#1565C0;font-weight:bold;")
        btn_row.addWidget(self._summary_lbl)
        lay.addLayout(btn_row)

    def refresh(self):
        from datetime import datetime
        status_f = self._status_filter.currentData() or ""
        rows = db.get_boyahane_queue(status_filter=status_f)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        total_m = 0.0; total_amt = 0.0
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            dt = r.get("received_at","") or ""
            try:
                dt = datetime.strptime(dt[:16], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass
            m = float(r.get("meter",0) or 0)
            k = float(r.get("kg",0) or 0)
            up = float(r.get("unit_price",0) or 0)
            amt = m * up
            total_m += m; total_amt += amt
            st = r.get("status","")
            color = {"BEKLEMEDE":"#E65100","İŞLEMDE":"#1565C0",
                     "TAMAMLANDI":"#2E7D32","İPTAL":"#757575"}.get(st)

            for col, val in enumerate([
                dt, r.get("po_no",""), r.get("order_no",""),
                r.get("product_code",""), r.get("fabric_type",""),
                f"{m:.2f}", f"{k:.2f}",
                f"{up:,.4f}", f"{amt:,.2f}",
                r.get("location",""), r.get("supplier_name",""), st,
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setData(Qt.ItemDataRole.UserRole, r.get("id"))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 11 and color:
                    cell.setForeground(QBrush(QColor(color)))
                self.table.setItem(row, col, cell)
        self.table.setSortingEnabled(True)
        self._summary_lbl.setText(
            f"Toplam: {total_m:,.2f} mt  |  Tutar: {total_amt:,.2f}")

    def _change_status(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir satır seçin.")
            return
        cell = self.table.item(row, 0)
        receipt_id = cell.data(Qt.ItemDataRole.UserRole) if cell else None
        if not receipt_id:
            return
        cur_status = self.table.item(row, 11).text() if self.table.item(row, 11) else ""
        dlg = QDialog(self); dlg.setWindowTitle("Durum Değiştir")
        form = QFormLayout(dlg)
        combo = QComboBox()
        for s in BOYAHANE_STATUS_OPTIONS:
            combo.addItem(s)
        idx = combo.findText(cur_status)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        form.addRow("Yeni Durum:", combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec():
            db.update_boyahane_receipt_status(receipt_id, combo.currentText())
            self.refresh()

    def _selected_receipt_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Bilgi", "Önce bir satır seçin.")
            return None
        cell = self.table.item(row, 0)
        return cell.data(Qt.ItemDataRole.UserRole) if cell else None

    def _edit_receipt(self):
        role = CURRENT_USER.get("role","")
        if role not in ("admin", "planlama"):
            QMessageBox.warning(self, "Yetersiz Yetki",
                "Mal girişi düzenleme yalnızca planlamacı veya admin tarafından yapılabilir.")
            return
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return

        # Seçili satırdan mevcut verileri oku
        row = self.table.currentRow()
        def _txt(col): return self.table.item(row, col).text() if self.table.item(row, col) else ""

        dlg = QDialog(self)
        dlg.setWindowTitle("Mal Girişi Düzenle")
        dlg.setMinimumWidth(420)
        form = QFormLayout(dlg)

        metre_sb = QDoubleSpinBox(); metre_sb.setRange(0, 9_999_999); metre_sb.setDecimals(2)
        metre_sb.setSuffix(" mt")
        try: metre_sb.setValue(float(_txt(5)))
        except ValueError: pass

        kilo_sb = QDoubleSpinBox(); kilo_sb.setRange(0, 9_999_999); kilo_sb.setDecimals(2)
        kilo_sb.setSuffix(" kg")
        try: kilo_sb.setValue(float(_txt(6)))
        except ValueError: pass

        lot_e = QLineEdit(_txt(3) if self.table.columnCount() > 3 else "")

        loc_cb = QComboBox()
        loc_cb.addItem("— Lokasyon Seçiniz —", ("", ""))
        for loc in db.get_active_locations():
            grp = loc.get("group_name","")
            loc_cb.addItem(f"[{grp}]  {loc['name']}", (loc["name"], grp))
        cur_loc = _txt(9)
        for i in range(loc_cb.count()):
            d = loc_cb.itemData(i)
            if isinstance(d, tuple) and d[0] == cur_loc:
                loc_cb.setCurrentIndex(i); break

        form.addRow("Metre:", metre_sb)
        form.addRow("Kilo:", kilo_sb)
        form.addRow("Lot No:", lot_e)
        form.addRow("Lokasyon:", loc_cb)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        form.addRow(btns)

        if dlg.exec():
            loc_data = loc_cb.currentData()
            loc_name, grp = loc_data if isinstance(loc_data, tuple) else ("", "")
            if not loc_name:
                QMessageBox.warning(self, "Eksik", "Lokasyon seçilmelidir.")
                return
            try:
                db.update_boyahane_receipt(
                    receipt_id,
                    meter=metre_sb.value(),
                    kg=kilo_sb.value(),
                    lot=lot_e.text().strip(),
                    location=loc_name,
                    location_group=grp,
                    user_name=CURRENT_USER["full_name"],
                )
                self.refresh()
                QMessageBox.information(self, "Güncellendi",
                    "Mal girişi ve bağlı stok kaydı güncellendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncellenemedi:\n{e}")

    def _delete_receipt(self):
        role = CURRENT_USER.get("role","")
        if role not in ("admin", "planlama"):
            QMessageBox.warning(self, "Yetersiz Yetki",
                "Mal girişi silme yalnızca planlamacı veya admin tarafından yapılabilir.")
            return
        receipt_id = self._selected_receipt_id()
        if not receipt_id:
            return
        row = self.table.currentRow()
        po_no   = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        product = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
        reply = QMessageBox.question(
            self, "Mal Girişini Sil",
            f"<b>{po_no} / {product}</b> kaydı silinsin mi?<br><br>"
            f"<span style='color:#C62828'>Bağlı stok kaydı da silinir ve "
            f"sipariş miktarları güncellenir.</span>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.delete_boyahane_receipt(receipt_id, user_name=CURRENT_USER["full_name"])
                self.refresh()
                QMessageBox.information(self, "Silindi",
                    "Mal girişi ve bağlı stok kaydı silindi, sipariş miktarları güncellendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silinemedi:\n{e}")


class SevkiyatView(QWidget):
    """Depo-Sevkiyat personeli sipariş sevklerini buradan girer."""

    SHIP_STATUSES = ["TÜM KUMAŞLAR BOYAHANEDE", "MÜŞTERİYE SEVKLER BAŞLADI", "PLANLANDI", "BOYAHANAYA SEVKLER BAŞLADI"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_order_id = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("<b>🚚 Sevkiyat Modülü</b>"))
        top.addStretch()
        btn_ref = QPushButton("🔄 Yenile"); btn_ref.clicked.connect(self.refresh)
        top.addWidget(btn_ref)
        lay.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(splitter)

        # Sol: Sevk edilecek siparişler
        left = QWidget()
        ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 4, 0)
        ll.addWidget(QLabel("<b>Sevk Edilecek Siparişler</b>"))
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(6)
        self.order_table.setHorizontalHeaderLabels(
            ["Sipariş No", "Müşteri", "Termin", "Sip.Mt", "Sevk.Mt", "Durum"])
        self.order_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.order_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.order_table.verticalHeader().setVisible(False)
        self.order_table.setSortingEnabled(True)
        ohdr = self.order_table.horizontalHeader()
        ohdr.setSectionsMovable(True)
        ohdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in (0, 2, 3, 4, 5):
            ohdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.order_table.itemSelectionChanged.connect(self._on_order_select)
        ll.addWidget(self.order_table)
        splitter.addWidget(left)

        # Sağ: Sevk formu + geçmiş
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(4, 0, 0, 0)

        self._order_info = QLabel()
        self._order_info.setStyleSheet("background:#E3F2FD;padding:6px;border-radius:4px;")
        self._order_info.setWordWrap(True)
        self._order_info.setVisible(False)
        rl.addWidget(self._order_info)

        rl.addWidget(QLabel("<b>Yeni Sevk Girişi</b>"))
        form = QFormLayout(); form.setSpacing(8)
        self._ship_product = QComboBox()
        self._ship_product.setEditable(True)
        self._ship_fabric_type = QComboBox()
        for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI", "MAMÜL"]:
            self._ship_fabric_type.addItem(t, t)
        self._ship_color = QLineEdit()
        self._ship_lot = QLineEdit(); self._ship_lot.setPlaceholderText("Boş: otomatik")
        self._ship_meter = QDoubleSpinBox()
        self._ship_meter.setRange(0, 999999); self._ship_meter.setDecimals(2)
        self._ship_kg = QDoubleSpinBox()
        self._ship_kg.setRange(0, 999999); self._ship_kg.setDecimals(2)
        self._ship_notes = QLineEdit()
        form.addRow("Ürün Kodu:", self._ship_product)
        form.addRow("Kumaş Tipi:", self._ship_fabric_type)
        form.addRow("Renk:", self._ship_color)
        form.addRow("Lot:", self._ship_lot)
        form.addRow("Metre:", self._ship_meter)
        form.addRow("Kilo:", self._ship_kg)
        form.addRow("Notlar:", self._ship_notes)
        rl.addLayout(form)

        btn_add = QPushButton("+ Sevk Ekle")
        btn_add.setStyleSheet("background:#1565C0;color:white;font-weight:bold;"
                              "border-radius:4px;padding:6px 14px;")
        btn_add.clicked.connect(self._add_shipment)
        rl.addWidget(btn_add)

        rl.addWidget(QLabel("<b>Sevkiyat Geçmişi</b>"))
        self.ship_table = QTableWidget()
        self.ship_table.setColumnCount(7)
        self.ship_table.setHorizontalHeaderLabels(
            ["Tarih", "Ürün Kodu", "Kumaş Tipi", "Renk", "Lot", "Metre", "Kilo"])
        self.ship_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ship_table.verticalHeader().setVisible(False)
        self.ship_table.setSortingEnabled(True)
        shdr = self.ship_table.horizontalHeader()
        shdr.setSectionsMovable(True)
        shdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in (0, 2, 3, 4, 5, 6):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        rl.addWidget(self.ship_table)
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([350, 650])

    def refresh(self):
        from datetime import datetime
        orders = db.get_shippable_orders()
        self.order_table.blockSignals(True)
        self.order_table.setSortingEnabled(False)
        self.order_table.setRowCount(0)
        for r in orders:
            row = self.order_table.rowCount()
            self.order_table.insertRow(row)
            item0 = QTableWidgetItem(r.get("order_no",""))
            item0.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.order_table.setItem(row, 0, item0)
            self.order_table.setItem(row, 1, QTableWidgetItem(r.get("customer_name","") or ""))
            td = r.get("delivery_date","") or ""
            try:
                td = datetime.strptime(td[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
            except Exception:
                pass
            self.order_table.setItem(row, 2, QTableWidgetItem(td))
            tm = float(r.get("total_meter",0) or 0)
            sm = float(r.get("shipped_meter",0) or 0)
            self.order_table.setItem(row, 3, QTableWidgetItem(f"{tm:.2f}"))
            sm_item = QTableWidgetItem(f"{sm:.2f}")
            sm_item.setForeground(QBrush(QColor("#2E7D32" if sm >= tm else "#C62828")))
            self.order_table.setItem(row, 4, sm_item)
            st = r.get("status","")
            st_item = QTableWidgetItem(st)
            st_item.setForeground(QBrush(QColor(
                "#2E7D32" if st == "SİPARİŞ TAMAMLANDI" else
                "#1565C0" if st == "MÜŞTERİYE SEVKLER BAŞLADI" else "#E65100")))
            self.order_table.setItem(row, 5, st_item)
            if r["id"] == self._current_order_id:
                self.order_table.selectRow(row)
        self.order_table.setSortingEnabled(True)
        self.order_table.blockSignals(False)

    def _on_order_select(self):
        row = self.order_table.currentRow()
        if row < 0:
            return
        item = self.order_table.item(row, 0)
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        self._current_order_id = oid
        order = db.get_order(oid)
        if order:
            codes = list(dict.fromkeys(
                it.get("product_code","") for it in (order.get("items") or [])
                if it.get("product_code")))
            self._order_info.setText(
                f"<b>{order.get('order_no','')} — {order.get('customer_name','')}</b>  "
                f"Ürünler: {', '.join(codes)}")
            self._order_info.setVisible(True)
            # Ürün kodu combosunu doldur
            self._ship_product.blockSignals(True)
            self._ship_product.clear()
            for it in (order.get("items") or []):
                pc = it.get("product_code","")
                pn = it.get("product_name","")
                label = f"{pc} — {pn}" if pn else pc
                self._ship_product.addItem(label, pc)
            self._ship_product.blockSignals(False)
        self._refresh_ship_table(oid)

    def _refresh_ship_table(self, order_id):
        from datetime import datetime
        shipments = db.get_order_shipments(order_id)
        self.ship_table.setSortingEnabled(False)
        self.ship_table.setRowCount(0)
        for s in shipments:
            row = self.ship_table.rowCount()
            self.ship_table.insertRow(row)
            dt = s.get("shipment_date","") or ""
            try:
                dt = datetime.strptime(dt[:16], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass
            for col, val in enumerate([
                dt, s.get("product_code",""), s.get("fabric_type",""),
                s.get("color",""), s.get("lot",""),
                f"{float(s.get('meter',0) or 0):.2f}",
                f"{float(s.get('kg',0) or 0):.2f}",
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.ship_table.setItem(row, col, cell)
        self.ship_table.setSortingEnabled(True)

    def _add_shipment(self):
        if not self._current_order_id:
            QMessageBox.information(self, "Bilgi", "Önce sol taraftan bir sipariş seçin.")
            return
        meter = self._ship_meter.value()
        kg = self._ship_kg.value()
        if meter <= 0 and kg <= 0:
            QMessageBox.warning(self, "Hata", "Metre veya kilo girilmelidir.")
            return
        import datetime as _dt
        lot = self._ship_lot.text().strip()
        if not lot:
            lot = f"SEV-{_dt.date.today().strftime('%Y%m%d')}"
        items = [{
            "product_code": self._ship_product.currentData() or self._ship_product.currentText(),
            "product_name": "",
            "fabric_type": self._ship_fabric_type.currentData() or "",
            "color": self._ship_color.text().strip(),
            "lot": lot,
            "meter": meter,
            "kg": kg,
            "notes": self._ship_notes.text().strip(),
        }]
        try:
            db.add_order_shipment(self._current_order_id, items, CURRENT_USER["full_name"])
            self._ship_meter.setValue(0)
            self._ship_kg.setValue(0)
            self._ship_lot.clear()
            self._ship_notes.clear()
            self.refresh()
            self._refresh_ship_table(self._current_order_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sevk kaydedilemedi:\n{e}")


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
        self.stat_iplikboyali = QLabel("—")
        self.stat_baskili= QLabel("—")
        row2 = QHBoxLayout()
        for icon, lbl, color, wgt in [
            ("🟫","HAM (Metre)","#5D4037",   self.stat_ham),
            ("🟩","PFD (Metre)","#00695C",   self.stat_pfd),
            ("🟦","BOYALI (Metre)","#1565C0", self.stat_boyali),
            ("🟧","İPLİĞİ BOYALI (Metre)","#EF6C00", self.stat_iplikboyali),
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
        tip_mt = {"HAM": 0.0, "PFD": 0.0, "BOYALI": 0.0, "İPLİĞİ BOYALI": 0.0, "BASKILI": 0.0}
        for r in all_rows:
            t = r["fabric_type"] or ""
            if t in tip_mt:
                tip_mt[t] += r["meter"] or 0
        self.stat_ham.setText(f"{tip_mt['HAM']:,.0f} mt")
        self.stat_pfd.setText(f"{tip_mt['PFD']:,.0f} mt")
        self.stat_boyali.setText(f"{tip_mt['BOYALI']:,.0f} mt")
        self.stat_iplikboyali.setText(f"{tip_mt['İPLİĞİ BOYALI']:,.0f} mt")
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
        self.orders_view = OrdersView(self)
        self.planning_view = PlanningView(self)
        self.boyahane_view = BoyahanePlanningView(self)
        self.sevkiyat_view = SevkiyatView(self)

        self._rebuild_tabs()
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

        sup_menu = menubar.addMenu("🏭 Tedarikçiler")
        sup_menu.addAction("Tedarikçi Listesi...").triggered.connect(
            lambda: SupplierManagementDialog(self).exec())

        prod_menu = menubar.addMenu("📦 Ürünler")
        prod_menu.addAction("Ürün Kataloğu...").triggered.connect(
            lambda: ProductManagementDialog(self).exec())

        loc_menu = menubar.addMenu("🗄 Lokasyonlar")
        loc_menu.addAction("Raf / Lokasyon Tanımlamaları...").triggered.connect(
            lambda: LocationManagementDialog(self).exec())

        order_menu = menubar.addMenu("📋 Siparişler")
        order_menu.addAction("Yeni Sipariş...").triggered.connect(self._new_order)
        if CURRENT_USER.get("role") == "admin":
            order_menu.addSeparator()
            order_menu.addAction("Şirket / Banka Ayarları...").triggered.connect(
                lambda: CompanySettingsDialog(self).exec())

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
        icons = {"admin": "👑", "planlama": "📌", "satışçı": "📋",
                 "depo-sevkiyat": "🚚"}
        role_icon = icons.get(CURRENT_USER.get("role", ""), "👤")
        self._user_label.setText(f"{role_icon} {CURRENT_USER.get('full_name', '')}")

    def _new_order(self):
        dlg = OrderDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            oid, order_no = db.add_order(**data, created_by=CURRENT_USER["full_name"])
            self.orders_view.refresh()
            self.planning_view.refresh()
            QMessageBox.information(self, "Sipariş Oluşturuldu",
                f"Sipariş kaydedildi.\n\nSipariş No: {order_no}\nDurum: ONAYDA\n\nAdmin onayı bekleniyor.")

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
        role = CURRENT_USER.get("role", "")
        if role == "admin":
            self.tabs.addTab(self.dashboard, "📊 Dashboard")
        if role in ("admin", "kullanici", "depo-sevkiyat"):
            self.tabs.addTab(self.stock_table, "📦 Stok Listesi")
            self.tabs.addTab(self.location_view, "🗂 Lokasyon Görünümü")
        if role in ("admin", "kullanici"):
            self.tabs.addTab(self.fire_view, "🔥 Boyahane Fire Oranları")
        if role in ("admin", "satışçı", "kullanici"):
            self.tabs.addTab(self.orders_view, "📋 Siparişler")
        if role in ("admin", "planlama", "kullanici"):
            self.tabs.addTab(self.planning_view, "📌 Planlama")
            self.tabs.addTab(self.boyahane_view, "🧶 Boyahane Planlama")
        if role in ("admin", "depo-sevkiyat", "kullanici"):
            self.tabs.addTab(self.sevkiyat_view, "🚚 Sevkiyat")
        self.stock_table.refresh_with_locations()
        # Admin: onay bekleyen sipariş bildirimi
        if role == "admin":
            QTimer.singleShot(1500, self._check_pending_orders)

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
        # Admin planlama sekmesine geçince pending check
        if CURRENT_USER.get("role") == "admin" and w is self.planning_view:
            self._check_pending_orders()

    def _check_pending_orders(self):
        pending = db.get_pending_approval_orders()
        if not pending:
            return
        nos = ", ".join(p.get("order_no","") for p in pending[:5])
        extra = f" ve {len(pending)-5} daha..." if len(pending) > 5 else ""
        dlg = QDialog(self); dlg.setWindowTitle("⚠ Onay Bekleyen Siparişler")
        lay = QVBoxLayout(dlg)
        lbl = QLabel(
            f"<b>{len(pending)} sipariş admin onayı bekliyor!</b><br><br>"
            f"<span style='color:#B71C1C'>{nos}{extra}</span><br><br>"
            "Planlama ekranından siparişi seçip <b>✅ Seçili Siparişi Onayla</b> "
            "butonuna tıklayarak onaylayabilirsiniz.")
        lbl.setWordWrap(True); lbl.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(lbl)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(dlg.accept)
        lay.addWidget(btns)
        dlg.exec()

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
    import traceback, datetime
    try:
        main()
    except Exception:
        _log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error.log")
        with open(_log, "a", encoding="utf-8") as _f:
            _f.write(f"\n{'='*60}\n{datetime.datetime.now()}\n")
            _f.write(traceback.format_exc())
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            _a = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Başlatma Hatası",
                f"Program başlatılamadı.\nHata detayları kaydedildi:\n{_log}")
        except Exception:
            pass
        sys.exit(1)
