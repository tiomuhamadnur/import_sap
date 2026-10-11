# Import SAP

Aplikasi web internal untuk mengimpor, menyimpan, mencari, dan mengekspor data maintenance SAP. Data diproses dari file Excel/CSV melalui proses validasi, pratinjau perubahan, dan worker asinkron.

## Stack dan layanan

- FastAPI, Jinja2, HTMX, Alpine.js, dan Tailwind CSS
- PostgreSQL 16 sebagai basis data
- Redis dan RQ untuk antrean impor per jenis data
- Docker Compose untuk `web`, `worker`, `db`, `redis`, dan `backup`

Jenis data yang tersedia: Equipment, Functional Location, Measuring Document, Measuring Point, Notification, dan Work Order.

## Prasyarat

Untuk menjalankan dengan Docker:

- Docker Desktop dengan Docker Compose v2
- Port host `APP_PORT` (default `8000`), `POSTGRES_PORT` (default `5432`), dan `REDIS_PORT` (default `6379`) tersedia

Untuk pengembangan lokal tanpa container aplikasi:

- Python 3.12+
- PostgreSQL 16 dan Redis 7 yang dapat diakses dari host
- Node.js hanya bila perlu membangun ulang CSS Tailwind

## Konfigurasi environment

Salin template konfigurasi terlebih dahulu.

```powershell
Copy-Item .env.example .env
```

Jangan commit `.env`. Untuk lingkungan produksi, setidaknya ubah nilai berikut menjadi kredensial rahasia yang unik:

```dotenv
APP_ENV=production
SECRET_KEY=<random-string-panjang>
POSTGRES_PASSWORD=<password-db-yang-kuat>
BOOTSTRAP_ADMIN_EMAIL=<email-admin-pertama>
BOOTSTRAP_ADMIN_PASSWORD=<password-admin-pertama-yang-kuat>
```

`POSTGRES_HOST=db` dan `REDIS_HOST=redis` adalah nilai yang tepat saat aplikasi dijalankan di Docker Compose. Untuk perintah Python yang dijalankan dari Windows host, gunakan `POSTGRES_HOST=localhost` dan `REDIS_HOST=localhost` sementara, karena nama `db` dan `redis` hanya dikenal di jaringan Docker.

## Menjalankan development dengan Docker

```powershell
docker compose up -d --build
docker compose ps
```

Buka `http://localhost:<APP_PORT>` (default: `http://localhost:8000`). Cek kesehatan aplikasi melalui `http://localhost:<APP_PORT>/health`.

Lihat log bila ada masalah:

```powershell
docker compose logs -f web
docker compose logs -f worker
```

Hentikan layanan tanpa menghapus data:

```powershell
docker compose down
```

Database dan Redis disimpan pada Docker volume, sehingga data tetap ada setelah `down`. Jangan gunakan `docker compose down -v` kecuali memang ingin menghapus seluruh database, antrean Redis, dan data unggahan sementara.

## Fresh deployment / instalasi pertama

Langkah ini dipakai untuk server baru, atau setelah volume database benar-benar kosong.

1. Siapkan `.env` dari `.env.example` dan ganti seluruh secret/kredensial default.
2. Jalankan stack:

   ```powershell
   docker compose up -d --build
   ```

3. Service `web` otomatis menjalankan `alembic upgrade head`, sehingga seluruh schema database dibuat atau dimigrasikan ke versi terbaru.
4. Saat aplikasi mulai dan tabel `users` masih kosong, aplikasi otomatis membuat satu akun Admin bootstrap menggunakan:

   - username: `BOOTSTRAP_ADMIN_USERNAME`
   - email: `BOOTSTRAP_ADMIN_EMAIL`
   - password: `BOOTSTRAP_ADMIN_PASSWORD`

   Akun ini dibuat sekali saja. Jika sudah ada user apa pun di database, nilai bootstrap tidak akan menimpa akun tersebut.
5. Login di `http://<host>:<APP_PORT>/login`. Pengguna bootstrap wajib mengganti password saat login pertama. Setelah itu, buat akun Admin/Viewer lain melalui menu **Users**.
6. Verifikasi komponen penting:

   ```powershell
   docker compose ps
   docker compose logs --tail=100 web
   docker compose logs --tail=100 worker
   ```

