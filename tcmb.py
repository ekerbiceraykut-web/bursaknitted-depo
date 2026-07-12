"""TCMB günlük döviz kurları (today.xml) — önbellekli, çevrimdışı toleranslı.

Kaynak: https://www.tcmb.gov.tr/kurlar/today.xml (ücretsiz, anahtar gerekmez).
Kurlar iş günlerinde ~15:30'da güncellenir; today.xml her zaman son yayını verir.
Ağ yoksa: önce bellekteki, sonra diske yazılmış son başarılı veri kullanılır.
"""
import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET

_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"
_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcmb_cache.json")
_TTL = 3 * 3600   # 3 saat: gün içinde tekrar tekrar istek atma
_mem = {"t": 0.0, "data": None}


def _parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = {"tarih": root.get("Tarih") or "", "kurlar": {}}
    for cur in root.findall("Currency"):
        kod = cur.get("CurrencyCode") or ""

        def _f(tag):
            t = (cur.findtext(tag) or "").strip()
            try:
                return float(t.replace(",", "."))
            except ValueError:
                return 0.0

        try:
            birim = int(cur.findtext("Unit") or 1)
        except ValueError:
            birim = 1
        out["kurlar"][kod] = {
            "doviz_alis": _f("ForexBuying"),
            "doviz_satis": _f("ForexSelling"),
            "efektif_satis": _f("BanknoteSelling"),
            "birim": birim or 1,
        }
    return out


def get_rates(force=False):
    """Kur tablosu döner; başarısızlıkta önbellek, o da yoksa None."""
    now = time.time()
    if not force and _mem["data"] and now - _mem["t"] < _TTL:
        return _mem["data"]
    try:
        req = urllib.request.Request(_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = _parse(r.read())
        data["kaynak"] = "TCMB"
        _mem["t"], _mem["data"] = now, data
        try:
            with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass
        return data
    except Exception:
        if _mem["data"]:
            return _mem["data"]
        try:
            with open(_CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            data["kaynak"] = "önbellek"
            _mem["t"], _mem["data"] = now, data
            return data
        except Exception:
            return None


def satis(kod="USD"):
    """Döviz Satış kuru: (kur_TL, tarih, kaynak). Ulaşılamazsa (0, '', '')."""
    d = get_rates()
    if not d:
        return 0.0, "", ""
    k = (d.get("kurlar") or {}).get(kod) or {}
    birim = k.get("birim") or 1
    return (k.get("doviz_satis") or 0.0) / birim, d.get("tarih", ""), d.get("kaynak", "TCMB")


def eur_usd():
    """1 EUR kaç USD (döviz satış çaprazı): (kur, tarih, kaynak)."""
    u, _, _ = satis("USD")
    e, tarih, kaynak = satis("EUR")
    return (e / u if u else 0.0), tarih, kaynak
