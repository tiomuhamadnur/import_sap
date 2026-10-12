# Business Requirements Document (BRD)
## Aplikasi Import dan Analisis Data Maintenance SAP

**Status dokumen:** As-built — implementasi selesai (lihat [TODO.md](TODO.md) untuk trace pelaksanaan)  
**Versi:** 1.0  
**Tanggal:** 12 Oktober 2026  
**Bahasa:** Indonesia

> **Catatan status:** Dokumen ini awalnya disusun sebagai draft kebutuhan. Seluruh keputusan terbuka pada saat draft (composite key, kolom wajib, aturan update, backup, stack, dsb.) kini sudah ditetapkan dan diimplementasikan. Tabel **Keputusan Terkunci** di [TODO.md](TODO.md) menjadi acuan tunggal keputusan final; dokumen ini dipertahankan sebagai rujukan latar belakang dan kebutuhan bisnis.
>
> Perluasan di luar draft awal: implementasi menambahkan **Functional Location** dan **Measuring Point** (di luar empat jenis data yang disebut di draft), sehingga saat ini ada **enam** jenis data.

---

## 1. Ringkasan Eksekutif

Aplikasi web ini digunakan untuk mengimpor data hasil ekspor SAP ke database tersendiri agar data dapat dicari, difilter, diekspor, dan dianalisis tanpa harus melakukan analisis langsung di SAP.

Aplikasi menangani empat jenis data:
1. Notification
2. Work Order
3. Measuring Document
4. Equipment

Setiap jenis data disimpan pada tabel tersendiri. Equipment merupakan master data yang dapat dihubungkan dengan Notification, Work Order, dan Measuring Document. Aplikasi mendukung banyak pengguna dengan dua peran utama: **Admin** dan **Viewer**.

BRD ini merupakan draft awal. Sampel ekspor SAP belum tersedia, sehingga nama kolom wajib, composite key, aturan relasi rinci, dan kebijakan pembaruan untuk setiap jenis data harus dikonfirmasi sebelum desain teknis final.

## 2. Latar Belakang dan Permasalahan

Data maintenance yang diekspor dari SAP perlu tersedia pada database terpisah untuk mendukung analisis dan eksplorasi data yang lebih fleksibel. Proses pemuatan data harus dapat diulang tanpa membuat duplikasi, mempertahankan data lama yang tidak muncul dalam file terbaru, serta memberikan transparansi atas perubahan dan kegagalan impor.

Aplikasi harus dapat menangani volume data yang cukup besar dan menyediakan riwayat serta audit aktivitas pengguna.

## 3. Tujuan

- Menyediakan proses impor data SAP yang terkontrol dan dapat diulang.
- Menyimpan Notification, Work Order, Measuring Document, dan Equipment secara terpisah.
- Mendukung analisis lintas data melalui relasi antarentitas.
- Menyediakan pencarian, filter per kolom, dan ekspor data.
- Mencatat riwayat impor, hasil pemrosesan, dan aktivitas penting pengguna.
- Mendukung pemrosesan file besar secara asinkron.
- Menyediakan kontrol akses berbasis peran.

## 4. Ruang Lingkup

### 4.1 Termasuk dalam ruang lingkup

- Autentikasi menggunakan username dan password lokal.
- Manajemen akun pengguna oleh Admin.
- Impor file Excel atau CSV.
- Pemilihan jenis data secara manual sebelum file diunggah.
- Validasi struktur dan isi file sebelum impor.
- Pratinjau perbandingan dengan data yang sudah tersimpan.
- Pemrosesan impor sebagai background job.
- Pemantauan progres dan status impor.
- Penanganan kegagalan parsial dan impor ulang.
- Penyimpanan riwayat impor dan audit log.
- Halaman data untuk keempat jenis data.
- Filter per kolom, pencarian pada halaman terkait, dan ekspor Excel/CSV.
- Pembaruan dan penghapusan data oleh Admin, termasuk penghapusan massal.
- Relasi antara Equipment dengan Notification, Work Order, dan Measuring Document.

