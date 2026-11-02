# Case 01 — build and run guide

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## What the lab demonstrates

The fixture creates 20 synthetic consent-change events. Seventeen use schema v1 (`consent`); three use schema v2 (`consent_v2`). The broken worker stays alive, reads and commits all records, but silently drops records with the unfamiliar field. The producer commits each record to the PostgreSQL source ledger before publishing it to Kafka. The hardened worker writes valid records to PostgreSQL and places incompatible records in a durable quarantine table before committing their Kafka offsets. Reconciliation compares the source ledger with delivered and pending-quarantine IDs. A recovery adapter maps `consent_v2` to the sink contract, and the sink primary key makes repeat writes idempotent.

The lab uses Kafka, PostgreSQL, a Python worker, Prometheus and a small metrics exporter. Allow about 3 GiB of Docker memory for this modest local stack (container limits total about 2.1 GiB, plus Docker overhead). Images are pinned; the first pull and run will confirm compatibility. No cloud resources are involved.

## Requirements

Docker Desktop or Docker Engine with the Compose plugin is required. Allow about 3 GiB of Docker memory for this local stack. The app runs in a Python 3.12.8 container; host Python does not need to be upgraded for this lab.

Install/start Docker Desktop with Compose v2, then from this directory run:

```sh
docker compose config
docker compose up -d --build
docker compose run --rm lab seed --count 20
```

## Reproduce silent loss

```sh
docker compose run --rm lab worker --mode broken --run-id broken --group-id broken-v1 --once --count 20
docker compose run --rm lab report --run-id broken
```

Measured fixture counts: 20 source, 17 delivered, 0 quarantined, and 3 unaccounted (`evt-018`–`evt-020`). The detailed results are in [test evidence](test-evidence.md).

## Harden and recover

```sh
docker compose run --rm lab worker --mode hardened --run-id hardened --group-id hardened-v1 --once --count 20
docker compose run --rm lab report --run-id hardened
docker compose run --rm lab recover --run-id hardened
docker compose run --rm lab recover --run-id hardened
docker compose run --rm lab report --run-id hardened
```

Measured before replay: 17 delivered, 3 pending quarantine, 0 unaccounted. Measured after replay: 20 delivered, 0 pending quarantine, 0 unaccounted, and 0 duplicate sink rows. The second recovery reported zero newly recovered rows.

Prometheus is at `http://localhost:9090`; the exporter is at `http://localhost:8001/metrics`. Query `consent_lab_unaccounted_events`, `consent_lab_pending_quarantine_events`, and `consent_lab_max_source_to_sink_lag_seconds`.

## Crash window and duplicate delivery

The worker commits the PostgreSQL transaction before committing the Kafka offset. The two systems do not share an atomic transaction. If the process exits after the sink write but before offset commit, Kafka can deliver the same event again. The sink primary key `(run_id,event_id)` turns that redelivery into a no-op.

For an isolated crash demonstration, seed a fresh Kafka topic/consumer group in a clean lab state, run:

```sh
docker compose run --rm lab worker --mode hardened --run-id crash-demo --group-id crash-demo-v1 --once --count 20 --crash-after-sink-once
```

The process intentionally exits with status 17 after its first sink write and before offset commit. Restart it with the same group ID and without the crash flag. Reconcile to verify no lost or duplicated sink records. The command uses a single-purpose local lab database and the named volumes below, so read the cleanup warning before resetting a run.

## Metrics, evidence, and limits

Run reports are generated from PostgreSQL, not hand-entered. Fixture counts demonstrate correctness; observed source-to-sink lag includes time spent between demo commands and is not a controlled latency benchmark. Throughput and latency benchmarks require a separately stated workload, warm-up, duration, concurrency, and comparable resource limits.

The source ledger is the durable reconciliation reference for this simulation. In a real system its retention, privacy controls, completeness, and ownership would need explicit design. The demo uses a single broker and one database, so it does not demonstrate high availability, production security, schema registry operations, or exactly-once processing.

## Scoped cleanup

This removes only the named Compose project's containers and its three lab volumes, including all synthetic lab data:

```sh
docker compose down --volumes --remove-orphans
```

Do not run generic Docker prune commands for this lab.

<a id="bahasa-indonesia"></a>

## Panduan build dan menjalankan Case 01

## Yang didemonstrasikan

Fixture membuat 20 event perubahan consent sintetis. Tujuh belas memakai schema v1 (`consent`); tiga memakai schema v2 (`consent_v2`). Worker yang rusak tetap hidup dan mengakui semua record, tetapi diam-diam melewatkan record dengan field yang tidak dikenal. Producer mencatat setiap record ke source ledger PostgreSQL sebelum menerbitkannya ke Kafka. Worker hardened menulis event valid ke PostgreSQL dan menempatkan event yang tidak kompatibel di tabel karantina durabel sebelum mengakui offset Kafka. Rekonsiliasi membandingkan ID source ledger dengan ID yang terkirim dan yang masih dikarantina. Adapter recovery memetakan field v2 ke kontrak sink; primary key sink membuat penulisan ulang aman.