Data SAP tidak di-seed otomatis. Gunakan menu **Import** dengan akun Admin untuk mengunggah file sumber setelah akun pertama siap. Sample data hanya ditujukan untuk development.

## Seed sample data untuk development (opsional)

Letakkan file sample pada folder `samples/<data_type>/`, kemudian jalankan dari host setelah stack Docker aktif:

```powershell
$env:PYTHONPATH='.'
$env:POSTGRES_HOST='localhost'
.\.venv\Scripts\python.exe tools\seed_samples.py
```

Script ini bukan bagian dari proses produksi dan tidak boleh digunakan sebagai pengganti proses impor yang diaudit.

## Development lokal dan pengujian

Buat virtual environment dan instal dependensi:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Dengan PostgreSQL dan Redis dari Docker aktif, jalankan migrasi dan server lokal:

```powershell
$env:POSTGRES_HOST='localhost'
$env:REDIS_HOST='localhost'
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Worker lokal, bila diperlukan:

```powershell
$env:POSTGRES_HOST='localhost'
$env:REDIS_HOST='localhost'
rq worker --url redis://localhost:6379/0 import:notification import:work_order import:measuring_document import:measuring_point import:equipment import:functional_location
```

Jalankan test dan lint dengan koneksi database host:

```powershell
$env:POSTGRES_HOST='localhost'
python -m pytest
python -m ruff check app tests tools
```

Bangun ulang CSS setelah mengubah template atau `app/static/css/input.css`:

```powershell
npx --yes tailwindcss@3.4.17 -c tailwind.config.js -i app/static/css/input.css -o app/static/css/app.css --minify
```

## Migration database

Container `web` menjalankan migration otomatis saat start. Untuk membuat migration baru saat pengembangan:

```powershell
$env:POSTGRES_HOST='localhost'
python -m alembic revision --autogenerate -m "deskripsi perubahan"
python -m alembic upgrade head
```

Sebelum deployment, migration baru harus sudah berada di repository. Deployment kemudian cukup menjalankan `docker compose up -d --build`; jangan membuat migration baru langsung di server produksi.

## Operasional produksi

- Jalankan aplikasi di balik reverse proxy HTTPS; Docker Compose mengekspos aplikasi pada `APP_PORT` (default `8000`).
- Batasi atau jangan expose port PostgreSQL (`POSTGRES_PORT`, default `5432`) dan Redis (`REDIS_PORT`, default `6379`) ke jaringan publik. Port tersebut dipetakan untuk kemudahan development.
- Simpan `.env` dengan akses terbatas dan gunakan secret yang berbeda untuk setiap environment.
- Service `backup` membuat dump PostgreSQL format custom secara berkala ke direktori `backups/`, dengan retensi `BACKUP_RETENTION_DAYS` (default 14 hari). Direktori ini perlu dicadangkan ke storage terpisah.
- Uji pemulihan backup sebelum go-live. Contoh restore ke database target:

  ```powershell
  docker compose exec -T db pg_restore -U <db-user> -d <db-target> --clean --if-exists < backup.dump
  ```

  Jalankan restore hanya pada database target yang sudah dipastikan benar; opsi `--clean` menghapus objek yang ada.

## Reset password Admin

Jika memiliki akses ke environment aplikasi dan database, password dapat di-reset dari host:

```powershell
$env:POSTGRES_HOST='localhost'
.\.venv\Scripts\python.exe -m app.seed reset-password <username> <password-baru>
```

Pengguna tersebut akan diwajibkan mengganti password pada login berikutnya.

## Catatan penting

- File sumber hanya disimpan sementara selama pekerjaan impor berjalan, lalu dihapus setelah proses terminal. Riwayat dan hasil per-record tetap tersimpan di database.
- Jangan menghapus Docker volume database untuk deployment yang sudah berisi data.
- Lihat [TODO.md](TODO.md) untuk keputusan teknis, batasan performa, dan riwayat implementasi.
