# Case 02 — Load-test evidence

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Scope and policy

Comparable steady-state runs used 40 offered requests/s for 130s, 50 preallocated VUs, and at most 100 VUs. Canary tests used 50% traffic solely to reach the full sample floor in this capacity-limited local lab; this is not a production rollout recommendation.

The gate policy was not reduced: two independent one-minute windows; at least 1,000 total routed and 1,000 served-canary requests per window; served-canary 5xx ≤1%; canary p95 ≤120% of stable p95. The k6 p95 threshold remained <1,000 ms. Load-shed responses are counted separately and do not qualify as served canary samples.

“Offered” means iterations actually started by k6. Any iterations the generator could not start are listed as dropped iterations.

## Test configuration

| Component | Observed |
| --- | --- |
| Load generator | grafana/k6:0.56.0 |
| Other services | PostgreSQL 17.2-alpine, Prometheus 3.1.0; router, stable, and canary healthy before measured runs |
| App resource limits | stable/canary 0.75 CPU and 192 MiB each; router 192 MiB; PostgreSQL 384 MiB; Prometheus 256 MiB; k6 256 MiB |

The final stable baseline, latency fault, rollback recovery, and overload rerun used the final router code. The healthy-canary full-gate measurement used the same 40 req/s profile before router admission control was added. The router rejects only when its 25 total / 15 low-priority in-flight limits are full; at 40 req/s those limits were not approached. The healthy canary full gate passed both configured windows.

## Results: actual measurements vs targets

Latency is k6 `successful_request_duration` p95/p99 unless marked **overall**. Gate p95 is the Prometheus histogram estimate in seconds. Router totals do not include requests dropped before routing.

| Scenario | Offered load | Successful | Controlled rejects | Unexpected failures | p95 / p99 | Dropped iterations | Target and actual result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Stable, no fault (final router) | 5,201 total; 40.01/s | 5,201 | 0 | 0 | 11.96 / 48.30 ms | 0 | Target p95 <300 ms, 5xx <1%; **met**. |
| Healthy 5% canary, sample-floor check | 2,600 total; 20.00/s | 2,600 | 0 | 0 | 14.69 / 34.88 ms | 0 | 1,199.93 total routed, but only 49.09 canary served in the measured window vs 1,000 required; **HOLD**. |
| 50% canary, 350 ms latency fault | 5,201 total; 39.90/s | 5,201 | 0 | 0 | 361.91 / 371.76 ms | 0 | Gate observed canary p95 490.00 ms vs stable 9.75 ms (~50.2×), 1,225.07 canary samples, 0% 5xx; **FAIL; `promote` left traffic at 50%**. |
| Rollback and stable recovery (final router) | 5,200 total; 40.00/s | 5,200 | 0 | 0 | 10.26 / 33.49 ms | 0 | Target stable=100%, p95 <300 ms; **met**. API returned 200, `X-Upstream: stable`, `fault: none`. |
| Healthy 50% canary, full gate | 5,200 total; 40.00/s | 5,200 | 0 | 0 | 10.70 / 27.95 ms | 0 | Window totals 2,400.04 / 2,400.00; canary samples 1,213.11 / 1,206.59; 0% errors; p95 canary 9.87 / 9.75 ms vs stable 9.85 / 9.73 ms; **PASS, promoted 50% →100%**. |
| Overload after router admission control | 12,000 started; 398.46/s | 7,984 | 4,016 | 0 | Success p95/p99 100.06 / 179.72 ms; overall 92.52 / 150.04 ms | 0 | Target k6 p95 <1,000 ms; **met while shedding load**. 12,000/12,000 scheduled iterations started. |

### Sample sufficiency and gate outputs

At 5%, total requests passed the floor but served-canary samples did not. The gate correctly held promotion:

```text
Window 1/2: {'samples': 1199.9345490245987, 'canary_served_samples': 49.08644668666484, 'errors': 0.0, 'canary_p95': 0.02162499999999999, 'stable_p95': 0.013014705882352906}
HOLD: only 49 served canary requests in the window; at least 1000 are required to evaluate the canary.
```

Final latency-fault gate, with sufficient canary samples:

