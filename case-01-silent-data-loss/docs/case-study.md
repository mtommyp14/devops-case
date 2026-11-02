# Case study — The green dashboard that lost customer events

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Status and setting

This is a synthetic local exercise about data reliability. It is not a real incident. The fixture contains 20 fabricated consent-change events, with three using a newer field name. No real customer data is used.

## Incident narrative

The service health check stayed green and the consumer advanced its Kafka offsets. A count of consumed records looked healthy, yet the downstream sink had only 17 of the 20 source IDs. The original monitoring measured process liveness and offset progress, not end-to-end delivery. That left three records unaccounted for without an operational alert.

## Illustrative timeline

This sequence describes the fixture, not measured wall-clock timings: **T+0** seed 20 source events and publish them; **T+1** the broken consumer processes and commits offsets while skipping the three v2 payloads; **T+2** reconciliation reveals 17 delivered and three missing IDs; **T+3** hardened processing accounts for the same stream as 17 delivered plus three quarantined; **T+4** the reviewed adapter replays the three events and reconciliation reaches 20 delivered. Detection and recovery durations must be measured when the Docker scenario is run.

## User impact and hypotheses

The simulated downstream service can make a decision using stale consent state for the affected customers. The scenario does not model a real customer or an actual decision. Tested hypotheses are: (1) the consumer or broker stopped—rejected by continued liveness and offset progress; (2) the sink is unavailable—rejected by the 17 successful writes and lack of database errors in the fixture; (3) payload contract drift caused selective loss—supported by the missing IDs' schema version and field name. Runtime logs and broker/database evidence would be required to make these claims during a real incident.

## Investigation

1. Compare source-ledger IDs with sink IDs and list the missing IDs.
2. Compare one delivered payload with one missing payload. The latter carries `consent_v2` and schema version 2 rather than the expected `consent` field.
3. Confirm the consumer remained available and committed offsets after skipping the unknown field.
4. Reject infrastructure outage as the primary explanation: broker progress and process health continued while specific schema-v2 records were absent.

The causal mechanism is deliberately encoded in the broken fixture consumer. A real incident would require timestamped logs, deployed artifact identity, broker offsets, and database evidence before assigning root cause.

## Recovery design

The hardened path validates the required consent value. It writes valid events to the sink and writes unsupported payloads plus a reason to quarantine before committing their Kafka offsets. An adapter maps the reviewed v2 field to the canonical sink field. Replay retains the event ID, and the sink's unique key protects against duplicate delivery.

PostgreSQL commit and Kafka offset commit are separate operations. The worker commits the database write first, then the broker offset. A crash in between causes redelivery, handled through idempotent sink writes. Reversing the order could lose an event if the offset advanced before a durable database write.

## Measurement plan

The program reports source count, delivered count, pending quarantine count, unaccounted count and IDs, duplicate sink rows, and maximum source-to-sink write lag. Prometheus exposes the corresponding gauges. On the recorded Docker run, the broken path measured 20 source, 17 delivered, 3 unaccounted; hardened processing measured 17 delivered plus 3 quarantined and 0 unaccounted; replay measured 20 delivered, 0 pending quarantine, and 0 duplicates. A deliberate crash and restart also ended with 17 delivered, 3 pending quarantine, 0 unaccounted, and 0 duplicate sink rows. Exact detection and recovery durations remain unmeasured; the observed lag values are demo elapsed time, not a controlled benchmark.

## Prevention and follow-up

- Validate schema compatibility before rollout and validate required fields at runtime.
- Alert on unaccounted IDs, quarantine growth, stale source-to-sink freshness, and consumer lag; liveness alone is not a delivery SLO.
- Preserve source evidence and quarantine reason/payload under explicit retention controls.
- Review every adapter change and replay a bounded batch before broad recovery.
- Test worker restarts and the sink-write/offset-commit crash window.
- Add independent reconciliation and runbook ownership to the service's operational review.

## Trade-offs and limits

Quarantine avoids silent loss but requires retention, access controls, and an operator path to resolve poison records. Strict validation can reduce throughput during a schema rollout; compatibility checks and staged adapters lower that risk. Idempotency handles redelivery but does not create an atomic transaction spanning PostgreSQL and Kafka. A single-broker Docker setup is a learning lab, not a high-availability topology.

<a id="bahasa-indonesia"></a>

## Studi kasus — Dashboard tetap hijau saat event pelanggan hilang

### Status dan konteks

Ini adalah latihan lokal sintetis tentang keandalan data, bukan insiden nyata. Fixture berisi 20 event perubahan consent buatan; tiga memakai nama field yang lebih baru. Tidak ada data pelanggan sungguhan.

### Kronologi insiden

Health check service tetap hijau dan consumer memajukan offset Kafka. Jumlah record yang dibaca terlihat sehat, tetapi sink downstream hanya memiliki 17 dari 20 ID sumber. Monitoring awal mengukur liveness proses dan kemajuan offset, bukan keberhasilan pengiriman dari ujung ke ujung. Akibatnya, tiga record tidak memiliki hasil yang terhitung dan tidak memicu alert operasional.

