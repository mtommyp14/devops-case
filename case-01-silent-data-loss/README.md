# Case 01 — Silent Data Loss

[Bahasa Indonesia](#bahasa-indonesia) | [English](#english)

<a id="bahasa-indonesia"></a>

## Tujuan
Mendemonstrasikan pipeline yang tetap terlihat sehat walaupun sebagian event hilang akibat perubahan schema, lalu mendeteksi, mengarantina, dan memulihkan event tanpa duplikasi.

## Rancangan dan implementasi
Rancangan awal mencakup schema registry dan Grafana. Implementasi demo saat ini memakai Docker Compose, producer/consumer Python, Kafka, PostgreSQL source ledger/sink/quarantine, Prometheus, dan exporter kecil. Schema Registry dan Grafana belum dibuat; diagram aktual ada di [architecture](docs/architecture.md).

Alur aktual: producer mencatat source ledger lalu menerbitkan ke Kafka → consumer menulis event valid ke sink atau payload yang belum didukung ke tabel quarantine PostgreSQL → adapter memulihkan payload setelah ditinjau.

## Skenario demo
1. Kirim event valid dan catat jumlah serta ID pada sumber dan tujuan.
2. Simulasikan perilaku consumer lama yang membuang field/event tidak dikenal tanpa alarm. Tunjukkan proses tetap hidup tetapi rekonsiliasi menemukan selisih.
3. Aktifkan validator dan kirim schema baru yang tidak kompatibel, misalnya perubahan tipe `amount` dari angka menjadi string.
4. Karantina event dengan payload asli, alasan, schema version, dan offset sumber. Commit offset hanya setelah penulisan tujuan atau karantina dikonfirmasi durabel.
5. Perbaiki mapping, replay event terpilih, kemudian ulangi replay yang sama untuk membuktikan idempotensi.

## Deteksi dan pemulihan
- Pemeriksaan kompatibilitas schema di CI dan runtime; perubahan tidak kompatibel ditolak atau dikarantina.
- Pantau jumlah event masuk, berhasil, dikarantina, lag, usia event tertua, serta rekonsiliasi ID per rentang waktu. Gunakan watermark agar event terlambat tidak langsung dianggap hilang.
- Alarm jika selisih tetap ada setelah watermark, tingkat karantina meningkat, atau pipeline berhenti memproses meski health endpoint sehat.
- Gunakan unique constraint `event_id` dan transaksi untuk penulisan hasil serta ledger pemrosesan. Pengiriman bersifat at-least-once; efek penulisan dibuat idempotent.
- Replay mempertahankan `event_id` asli, mendukung batch/rate limit dan checkpoint. Event yang masih gagal kembali ke karantina; jangan hapus raw data sebelum rekonsiliasi lulus.

## Kriteria keberhasilan
Pada run Docker tercatat, 20 event menghasilkan 17 delivered dan 3 unaccounted pada consumer rusak; jalur hardened menghasilkan 17 delivered, 3 quarantined, dan 0 unaccounted; replay mencapai 20 delivered, 0 pending quarantine, dan 0 duplicate rows. Crash setelah penulisan sink diikuti restart juga menghasilkan 0 unaccounted dan 0 duplikasi. Detail environment ada di [test evidence](docs/test-evidence.md).

## Artefak implementasi
Kode producer/worker/replay, Compose, skema PostgreSQL, fixture sintetis, exporter Prometheus, alert rules, dan runbook sudah ada. Data demo sepenuhnya sintetis; volume Docker menyimpan state selama pengujian. Target lag yang terlihat pada run ini mencakup waktu antarperintah demo dan bukan benchmark.

## Status
Implementasi Docker lokal sudah dijalankan. Reproduksi menemukan 3 event tidak terhitung dari 20; jalur hardened mengarantina ketiganya dan memulihkan sink menjadi 20/20 tanpa duplikasi. Hasil dan batas pengujian dicatat di [test evidence](docs/test-evidence.md).

Jalur Kubernetes opsional tersedia di [`kubernetes/`](kubernetes/) dengan [panduan apply dan skenario](docs/kubernetes.md). Contohnya memakai broker Kafka tunggal dan namespace lokal.


<a id="english"></a>

## English

An optional Kubernetes deployment is available under [`kubernetes/`](kubernetes/) with an [apply and scenario guide](docs/kubernetes.md). It uses one Kafka broker in a local learning namespace.

### Purpose
Demonstrate a pipeline that appears healthy while losing events after a schema change, then detect, quarantine, and recover those events without duplicates.

### Design and implementation
The initial design included Schema Registry and Grafana. The current demo uses Docker Compose, Python producer/consumer, Kafka, PostgreSQL source ledger/sink/quarantine, Prometheus, and a small exporter. Schema Registry and Grafana have not been implemented; see the [actual architecture](docs/architecture.md).

The producer records each event in the source ledger and publishes it to Kafka. The consumer writes valid events to the sink or stores unsupported payloads in PostgreSQL quarantine. A reviewed adapter later converts the payload so it can be replayed.

### Demo scenario
1. Send valid events and record source and destination counts and IDs.
2. Reproduce the old consumer behavior: it skips an unknown field without an alert, while process health remains green.
3. Enable validation and send an incompatible schema, such as changing `amount` from a number to a string.
4. Store the original payload, rejection reason, schema version, and source offset in quarantine. Commit the Kafka offset only after the destination or quarantine write is durable.
5. Correct the mapping and replay selected events. Repeat the replay to verify idempotency.

### Detection and recovery
- Check schema compatibility in CI and at runtime; reject or quarantine incompatible changes.
- Monitor incoming, delivered, and quarantined event counts, lag, oldest-event age, and ID reconciliation over time windows. Use a watermark so delayed events are not immediately reported as lost.
- Alert when a gap remains after the watermark, quarantine grows, or processing stops while the health endpoint still responds.
- Use a unique `event_id` constraint and transactions for sink writes and processing records. Delivery is at-least-once; sink effects are idempotent.
- Preserve the original `event_id` during replay; support batches, rate limits, and checkpoints. Return failures to quarantine and retain raw data until reconciliation succeeds.

### Success criteria and evidence
In the recorded Docker run, the broken consumer left 3 of 20 events unaccounted. The hardened path delivered 17, quarantined 3, and accounted for every event. Replay restored 20 delivered events with no pending quarantine or duplicate rows. A crash after the sink write followed by restart also ended with no missing or duplicate events. Environment details are in [test evidence](docs/test-evidence.md).

### Implementation and limits
The lab includes producer/worker/replay code, Compose configuration, PostgreSQL schema, synthetic fixtures, Prometheus exporter and alert rules, and an operational runbook. All demo data is synthetic; Docker volumes retain state during a run. The observed lag includes time between interactive commands and is not a benchmark.

The Docker lab was built and run locally on Apple Silicon. The implementation does not include Schema Registry or a Grafana dashboard. Start with the [build and run guide](docs/build-and-run.md), then review the [architecture](docs/architecture.md), [case study](docs/case-study.md), [runbook](docs/runbook.md), and [walkthrough](docs/walkthrough-id.md).
