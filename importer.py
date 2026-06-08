import pandas as pd
import re


def _clean(val):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return ""
    return str(val).strip()


def _num(val):
    if val is None or (isinstance(val, float) and str(val) == "nan"):
        return 0.0
    try:
        return float(str(val).replace(",", "."))
    except Exception:
        return 0.0


def import_from_excel(filepath):
    xl = pd.ExcelFile(filepath)
    records = []

    shelf_sheets = [s for s in xl.sheet_names if re.match(r"^(RAF|P|H|HP|H-P)\d*[-\d]*$", s.strip(), re.IGNORECASE)]

    for sheet_name in shelf_sheets:
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
        location = sheet_name.strip()

        # Find the data start row (row with SN or ÜRÜN header)
        data_start = None
        for i, row in df.iterrows():
            row_vals = [str(v).upper().strip() for v in row if str(v).strip() not in ("", "NAN")]
            if "ÜRÜN ADI" in row_vals or "ÜRÜN KODU" in row_vals:
                data_start = i
                break

        if data_start is None:
            continue

        # Determine column indices from header rows
        header_row = df.iloc[data_start]
        col_map = {}
        for ci, val in enumerate(header_row):
            v = _clean(val).upper()
            if v == "ÜRÜN ADI":
                col_map["product_name"] = ci
            elif v == "ÜRÜN KODU":
                col_map["product_code"] = ci
            elif v == "RENK":
                col_map["color"] = ci
            elif v == "AÇIKLAMA":
                col_map["description"] = ci

        # Check next row for METRE / KİLO / BİRİM
        if data_start + 1 < len(df):
            sub_row = df.iloc[data_start + 1]
            for ci, val in enumerate(sub_row):
                v = _clean(val).upper()
                if v == "METRE":
                    col_map["meter"] = ci
                elif v == "KİLO":
                    col_map["kg"] = ci
                elif "BİRİM" in v or "ADET" in v:
                    col_map["piece_count"] = ci

        if "product_code" not in col_map:
            continue

        for i in range(data_start + 2, len(df)):
            row = df.iloc[i]
            code = _clean(row.iloc[col_map["product_code"]])
            if not code or code.upper() in ("ÜRÜN KODU", "NAN", ""):
                continue

            record = {
                "product_name": _clean(row.iloc[col_map["product_name"]]) if "product_name" in col_map else "",
                "product_code": code,
                "color": _clean(row.iloc[col_map["color"]]) if "color" in col_map else "",
                "location": location,
                "meter": _num(row.iloc[col_map["meter"]]) if "meter" in col_map else 0,
                "kg": _num(row.iloc[col_map["kg"]]) if "kg" in col_map else 0,
                "piece_count": _clean(row.iloc[col_map["piece_count"]]) if "piece_count" in col_map else "",
                "description": _clean(row.iloc[col_map["description"]]) if "description" in col_map else "",
            }
            records.append(record)

    return records


def import_from_main_sheet(filepath):
    df = pd.read_excel(filepath, sheet_name="STOK RAPORU ", header=None)
    records = []

    # Headers are in rows 1-2 (0-indexed)
    # Col mapping from analysis:
    # 1=SIRA NO, 2=ÜRÜN ADI, 3=ÜRÜN KODU, 4=RENK, 5=EMANET, 6=RAF NO
    # 7=METRE, 8=KİLO, 9=BİRİM ADEDİ
    # 10=?, 11=ÇIKIŞ MT, 12=ÇIKIŞ KG, 13=ÇIKIŞ TOP ADEDİ
    # 14=KALAN MT, 15=KALAN KG, 16=KALAN TOP ADEDİ, 17=AÇIKLAMA

    for i in range(5, len(df)):
        row = df.iloc[i]
        code = _clean(row.iloc[3])
        if not code or code.upper() in ("ÜRÜN KODU", "NAN", ""):
            continue

        kalan_mt = _num(row.iloc[14])
        kalan_kg = _num(row.iloc[15])
        kalan_adet = _clean(row.iloc[16])

        record = {
            "product_name": _clean(row.iloc[2]),
            "product_code": code,
            "color": _clean(row.iloc[4]),
            "location": _clean(row.iloc[6]),
            "meter": kalan_mt,
            "kg": kalan_kg,
            "piece_count": kalan_adet,
            "description": _clean(row.iloc[17]),
        }
        records.append(record)

    return records
