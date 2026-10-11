# Graph Report - import-sap  (2026-10-11)

## Corpus Check
- 65 files · ~31,693 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 749 nodes · 1945 edges · 37 communities (35 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 99 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- render
- 7. Persyaratan Fungsional
- alpine.min.js
- data.py
- htmx.min.js
- h
- specs.py
- TODO — Import SAP (Maintenance Data)
- inspect_samples.py
- _r
- $n
- Gt
- Wt
- S
- test_profile.py
- check_keys.py
- se
- backup.sh
- importer.py
- imports.py
- main.py
- test_security.py
- queue.py
- has
- _i

## God Nodes (most connected - your core abstractions)
1. `t()` - 35 edges
2. `oe()` - 33 edges
3. `re()` - 30 edges
4. `render()` - 30 edges
5. `ae()` - 25 edges
6. `He()` - 24 edges
7. `AuditLog` - 23 edges
8. `import_upload()` - 19 edges
9. `o()` - 19 edges
10. `CurrentUser` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_extra_columns_detects_unknown()` --calls--> `extra_columns()`  [EXTRACTED]
  tests/test_pipeline.py → app/importing/pipeline.py
- `test_validate_row_missing_key()` --calls--> `validate_row()`  [EXTRACTED]
  tests/test_pipeline.py → app/importing/pipeline.py
- `test_notification_key_is_notification()` --calls--> `row_key()`  [EXTRACTED]
  tests/test_pipeline.py → app/importing/pipeline.py
- `test_sanitize_datetime()` --calls--> `sanitize()`  [EXTRACTED]
  tests/test_importing.py → app/importing/reader.py
- `test_parse_date_formats()` --calls--> `parse_date()`  [EXTRACTED]
  tests/test_importing.py → app/importing/reader.py

## Import Cycles
- None detected.

## Communities (37 total, 2 thin omitted)

### Community 0 - "render"
Cohesion: 0.05
Nodes (60): Base, get_db(), Session, admin_required(), CurrentUser, get_current_user(), load_user_by_username(), DbDep (+52 more)

### Community 1 - "7. Persyaratan Fungsional"
Cohesion: 0.04
Nodes (47): 10. Alur Utama Impor, 11. Kriteria Penerimaan Awal, 12. Risiko dan Ketergantungan, 13. Keputusan yang Masih Terbuka, 14. Rekomendasi Tahap Implementasi, 1. Ringkasan Eksekutif, 2. Latar Belakang dan Permasalahan, 3. Tujuan (+39 more)

### Community 2 - "alpine.min.js"
Cohesion: 0.06
Nodes (21): ei(), Fe(), Fr(), he(), Hi(), Hr(), je(), ji() (+13 more)

### Community 3 - "data.py"
Cohesion: 0.11
Nodes (41): bulk_delete(), bulk_delete_get(), _cell(), data_delete(), data_detail(), data_edit(), data_export(), data_list() (+33 more)

### Community 4 - "htmx.min.js"
Cohesion: 0.08
Nodes (105): Ne(), Ot(), set(), A(), ae(), ar(), at(), B() (+97 more)

### Community 5 - "h"
Cohesion: 0.21
Nodes (15): Ci(), gr(), h(), It(), j(), P(), q(), qr() (+7 more)

### Community 6 - "specs.py"
Cohesion: 0.06
Nodes (64): extra_columns(), iter_records(), key_dict(), preview(), PreviewResult, Any, Yield (row_number, converted_values, errors) for each file row., row_key() (+56 more)

### Community 8 - "TODO — Import SAP (Maintenance Data)"
Cohesion: 0.12
Nodes (16): Catatan / Risiko, Composite key (terverifikasi unik di data nyata), Fase 0 — Setup & Scaffold  `[x]`, Fase 1 — Data & Desain  `[x]`, Fase 2 — Fondasi Aplikasi (Auth & User)  `[x]`, Fase 3 — Mesin Impor  `[x]`, Fase 4 — Halaman Data & Relasi  `[x]`, Fase 5 — Hardening & Pengujian  `[x]` (+8 more)

### Community 9 - "inspect_samples.py"
Cohesion: 0.60
Nodes (4): count_rows(), inspect_csv(), inspect_xlsx(), Path

### Community 10 - "_r"
Cohesion: 0.15
Nodes (15): A(), Ae(), ar(), Bn(), d(), E(), Ee(), G() (+7 more)

### Community 11 - "$n"
Cohesion: 0.16
Nodes (15): De(), Dn(), dr(), Fn(), get(), kr(), lr(), M() (+7 more)

### Community 12 - "Gt"
Cohesion: 0.29
Nodes (8): Ce(), F(), Gt(), In(), kn(), Ln(), ue(), Vn()

### Community 13 - "Wt"
Cohesion: 0.29
Nodes (7): Cn(), effect(), qt(), Rn(), Tn(), ur(), Wt()

### Community 15 - "S"
Cohesion: 0.18
Nodes (12): at(), Bt(), ct(), ft(), Gn(), Mn(), Mr(), pt() (+4 more)

### Community 16 - "test_profile.py"
Cohesion: 0.15
Nodes (33): avatar_image(), profile_page(), _profile_response(), CsrfDep, DbDep, File, Form, get (+25 more)

### Community 19 - "se"
Cohesion: 0.33
Nodes (7): et(), Ke(), Ki(), qi(), se(), ze(), zi()

### Community 26 - "importer.py"
Cohesion: 0.11
Nodes (37): Equipment, ImportJob, _append_results(), _discard_source(), existing_keys(), _fetch_existing(), _finish(), _flush_batch() (+29 more)

### Community 27 - "imports.py"
Cohesion: 0.21
Nodes (28): _dataset_list(), _get_job(), import_cancel(), import_confirm(), import_detail(), import_errors(), import_history(), import_page() (+20 more)

### Community 28 - "main.py"
Cohesion: 0.06
Nodes (34): get_settings(), Settings, configure_logging(), lifespan(), security_headers(), health(), healthz(), get (+26 more)

### Community 30 - "test_security.py"
Cohesion: 0.27
Nodes (8): _csrf(), _first_equipment(), test_delete_writes_audit_log(), test_upload_rejects_binary_csv(), test_upload_rejects_fake_xlsx(), test_upload_rejects_unsupported_extension(), test_viewer_cannot_edit_or_delete(), test_viewer_cannot_upload()

### Community 32 - "queue.py"
Cohesion: 0.42
Nodes (9): all_queue_names(), enqueue_import(), get_redis(), queue_name(), Redis, _redis_or_skip(), test_enqueue_import_targets_datatype_queue(), test_queue_names_are_per_datatype() (+1 more)

### Community 33 - "has"
Cohesion: 0.20
Nodes (10): ge(), has(), jn(), Kt(), Qe(), sn(), ti(), Ui() (+2 more)

### Community 34 - "_i"
Cohesion: 0.33
Nodes (6): en(), fi(), _i(), Li(), nn(), pi()

## Knowledge Gaps
- **55 isolated node(s):** `backup.sh script`, `Aplikasi Import dan Analisis Data Maintenance SAP`, `1. Ringkasan Eksekutif`, `2. Latar Belakang dan Permasalahan`, `3. Tujuan` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLog` connect `render` to `data.py`, `test_profile.py`, `importer.py`, `imports.py`, `test_security.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `render()` connect `render` to `imports.py`, `test_profile.py`, `data.py`, `main.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `t()` (e.g. with `get()` and `Ne()`) actually correct?**
  _`t()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `oe()` (e.g. with `_i()` and `mi()`) actually correct?**
  _`oe()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backup.sh script`, `Aplikasi Import dan Analisis Data Maintenance SAP`, `1. Ringkasan Eksekutif` to the rest of the system?**
  _55 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `render` be split into smaller, more focused modules?**
  _Cohesion score 0.05479818230419674 - nodes in this community are weakly interconnected._
- **Should `7. Persyaratan Fungsional` be split into smaller, more focused modules?**
  _Cohesion score 0.041666666666666664 - nodes in this community are weakly interconnected._