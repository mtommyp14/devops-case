# Portfolio roadmap

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This roadmap records what is planned, implemented, and measured. The local labs use synthetic data and Docker; no AWS resources are part of the plan.

## Stages

1. **Case 01 — data reliability:** implemented and run. The event producer, Kafka, PostgreSQL source ledger and sink, quarantine, metrics, reconciliation, and replay are documented with measured evidence.
2. **Case 02 — incident recovery:** implementation and the planned local load-test matrix are complete. Measured runs cover stable baseline, insufficient 5% canary samples, latency-fault gate rejection, rollback recovery, healthy-canary full-gate promotion, and overload/load shedding. The 5% canary correctly returned `HOLD` because it supplied only about 49 served-canary samples against a 1,000-per-window requirement. The faulted canary correctly failed promotion; the healthy 50% canary passed two independent windows and promoted to 100%. The overload run started 12,000/12,000 iterations, controlled 4,016 rejections, recorded zero unexpected failures and zero dropped iterations, and measured successful-request p95/p99 of 100.06/179.72 ms. See [Case 02 measured evidence](../case-02-incident-recovery/docs/test-evidence.md) for test configuration, commands, raw output, and the distinction between targets and measured results. The healthy full-gate run used the same 40 req/s profile before router admission control was added; stable, fault, recovery, and overload final runs used the final router code.
3. **Case 03 — developer platform:** local environment manager is built and running for isolated Compose projects, deterministic synthetic data, readiness/smoke checks, per-PR generation locks, TTL metadata, and exact cleanup. Provisioning and smoke checks passed.
4. **Case 04 — safe AI deployment:** deterministic proposal fixtures, restricted sandbox, independent OPA policy, hash-bound approval, mock controller/target, audit, and rollback are built and running. Safe and high-risk approvals, policy denials, and rollback were exercised. It does not use an AI model.
5. **Portfolio polish:** reproduce all documented commands from a clean checkout, capture results, and review limitations.

## Evidence rules

For each measured run record the scenario, relevant software/image versions, application resource limits, command, and raw output. Separate a target from a measured result. Do not imply cloud deployment or production use from a local simulation. Do not store personal or secret data in evidence.

<a id="bahasa-indonesia"></a>

## Peta jalan portofolio

Peta jalan ini mencatat pekerjaan yang direncanakan, diimplementasikan, dan diukur. Lab lokal menggunakan data sintetis dan Docker; tidak ada resource AWS yang termasuk dalam rencana.

## Tahapan

1. **Case 01 — keandalan data:** sudah diimplementasikan dan dijalankan. Producer event, Kafka, source ledger dan sink PostgreSQL, karantina, metrik, rekonsiliasi, serta replay dicatat dengan bukti pengukuran.
2. **Case 02 — pemulihan insiden:** implementasi dan matriks pengujian beban lokal yang direncanakan sudah selesai. Run terukur mencakup baseline stable, sampel canary 5% yang tidak cukup, penolakan gate saat fault latensi, recovery rollback, promosi gate penuh canary sehat, dan overload/load shedding. Canary 5% menghasilkan `HOLD` dengan benar karena hanya memberi sekitar 49 sampel canary served, di bawah syarat 1.000 per jendela. Canary dengan fault gagal promosi sesuai policy; canary sehat 50% melewati dua jendela independen dan dipromosikan ke 100%. Run overload memulai 12.000/12.000 iterasi, menolak 4.016 request secara terkendali, mencatat nol kegagalan tak terduga dan nol iterasi terlewat, dengan p95/p99 request sukses 100,06/179,72 ms. Lihat [bukti pengujian Case 02](../case-02-incident-recovery/docs/test-evidence.md) untuk konfigurasi pengujian, perintah, output mentah, serta pemisahan target dan hasil ukur. Run gate penuh canary sehat memakai profil 40 req/detik yang sama sebelum router admission control ditambahkan; run final baseline, fault, recovery, dan overload memakai kode router final.
3. **Case 03 — platform developer:** environment manager lokal sudah dibangun dan berjalan untuk project Compose terisolasi, data sintetis deterministik, pemeriksaan readiness/smoke, lock generasi per PR, metadata TTL, dan cleanup spesifik. Provisioning dan smoke check lulus.
4. **Case 04 — deployment AI yang aman:** fixture proposal deterministik, sandbox terbatas, policy OPA independen, persetujuan terikat hash, controller/target mock, audit, dan rollback sudah dibangun dan berjalan. Skenario aman/berisiko tinggi, penolakan policy, dan rollback sudah dicoba. Lab tidak memakai model AI.
5. **Penyempurnaan portofolio:** ulangi seluruh perintah terdokumentasi dari checkout bersih, simpan hasil, dan tinjau batasan.

## Aturan bukti

Untuk setiap run terukur, catat skenario, versi software/image yang relevan, batas resource aplikasi, perintah, dan output mentah. Bedakan target dari hasil ukur. Jangan menyatakan simulasi lokal sebagai deployment cloud atau penggunaan produksi. Jangan menyimpan data pribadi atau secret di bukti.