Lab menggunakan Kafka, PostgreSQL, worker Python, Prometheus, dan metrics exporter kecil. Sediakan sekitar 3 GiB memori Docker (batas container sekitar 2,1 GiB ditambah overhead). Image dipin; proses pull dan run pertama akan memeriksa kompatibilitas. Lab tidak menggunakan resource cloud.

## Prasyarat

Diperlukan Docker Desktop atau Docker Engine dengan plugin Compose. Sediakan sekitar 3 GiB memori Docker untuk stack lokal ini. Aplikasi berjalan dalam container Python 3.12.8; Python host tidak perlu diperbarui.

Pasang dan jalankan Docker Desktop dengan Compose v2, lalu dari folder ini jalankan:

```sh
docker compose config
docker compose up -d --build
docker compose run --rm lab seed --count 20
```

## Mereproduksi kehilangan data

```sh
docker compose run --rm lab worker --mode broken --run-id broken --group-id broken-v1 --once --count 20
docker compose run --rm lab report --run-id broken
```

Hasil fixture yang tercatat: 20 event di sumber, 17 terkirim, 0 dikarantina, dan 3 tidak terhitung (`evt-018`–`evt-020`). Rincian hasil ada di [bukti pengujian](test-evidence.md).

## Mengamankan dan memulihkan

```sh
docker compose run --rm lab worker --mode hardened --run-id hardened --group-id hardened-v1 --once --count 20
docker compose run --rm lab report --run-id hardened
docker compose run --rm lab recover --run-id hardened
docker compose run --rm lab recover --run-id hardened
docker compose run --rm lab report --run-id hardened
```

Sebelum replay: 17 terkirim, 3 menunggu di karantina, 0 tidak terhitung. Sesudah replay: 20 terkirim, 0 menunggu di karantina, 0 tidak terhitung, dan 0 baris sink duplikat. Pemulihan kedua melaporkan 0 baris baru yang dipulihkan.

Prometheus tersedia di `http://localhost:9090`, exporter di `http://localhost:8001/metrics`. Coba metrik `consent_lab_unaccounted_events`, `consent_lab_pending_quarantine_events`, dan `consent_lab_max_source_to_sink_lag_seconds`.

## Jendela crash dan pengiriman duplikat

Worker mengomit transaksi PostgreSQL sebelum mengomit offset Kafka. Kedua sistem tidak berbagi satu transaksi atomik. Jika proses berhenti setelah sink ditulis tetapi sebelum offset diomit, Kafka dapat mengirim ulang event tersebut. Primary key sink `(run_id,event_id)` mengubah penulisan ulang menjadi no-op.

Untuk demonstrasi crash terisolasi, seed topic dan consumer group Kafka baru pada state lab yang bersih, lalu jalankan:

```sh
docker compose run --rm lab worker --mode hardened --run-id crash-demo --group-id crash-demo-v1 --once --count 20 --crash-after-sink-once
```

Proses sengaja keluar dengan status 17 setelah penulisan sink pertama dan sebelum offset diomit. Jalankan ulang dengan group ID yang sama tanpa flag crash. Rekonsiliasi harus menunjukkan tidak ada event hilang atau baris duplikat. Perintah menggunakan database lab khusus dan named volume yang tercantum di bawah; baca peringatan cleanup sebelum mereset run.

## Metrik, bukti, dan batasan

Laporan run dibuat dari PostgreSQL, bukan diisi manual. Jumlah fixture membuktikan alur correctness, sedangkan lag sumber-ke-sink yang diamati mencakup waktu di antara perintah demo dan bukan benchmark latensi terkontrol. Benchmark throughput dan latensi membutuhkan workload, pemanasan, durasi, concurrency, serta batas resource yang dinyatakan.

Source ledger adalah referensi rekonsiliasi durabel untuk simulasi ini. Dalam sistem nyata, retensi, kontrol privasi, kelengkapan, dan kepemilikannya perlu dirancang eksplisit. Demo memakai satu broker dan satu database, jadi tidak membuktikan high availability, keamanan produksi, operasi schema registry, atau pemrosesan exactly-once.

## Cleanup terbatas

Perintah ini menghapus hanya container milik Compose project tersebut beserta tiga volume lab, termasuk seluruh data sintetis:

```sh
docker compose down --volumes --remove-orphans
```

Jangan jalankan perintah Docker prune umum untuk lab ini.
