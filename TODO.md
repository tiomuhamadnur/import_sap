# TODO — Import SAP (Maintenance Data)

Trace pelaksanaan pengembangan. Legenda: `[x]` selesai · `[~]` sebagian · `[ ]` belum.

Terakhir diperbarui: 11 Oktober 2026

---

## Keputusan Terkunci

| Topik | Keputusan |
|---|---|
| Stack | FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind (vendor lokal) |
| Database | PostgreSQL 16 |
| Queue | Redis + RQ worker |
| Deployment | Docker Compose internal (web, worker, db, redis, backup) |
| Bahasa UI | English; waktu disimpan UTC, ditampilkan WIB |
| Format file | **Semua jenis data = `.xlsx`** (Excel). CSV tetap didukung parser |
| Pemetaan kolom | **By header name (exact match) + occurrence** — key wajib harus cocok persis |
| Aturan update | Overwrite otomatis (upsert by natural key) |
| Mixed valid/invalid | Admin pilih saat pratinjau |
| Rollback | Per-record, lewati & catat konflik |
| Akun user | Nonaktifkan (bukan hapus); reset password & force change oleh Admin |
| Identitas user | Nama + email wajib (email unik); username & telepon opsional; login via email atau username |
| File sumber | Tidak disimpan (rollback dari histori DB) |
| Ekspor | Ikut filter aktif, tanpa batas (streaming) |
| URL record | Detail/edit/hapus memakai `public_id` (UUID acak), bukan PK numerik — URL tidak bisa ditebak |
| Foto profil | Upload gambar (≤1 MB) → di-resize & kompres JPEG (≤200 KB) via Pillow, disimpan sebagai string data-URI di kolom `user.avatar`; disajikan lewat `GET /avatar/{id}` |
| Backup | pg_dump harian, retensi 14 hari; audit log permanen |

### Composite key (terverifikasi unik di data nyata)

| Entitas | File | Key | Baris sampel |
|---|---|---|---|
| `equipment` | equipment.xlsx | `Equipment` | 65.206 |
| `functional_location` | functional_location.xlsx | `Functional Loc.` | 8.179 |
| `measuring_document` | measuring_document.xlsx | `MeasDocument` | 186 |
| `measuring_point` | measuring_point.xlsx | `Measuring point` | 38.800 |
| `notification` | notification.xlsx | `Notification` | 1.366 |
| `work_order` | work_order.xlsx | `Order` | 11.609 |

---

## Fase 0 — Setup & Scaffold  `[x]`

- [x] Struktur repo (`app/`, `tools/`, `migrations/`, `samples/`, `tests/`)
- [x] Docker Compose: web + worker + db + redis + backup
- [x] Config env, logging, settings
- [x] FastAPI skeleton + healthcheck (`/health`, `/healthz`)
- [x] Alembic init + migration awal (tabel sistem)
- [x] Ruff + pytest + smoke test
- [x] Verifikasi: lint, test, docker build & up

## Fase 1 — Data & Desain  `[x]`

- [x] Analisis 5 sampel SAP (header, tipe data, duplikat header)
- [x] Konversi `notification` & `work_order` dari CSV → XLSX (format seragam)
- [x] Tetapkan composite key tiap entitas (unik, terverifikasi)
- [x] Tetapkan kolom relasi (EQ/FL/NOTIF/ORDER)
- [x] Model 5 entitas + `raw_data` JSONB (simpan semua kolom SAP asli)
- [x] Parser Excel/CSV (duplicate header, delimiter, angka `1.234,56`, tanggal `DD/MM/YYYY`)
- [x] Spec kolom per jenis data (`app/importing/specs.py`)
- [x] Validasi struktur: key/header wajib harus match (`required_headers`)
- [x] Upsert idempoten (`app/services/upsert.py`)
- [x] Migration tabel entitas + apply
- [x] Seed sampel ke DB (86.546 record) + uji idempotensi
- [x] Unit test parser/spec (14 test)
- [x] Menu Sidebar + route Functional Location

## Fase 2 — Fondasi Aplikasi (Auth & User)  `[x]`

- [x] Halaman login + logout (terhubung DB, CSRF-protected)
- [x] Seed user admin default (bootstrap saat startup, `app/seed.py`)
- [x] Force change password saat login pertama
- [x] Middleware/guard role Admin vs Viewer (backend: `require_user`, `admin_required`)
- [x] Manajemen User: list, create, edit, nonaktifkan, set role
- [x] Reset password oleh Admin (must_change_password lagi)
- [x] Audit log: login ok/gagal, logout, change/reset password, kelola user
- [x] Sesi cookie (SessionMiddleware, SameSite=Lax) + CSRF token per sesi
- [x] Test auth (18 test lolos: CSRF, redirect guard)

## Fase 3 — Mesin Impor  `[x]`