```text
Window 1/2: {'samples': 2399.9563644297377, 'canary_served_samples': 1225.068635115725, 'errors': 0.0, 'canary_p95': 0.49, 'stable_p95': 0.00975189393939394}
FAIL: canary breached the 1% 5xx or 120% stable p95 gate.
Traffic was not changed.
canary=50% · stable=50%
```

Healthy-canary gate and promotion, both full independent windows:

```text
Window 1/2: {'samples': 2400.0436371570395, 'canary_served_samples': 1213.1129656902854, 'errors': 0.0, 'canary_p95': 0.009872897196261684, 'stable_p95': 0.009848455598455598}
Waiting 60s for the next independent observation window…
Window 2/2: {'samples': 2400.0, 'canary_served_samples': 1206.5893305211098, 'errors': 0.0, 'canary_p95': 0.009746753246753247, 'stable_p95': 0.009732142857142858}
PASS: all requested observation windows met the canary gate.
{'canary_percent': 100}
```

## Commands used

Run from `case-02-incident-recovery`. `--wait` confirms health before traffic. `--no-deps` prevents `docker compose run k6` from recreating dependencies with their default fault setting.

### 1. Stable baseline

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
python3 labctl.py rollback
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/stable-baseline-final-summary.json /scripts/load.js
```

### 2. 5% sample-floor check

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
python3 labctl.py canary 5
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=20 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/sample-floor-5pct-verified-summary.json /scripts/load.js
python3 labctl.py gate
```

### 3. Latency fault and gate

```sh
CANARY_FAULT=slow docker compose up -d --force-recreate --wait canary
python3 labctl.py canary 50
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/canary-promote-blocked-summary.json /scripts/load.js
# In a second terminal, after about 65 seconds of load:
python3 labctl.py promote
```

### 4. Rollback and recovery

```sh
python3 labctl.py rollback
python3 labctl.py status
curl -i 'http://127.0.0.1:8082/api/work?priority=critical'
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/rollback-recovery-summary.json /scripts/load.js
```

### 5. Healthy canary, full gate

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
python3 labctl.py canary 50
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/healthy-canary-final-summary.json /scripts/load.js
# In a second terminal, after about 60 seconds of load:
python3 labctl.py promote
```

### 6. Overload and load shedding

```sh
python3 labctl.py rollback
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=400 -e DURATION=30s -e MAX_VUS=400 -e PREALLOCATED_VUS=100 \
  k6 run --summary-export=/out/overload-after-admission-summary.json /scripts/load.js