### 4.2 Di luar ruang lingkup atau belum diputuskan

- Integrasi langsung melalui API SAP; sumber data saat ini adalah file ekspor.
- Penetapan nama kolom wajib dan composite key final.
- Aturan pembaruan final untuk setiap jenis data.
- Dashboard analitik khusus.
- Kebijakan backup, retensi, dan pemulihan bencana.
- Detail deployment, infrastruktur, serta teknologi aplikasi selain PostgreSQL dan Docker.
- Mekanisme analisis lanjutan yang spesifik, karena kebutuhan analitik akan diperinci setelah sampel data tersedia.

## 5. Pengguna dan Hak Akses

Aplikasi mendukung banyak akun pengguna yang dikelola secara lokal.

| Fitur | Admin | Viewer |
|---|---|---|
| Login/logout | Ya | Ya |
| Melihat dan menganalisis data | Ya | Ya |
| Mengimpor data | Ya | Tidak |
| Melihat riwayat dan hasil impor | Ya | Ya |
| Melakukan rollback sesi impor | Ya, sesuai aturan sesi | Tidak |
| Mengubah data secara manual | Ya | Tidak |
| Menghapus data | Ya | Tidak |
| Menghapus banyak record sekaligus | Ya | Tidak |
| Mengelola pengguna | Ya | Tidak |
| Melihat audit log | Ya | Tidak |

Detail izin untuk tindakan administratif tertentu, termasuk rollback sesi impor dan akses ke rincian audit, perlu dipastikan saat desain teknis.

## 6. Navigasi dan Antarmuka

Aplikasi menggunakan sidebar dengan menu:

1. Import
2. Notification
3. Work Order
4. Measuring Document
5. Equipment
6. Riwayat Import
7. Manajemen User

Halaman awal adalah **Import**, dengan pilihan jenis data yang akan diimpor. Tidak diperlukan dashboard analitik terpisah pada tahap awal.

Setiap halaman data menyediakan:
- Tabel data.
- Pencarian yang berlaku pada halaman tersebut saja.
- Filter untuk setiap kolom data.
- Ekspor hasil data ke Excel dan CSV.
- Aksi ubah dan hapus untuk Admin.
- Pemilihan beberapa record untuk penghapusan massal oleh Admin.

Kolom yang ditampilkan, format filter, pagination, dan batas jumlah baris per halaman ditetapkan pada tahap desain UI/UX.

## 7. Persyaratan Fungsional

### FR-01 — Pemilihan jenis data

Sebelum mengunggah file, Admin harus memilih salah satu jenis data: Notification, Work Order, Measuring Document, atau Equipment. Sistem tidak melakukan deteksi jenis data secara otomatis.

### FR-02 — Format file

Sistem menerima file Excel dan CSV. Satu file Excel hanya perlu memiliki satu sheet data. Penanganan encoding, pemisah CSV, format tanggal, format angka, dan ukuran file perlu ditentukan dalam desain teknis.

### FR-03 — Pemetaan kolom

Nama header file menjadi acuan untuk mengidentifikasi kolom. Urutan kolom dapat berbeda dari satu file ke file lainnya.

Sistem harus:
- Membaca kolom berdasarkan nama header, bukan posisi kolom.
- Mempertahankan kolom dan nilai asli SAP yang dikenali.
- Menolak impor apabila kolom wajib tidak tersedia atau nama header wajib tidak cocok.
- Menampilkan kesalahan validasi secara jelas.
- Mengabaikan kolom tambahan yang tidak dikenali, tetapi memberikan peringatan sebelum Admin melanjutkan.

Nama kolom wajib dan aturan header per jenis data masih **TBD** dan harus ditetapkan setelah sampel ekspor SAP diperiksa.

### FR-04 — Validasi sebelum impor

Sebelum impor dimulai, sistem harus memvalidasi struktur file dan isi record, lalu menampilkan seluruh kesalahan validasi yang dapat dideteksi.

