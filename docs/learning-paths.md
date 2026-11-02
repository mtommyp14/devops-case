# Learning paths: Docker Compose YAML and Kubernetes

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Choose a way to run the labs

Every case includes a `compose.yaml`. Docker Compose is the recommended starting point: it runs all four cases locally and does not require a Kubernetes cluster. Kubernetes manifests are an optional next step and currently cover **Case 02 only**. Both formats are YAML, but a Compose file is not a Kubernetes manifest; each is read by a different tool and describes different resources.

| Track | Choose this when… | Where to go |
| --- | --- | --- |
| Docker Compose | You want the shortest route through any of the four cases. | Start below, then use the chosen case's build/run guide. |
| Kubernetes | You want to learn Deployments, Services, StatefulSets, probes, and Jobs with the incident-recovery scenario. | Follow the [Case 02 Kubernetes guide](../case-02-incident-recovery/docs/kubernetes.md). |

The Kubernetes track is not yet available for Cases 01, 03, or 04. The scenarios are designed to be similar, but Compose and Kubernetes results can differ because networking, scheduling, storage, resource limits, and scaling behave differently.

## Track A — Docker Compose (all four cases)

### 1. Install and check prerequisites

Install [Docker Desktop](https://docs.docker.com/desktop/) for macOS/Windows, or Docker Engine and the Compose plugin for Linux. Then start Docker Desktop or the Docker daemon and check:

```sh
docker version
docker compose version
python3 --version
```

Python 3 is used by host-side control commands in Cases 02 and 03. Compose downloads images the first time, so an internet connection is needed then.

### 2. Get the source and choose one case

```sh
git clone https://github.com/mtommyp14/devops-portfolio.git
cd devops-portfolio
```

Choose one folder: `case-01-silent-data-loss`, `case-02-incident-recovery`, `case-03-developer-platform`, or `case-04-safe-ai-deployment`. Each case guide lists its prerequisites and exact scenario steps. For example, start Case 02:

```sh
cd case-02-incident-recovery
docker compose config
docker compose up -d --build
docker compose ps
```

Follow the [Case 02 build/run guide](../case-02-incident-recovery/docs/build-and-run.md) to run the traffic, gate, promotion, rollback, and load-shedding scenarios. Use the [Case 01](../case-01-silent-data-loss/docs/build-and-run.md), [Case 03](../case-03-developer-platform/docs/build-and-run.md), and [Case 04](../case-04-safe-ai-deployment/docs/build-and-run.md) guides for their case-specific commands. Case 03 uses `envctl.py` to provision a preview rather than starting with a generic `docker compose up` command.

### 3. Stop and clean up

For Cases 01, 02, and 04, run this from the case directory:

```sh
docker compose down --volumes --remove-orphans
```

This deletes the lab's containers and synthetic named-volume data. For Case 03, use its scoped cleanup command instead:

```sh
python3 envctl.py cleanup --pr 42
```

Use the same pull request number you provisioned. Read the case guide before cleanup if you want to keep evidence or data.

## Track B — Kubernetes (Case 02 only)

Use the [Case 02 Kubernetes guide](../case-02-incident-recovery/docs/kubernetes.md) for the complete manifest walkthrough. In short, the local `kind` route is:

1. Install and start Docker; install [`kubectl`](https://kubernetes.io/docs/tasks/tools/) and [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/).
2. From the repository root, create a local cluster and check the active context:

   ```sh
   kind create cluster --name case02 --wait 2m
   kubectl config current-context
   kubectl get nodes -o wide
   ```

   The current context should be `kind-case02`. Do not apply these lab manifests until you have confirmed the context is the local learning cluster you intend to use.
3. Follow the Case 02 guide to build `case-02-app:local`, load it into kind, create the local demo Secret, and apply `kubernetes/`.
4. Use `kubectl port-forward` for the router and Prometheus, then connect `labctl.py` and run the optional k6 Job as documented.
5. Remove the `case-02` namespace after the lab. To remove the whole local cluster too, run `kind delete cluster --name case02`.

`kind` runs Kubernetes nodes as containers on your machine; it does not create a cloud cluster. Give Docker Desktop enough CPU and memory for the cluster and lab pods. The manifests include a 1 GiB PostgreSQL PVC, so the cluster also needs a default StorageClass that supports `ReadWriteOnce` claims.

## Learn with AI

AI tools can explain a manifest, help interpret a sanitized error, or suggest a next diagnostic command. They are optional and are not integrated into the labs. For safe, useful prompts and privacy guidance, see [Learning with AI](learning-with-ai.md).

<a id="bahasa-indonesia"></a>

## Pilih cara menjalankan lab

Setiap case memiliki file `compose.yaml`. Docker Compose adalah awal yang disarankan: tool ini menjalankan keempat case secara lokal tanpa memerlukan Kubernetes cluster. Manifest Kubernetes merupakan jalur lanjutan yang opsional dan saat ini hanya tersedia untuk **Case 02**. Keduanya menggunakan YAML, tetapi file Compose bukan manifest Kubernetes; masing-masing dibaca oleh tool berbeda dan mendeskripsikan resource berbeda.

| Jalur | Pilih jika… | Panduan |
| --- | --- | --- |
| Docker Compose | Ingin mulai paling cepat untuk salah satu dari empat case. | Ikuti langkah di bawah, lalu buka panduan build/run case pilihan. |
| Kubernetes | Ingin belajar Deployment, Service, StatefulSet, probe, dan Job pada skenario pemulihan insiden. | Ikuti [panduan Kubernetes Case 02](../case-02-incident-recovery/docs/kubernetes.md). |

Jalur Kubernetes belum tersedia untuk Case 01, 03, dan 04. Skenarionya dirancang serupa, tetapi hasil Compose dan Kubernetes dapat berbeda karena cara kerja jaringan, scheduling, storage, batas resource, dan scaling berbeda.

## Jalur A — Docker Compose (semua empat case)

### 1. Pasang dan periksa prasyarat

Pasang [Docker Desktop](https://docs.docker.com/desktop/) untuk macOS/Windows, atau Docker Engine beserta plugin Compose untuk Linux. Jalankan Docker Desktop atau daemon Docker, lalu periksa:

```sh
docker version
docker compose version
python3 --version
```

Python 3 digunakan oleh perintah kontrol host-side pada Case 02 dan 03. Compose mengunduh image saat pertama kali dijalankan sehingga internet diperlukan pada saat itu.

### 2. Ambil source dan pilih case

```sh
git clone https://github.com/mtommyp14/devops-portfolio.git
cd devops-portfolio
```

Pilih salah satu folder: `case-01-silent-data-loss`, `case-02-incident-recovery`, `case-03-developer-platform`, atau `case-04-safe-ai-deployment`. Setiap panduan menjelaskan prasyarat dan langkah skenario. Contoh untuk memulai Case 02:

```sh
cd case-02-incident-recovery
docker compose config
docker compose up -d --build
docker compose ps
```

Ikuti [panduan build/run Case 02](../case-02-incident-recovery/docs/build-and-run.md) untuk menjalankan traffic, gate, promosi, rollback, dan load shedding. Gunakan panduan [Case 01](../case-01-silent-data-loss/docs/build-and-run.md), [Case 03](../case-03-developer-platform/docs/build-and-run.md), dan [Case 04](../case-04-safe-ai-deployment/docs/build-and-run.md) untuk langkah masing-masing. Case 03 menggunakan `envctl.py` untuk menyiapkan preview, bukan dimulai dengan perintah umum `docker compose up`.

### 3. Hentikan dan bersihkan

Untuk Case 01, 02, dan 04, jalankan dari folder case:

```sh
docker compose down --volumes --remove-orphans
```

Perintah ini menghapus container lab dan data sintetis dalam named volume. Untuk Case 03, gunakan perintah cleanup yang hanya menargetkan preview tertentu:

```sh
python3 envctl.py cleanup --pr 42
```

Gunakan nomor pull request yang sama dengan saat provisioning. Baca panduan case sebelum cleanup jika ingin menyimpan bukti atau data.

## Jalur B — Kubernetes (hanya Case 02)

Ikuti [panduan Kubernetes Case 02](../case-02-incident-recovery/docs/kubernetes.md) untuk langkah manifest lengkap. Ringkasnya, jalur lokal dengan `kind` adalah:

1. Pasang dan jalankan Docker; pasang [`kubectl`](https://kubernetes.io/docs/tasks/tools/) dan [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/).
2. Dari root repo, buat cluster lokal dan periksa context aktif:

   ```sh
   kind create cluster --name case02 --wait 2m
   kubectl config current-context
   kubectl get nodes -o wide
   ```

   Context yang aktif seharusnya `kind-case02`. Pastikan context adalah cluster belajar lokal yang benar sebelum menerapkan manifest lab.
3. Ikuti panduan Case 02 untuk membangun `case-02-app:local`, memuat image ke kind, membuat Secret demo lokal, dan menerapkan isi folder `kubernetes/`.
4. Gunakan `kubectl port-forward` untuk router dan Prometheus, lalu hubungkan `labctl.py` dan jalankan Job k6 opsional sesuai instruksi.
5. Hapus namespace `case-02` setelah lab selesai. Untuk menghapus seluruh cluster lokal, jalankan `kind delete cluster --name case02`.

`kind` menjalankan node Kubernetes sebagai container di mesin sendiri; tool ini tidak membuat cluster cloud. Sediakan CPU dan memori Docker Desktop yang cukup untuk cluster dan Pod lab. Manifest memakai PVC PostgreSQL 1 GiB, sehingga cluster perlu StorageClass default yang mendukung claim `ReadWriteOnce`.

## Belajar dengan AI

AI dapat membantu menjelaskan manifest, memahami error yang sudah disamarkan, atau menyarankan perintah diagnosis berikutnya. AI bersifat opsional dan tidak terintegrasi ke dalam lab. Lihat [Belajar dengan AI](learning-with-ai.md) untuk contoh prompt dan panduan privasi.