```

## Raw k6 output excerpts

These lines are copied from the k6 summaries. When dropped iterations are zero, k6 omits that metric; started iterations then equal the scheduled total.

### Stable baseline

```text
checks.........................: 100.00% 5201 out of 5201
http_req_duration..............: avg=8.26ms ... p(95)=11.95ms p(99)=48.3ms
http_req_failed................: 0.00%   0 out of 5201
offered_requests...............: 5201    40.005771/s
successful_requests............: 5201    40.005771/s
```

### Latency fault

```text
checks.........................: 100.00% 5201 out of 5201
http_req_duration..............: p(95)=361.91ms p(99)=371.76ms
offered_requests...............: 5201    39.900011/s
successful_requests............: 5201    39.900011/s
```

### Rollback recovery

```text
checks.........................: 100.00% 5200 out of 5200
http_req_duration..............: p(95)=10.26ms p(99)=33.49ms
offered_requests...............: 5200    39.999887/s
successful_requests............: 5200    39.999887/s
```

### Healthy canary

```text
checks.........................: 100.00% 5200 out of 5200
http_req_duration..............: p(95)=10.70ms p(99)=27.95ms
offered_requests...............: 5200    40.00/s
successful_requests............: 5200    40.00/s
```

### Overload after router admission control

```text
checks.........................: 100.00% 12000 out of 12000
controlled_rejections..........: 4016    133.352807/s
http_req_duration..............: avg=38.75ms p(95)=92.51ms p(99)=150.03ms
offered_requests...............: 12000   398.464563/s
successful_requests............: 7984    265.111756/s
```

## Findings and corrections

1. When canary had no 5xx, the original Prometheus error-rate query returned an empty vector. The gate stopped at `HOLD` before checking p95. `labctl.py` now treats an empty 5xx numerator as zero; the 1% threshold is unchanged. Final regression and healthy-canary runs exercise `FAIL` and `PASS`.
2. An early canary run began before the recreated container was healthy and recorded five transient 502 responses. It is excluded from the final healthy result. The reproducible sequence now uses Compose `--wait` and k6 `--no-deps`; the final healthy run had zero unexpected failures.
3. The first 400 req/s overload probe shed traffic, but admitted requests reached p95 4.87 s and p99 4.99 s because excess work waited in the upstream queue. Router-level admission control now sheds before that queue. The same 400 req/s profile was rerun at p95 92.51 ms / p99 150.04 ms. Load rate and k6 threshold were not lowered.
4. The default 5% share is insufficient for the full sample policy at the 20 req/s profile. The gate correctly holds. The 50% setting is only used to validate the full policy in this local lab.

Raw logs and k6 summary JSON were saved under `artifacts/local/` during execution. That directory is excluded from version control; commands, test configuration, results, and raw output excerpts needed to review and reproduce the measurements are preserved here.

<a id="bahasa-indonesia"></a>

## Ruang lingkup dan policy

Run steady-state yang dibandingkan memakai offered load sama, 40 request/detik selama 130 detik, 50 VU preallocated, maksimum 100 VU. Pengujian canary memakai porsi 50% hanya agar sample floor penuh tercapai pada lab lokal dengan kapasitas terbatas ini; bukan rekomendasi rollout produksi.

Policy gate tidak diturunkan: dua jendela independen masing-masing satu menit; minimal 1.000 request total yang dirutekan dan 1.000 request canary yang dilayani per jendela; 5xx canary served ≤1%; p95 canary ≤120% p95 stable. Ambang p95 k6 tetap <1.000 ms. Respons load-shed dihitung terpisah dan tidak menjadi sampel canary served.

“Offered” berarti iterasi yang benar-benar dimulai k6. Iterasi yang gagal dimulai oleh generator dicatat terpisah sebagai dropped iterations.

## Konfigurasi pengujian

| Komponen | Teramati |
| --- | --- |
| Load generator | grafana/k6:0.56.0 |
| Service lain | PostgreSQL 17.2-alpine, Prometheus 3.1.0; router, stable, dan canary sehat sebelum run terukur |
| Batas resource app | stable/canary masing-masing 0,75 CPU dan 192 MiB; router 192 MiB; PostgreSQL 384 MiB; Prometheus 256 MiB; k6 256 MiB |

Baseline final, fault latensi, recovery rollback, dan overload yang diulang memakai kode router final. Pengukuran full-gate canary sehat memakai profil 40 req/detik yang sama, sebelum router admission control ditambahkan. Router hanya menolak ketika batas 25 total / 15 prioritas rendah tercapai; pada 40 req/detik batas tersebut tidak didekati. Gate canary sehat melewati kedua jendela policy.

## Hasil: aktual dibanding target

Latensi memakai p95/p99 k6 `successful_request_duration`, kecuali bertanda **overall**. p95 gate adalah estimasi histogram Prometheus dalam detik. Total router tidak menghitung request yang ditolak sebelum dirutekan.

| Skenario | Offered load | Berhasil | Penolakan terkendali | Gagal tak terduga | p95 / p99 | Iterasi terlewat | Target dan hasil aktual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Stable tanpa fault (router final) | 5.201 total; 40,01/dtk | 5.201 | 0 | 0 | 11,96 / 48,30 ms | 0 | Target p95 <300 ms, 5xx <1%; **terpenuhi**. |
| Cek sample-floor canary sehat 5% | 2.600 total; 20,00/dtk | 2.600 | 0 | 0 | 14,69 / 34,88 ms | 0 | Total routed 1.199,93, tetapi canary served hanya 49,09 pada jendela ini vs kebutuhan 1.000; **HOLD**. |
| Canary 50%, fault latensi 350 ms | 5.201 total; 39,90/dtk | 5.201 | 0 | 0 | 361,91 / 371,76 ms | 0 | Gate membaca p95 canary 490,00 ms vs stable 9,75 ms (~50,2×), 1.225,07 sampel canary, 0% 5xx; **FAIL; `promote` membiarkan traffic tetap 50%**. |
| Rollback dan recovery stable (router final) | 5.200 total; 40,00/dtk | 5.200 | 0 | 0 | 10,26 / 33,49 ms | 0 | Target stable=100%, p95 <300 ms; **terpenuhi**. API menjawab 200, `X-Upstream: stable`, `fault: none`. |
| Canary sehat 50%, gate penuh | 5.200 total; 40,00/dtk | 5.200 | 0 | 0 | 10,70 / 27,95 ms | 0 | Jendela total 2.400,04 / 2.400,00; sampel canary 1.213,11 / 1.206,59; error 0%; p95 canary 9,87 / 9,75 ms vs stable 9,85 / 9,73 ms; **PASS, dipromosikan 50% →100%**. |
| Overload setelah admission control router | 12.000 dimulai; 398,46/dtk | 7.984 | 4.016 | 0 | Sukses p95/p99 100,06 / 179,72 ms; overall 92,52 / 150,04 ms | 0 | Target p95 k6 <1.000 ms; **terpenuhi sambil shedding**. 12.000/12.000 iterasi terjadwal dimulai. |

### Kecukupan sampel dan output gate

Pada canary 5%, jumlah total melewati floor tetapi sampel canary served belum cukup. Gate menahan promosi dengan benar:

```text
Window 1/2: {'samples': 1199.9345490245987, 'canary_served_samples': 49.08644668666484, 'errors': 0.0, 'canary_p95': 0.02162499999999999, 'stable_p95': 0.013014705882352906}
HOLD: only 49 served canary requests in the window; at least 1000 are required to evaluate the canary.
```

Gate final untuk fault latensi, dengan sampel canary yang cukup:

```text
Window 1/2: {'samples': 2395.636363636364, 'canary_served_samples': 1222.8868566026072, 'errors': 0.0, 'canary_p95': 0.4901696428571429, 'stable_p95': 0.00970691287878788}
FAIL: canary breached the 1% 5xx or 120% stable p95 gate.
Traffic was not changed.
canary=50% · stable=50%
```

Gate canary sehat dan promosi, dengan dua jendela penuh:

```text
Window 1/2: {'samples': 2400.0436371570395, 'canary_served_samples': 1213.1129656902854, 'errors': 0.0, 'canary_p95': 0.009872897196261684, 'stable_p95': 0.009848455598455598}
Waiting 60s for the next independent observation window…
Window 2/2: {'samples': 2400.0, 'canary_served_samples': 1206.5893305211098, 'errors': 0.0, 'canary_p95': 0.009746753246753247, 'stable_p95': 0.009732142857142858}
PASS: all requested observation windows met the canary gate.
{'canary_percent': 100}
```

## Perintah yang digunakan

Jalankan dari `case-02-incident-recovery`. `--wait` memastikan service sehat sebelum traffic dimulai. `--no-deps` mencegah `docker compose run k6` membuat ulang dependency memakai fault default.

### 1. Baseline stable

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
python3 labctl.py rollback
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/stable-baseline-final-summary.json /scripts/load.js
```