Hasil validasi setidaknya memuat:
- Jumlah record yang dibaca.
- Jumlah record valid.
- Jumlah record yang memiliki kesalahan.
- Daftar kesalahan dengan nomor baris/record dan penjelasan.
- Peringatan, termasuk kolom tambahan yang diabaikan.
- Pilihan bagi Admin untuk melanjutkan atau membatalkan.

Jika struktur inti file tidak valid, seperti kolom wajib hilang atau header wajib tidak cocok, impor ditolak dan tidak boleh diteruskan.

Jika record valid dan tidak valid bercampur, Admin menentukan tindakan setelah melihat hasil validasi. Perilaku rinci untuk record yang tidak valid harus ditetapkan pada tahap desain.

### FR-05 — Pratinjau perubahan data

Sebelum mengonfirmasi impor, sistem harus menampilkan perbandingan dengan database saat ini, sekurang-kurangnya:
- Record baru yang akan ditambahkan.
- Record lama yang terdeteksi akan diperbarui.
- Record yang tidak dapat diproses atau mengalami kesalahan.
- Ringkasan perubahan yang akan diterapkan.

Identitas record ditentukan menggunakan **composite key** yang terdiri dari beberapa kolom. Komposisi key untuk setiap jenis data belum ditentukan dan harus diperiksa dari sampel ekspor SAP.

Aturan pembaruan setiap jenis data belum ditetapkan. Belum diputuskan apakah perubahan nilai akan langsung diterapkan atau memerlukan persetujuan Admin. Aturan ini tidak boleh diasumsikan sama untuk semua jenis data.

### FR-06 — Aturan penggabungan data

Pada impor ulang:
- Record yang cocok berdasarkan composite key dikenali sebagai record yang sudah ada.
- Record baru ditambahkan.
- Record yang sudah ada dapat diperbarui sesuai aturan pembaruan jenis data yang kelak ditetapkan.
- Record yang ada di database tetapi tidak muncul di file terbaru **tidak dihapus** hanya karena tidak ada di file tersebut.

### FR-07 — Impor asinkron untuk file besar

Impor dijalankan sebagai background job agar pengguna dapat meninggalkan halaman tanpa menghentikan proses.

Sistem harus menyediakan:
- Progress bar.
- Status proses yang dapat dipantau dari halaman Riwayat Import.
- Status seperti antre, berjalan, selesai, selesai sebagian, dan gagal.
- Ringkasan jumlah record berhasil, ditambahkan, diperbarui, dilewati, dan gagal.
- Pesan kesalahan yang membantu Admin menentukan langkah berikutnya.

File besar diproses menggunakan streaming atau batch processing, bukan mengharuskan seluruh file dimuat ke memori sekaligus. Target volume awal adalah sekitar **100.000 sampai 1.000.000 record** untuk periode data 1–3 tahun. Batas ukuran file belum ditetapkan.

### FR-08 — Impor gagal dan impor ulang

Jika proses gagal di tengah jalan:
- Record yang sudah berhasil diproses tetap disimpan.
- Record yang belum berhasil diproses ditandai gagal atau belum diproses.
- Riwayat impor menunjukkan hasil parsial dan penyebab kegagalan yang tersedia.
- Admin dapat mengunggah ulang seluruh file.

Pada impor ulang, sistem menggunakan composite key dan aturan upsert yang berlaku agar data yang sudah berhasil tidak menimbulkan duplikasi. Record yang sudah berhasil dan tidak mengalami perubahan semestinya tidak diproses ulang secara tidak perlu. Detail mekanisme ini perlu dirancang agar aman untuk impor yang terputus.

### FR-09 — Antrean dan konkurensi impor

- Impor untuk jenis data yang berbeda boleh berjalan bersamaan.
- Impor untuk jenis data yang sama harus masuk antrean sehingga tidak berjalan bersamaan.
- Sistem harus mengelola status antrean dan memberi tahu pengguna jika job belum mulai.
- Integritas data tetap harus dijaga melalui transaksi, constraint, dan/atau mekanisme locking yang sesuai.

