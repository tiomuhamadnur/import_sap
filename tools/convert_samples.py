from pathlib import Path

from openpyxl import Workbook

from app.importing.reader import is_empty

CONVERSIONS = {
    "notification": Path("samples/notification/notification.csv"),
    "work_order": Path("samples/work_order/work_order.csv"),
}


def convert(path: Path) -> Path:
    data = path.read_bytes()
    encodings = ("utf-8-sig", "utf-8", "cp1252")
    text = None
    for enc in encodings:
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError(f"Cannot decode {path}")

    import csv
    import io

    sample = text[:4000]
    delimiter = ";" if ";" in sample else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    header = [h.strip() for h in next(reader)]
    width = len(header)

    out = Path(str(path).replace(".csv", ".xlsx"))
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title="Sheet1")
    ws.append(header)
    n = 0
    empty = 0
    for row in reader:
        n += 1
        if n <= 2:
            empty += sum(1 for v in row if is_empty(v))
        padded = (list(row) + [""] * width)[:width]
        ws.append(padded)
    wb.save(out)
    wb.close()
    print(f"[ok] {path.name} -> {out.name}: rows={n} empty_cols_in_first2={empty}")
    return out


def main():
    for _data_type, src in CONVERSIONS.items():
        if not src.exists():
            print(f"[skip] {src} not found")
            continue
        convert(src)


if __name__ == "__main__":
    main()
