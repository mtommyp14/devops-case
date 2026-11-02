# Walkthrough Bahasa Indonesia

[Bahasa Indonesia](#bahasa-indonesia) | [English](#english)

<a id="bahasa-indonesia"></a>

## Apa yang terjadi?

Bayangkan layanan mengirim perubahan persetujuan pelanggan ke Kafka. Dari 20 event buatan, 17 memakai nama field lama `consent`, sedangkan tiga memakai nama baru `consent_v2`. Consumer versi rusak tetap hidup dan mengakui semua pesan. Dashboard yang hanya memeriksa proses dan kemajuan consumer tetap hijau, padahal tiga event tidak pernah masuk ke database tujuan.

## Bagaimana membuktikannya?

Jangan hanya bertanya “consumer sehat?”. Cocokkan ID dari source ledger dengan ID di sink. Selisih ID menunjukkan data mana yang hilang. Setelah itu bandingkan payload yang berhasil dan yang hilang: versi skema dan nama field mengarah pada penyebabnya. Dengan urutan ini kita membuktikan dampak lebih dulu, lalu menguji dugaan penyebabnya.

## Mengapa source ledger, Kafka, dan PostgreSQL?

Kafka mewakili antrean event yang dapat dibaca ulang. PostgreSQL menyimpan hasil downstream. Source ledger memberi daftar pembanding independen agar rekonsiliasi bisa menemukan ID yang tidak ada di sink. Payload seluruhnya sintetis. PostgreSQL juga menyimpan quarantine dengan payload serta alasan penolakan.

## Apa yang diperbaiki?

Consumer hardened menerima payload yang kontraknya dikenal. Payload yang belum didukung tidak dibuang: payload dan alasan disimpan di quarantine, lalu offset Kafka baru dikomit setelah penyimpanan berhasil. Setelah adapter `consent_v2` ditinjau, perintah recovery membaca karantina dan menulis nilai kanonis ke sink.

## Mengapa tulis database sebelum commit offset?

Keduanya adalah transaksi berbeda. Jika database ditulis lalu proses mati sebelum offset dikomit, Kafka akan mengirim pesan lagi. Kunci unik `(run_id,event_id)` membuat penulisan kedua aman. Jika offset dikomit dahulu lalu proses mati sebelum database menulis, event bisa hilang dari sink. Pola ini memberi pemrosesan at-least-once dengan efek sink idempotent; tidak mengklaim exactly-once lintas dua sistem.

## Apa yang perlu diamati?

Pisahkan kesehatan proses dari keberhasilan pengiriman. Perhatikan jumlah source, delivered, pending quarantine, ID yang belum terhitung, duplicate sink rows, freshness dan lag. Alarm harus memicu ketika event tidak dapat ditemukan baik di sink maupun quarantine. Angka fixture 20/17/3 membantu demonstrasi alur; itu bukan benchmark performa.

## Ringkasan teknis

Pada fixture demonstrasi, consumer terlihat sehat, tetapi rekonsiliasi menemukan tiga dari 20 event tidak ada di sink. Perbedaan schema menjelaskan penyebabnya. Perbaikan menambahkan validasi, karantina durabel, metrik gap, adapter yang ditinjau, dan replay idempotent. Karena offset Kafka dan commit PostgreSQL bukan satu transaksi atomik, sistem menerima kemungkinan redelivery dan membuat penulisan sink aman untuk diulang.

<a id="english"></a>

## English walkthrough

### What happened?

Imagine a service sending customer consent changes to Kafka. Of 20 synthetic events, 17 use the old `consent` field and three use the new `consent_v2` field. The broken consumer stays alive and acknowledges every message. A dashboard that checks only process health and consumer progress stays green, even though three events never reach the destination database.

### How can we prove it?

Do not ask only whether the consumer is healthy. Compare IDs in the source ledger with IDs in the sink. The missing IDs show which records were lost. Then compare delivered and missing payloads: the schema version and field name point to the cause. This order proves impact first, then tests the suspected cause.

### Why use a source ledger, Kafka, and PostgreSQL?

Kafka represents a replayable event queue. PostgreSQL stores downstream results. The source ledger provides an independent comparison set so reconciliation can find IDs absent from the sink. All payloads are synthetic. PostgreSQL also stores quarantined payloads and rejection reasons.

### What changed?

The hardened consumer accepts payloads that match a known contract. Unsupported payloads are not discarded: the payload and reason are stored in quarantine, and the Kafka offset is committed only after storage succeeds. After a `consent_v2` adapter is reviewed, the recovery command reads quarantine and writes a canonical value to the sink.

### Why write the database before committing the offset?

They are separate transactions. If the database write succeeds but the process stops before the offset commit, Kafka may deliver the message again. A unique `(run_id,event_id)` key makes the repeated write safe. If the offset were committed first and the process stopped before writing to the database, the event could disappear from the sink. This is at-least-once processing with idempotent sink effects; it does not claim exactly-once behavior across both systems.

### What should be monitored?

Separate process health from delivery success. Track source, delivered, and pending-quarantine counts, unaccounted IDs, duplicate sink rows, freshness, and lag. Alert when an event has no durable outcome in either the sink or quarantine. The 20/17/3 fixture counts illustrate the flow; they are not a performance benchmark.

### Technical summary

In the demo fixture, the consumer looks healthy while reconciliation finds three of 20 events missing from the sink. A schema difference explains the cause. The fix adds validation, durable quarantine, gap metrics, a reviewed adapter, and idempotent replay. Kafka offsets and PostgreSQL commits are not one atomic transaction, so the design allows redelivery and makes repeated sink writes safe.