### FR-10 — Riwayat impor

Sistem menyimpan riwayat setiap sesi impor, meliputi:
- Pengguna yang memulai impor.
- Jenis data.
- Nama file.
- Waktu mulai dan selesai.
- Status proses.
- Jumlah record yang dibaca, ditambahkan, diperbarui, dilewati, dan gagal.
- Rincian kesalahan yang relevan.
- Status rollback jika dilakukan.

Admin dapat melakukan rollback pada sesi impor sesuai ketentuan. Rollback hanya boleh membatalkan perubahan yang dilakukan oleh sesi tersebut dan tidak boleh menghapus atau menimpa perubahan yang berasal dari sesi lain. Desain harus menangani konflik jika record telah diubah kembali setelah sesi awal.

### FR-11 — Relasi antarentitas

Equipment merupakan master data terpisah yang dapat direlasikan dengan Notification, Work Order, dan Measuring Document.

Relasi Notification–Work Order juga perlu tersedia apabila terdapat nomor referensi yang sesuai. Jika referensi tidak tersedia, kedua jenis data tetap dapat disimpan dan dianalisis secara terpisah.

Jika Notification atau Work Order diimpor sebelum master Equipment tersedia:
- Impor tetap berjalan.
- Data transaksi disimpan.
- Sistem mencoba menautkan Equipment secara otomatis ketika master terkait kemudian tersedia.

Jika Equipment dihapus oleh Admin:
- Data Notification, Work Order, dan Measuring Document yang terkait tidak ikut dihapus.
- Data transaksi tetap tersedia.
- Relasi yang kehilangan master ditandai sebagai tidak tersedia atau tidak terhubung.

Nama kolom relasi, kardinalitas, dan aturan pencocokan final menunggu pemeriksaan sampel ekspor SAP.

### FR-12 — Perubahan Equipment saat impor

Jika Equipment yang sudah ada ditemukan dalam file dengan atribut berbeda, sistem harus menampilkan perbandingan nilai lama dan baru. Perubahan tidak boleh diterapkan secara otomatis sebelum aturan final disepakati.

### FR-13 — Halaman data

Sistem menyediakan halaman data terpisah untuk Notification, Work Order, Measuring Document, dan Equipment. Setiap halaman mendukung pencarian dan filter per kolom, serta ekspor data.

Analisis relasi antarjenis data dilakukan melalui halaman data yang relevan; dashboard analitik khusus tidak menjadi persyaratan tahap awal.

### FR-14 — Ekspor data

Pengguna yang berwenang melihat data dapat mengekspor data ke Excel dan CSV. Perilaku ekspor terhadap filter aktif perlu ditetapkan pada desain UI/UX; rekomendasi awal adalah mengekspor hasil yang sedang difilter agar sesuai konteks analisis pengguna.

### FR-15 — Manajemen data

Admin dapat mengubah dan menghapus data secara manual. Admin juga dapat memilih beberapa record dan menghapusnya sekaligus.

Penghapusan harus disertai konfirmasi. Dampak terhadap relasi mengikuti aturan integritas data, termasuk aturan bahwa penghapusan Equipment tidak menghapus record transaksi terkait.

### FR-16 — Manajemen pengguna

Admin dapat membuat, melihat, mengubah, menonaktifkan, dan/atau menghapus akun pengguna serta menetapkan peran Admin atau Viewer. Detail apakah akun dihapus permanen atau dinonaktifkan perlu ditetapkan pada desain teknis.

Password harus disimpan dalam bentuk hash yang aman, bukan teks biasa. Aplikasi harus menerapkan kontrol akses pada backend, bukan hanya menyembunyikan tombol di antarmuka.

### FR-17 — Audit log

Sistem mencatat aktivitas penting, setidaknya:
- Login yang berhasil dan gagal, sesuai kebijakan keamanan.
- Mulai, selesai, dan kegagalan impor.
- Perubahan data manual.
- Penghapusan satu atau banyak record.
- Rollback sesi impor.
- Pembuatan, perubahan, penonaktifan, atau penghapusan akun.
- Perubahan peran pengguna.