### Timeline ilustratif

Urutan ini menggambarkan fixture, bukan durasi nyata yang diukur: **T+0** seed 20 event sumber dan terbitkan; **T+1** consumer rusak memproses dan mengomit offset sambil melewatkan tiga payload v2; **T+2** rekonsiliasi menemukan 17 terkirim dan 3 ID hilang; **T+3** pemrosesan hardened mencatat stream yang sama sebagai 17 terkirim dan 3 dikarantina; **T+4** adapter yang ditinjau melakukan replay tiga event dan rekonsiliasi mencapai 20 terkirim. Waktu deteksi dan pemulihan harus diukur ketika skenario Docker dijalankan.

### Dampak simulasi dan hipotesis

Dalam simulasi, service downstream dapat mengambil keputusan dengan state consent yang usang untuk pelanggan terdampak. Skenario ini tidak memodelkan pelanggan atau keputusan nyata. Hipotesis yang diuji: (1) consumer atau broker berhenti — tidak didukung karena liveness dan offset terus bergerak; (2) sink tidak tersedia — tidak didukung karena ada 17 penulisan berhasil dan fixture tidak menunjukkan error database; (3) drift kontrak payload menyebabkan kehilangan selektif — didukung oleh versi schema dan nama field pada ID yang hilang. Dalam insiden nyata, log runtime serta bukti broker/database diperlukan sebelum membuat kesimpulan tersebut.

### Investigasi

1. Bandingkan ID source ledger dengan ID sink dan daftar ID yang hilang.
2. Bandingkan satu payload terkirim dengan satu payload hilang. Payload yang hilang membawa `consent_v2` dan schema versi 2, bukan field `consent` yang diharapkan.
3. Pastikan consumer tetap tersedia dan mengomit offset setelah melewatkan field yang tidak dikenal.
4. Tolak outage infrastruktur sebagai penjelasan utama: kemajuan broker dan health proses berlanjut, sementara record schema v2 tertentu tidak ada.

Mekanisme penyebab sengaja ditanam di consumer fixture yang rusak. Insiden nyata memerlukan log bertimestamp, identitas artefak yang dirilis, offset broker, dan bukti database sebelum menetapkan root cause.

### Rancangan pemulihan

Jalur hardened memvalidasi nilai consent wajib. Event valid ditulis ke sink; payload yang belum didukung beserta alasannya ditulis ke karantina sebelum offset Kafka dikomit. Adapter memetakan field v2 yang sudah ditinjau ke field kanonis sink. Replay mempertahankan ID event, dan unique key sink melindungi dari pengiriman duplikat.

Commit PostgreSQL dan commit offset Kafka merupakan operasi terpisah. Worker mengomit penulisan database terlebih dahulu, kemudian offset broker. Crash di antaranya menyebabkan redelivery yang ditangani penulisan sink idempotent. Urutan sebaliknya dapat menghilangkan event jika offset maju sebelum penulisan database durabel.

### Rencana pengukuran

Program melaporkan jumlah sumber, terkirim, karantina tertunda, tidak terhitung beserta ID, baris sink duplikat, dan lag maksimum penulisan dari sumber ke sink. Prometheus menyediakan gauge terkait. Pada run Docker tercatat, jalur rusak menghasilkan 20 sumber, 17 terkirim, dan 3 tidak terhitung; jalur hardened menghasilkan 17 terkirim ditambah 3 dikarantina dan 0 tidak terhitung; replay menghasilkan 20 terkirim, 0 karantina tertunda, dan 0 duplikat. Crash dan restart berakhir dengan 17 terkirim, 3 karantina tertunda, 0 tidak terhitung, dan 0 baris duplikat. Durasi deteksi dan pemulihan belum diukur; angka lag adalah waktu demo, bukan benchmark terkontrol.

### Pencegahan dan tindak lanjut

- Validasi kompatibilitas schema sebelum rollout dan field wajib saat runtime.
- Buat alert untuk ID tidak terhitung, pertumbuhan karantina, freshness sumber-ke-sink yang usang, dan lag consumer; liveness saja bukan SLO pengiriman.
- Pertahankan bukti sumber dan payload/alasan karantina dengan kontrol retensi eksplisit.
- Tinjau setiap perubahan adapter dan replay batch terbatas sebelum pemulihan luas.
- Uji restart worker dan jendela crash antara penulisan sink dan commit offset.
- Tambahkan rekonsiliasi independen dan penanggung jawab runbook dalam tinjauan operasional service.

### Trade-off dan batasan

Karantina mencegah kehilangan senyap, tetapi membutuhkan retensi, kontrol akses, dan proses operator untuk memperbaiki poison record. Validasi ketat dapat mengurangi throughput saat rollout schema; pemeriksaan kompatibilitas dan adapter bertahap mengurangi risiko tersebut. Idempotensi menangani redelivery, tetapi tidak membuat transaksi atomik antara PostgreSQL dan Kafka. Docker dengan satu broker adalah lab pembelajaran, bukan topologi high availability.