### 2. Pemeriksaan sample-floor 5%

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
python3 labctl.py canary 5
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=20 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/sample-floor-5pct-verified-summary.json /scripts/load.js
python3 labctl.py gate
```

### 3. Fault latensi dan gate

```sh
CANARY_FAULT=slow docker compose up -d --force-recreate --wait canary
python3 labctl.py canary 50
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/canary-promote-blocked-summary.json /scripts/load.js
# Di terminal kedua, setelah sekitar 65 detik beban berjalan:
python3 labctl.py promote
```

### 4. Rollback dan recovery

```sh
python3 labctl.py rollback
python3 labctl.py status
curl -i 'http://127.0.0.1:8082/api/work?priority=critical'
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/rollback-recovery-summary.json /scripts/load.js
```

### 5. Canary sehat dan gate penuh

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
python3 labctl.py canary 50
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=40 -e DURATION=130s -e MAX_VUS=100 -e PREALLOCATED_VUS=50 \
  k6 run --summary-export=/out/healthy-canary-final-summary.json /scripts/load.js
# Di terminal kedua, setelah sekitar 60 detik beban berjalan:
python3 labctl.py promote
```

### 6. Overload dan load shedding

```sh
python3 labctl.py rollback
docker compose run --rm --no-deps \
  -v "$PWD/artifacts/local:/out" \
  -e RATE=400 -e DURATION=30s -e MAX_VUS=400 -e PREALLOCATED_VUS=100 \
  k6 run --summary-export=/out/overload-after-admission-summary.json /scripts/load.js
```

