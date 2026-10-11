import csv
from pathlib import Path

from openpyxl import load_workbook

BASE = Path("samples")


def inspect_xlsx(path: Path, max_rows: int = 8):
    print(f"\n===== {path.name} (xlsx) =====")
    wb = load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        print(f"--- Sheet: {ws.title} | dims={ws.max_row}x{ws.max_column} ---")
        it = ws.iter_rows(values_only=True)
        try:
            header = next(it)
        except StopIteration:
            print("(empty)")
            continue
        print("HEADER:", list(header))
        for i, row in enumerate(it):
            if i >= max_rows:
                break
            print(f"R{i+2}:", list(row))
        wb.close()
        break


def inspect_csv(path: Path, max_rows: int = 8):
    print(f"\n===== {path.name} (csv) =====")
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(2048)
    print("PEEK:", sample[:500].replace("\n", "\\n"))
    delimiter = ";"
    if "," in sample and ";" not in sample:
        delimiter = ","
    print("DELIMITER:", repr(delimiter))
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        r = csv.reader(f, delimiter=delimiter)
        header = next(r)
        print("HEADER:", header)
        for i, row in enumerate(r):
            if i >= max_rows:
                break
            print(f"R{i+2}:", row)


def count_rows(path: Path):
    if path.suffix == ".xlsx":
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        n = ws.max_row
        wb.close()
        return n
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return sum(1 for _ in f) - 1


for p in sorted(BASE.rglob("*")):
    if p.suffix == ".xlsx":
        inspect_xlsx(p)
        print("Data rows:", count_rows(p))
    elif p.suffix == ".csv":
        inspect_csv(p)
        print("Data rows:", count_rows(p))