Log mencatat pengguna, waktu, jenis tindakan, objek terkait, dan hasil tindakan. Nilai sebelum/sesudah untuk perubahan penting sebaiknya disimpan jika memungkinkan. Kebijakan retensi audit log belum ditentukan.

## 8. Persyaratan Data dan Model Awal

Tabel/entitas konseptual minimal:

| Entitas | Tujuan | Keterangan |
|---|---|---|
| `equipment` | Master Equipment | Memiliki key unik yang masih harus ditentukan |
| `notification` | Data Notification SAP | Composite key dan kolom wajib TBD |
| `work_order` | Data Work Order SAP | Composite key dan kolom wajib TBD |
| `measuring_document` | Data Measuring Document SAP | Composite key dan kolom wajib TBD |
| `import_job` | Metadata sesi impor | Status, file, pengguna, waktu, ringkasan hasil |
| `import_record_result` | Hasil pemrosesan per record | Berhasil/gagal/dilewati dan pesan kesalahan; rancangan fisik TBD |
| `users` | Akun pengguna | Username, hash password, peran, status |
| `audit_log` | Catatan aktivitas penting | Pengguna, waktu, tindakan, objek, hasil |

Entitas ini bersifat konseptual. Struktur tabel fisik, indeks, tipe data, foreign key, dan strategi penyimpanan nilai SAP asli ditetapkan setelah sampel tersedia.

### 8.1 Composite key

Composite key wajib ditentukan secara terpisah untuk Notification, Work Order, Measuring Document, dan Equipment. Sistem tidak boleh menebak key final dari nama entitas saja.

### 8.2 Pelestarian data sumber

Data dan nama kolom SAP yang relevan harus dipertahankan. Perlu diputuskan apakah skema akan menggunakan kolom terstruktur yang eksplisit, penyimpanan kolom sumber tambahan, atau pendekatan kombinasi setelah struktur file diketahui.

## 9. Persyaratan Nonfungsional

### NFR-01 — Kinerja dan kapasitas

- Mendukung target awal 100.000–1.000.000 record untuk data historis 1–3 tahun.
- Menggunakan pemrosesan batch/streaming untuk file besar.
- Menyediakan progres yang informatif.
- Halaman data menggunakan pagination dan query database yang efisien.
- Indeks disesuaikan dengan composite key, kolom relasi, dan kolom yang sering difilter.

Target waktu impor dan respons halaman belum ditetapkan dan perlu diuji menggunakan data representatif.

### NFR-02 — Konsistensi data

- Proses impor harus idempoten sejauh memungkinkan berdasarkan composite key.
- Impor ulang tidak boleh menghasilkan duplikasi record yang sama.
- Konflik concurrent import harus ditangani.
- Perubahan yang diterapkan harus dapat ditelusuri melalui riwayat impor dan audit log.

### NFR-03 — Keamanan

- Autentikasi username/password lokal.
- Password di-hash menggunakan algoritma yang sesuai.
- Otorisasi diperiksa pada backend.
- Validasi tipe file, ukuran, struktur, dan isi file.
- Akses database tidak boleh diekspos langsung kepada pengguna.
- Proteksi terhadap serangan umum web dan pembatasan akses ke file impor.
- Kebijakan session, password reset, dan pembatasan percobaan login perlu ditentukan.

### NFR-04 — Deployment

- PostgreSQL sebagai database.
- Docker sebagai dasar deployment.
- Detail stack frontend/backend, reverse proxy, queue worker, dan object/file storage belum ditetapkan.

### NFR-05 — Backup dan pemulihan

Kebijakan backup, jadwal, retensi, enkripsi, dan pengujian restore belum diputuskan. Hal ini harus diselesaikan sebelum aplikasi digunakan untuk operasional.

## 10. Alur Utama Impor

