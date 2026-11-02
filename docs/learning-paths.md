# Learning paths: Docker Compose YAML and Kubernetes

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Choose a way to run the labs

Every case includes a `compose.yaml` and a Kubernetes manifest directory named `kubernetes/`. Docker Compose is the easiest local starting point. Kubernetes is an optional deployment track for all four cases; each track has its own guide, prerequisites, and scope. Both formats use YAML, but Compose files and Kubernetes manifests describe different resources and are applied with different tools.

| Track | Choose this when… | Where to go |
| --- | --- | --- |
| Docker Compose | You want the shortest route through any of the four cases. | Start below, then use the chosen case's build/run guide. |
| Kubernetes | You want to practice Kubernetes resources and workflows for a particular scenario. | Choose one: [Case 01](../case-01-silent-data-loss/docs/kubernetes.md) · [Case 02](../case-02-incident-recovery/docs/kubernetes.md) · [Case 03](../case-03-developer-platform/docs/kubernetes.md) · [Case 04](../case-04-safe-ai-deployment/docs/kubernetes.md). |

Kubernetes resources are learning examples with case-specific limits. Compose and Kubernetes behavior can differ because networking, scheduling, storage, permissions, resource limits, and cleanup behave differently. Read the chosen case's Kubernetes guide before applying manifests.

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

## Track B — Kubernetes (all four cases)

Choose a case-specific guide for complete image build/load, apply, scenario, and cleanup steps:

- [Case 01 — silent data loss](../case-01-silent-data-loss/docs/kubernetes.md)
- [Case 02 — incident recovery](../case-02-incident-recovery/docs/kubernetes.md)
- [Case 03 — developer platform](../case-03-developer-platform/docs/kubernetes.md)
- [Case 04 — safe AI deployment](../case-04-safe-ai-deployment/docs/kubernetes.md)

The guides use local clusters such as `kind` or minikube. One shared local cluster can host the cases in separate namespaces; Case 02's guide also describes its standalone `case02` kind cluster. Always check `kubectl config current-context` before applying YAML.

