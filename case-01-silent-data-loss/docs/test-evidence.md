# Test evidence

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Local checks

### Executed

Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`

Result: 4 tests passed. They verify the 20-event fixture has 17 v1 and 3 v2 records with unique IDs, hardened validation rejects the unadapted v2 field with a reason, the reviewed adapter accepts it and preserves the boolean, and invalid consent types are rejected. Python source files passed an in-memory syntax compilation check. Ruby's YAML parser accepted `compose.yaml`, `prometheus.yml`, and `alerts.yml`; this checks YAML syntax only, not Docker Compose semantics or Prometheus rule compatibility.

## Docker integration run

The app image uses Python 3.12.8. Compose validation, image build, service health checks, and the end-to-end scenario completed locally.

| Run | Source | Delivered | Pending quarantine | Unaccounted | Duplicate sink rows |
|---|---:|---:|---:|---:|---:|
| Broken consumer | 20 | 17 | 0 | 3 (`evt-018`–`evt-020`) | 0 |
| Hardened, before replay | 20 | 17 | 3 | 0 | 0 |
| Hardened, after replay | 20 | 20 | 0 | 0 | 0 |
| Crash and restart | 20 | 17 | 3 | 0 | 0 |

The first recovery applied 3 events; repeating it applied 0. The crash test intentionally exited with status 17 after writing the first valid sink record and before committing its Kafka offset. Restarting the same consumer group redelivered the event; the unique sink key prevented a duplicate. The resulting crash-demo report showed 17 unique sink rows, 3 quarantined, and 0 unaccounted.

Prometheus scraped the exporter. Its API returned `ConsentEventsUnaccounted` in `firing` state for `run_id="broken"` and `ConsentQuarantinePending` in `firing` state for `run_id="crash-demo"` after each rule's pending period. Exported source, delivery, quarantine, gap, and source-to-sink lag gauges were visible. The lag values (41.07 s broken, 56.40 s hardened before replay, 68.12 s after replay, and 136.68 s crash-demo) include elapsed time between interactive demo commands, so they are not performance benchmarks. Detection duration, recovery duration, throughput, and controlled latency remain unmeasured.

During setup, the initial Kafka volume permissions prevented the non-root broker from starting; a small init service now assigns the volume to Kafka's container UID. The initial Kafka client pin was incompatible with Python 3.12; it was updated to `kafka-python==2.2.21`, and the worker now commits the individual processed offset with its leader epoch. The crash test also exposed a too-short one-shot rebalance wait; the worker now uses a 10-second session timeout and a 30-second consumer idle timeout.

<a id="bahasa-indonesia"></a>

## Bukti pengujian

### Pemeriksaan lokal

Perintah: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`

Hasil: 4 pengujian lulus. Pengujian memeriksa fixture 20 event terdiri dari 17 record v1 dan 3 record v2 dengan ID unik; validasi hardened menolak field v2 tanpa adapter beserta alasannya; adapter yang ditinjau menerima field tersebut dan mempertahankan nilai boolean; serta tipe consent yang tidak valid ditolak. File Python lulus pemeriksaan sintaks di memori. Parser YAML Ruby menerima `compose.yaml`, `prometheus.yml`, dan `alerts.yml`; pemeriksaan ini hanya memastikan sintaks YAML, bukan semantik Docker Compose atau kompatibilitas rule Prometheus.

### Run integrasi Docker

Image app menggunakan Python 3.12.8. Validasi Compose, build image, health check service, dan skenario end-to-end selesai secara lokal.

| Run | Sumber | Terkirim | Karantina tertunda | Tidak terhitung | Baris sink duplikat |
|---|---:|---:|---:|---:|---:|
| Consumer rusak | 20 | 17 | 0 | 3 (`evt-018`–`evt-020`) | 0 |
| Hardened, sebelum replay | 20 | 17 | 3 | 0 | 0 |
| Hardened, setelah replay | 20 | 20 | 0 | 0 | 0 |
| Crash dan restart | 20 | 17 | 3 | 0 | 0 |

Recovery pertama menerapkan 3 event; recovery ulang menerapkan 0. Uji crash sengaja keluar dengan status 17 setelah menulis record sink valid pertama dan sebelum commit offset Kafka. Restart consumer group yang sama mengirim ulang event; unique key sink mencegah duplikasi. Laporan crash-demo menunjukkan 17 baris sink unik, 3 dikarantina, dan 0 tidak terhitung.

Prometheus berhasil scrape exporter. API-nya mengembalikan `ConsentEventsUnaccounted` dalam status `firing` untuk `run_id="broken"` dan `ConsentQuarantinePending` dalam status `firing` untuk `run_id="crash-demo"` setelah masa pending rule selesai. Gauge sumber, delivery, karantina, gap, dan lag sumber-ke-sink terlihat. Angka lag (41,07 dtk broken, 56,40 dtk hardened sebelum replay, 68,12 dtk setelah replay, dan 136,68 dtk crash-demo) mencakup waktu antarperintah demo interaktif, jadi bukan benchmark performa. Durasi deteksi/pemulihan, throughput, dan latensi terkontrol belum diukur.

Saat setup awal, permission volume Kafka mencegah broker non-root berjalan; service init kecil kini mengatur volume ke UID container Kafka. Pin client Kafka awal tidak kompatibel dengan Python 3.12; pin diperbarui menjadi `kafka-python==2.2.21`, dan worker kini mengomit offset yang diproses secara individual dengan leader epoch. Uji crash juga mengungkap waktu tunggu rebalance sekali jalan terlalu pendek; worker kini memakai session timeout 10 detik dan consumer idle timeout 30 detik.