- [x] Halaman Import: pilih jenis data + upload (`app/routers/imports.py`)
- [x] Validasi struktur file → tolak bila key/header wajib tidak cocok
- [x] Peringatan kolom tambahan tak dikenali (`extra_columns`)
- [x] Validasi isi record + daftar error per baris (`pipeline.iter_records`)
- [x] Pratinjau diff (baru/update/error) via composite key (`pipeline.preview`)
- [x] Pilihan Admin: lanjut partial / abort total (`on_invalid`)
- [x] Enqueue Redis + RQ worker (queue per jenis `import:<datatype>`; beda jenis paralel, sama jenis antre)
- [x] Batch/streaming upsert + progress (`import_job.processed/total_rows`)
- [x] Hasil per record (`import_record_result`) + ringkasan
- [x] Gagal parsial + unggah ulang aman (upsert idempoten)
- [x] Riwayat Import + filter + status + detail (HTMX polling)
- [x] Rollback sesi per-record (skip konflik `import_job_id` berbeda)
- [~] Auto-link Equipment/Functional Location → relasi berbasis nilai; tampilan "unlinked" dikerjakan di Fase 4

## Fase 4 — Halaman Data & Relasi  `[x]`

- [x] Tabel + pagination 5 entitas
- [x] Pencarian per halaman
- [x] Filter per kolom
- [x] Ekspor Excel/CSV streaming (ikut filter)
- [x] Edit record (Admin)
- [x] Hapus satu + hapus massal + konfirmasi
- [x] Tampilan relasi + status "unlinked"
- [x] Hapus Equipment tidak menghapus record transaksi

## Fase 5 — Hardening & Pengujian  `[x]`

- [x] Uji volume 100k–1jt record
- [x] Uji concurrent import
- [x] Uji gagal parsial + rollback konflik
- [x] Uji hak akses role + audit
- [x] Backup/restore drill (retensi 14 hari)
- [x] Uji keamanan web & validasi tipe/ukuran file
- [x] Tuning indeks & query halaman

---

## Fase 6 — UI/UX Overhaul  `[x]`

- [x] Design system (`_macros.html`): ikon SVG, status/role/record badge, alert, stat card, empty state, pagination bernomor, progress bar
- [x] Layout responsif: sidebar off-canvas (HP/tablet) + fixed (desktop), header sticky, dropdown user (avatar + role)
- [x] Redesign halaman auth (login 2-panel, change password) + toggle show/hide password
- [x] Halaman data: header tabel sticky, filter chips, pagination bernomor + info rentang, kolom numerik rata kanan
- [x] Detail record: kartu ringkasan, relasi, dan "Raw SAP values" (collapsible JSON)
- [x] Edit record via modal (fragment HTMX `data_edit_modal.html`, fallback halaman penuh)
- [x] Modal konfirmasi global (Alpine) menggantikan `window.confirm` untuk hapus/rollback/discard
- [x] Poles halaman Users, User form, Import, Preview, Job, Import History, partial status/error
- [x] Verifikasi: 48 test lolos, `ruff` bersih, semua halaman 200 (TestClient), CSS dibangun ulang

### Identifier publik (UUID)  `[x]`

- [x] Kolom `public_id` (uuid) + unique index di 5 tabel entitas (migration `c3a9e1f27b04`)
- [x] Detail/edit/update/hapus pakai `public_id`; PK numerik tidak lagi di URL (URL numerik → 422, UUID acak → 404)
- [x] Snapshot rollback mengecualikan `public_id` (mencegah error serialisasi JSONB)
- [x] Bulk delete tetap memakai PK numerik (dikirim di body POST, bukan URL)

---

## Fase 7 — Entitas Measuring Point  `[x]`

- [x] Analisis sampel `samples/measuring_point/measuring_point.xlsx`: 38.800 baris, 47 kolom, tanpa header duplikat, key `Measuring point` unik 100%
- [x] Model `MeasuringPoint` + kolom `public_id` (UUID) + FK `import_job_id` + `raw_data` (migration `d7e4b1c90a24`)
- [x] Spec impor `MEASURING_POINT` (26 kolom terkurasi) + registrasi di `DATASETS`, `DATA_TYPES`, antrean worker `import:measuring_point`
- [x] Dataview `measuring-point` (16 kolom, relasi ke Equipment & Functional Location) + item sidebar
- [x] Indeks trigram: description, equipment, functional_location, characteristic
- [x] Seed sampel 38.800 baris; 49 test lolos; `ruff` bersih; verifikasi halaman list/detail/edit 200

---

## Fase 8 — Kontak User & Login via Email  `[x]`

- [x] Kolom baru `user`: `name` (wajib), `email` (wajib, unik, huruf kecil), `phone` (opsional); `username` jadi opsional (migration `e2f5a7c3b901`)
- [x] Login memakai email **atau** username (`load_user_by_identifier`); label form "Email or username"
- [x] Form create/edit: name, email, username (opsional), phone (opsional); validasi nama/email wajib + format `@`, cek duplikat email/username
- [x] Header & menu sidebar menampilkan `display_name` + `initials` (fallback ke username/email)
- [x] Tabel Users: kolom Name (avatar), Email, Phone
- [x] Seed admin default diberi `name`; 53 test lolos (`tests/test_users.py` baru); `ruff` bersih; verifikasi halaman 200