1. Install and start Docker; install [`kubectl`](https://kubernetes.io/docs/tasks/tools/) and a local cluster tool such as [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/) or minikube.
2. Create a local cluster if needed, then check the active context:

   ```sh
   kind create cluster --name devops-labs --wait 2m
   kubectl config current-context
   kubectl get nodes -o wide
   ```

   The current context should be `kind-devops-labs`. Do not apply these lab manifests until you have confirmed the context is the local learning cluster you intend to use.
3. Follow the selected case guide to build/load its image, create its local demo Secret or ConfigMaps when required, then apply the case's `kubernetes/` directory or documented Jobs.
4. Follow that guide for readiness checks, scenario commands, port-forwarding, and expected results.
5. Delete only the case namespace named in that guide. To delete the shared local cluster, run `kind delete cluster --name devops-labs` after finishing every case.

`kind` runs Kubernetes nodes as containers on your machine; it does not create a cloud cluster. Give Docker Desktop enough CPU and memory for the cluster and lab pods. The cases with database or state PVCs need a default StorageClass that supports `ReadWriteOnce` claims. Case 01 includes Kafka and needs additional memory. Each Kubernetes guide describes its own limits, including cleanup behavior.

## Learn with AI

AI tools can explain a manifest, help interpret a sanitized error, or suggest a next diagnostic command. They are optional and are not integrated into the labs. For safe, useful prompts and privacy guidance, see [Learning with AI](learning-with-ai.md).

<a id="bahasa-indonesia"></a>

## Pilih cara menjalankan lab

Setiap case memiliki `compose.yaml` dan direktori manifest Kubernetes bernama `kubernetes/`. Docker Compose adalah awal lokal yang paling mudah. Kubernetes merupakan jalur deployment opsional untuk keempat case; setiap jalur punya panduan, prasyarat, dan cakupan tersendiri. Keduanya memakai YAML, tetapi file Compose dan manifest Kubernetes mendeskripsikan resource berbeda dan diterapkan dengan tool yang berbeda.

| Jalur | Pilih jika… | Panduan |
| --- | --- | --- |
| Docker Compose | Ingin mulai paling cepat untuk salah satu dari empat case. | Ikuti langkah di bawah, lalu buka panduan build/run case pilihan. |
| Kubernetes | Ingin berlatih resource dan workflow Kubernetes untuk skenario tertentu. | Pilih salah satu: [Case 01](../case-01-silent-data-loss/docs/kubernetes.md) · [Case 02](../case-02-incident-recovery/docs/kubernetes.md) · [Case 03](../case-03-developer-platform/docs/kubernetes.md) · [Case 04](../case-04-safe-ai-deployment/docs/kubernetes.md). |

Resource Kubernetes adalah contoh belajar dengan batasan spesifik per case. Perilaku Compose dan Kubernetes dapat berbeda karena jaringan, scheduling, storage, permission, batas resource, dan cleanup berjalan berbeda. Baca panduan Kubernetes case yang dipilih sebelum menerapkan manifest.

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

## Jalur B — Kubernetes (semua case)

Pilih panduan case untuk instruksi lengkap build/load image, apply, skenario, dan cleanup:

- [Case 01 — kehilangan data senyap](../case-01-silent-data-loss/docs/kubernetes.md)
- [Case 02 — pemulihan insiden](../case-02-incident-recovery/docs/kubernetes.md)
- [Case 03 — platform developer](../case-03-developer-platform/docs/kubernetes.md)
- [Case 04 — deployment AI aman](../case-04-safe-ai-deployment/docs/kubernetes.md)

Panduan menggunakan cluster lokal seperti `kind` atau minikube. Satu cluster lokal bersama dapat menjalankan case di namespace terpisah; panduan Case 02 juga menjelaskan cluster kind mandiri bernama `case02`. Selalu periksa `kubectl config current-context` sebelum menerapkan YAML.

1. Pasang dan jalankan Docker; pasang [`kubectl`](https://kubernetes.io/docs/tasks/tools/) dan tool cluster lokal seperti [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/) atau minikube.
2. Buat cluster lokal jika belum tersedia, lalu periksa context aktif:

   ```sh
   kind create cluster --name devops-labs --wait 2m
   kubectl config current-context
   kubectl get nodes -o wide
   ```

   Context yang aktif seharusnya `kind-devops-labs`. Pastikan context adalah cluster belajar lokal yang benar sebelum menerapkan manifest lab.
3. Ikuti panduan case pilihan untuk build/muat image, membuat Secret atau ConfigMap demo lokal jika dibutuhkan, lalu menerapkan folder `kubernetes/` atau Job sesuai petunjuk.
4. Ikuti panduan tersebut untuk pemeriksaan kesiapan, perintah skenario, port-forward, dan hasil yang diharapkan.
5. Hapus hanya namespace case yang disebut dalam panduannya. Untuk menghapus shared cluster lokal setelah semua case selesai, jalankan `kind delete cluster --name devops-labs`.

`kind` menjalankan node Kubernetes sebagai container di mesin sendiri; tool ini tidak membuat cluster cloud. Sediakan CPU dan memori Docker Desktop yang cukup untuk cluster dan Pod lab. Case yang memakai database atau PVC state membutuhkan StorageClass default yang mendukung claim `ReadWriteOnce`. Case 01 juga menjalankan Kafka dan memerlukan memori tambahan. Setiap panduan Kubernetes menjelaskan batasan, termasuk cara cleanup.

## Belajar dengan AI

AI dapat membantu menjelaskan manifest, memahami error yang sudah disamarkan, atau menyarankan perintah diagnosis berikutnya. AI bersifat opsional dan tidak terintegrasi ke dalam lab. Lihat [Belajar dengan AI](learning-with-ai.md) untuk contoh prompt dan panduan privasi.
