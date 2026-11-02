# Runbook — schema drift and missing events

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

1. **Assess:** record alert time, affected source/time range, deployed worker version, Kafka lag, and sink freshness. Avoid resetting the lab or deleting offsets before preserving evidence.
2. **Reconcile:** compare source-ledger event IDs with sink and pending quarantine IDs. Report exact missing IDs and counts.
3. **Inspect:** compare valid and missing payloads, schema versions, producer rollout time, consumer logs, and offset movement. Treat an unexplained gap as an incident even if liveness is green.
4. **Contain:** stop promotion of the producer schema or route incompatible events to quarantine. Keep the source ledger and original payload available under retention controls.
5. **Validate fix:** review schema compatibility and adapter mapping. Test the adapter on a bounded sample and confirm required fields and types.
6. **Replay:** use the recovery command for the intended run. Keep original event IDs. Repeat reconciliation after replay; rerun safely to verify idempotency.
7. **Verify:** require zero unaccounted IDs, expected pending quarantine, no duplicate sink rows, and acceptable freshness before declaring recovery.
8. **Learn:** preserve the timeline, evidence, cause, detection gap, and follow-up actions. Add a regression test for the observed field change and an alert on unaccounted events.

For the demo commands and resource-scoped cleanup, see [build and run](build-and-run.md).

<a id="bahasa-indonesia"></a>

## Runbook — schema drift dan event hilang

1. **Nilai dampak:** catat waktu alert, rentang waktu/sumber terdampak, versi worker yang berjalan, lag Kafka, dan freshness sink. Jangan reset lab atau menghapus offset sebelum bukti tersimpan.
2. **Rekonsiliasi:** bandingkan ID event source ledger dengan ID di sink dan karantina tertunda. Laporkan ID dan jumlah yang benar-benar hilang.
3. **Periksa:** bandingkan payload valid dan hilang, versi schema, waktu rollout producer, log consumer, dan pergerakan offset. Anggap gap yang belum terjelaskan sebagai insiden meski liveness hijau.
4. **Batasi dampak:** hentikan promosi schema producer atau arahkan event yang tidak kompatibel ke karantina. Pertahankan source ledger dan payload asli sesuai kontrol retensi.
5. **Validasi perbaikan:** tinjau kompatibilitas schema dan mapping adapter. Uji adapter pada sampel terbatas dan pastikan field serta tipe yang diwajibkan benar.
6. **Replay:** gunakan perintah recovery untuk run yang dimaksud. Pertahankan ID event asli. Ulangi rekonsiliasi setelah replay; jalankan kembali dengan aman untuk memeriksa idempotensi.
7. **Verifikasi:** pastikan tidak ada ID tidak terhitung, jumlah karantina sesuai harapan, tidak ada baris sink duplikat, serta freshness memenuhi target sebelum menyatakan pulih.
8. **Ambil pelajaran:** simpan timeline, bukti, penyebab, celah deteksi, dan tindak lanjut. Tambahkan regression test untuk perubahan field yang ditemukan serta alert untuk event tidak terhitung.

Untuk perintah demo dan cleanup dengan scope resource terbatas, lihat [panduan build dan run](build-and-run.md).
