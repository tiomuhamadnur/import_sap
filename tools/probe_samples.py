from pathlib import Path

from app.importing import DATASETS, convert, rows_iterator, validate_structure


def probe(data_type, path):
    spec = DATASETS[data_type]
    it = rows_iterator(path)
    headers_checked = False
    n = 0
    errors = 0
    sample_fields = None
    for row in it:
        if not headers_checked:
            headers = list(row.keys())
            missing = validate_structure(spec, [h for h, _ in set(headers)])
            print(f"[{data_type}] headers found={len(headers)} missing_required={missing}")
            headers_checked = True
        n += 1
        vals = convert(spec, row)
        if spec.keys[0].field not in vals or vals[spec.keys[0].field] is None:
            errors += 1
            continue
        if n <= 2 and sample_fields is None:
            sample_fields = vals
    print(f"[{data_type}] rows={n} missing_key={errors}")
    if sample_fields:
        print(
            f"[{data_type}] sample: id={sample_fields.get('id','-')} "
            f"keys={ {k.field: sample_fields.get(k.field) for k in spec.keys} }"
        )
        shown = 0
        for k, v in sample_fields.items():
            if k == "raw_data" or v is None or v == "":
                continue
            print(f"    {k} = {v}")
            shown += 1
            if shown >= 10:
                break
    print()


B = Path("samples")
probe("equipment", B / "equipment" / "equipment.xlsx")
probe("functional_location", B / "functional_location" / "functional_location.xlsx")
probe("measuring_document", B / "measuring_document" / "measuring_document.xlsx")
probe("measuring_point", B / "measuring_point" / "measuring_point.xlsx")
probe("notification", B / "notification" / "notification.csv")
probe("work_order", B / "work_order" / "work_order.csv")