1. Admin membuka menu **Import**.
2. Admin memilih jenis data.
3. Admin mengunggah file Excel/CSV.
4. Sistem memeriksa format, header, kolom wajib, dan isi file.
5. Sistem menampilkan seluruh kesalahan serta peringatan yang ditemukan.
6. Jika struktur inti tidak valid, sistem menolak file dan menjelaskan kesalahan.
7. Jika struktur dapat diproses, sistem membandingkan record file dengan database menggunakan composite key.
8. Sistem menampilkan ringkasan record baru, record yang akan diperbarui, dan record bermasalah.
9. Admin memutuskan apakah akan melanjutkan atau membatalkan.
10. Jika dilanjutkan, job masuk antrean sesuai jenis data.
11. Background worker memproses file per batch dan memperbarui progres.
12. Pengguna dapat meninggalkan halaman dan memantau status dari Riwayat Import.
13. Sistem menyimpan hasil per record dan ringkasan akhir.
14. Jika proses gagal sebagian, data yang telah berhasil tetap disimpan dan record yang gagal ditandai.
15. Admin dapat mengunggah ulang file yang sama; sistem mengenali record berdasarkan composite key.

## 11. Kriteria Penerimaan Awal

1. Admin dapat memilih satu dari empat jenis data dan mengunggah Excel atau CSV.
2. Perbedaan urutan kolom tidak menyebabkan data salah dipetakan selama header cocok.
3. File yang kehilangan kolom wajib atau memiliki header wajib yang tidak cocok ditolak dengan pesan yang jelas.
4. Kolom tambahan menghasilkan peringatan sebelum impor dilanjutkan.
5. Sistem menampilkan ringkasan perubahan sebelum Admin mengonfirmasi impor.
6. Impor ulang tidak membuat duplikasi berdasarkan composite key yang telah ditetapkan.
7. Record yang tidak muncul dalam file terbaru tidak otomatis dihapus.
8. File besar diproses di background dan progres dapat dipantau dari Riwayat Import.
9. Impor gagal sebagian tetap menyimpan record yang berhasil serta mengidentifikasi record gagal.
10. Impor ulang seluruh file dapat dilakukan tanpa membuat duplikasi.
11. Impor jenis data berbeda dapat berjalan bersamaan; impor jenis yang sama masuk antrean.
12. Relasi Equipment yang belum tersedia dapat dicocokkan otomatis setelah master Equipment diimpor.
13. Penghapusan Equipment tidak menghapus record transaksi yang terkait.
14. Setiap halaman data menyediakan pencarian, filter per kolom, dan ekspor Excel/CSV.
15. Hak Admin dan Viewer ditegakkan pada backend.
16. Riwayat impor dan audit log mencatat aktivitas penting.
17. Rollback sesi impor tidak membatalkan perubahan dari sesi lain.

Kriteria yang bergantung pada composite key, kolom wajib, relasi, dan aturan pembaruan baru dapat diuji secara final setelah sampel ekspor SAP tersedia.

## 12. Risiko dan Ketergantungan

| Risiko/ketergantungan | Dampak | Mitigasi |
|---|---|---|
| Sampel ekspor SAP belum tersedia | Key, kolom wajib, tipe data, dan relasi belum dapat ditetapkan | Sediakan sampel dari keempat jenis data sebelum desain database final |
| Aturan pembaruan per jenis data belum ditetapkan | Data lama dapat berubah dengan perilaku yang tidak diinginkan | Tetapkan kebijakan per jenis data sebelum implementasi impor final |
| Data berukuran besar | Impor lambat atau membebani memori | Background worker, batch processing, indeks, dan pengujian beban |
| Rollback setelah perubahan lanjutan | Risiko membatalkan perubahan dari sesi lain | Catat perubahan per sesi dan gunakan strategi kompensasi/validasi konflik |
| Referensi Equipment belum tersedia | Relasi transaksi sementara belum terhubung | Pencocokan otomatis setelah master Equipment masuk |
| Kebijakan backup belum diputuskan | Risiko kehilangan data | Tetapkan backup dan uji restore sebelum go-live |