---

## Fase 9 — Halaman Import & Profil  `[x]`

- [x] Halaman Import: pilihan **Data type** default kosong ("Select a data type…"), tidak lagi terpilih Equipment
- [x] Tabel "Recent imports": kolom **By** menampilkan nama user pengunggah (`_user_map`)
- [x] Riwayat Import: kolom **By**; halaman detail menampilkan nama/email pengunggah (`actor`)
- [x] Halaman **Profile**: lihat detail akun, edit nama/username/telepon (email read-only), tombol Change password
- [x] Upload foto profil (≤1 MB) → di-resize/kompres JPEG ≤200 KB via Pillow, disimpan sebagai data-URI di `user.avatar` (migration `e39f3523523a`); `GET /avatar/{id}` menyajikan gambar
- [x] Avatar tampil di sidebar, header, dan tabel Users (fallback inisial)
- [x] Menu dropdown header: tautan **Profile** di atas **Change password**
- [x] 8 test baru (`tests/test_profile.py`); 62 test lolos; `ruff` bersih; CSS + container dibangun ulang; verifikasi halaman 200

---

## Perintah Pengembangan

```powershell
# Start stack
docker compose up -d --build

# Lint & test (venv lokal)
.\.venv\Scripts\python.exe -m ruff check app tests tools
.\.venv\Scripts\python.exe -m ruff format app tests tools
.\.venv\Scripts\python.exe -m pytest

# Migration
$env:POSTGRES_HOST="localhost"; .\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "..."
$env:POSTGRES_HOST="localhost"; .\.venv\Scripts\python.exe -m alembic upgrade head

# Seed sampel ke DB
$env:PYTHONPATH="."; $env:POSTGRES_HOST="localhost"; .\.venv\Scripts\python.exe tools\seed_samples.py

# Reset password user (admin)
$env:PYTHONPATH="."; $env:POSTGRES_HOST="localhost"; .\.venv\Scripts\python.exe -m app.seed reset-password admin admin123

# Worker (antrean impor) — setiap jenis punya antrean sendiri
rq worker --url redis://localhost:6379/0 import:notification import:work_order import:measuring_document import:measuring_point import:equipment import:functional_location

# Build CSS Tailwind (wajib dijalankan ulang setiap kali template HTML berubah)
npx --yes tailwindcss@3.4.17 -c tailwind.config.js -i app/static/css/input.css -o app/static/css/app.css --minify
```

## Catatan / Risiko

- Sampel `measuring_document` baru 186 baris → validasi volume perlu data lebih besar.
- Relasi banyak kosong di data nyata (mis. Work Order hampir semua tanpa Notification) → tampilkan sebagai "unlinked".
- Belum ada: target performa konkret, kebijakan retensi file sumber (file tidak disimpan).
- Pratinjau impor dihitung sinkron saat upload (scan penuh + muat seluruh composite key). Perlu diuji/dioptimalkan untuk volume 100k–1jt.
- Rollback dijalankan sinkron di request admin; untuk sesi sangat besar sebaiknya dijadikan background job (Fase 5).
- File sumber disimpan sementara di volume `import_uploads` saat diproses, lalu dihapus setelah selesai.
- Filter kolom memakai `CAST(kolom AS text) ILIKE` (seragam untuk teks/numerik/tanggal) → tidak memakai indeks; perlu tuning/indeks Fase 5 untuk tabel besar.
- Halaman data menghitung `COUNT(*)` penuh tiap request untuk total pagination; pertimbangkan estimasi/keyset pagination bila volume besar.
- Ekspor XLSX menulis ke file sementara di server lalu di-stream; CSV streaming langsung (aman untuk volume besar).
- Hasil uji volume (equipment 65k nyata + 300k sintetis = 365k baris): COUNT filter description (indeks trigram) 107 ms; pencarian `q` 4 kolom 122 ms; halaman-1 (limit 25) 121 ms; deep page OFFSET 200k 266 ms; stream 300k baris 4,3 s; COUNT(*) seluruh tabel 24 ms. Indeks trigram mempercepat `ILIKE '%...%'` (mis. description: 68 ms → 0,7 ms).
- Pencarian `q` masih menyertakan kolom tanpa indeks trigram (mis. serial_number/location) → untuk volume lebih besar tambahkan indeks trigram pada sisa kolom `searchable` atau batasi kolom pencarian.
- Deep OFFSET mahal pada volume besar; pertimbangkan keyset pagination bila perlu.
- Setiap indeks GIN trigram menambah biaya tulis saat impor; timbang bila volume impor sangat besar.
- Backup/restore drill: `pg_dump -Fc` (6 MB) → restore ke DB scratch cocok (equipment 65.206, work_order 11.609, notification 1.366). Retensi 14 hari via `find -mtime +14`.
