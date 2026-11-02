<div align="center">

# DevOps Practice Labs

**Four hands-on scenarios. One local Docker workspace.**

Practice data recovery, incident response, pull request environments, and safer deployments with reproducible labs you can run and reset on your own machine.

[English](#english) · [Bahasa Indonesia](#bahasa-indonesia) · [Quick start](#quick-start)

</div>

<a id="english"></a>

Four local, Docker-based labs for practicing data reliability, incident recovery, developer environments, and policy-controlled deployment. Sample records and credentials are synthetic. These labs create no cloud resources and are not production deployments.

**Choose your setup:** Docker Compose runs all four cases. Kubernetes manifests are available as an optional learning track for Case 02. [Follow the setup paths](docs/learning-paths.md) · [Learn how to use AI safely](docs/learning-with-ai.md).

## Explore the cases

<table>
  <tr>
    <td align="center" width="50%">
      <a href="case-01-silent-data-loss/docs/build-and-run.md"><img src="case-01-silent-data-loss/docs/case-01-flow.svg" width="100%" alt="Case 01 flow: detect schema drift, quarantine invalid events, and replay them safely"></a>
      <br><strong>01 · Silent data loss</strong><br>Detect schema drift, quarantine invalid events, reconcile IDs, and replay safely.<br><sub>ID: Deteksi schema drift, karantina event, cocokkan ID, lalu replay dengan aman.</sub>
    </td>
    <td align="center" width="50%">
      <a href="case-02-incident-recovery/docs/build-and-run.md"><img src="case-02-incident-recovery/docs/case-02-flow.svg" width="100%" alt="Case 02 flow: compare stable and canary, gate promotion, and recover from regressions"></a>
      <br><strong>02 · Incident recovery</strong><br>Investigate latency and errors, gate a canary, roll back, and shed load.<br><sub>ID: Investigasi latensi dan error, tahan canary dengan gate, rollback, dan batasi beban.</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="case-03-developer-platform/docs/build-and-run.md"><img src="case-03-developer-platform/docs/case-03-flow.svg" width="100%" alt="Case 03 flow: provision isolated pull request environments, verify them, and clean them up"></a>
      <br><strong>03 · Developer platform</strong><br>Provision isolated pull request previews with synthetic data and scoped cleanup.<br><sub>ID: Buat preview pull request terisolasi dengan data sintetis dan cleanup terbatas.</sub>
    </td>
    <td align="center" width="50%">
      <a href="case-04-safe-ai-deployment/docs/build-and-run.md"><img src="case-04-safe-ai-deployment/docs/case-04-flow.svg" width="100%" alt="Case 04 flow: sandbox a proposal, check policy, require approval, and verify deployment"></a>
      <br><strong>04 · Safe AI deployment</strong><br>Sandbox proposed changes, enforce policy, limit secrets, and approve risky actions.<br><sub>ID: Sandbox perubahan, terapkan policy, batasi secret, dan setujui tindakan berisiko.</sub>
    </td>
  </tr>
</table>

<div align="center"><sub>Choose a diagram to open its case guide. / Pilih diagram untuk membuka panduan case.</sub></div>

## Labs

| Lab | Scenario | Main components | Guide |
|---|---|---|---|
| 01 — Silent data loss | Find schema drift, quarantine invalid events, reconcile IDs, and replay safely | Kafka, PostgreSQL, Python, Prometheus | [Case 01 guide](case-01-silent-data-loss/docs/build-and-run.md) |
| 02 — Incident recovery | Detect a canary regression, gate promotion, roll back, and shed load | Python services, PostgreSQL, Prometheus, k6 | [Case 02 guide](case-02-incident-recovery/docs/build-and-run.md) |
| 03 — Developer platform | Provision isolated pull-request previews with synthetic data and scoped cleanup | Python, Docker Compose, PostgreSQL | [Case 03 guide](case-03-developer-platform/docs/build-and-run.md) |
| 04 — Safe AI deployment | Evaluate deterministic change proposals in a sandbox with policy checks and approval gates | Docker Compose, OPA, Python | [Case 04 guide](case-04-safe-ai-deployment/docs/build-and-run.md) |

Each case folder includes its own README, architecture or flow diagram, and build/run instructions. See the [Case 03 isolation/cleanup evidence](case-03-developer-platform/docs/test-evidence.md) and [Case 04 approval/rollback/sandbox evidence](case-04-safe-ai-deployment/docs/test-evidence.md). Case 04 uses fixed proposal fixtures; it does not call an AI model.

Want a guided setup? Choose between [Docker Compose or Kubernetes](docs/learning-paths.md). If you use an AI assistant while learning, read [Learning with AI](docs/learning-with-ai.md) first.

## Why Docker?

- **Low-cost practice:** the labs run on your own machine and create no cloud resources or cloud bill. Docker still uses local CPU, memory, disk, electricity, and bandwidth when it downloads images.
- **Separated from host projects:** each case runs in its own Compose project with its own containers, network, and named volumes. Dependencies such as Kafka and PostgreSQL do not need to be installed globally, and cleanup targets the lab's resources.
- **Repeatable setup:** Compose files pin services and configuration so another learner can reproduce the same lab without manually assembling each dependency.
- **Disposable data:** the cases use synthetic records and dummy credentials. You can remove their containers and lab volumes with the documented cleanup commands.

Docker provides useful process and network separation, but containers still share the host kernel. Treat these labs as local development environments, not as a security boundary for hostile code or as production infrastructure.

## Requirements

- Docker Desktop or Docker Engine with the Docker Compose plugin.
- Python 3 for host-side control commands in Cases 02 and 03.
- Internet access the first time images are pulled.

Start Docker before launching a lab. Run commands from the corresponding case directory so Compose uses the correct project and scoped cleanup settings.

## Quick start

### Case 01 — Silent data loss

```sh
cd case-01-silent-data-loss
docker compose config
docker compose up -d --build
docker compose run --rm lab seed --count 20
```

Continue with the [Case 01 guide](case-01-silent-data-loss/docs/build-and-run.md) to reproduce the loss, enable quarantine, and replay events.

### Case 02 — Incident recovery

```sh
cd case-02-incident-recovery
docker compose config
docker compose up -d --build
python3 labctl.py status
```

The router starts with 5% canary traffic. The [Case 02 guide](case-02-incident-recovery/docs/build-and-run.md) covers load generation, promotion gates, rollback, and load shedding.

### Case 03 — Developer platform

```sh
cd case-03-developer-platform
docker compose config
python3 envctl.py provision --pr 42 --generation 1 --port 18421
```

The command builds and checks a local preview at `http://127.0.0.1:18421`. See the [Case 03 guide](case-03-developer-platform/docs/build-and-run.md) for updating and cleaning up environments.

### Case 04 — Safe AI deployment

```sh
cd case-04-safe-ai-deployment
docker compose config
docker compose up -d --build volume-init opa target
```

Run a proposal scenario using the [Case 04 guide](case-04-safe-ai-deployment/docs/build-and-run.md). The target is available at `http://127.0.0.1:18084`.

## Local endpoints

Services bind to loopback where they publish host ports.

| Case | Endpoint | Purpose |
|---|---|---|
| 01 | `localhost:9092` | Kafka |
| 01 | `localhost:5432` | PostgreSQL |
| 01 | `localhost:9090` | Prometheus |
| 01 | `localhost:8001/metrics` | Metrics exporter |
| 02 | `localhost:8082` | Router API and health |
| 02 | `localhost:9093` | Prometheus |
| 03 | `127.0.0.1:18421` | Example preview; choose another free port for parallel previews |
| 04 | `127.0.0.1:18084` | Mock deployment target |

Cases 01 and 02 use separate ports for Kafka and Prometheus so both Compose projects can run at once.

## Stop and clean up

For Cases 01, 02, and 04, run this from that case directory to stop its containers and remove its synthetic named volumes:

```sh
docker compose down --volumes --remove-orphans
```

For Case 03, use the environment manager so it removes only the selected preview:

```sh
python3 envctl.py cleanup --pr 42
```

These cleanup commands delete lab data. Each case guide lists its ports, resource needs, persistence behavior, and limitations.

## License

The original code and documentation in this repository are licensed under the [MIT License](LICENSE). Third-party tools and images remain subject to their own licenses and terms.

<a id="bahasa-indonesia"></a>

## Bahasa Indonesia

# Laboratorium Praktik DevOps

Empat lab lokal berbasis Docker untuk mempraktikkan keandalan data, pemulihan insiden, environment developer, dan deployment dengan kontrol policy. Semua record contoh dan kredensial merupakan placeholder sintetis. Lab ini tidak membuat resource cloud dan bukan deployment produksi.

**Pilih setup:** Docker Compose dapat menjalankan keempat case. Manifest Kubernetes tersedia sebagai jalur belajar opsional untuk Case 02. [Ikuti panduan setup](docs/learning-paths.md) · [Pelajari cara memakai AI dengan aman](docs/learning-with-ai.md).

## Lab

| Lab | Skenario | Komponen utama | Panduan |
|---|---|---|---|
| 01 — Kehilangan data senyap | Menemukan schema drift, mengarantina event tidak valid, merekonsiliasi ID, dan melakukan replay dengan aman | Kafka, PostgreSQL, Python, Prometheus | [Panduan Case 01](case-01-silent-data-loss/docs/build-and-run.md) |
| 02 — Pemulihan insiden | Mendeteksi regresi canary, menahan promosi dengan gate, melakukan rollback, dan membatasi beban | Layanan Python, PostgreSQL, Prometheus, k6 | [Panduan Case 02](case-02-incident-recovery/docs/build-and-run.md) |
| 03 — Platform developer | Menyediakan preview terisolasi untuk pull request dengan data sintetis dan cleanup terbatas | Python, Docker Compose, PostgreSQL | [Panduan Case 03](case-03-developer-platform/docs/build-and-run.md) |
| 04 — Deployment AI yang aman | Mengevaluasi proposal perubahan deterministik di sandbox dengan pemeriksaan policy dan gate persetujuan | Docker Compose, OPA, Python | [Panduan Case 04](case-04-safe-ai-deployment/docs/build-and-run.md) |

Setiap folder case berisi README, diagram arsitektur atau alur, dan instruksi build/run. Lihat [bukti isolasi/cleanup Case 03](case-03-developer-platform/docs/test-evidence.md) dan [bukti approval/rollback/sandbox Case 04](case-04-safe-ai-deployment/docs/test-evidence.md). Case 04 menggunakan fixture proposal tetap; tidak memanggil model AI.

Butuh panduan setup? Pilih [Docker Compose atau Kubernetes](docs/learning-paths.md). Jika belajar dengan asisten AI, baca [Belajar dengan AI](docs/learning-with-ai.md) terlebih dahulu.

## Mengapa Docker?

- **Latihan berbiaya rendah:** lab berjalan di komputer sendiri dan tidak membuat resource atau tagihan cloud. Docker tetap memakai CPU, memori, penyimpanan, listrik, dan bandwidth lokal saat mengunduh image.
- **Terpisah dari project di host:** setiap case berjalan sebagai Compose project sendiri dengan container, network, dan named volume masing-masing. Dependency seperti Kafka dan PostgreSQL tidak perlu dipasang global; cleanup dibatasi pada resource lab.
- **Setup yang dapat diulang:** file Compose menentukan service dan konfigurasinya sehingga orang lain dapat menjalankan lab yang sama tanpa merakit dependency secara manual.
- **Data yang mudah dibuang:** semua case memakai record sintetis dan kredensial dummy. Container dan volume lab dapat dihapus dengan perintah cleanup yang didokumentasikan.

Docker memberi pemisahan proses dan network yang berguna, tetapi container tetap berbagi kernel host. Anggap lab ini sebagai environment development lokal, bukan batas keamanan untuk kode berbahaya atau infrastruktur produksi.

## Prasyarat

- Docker Desktop atau Docker Engine dengan plugin Docker Compose.
- Python 3 untuk perintah kontrol dari host pada Case 02 dan 03.
- Akses internet saat pertama kali mengunduh image.

Jalankan Docker sebelum memulai lab. Jalankan perintah dari folder case terkait agar Compose menggunakan project dan pengaturan cleanup yang benar.

## Mulai cepat

### Case 01 — Kehilangan data senyap

```sh
cd case-01-silent-data-loss
docker compose config
docker compose up -d --build
docker compose run --rm lab seed --count 20
```

Lanjutkan dengan [panduan Case 01](case-01-silent-data-loss/docs/build-and-run.md) untuk mereproduksi kehilangan data, mengaktifkan karantina, dan melakukan replay event.

### Case 02 — Pemulihan insiden

```sh
cd case-02-incident-recovery
docker compose config
docker compose up -d --build
python3 labctl.py status
```

Router memulai dengan traffic canary 5%. [Panduan Case 02](case-02-incident-recovery/docs/build-and-run.md) menjelaskan pembuatan beban, gate promosi, rollback, dan load shedding.

### Case 03 — Platform developer

```sh
cd case-03-developer-platform
docker compose config
python3 envctl.py provision --pr 42 --generation 1 --port 18421
```

Perintah tersebut membangun dan memeriksa preview lokal di `http://127.0.0.1:18421`. Lihat [panduan Case 03](case-03-developer-platform/docs/build-and-run.md) untuk pembaruan dan cleanup environment.

### Case 04 — Deployment AI yang aman

```sh
cd case-04-safe-ai-deployment
docker compose config
docker compose up -d --build volume-init opa target
```

Jalankan skenario proposal sesuai [panduan Case 04](case-04-safe-ai-deployment/docs/build-and-run.md). Target tersedia di `http://127.0.0.1:18084`.

## Endpoint lokal

Service mengikat port host ke loopback jika port host dipublikasikan.

| Case | Endpoint | Fungsi |
|---|---|---|
| 01 | `localhost:9092` | Kafka |
| 01 | `localhost:5432` | PostgreSQL |
| 01 | `localhost:9090` | Prometheus |
| 01 | `localhost:8001/metrics` | Metrics exporter |
| 02 | `localhost:8082` | Router API dan health |
| 02 | `localhost:9093` | Prometheus |
| 03 | `127.0.0.1:18421` | Contoh preview; pilih port lokal lain untuk preview paralel |
| 04 | `127.0.0.1:18084` | Target deployment mock |

Case 01 dan 02 menggunakan port terpisah untuk Kafka dan Prometheus sehingga kedua project Compose dapat berjalan bersamaan.

## Hentikan dan bersihkan

Untuk Case 01, 02, dan 04, jalankan dari folder case untuk menghentikan container serta menghapus volume sintetis milik project tersebut:

```sh
docker compose down --volumes --remove-orphans
```

Untuk Case 03, gunakan environment manager agar hanya preview yang dipilih yang dihapus:

```sh
python3 envctl.py cleanup --pr 42
```

Perintah cleanup ini menghapus data lab. Panduan tiap case menjelaskan port, kebutuhan resource, perilaku penyimpanan, dan batasannya.

## Lisensi

Kode dan dokumentasi asli dalam repo ini dilisensikan dengan [MIT License](LICENSE). Tool dan image pihak ketiga tetap mengikuti lisensi serta ketentuannya masing-masing.