## 13. Keputusan yang Semula Terbuka (kini ditetapkan)

Seluruh keputusan berikut sudah diselesaikan dan diimplementasikan. Ringkasan final ada di tabel **Keputusan Terkunci** pada [TODO.md](TODO.md); bagian ini memetakan tiap pertanyaan draft ke keputusan yang diambil.

| # | Pertanyaan draft | Keputusan final |
|---|---|---|
| 1 | Nama header dan kolom wajib setiap jenis data | `required_headers` per jenis di `app/importing/specs.py`; pemetaan by header name (exact match) |
| 2 | Composite key tiap jenis data | Kunci natural per entitas (mis. `Equipment`, `Order`, `Notification`) — lihat tabel di TODO.md |
| 3 | Kolom relasi Notification–Work Order dan ke Equipment | Auto-link berbasis nilai EQ/FL/NOTIF/ORDER; ditampilkan sebagai "unlinked" bila master belum ada |
| 4 | Aturan pembaruan saat impor ulang | Upsert otomatis (overwrite) berdasarkan natural key (`app/services/upsert.py`) |
| 5 | Kebijakan record valid/invalid | Admin memilih pada pratinjau: lanjut parsial atau batalkan |
| 6 | Persetujuan perubahan Equipment | Tanpa approval terpisah; overwrite otomatis seperti jenis lain |
| 7 | Penyimpanan kolom SAP asli | Kolom terkurasi + `raw_data` JSONB menyimpan seluruh kolom SAP asli |
| 8 | Kebijakan backup, retensi, pemulihan | `pg_dump -Fc` harian via service `backup`, retensi 14 hari; drill restore diuji |
| 9 | Stack, job queue, deployment | FastAPI + Jinja2 + HTMX + Alpine + Tailwind; Redis/RQ per jenis; Docker Compose |
| 10 | Target performa, batas file, retensi file sumber | Uji volume 100k–1jt; file sumber tidak disimpan permanen (rollback dari histori DB) |
| 11 | Rollback bila record diubah proses lain | Per-record, lewati & catat konflik `import_job_id` berbeda |
| 12 | Penonaktifan akun & retensi audit log | Akun dinonaktifkan (bukan dihapus); audit log permanen |

## 14. Rekomendasi Tahap Implementasi

### Tahap 1 — Konfirmasi data dan desain
- Kumpulkan sampel ekspor SAP untuk empat jenis data.
- Petakan header, tipe data, kolom wajib, composite key, dan relasi.
- Tetapkan aturan pembaruan per jenis data.
- Validasi rancangan database konseptual.

### Tahap 2 — Fondasi aplikasi
- Autentikasi dan role Admin/Viewer.
- Sidebar dan halaman dasar.
- PostgreSQL, Docker, dan audit log dasar.

### Tahap 3 — Mesin impor
- Upload dan validasi.
- Pratinjau perubahan.
- Background queue, progress, dan antrean per jenis data.
- Hasil per record, impor ulang, dan riwayat impor.

### Tahap 4 — Halaman data dan relasi
- Halaman Notification, Work Order, Measuring Document, Equipment.
- Filter per kolom, pencarian, pagination, ekspor.
- Penautan Equipment dan relasi Notification–Work Order.
- Aksi edit/hapus dan penghapusan massal.

### Tahap 5 — Hardening dan pengujian
- Pengujian volume besar.
- Pengujian concurrent import.
- Pengujian kegagalan parsial dan rollback.
- Pengujian hak akses dan audit.
- Penetapan serta pengujian backup/restore.

---

**Catatan akhir:** Dokumen ini dipertahankan sebagai rujukan kebutuhan bisnis. Implementasi telah mengunci struktur kolom, composite key, aturan pembaruan, dan relasi berdasarkan sampel ekspor SAP yang diperiksa — semuanya tercatat di [TODO.md](TODO.md). Perubahan kebutuhan selanjutnya sebaiknya dicatat sebagai revisi dokumen ini.
