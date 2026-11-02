# Case 02 — Build and run

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This local lab uses a weighted router, stable and canary Python services, PostgreSQL, Prometheus, and a k6 workload. The canary starts at 5% with a synthetic latency fault. The router's admin port and Prometheus are bound to localhost. Values in Compose are disposable demo credentials.

Prefer Kubernetes manifests? See the optional [Kubernetes deployment guide](kubernetes.md). Compose remains the default path; both variants implement the same scenario, while measured latency and throughput can differ by cluster and machine.

The Compose services have about 1.2 GiB of configured limits, or about 1.5 GiB when the optional k6 load runner is active, plus Docker overhead. Docker Desktop should have at least 2 GiB available. Start Docker Desktop before running commands. From this directory:

```sh
docker compose config
docker compose up -d --build --wait
docker compose ps
```

Check the router and Prometheus at `http://localhost:8082/health` and `http://localhost:9093`. The canary share is initially 5%:

```sh
python3 labctl.py status
curl -s 'http://localhost:8082/api/work?priority=critical'
```

## Reproduce a regression

The default profile offers 20 requests per second for a little over two minutes. At the default 5% canary share this produces only about 60 canary samples per minute, so the gate should return `HOLD` even though total traffic exceeds 1,000. Keep both sample floors: each independent one-minute window requires at least 1,000 routed requests and 1,000 served canary requests. Load-shed responses do not count as served canary samples. To exercise the full gate in this capacity-limited local lab without reducing either floor, set canary traffic to 50% and use the same 40 requests/second offered load for baseline, regression, recovery, and healthy-canary runs. This is a gate-validation setting, not a recommended production rollout percentage. Use one terminal for the workload and another for the gate.

```sh
docker compose run --rm --no-deps -e RATE=40 -e DURATION=130s -e MAX_VUS=100 k6 run /scripts/load.js
```

The canary defaults to a 350 ms application delay. Inspect the metrics at `http://localhost:9093/graph` or run:

```sh
curl -s 'http://localhost:8082/api/work?priority=low'
docker compose logs --tail=30 stable canary router
```

Start `labctl.py gate` in the second terminal after about 50 seconds of load, when the first one-minute window has enough traffic. An earlier invocation returns `HOLD` without changing traffic; run it again after the sample floor is met.

The JSON service logs include release, priority, response status, and duration. Prometheus stores stable/canary request totals and latency histograms. Database delay is available with `CANARY_FAULT=db-slow`; an error regression is available with `CANARY_FAULT=error`.

## Gate, promote, and roll back

```sh
python3 labctl.py gate
python3 labctl.py promote
python3 labctl.py status
python3 labctl.py rollback
```

Promotion requires two independent one-minute windows, at least 1,000 total requests and 1,000 served-canary requests per window, served-canary 5xx at or below 1%, and served-canary p95 at or below 120% of stable. Load-shed 429/503 responses are counted separately and do not qualify as canary samples. The next stage is 5% → 25% → 50% → 100%. Insufficient samples return `HOLD`; they do not count as a pass. Rollback sets canary traffic to 0% and sends all requests to stable. The local controller fails closed if it cannot reach Prometheus or the router.

To demonstrate a passing gate and staged promotion, remove the synthetic regression and keep the same override for the load command:

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
docker compose run --rm --no-deps -e RATE=40 -e DURATION=130s -e MAX_VUS=100 k6 run /scripts/load.js
```

Start `python3 labctl.py promote` after the first sample window is ready. Repeat the workload and promotion command for each later stage. For a failing 5xx case, recreate canary with `CANARY_FAULT=error` instead.

For a small or stopped workload, keep the default sample floors and expect `HOLD`. Do not reduce the floors to force a pass; a low-volume pass is not evidence for the full policy.

```sh
python3 labctl.py gate
```

## Load shedding

The router and each service cap total in-flight work at 25, and low-priority work at 15, reserving capacity for critical requests. The router rejects excess work before it queues in an upstream: low-priority work receives 429 and exhausted total capacity receives 503; both responses include `Retry-After` and `X-Load-Shed: true`. Run `docker compose run --rm --no-deps -e RATE=400 -e DURATION=30s -e MAX_VUS=400 -e PREALLOCATED_VUS=100 k6 run /scripts/load.js` to observe shed responses. The k6 summary reports successful requests, controlled rejections, unexpected failures, p95/p99, and dropped iterations so overload and generator limits remain distinct. See [measured test evidence](test-evidence.md) for actual results, test configuration, commands, and output excerpts.

## Reset

This removes only this Compose project and its synthetic PostgreSQL and Prometheus data:

```sh
docker compose down --volumes --remove-orphans
```

The lab demonstrates local routing and one database, not production-grade proxying, distributed tracing, high availability, or real traffic control. Do not expose the demo admin token or service ports to a network.

<a id="bahasa-indonesia"></a>

## Case 02 — Build dan jalankan

Lab lokal ini memakai router berbobot, service Python stable dan canary, PostgreSQL, Prometheus, serta workload k6. Canary dimulai pada 5% dengan fault latensi sintetis. Port admin router dan Prometheus hanya terikat ke localhost. Nilai di Compose adalah kredensial demo yang boleh dibuang.

Jika ingin belajar memakai manifest Kubernetes, lihat [panduan deployment Kubernetes](kubernetes.md). Compose tetap menjadi jalur default; kedua varian menjalankan skenario yang sama, sedangkan angka latensi dan throughput dapat berbeda bergantung pada cluster dan mesin.

Batas resource service Compose sekitar 1,2 GiB, atau sekitar 1,5 GiB saat load runner k6 opsional aktif, ditambah overhead Docker. Docker Desktop sebaiknya menyediakan minimal 2 GiB. Jalankan Docker Desktop, lalu dari folder ini:

```sh
docker compose config
docker compose up -d --build --wait
docker compose ps
```

Router dan Prometheus tersedia di `http://localhost:8082/health` dan `http://localhost:9093`. Canary dimulai pada 5%:

```sh
python3 labctl.py status
curl -s 'http://localhost:8082/api/work?priority=critical'
```

## Mereproduksi regresi

Profil default menawarkan 20 request/detik selama sedikit lebih dari dua menit. Dengan traffic canary default 5%, profil ini hanya menghasilkan sekitar 60 sampel canary per menit, sehingga gate semestinya memberi `HOLD` walaupun traffic total melewati 1.000. Pertahankan kedua sample floor: setiap jendela independen satu menit membutuhkan minimal 1.000 request yang dirutekan dan 1.000 request canary yang dilayani. Respons load shedding tidak dihitung sebagai sampel canary. Untuk menguji gate penuh pada lab lokal yang kapasitasnya terbatas tanpa mengurangi kedua ambang, atur traffic canary ke 50% dan gunakan offered load yang sama, 40 request/detik, pada run baseline, regresi, recovery, dan canary sehat. Persentase ini hanya untuk validasi gate lokal, bukan rekomendasi rollout produksi. Jalankan workload di satu terminal dan gate di terminal lain.

```sh
docker compose run --rm --no-deps -e RATE=40 -e DURATION=130s -e MAX_VUS=100 k6 run /scripts/load.js
```

Canary memiliki delay aplikasi default 350 ms. Periksa metrik di `http://localhost:9093/graph` atau jalankan:

```sh
curl -s 'http://localhost:8082/api/work?priority=low'
docker compose logs --tail=30 stable canary router
```

Jalankan `labctl.py gate` di terminal kedua setelah sekitar 50 detik beban, saat jendela satu menit pertama memiliki cukup traffic. Jika terlalu awal, gate mengembalikan `HOLD` tanpa mengubah traffic; coba lagi setelah jumlah sampel terpenuhi.

Log JSON mencakup release, priority, status respons, dan durasi. Prometheus menyimpan total request dan histogram latensi stable/canary. Delay database dapat disimulasikan dengan `CANARY_FAULT=db-slow`; regresi error dengan `CANARY_FAULT=error`.

## Gate, promosi, dan rollback

```sh
python3 labctl.py gate
python3 labctl.py promote
python3 labctl.py status
python3 labctl.py rollback
```

Promosi butuh dua jendela satu menit terpisah, minimal 1.000 request total dan 1.000 request canary yang dilayani pada setiap jendela, 5xx canary maksimal 1%, serta p95 canary maksimal 120% dari stable. Respons 429/503 akibat load shedding dihitung terpisah dan tidak menjadi sampel evaluasi canary. Tahap berikutnya adalah 5% → 25% → 50% → 100%. Sampel yang kurang menghasilkan `HOLD`, bukan kelulusan. Rollback mengatur traffic canary menjadi 0% dan mengarahkan seluruh request ke stable. Controller lokal fail-closed jika Prometheus atau router tidak dapat dihubungi.

Untuk demonstrasi gate yang lolos dan promosi bertahap, hilangkan regresi sintetis dan gunakan override yang sama pada perintah workload:

```sh
CANARY_FAULT=none docker compose up -d --force-recreate --wait canary
docker compose run --rm --no-deps -e RATE=40 -e DURATION=130s -e MAX_VUS=100 k6 run /scripts/load.js
```

Jalankan `python3 labctl.py promote` setelah jendela sampel pertama siap. Ulangi workload dan perintah promosi untuk setiap tahap. Untuk menunjukkan kegagalan 5xx, buat ulang canary dengan `CANARY_FAULT=error`.

Untuk workload kecil atau yang sudah berhenti, pertahankan sample floor default dan harapkan hasil `HOLD`. Jangan turunkan ambang agar terlihat lulus; hasil traffic rendah bukan bukti untuk policy penuh.

```sh
python3 labctl.py gate
```

## Load shedding

Router dan setiap service membatasi total pekerjaan berjalan ke 25 dan pekerjaan prioritas rendah ke 15 agar kapasitas tersisa untuk request kritis. Router menolak kelebihan beban sebelum request mengantre panjang di upstream: request prioritas rendah menerima 429 dan kapasitas total yang habis menghasilkan 503; keduanya menyertakan `Retry-After` dan `X-Load-Shed: true`. Jalankan `docker compose run --rm --no-deps -e RATE=400 -e DURATION=30s -e MAX_VUS=400 -e PREALLOCATED_VUS=100 k6 run /scripts/load.js` untuk melihat respons yang ditolak. Ringkasan k6 melaporkan request sukses, penolakan terkendali, kegagalan tak terduga, p95/p99, dan iterasi yang terlewat agar overload tidak tercampur dengan batas generator beban. Lihat [bukti pengujian terukur](test-evidence.md) untuk hasil aktual, konfigurasi pengujian, perintah, dan cuplikan output.

## Reset dan batasan

Perintah ini menghapus hanya Compose project ini beserta data sintetis PostgreSQL dan Prometheus:

```sh
docker compose down --volumes --remove-orphans
```

Lab mendemonstrasikan routing lokal dan satu database, bukan proxy produksi, distributed tracing, high availability, atau kontrol traffic nyata. Jangan paparkan token admin demo atau port service ke jaringan.