## Cuplikan output mentah k6

Baris berikut disalin dari ringkasan k6. Jika dropped iterations nol, k6 tidak menampilkan metriknya; jumlah iterasi yang dimulai sama dengan yang dijadwalkan.

### Baseline stable

```text
checks.........................: 100.00% 5201 out of 5201
http_req_duration..............: avg=8.26ms ... p(95)=11.95ms p(99)=48.3ms
http_req_failed................: 0.00%   0 out of 5201
offered_requests...............: 5201    40.005771/s
successful_requests............: 5201    40.005771/s
```

### Fault latensi

```text
checks.........................: 100.00% 5201 out of 5201
http_req_duration..............: p(95)=361.91ms p(99)=371.76ms
offered_requests...............: 5201    39.900011/s
successful_requests............: 5201    39.900011/s
```

### Recovery rollback

```text
checks.........................: 100.00% 5200 out of 5200
http_req_duration..............: p(95)=10.26ms p(99)=33.49ms
offered_requests...............: 5200    39.999887/s
successful_requests............: 5200    39.999887/s
```

### Canary sehat

```text
checks.........................: 100.00% 5200 out of 5200
http_req_duration..............: p(95)=10.70ms p(99)=27.95ms
offered_requests...............: 5200    40.00/s
successful_requests............: 5200    40.00/s
```

### Overload setelah admission control router

```text
checks.........................: 100.00% 12000 out of 12000
controlled_rejections..........: 4016    133.352807/s
http_req_duration..............: avg=38.75ms p(95)=92.51ms p(99)=150.03ms
offered_requests...............: 12000   398.464563/s
successful_requests............: 7984    265.111756/s
unexpected_failures............: 0
```

## Temuan dan perbaikan

1. Query error-rate awal mengembalikan vector Prometheus kosong saat canary tidak memiliki 5xx. Gate berhenti di `HOLD` sebelum memeriksa p95. `labctl.py` kini menganggap numerator 5xx kosong sebagai nol; ambang 1% tidak berubah. Run final regresi dan canary sehat menjalankan jalur `FAIL` dan `PASS`.
2. Run canary awal dimulai sebelum container hasil recreate dinyatakan sehat dan merekam lima respons 502 sementara. Run itu tidak dipakai sebagai hasil sehat final. Prosedur kini menunggu health Compose dengan `--wait`, lalu menjalankan k6 memakai `--no-deps`; run final mencatat nol kegagalan tak terduga.
3. Probe overload 400 req/detik pertama melakukan shedding, tetapi request yang diterima mencapai p95 4,87 detik dan p99 4,99 detik karena kelebihan kerja mengantre di upstream. Admission control router kini melakukan shedding sebelum antrean itu. Profil 400 req/detik yang sama diulang dengan p95 92,51 ms / p99 150,04 ms. Rate dan ambang k6 tidak diturunkan.
4. Porsi default 5% tidak cukup untuk sample policy penuh pada profil 20 req/detik. Gate menahan promosi dengan benar. Setting 50% hanya dipakai untuk memvalidasi policy penuh di lab lokal.

Log mentah dan summary JSON k6 disimpan di `artifacts/local/` selama eksekusi. Folder itu diabaikan oleh version control; perintah, konfigurasi pengujian, hasil, dan cuplikan output mentah untuk meninjau serta mengulang pengukuran ada di dokumen ini.
