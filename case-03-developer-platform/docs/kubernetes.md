# Kubernetes deployment path

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This optional Kubernetes example creates one preview environment for **PR 42, generation 1** in its own namespace. The namespace contains its own PostgreSQL StatefulSet and persistent volume, so another PR or generation can use a separate namespace and database. The manifests demonstrate isolation primitives; they do not include a GitHub integration or an automatic namespace TTL controller. The existing Compose `envctl.py` lab demonstrates the automated lifecycle manager.

## Prerequisites

- A local Kubernetes cluster such as kind or minikube, `kubectl`, and a default StorageClass supporting 1 GiB `ReadWriteOnce` PVCs.
- Build the app image and make it available to your cluster. With kind:

  ```sh
  docker build -t case-03-app:local case-03-developer-platform
  kind load docker-image case-03-app:local --name devops-labs
  ```

  Create the local cluster once if needed: `kind create cluster --name devops-labs`.

## Apply and inspect

From the repository root, verify your active context, then apply the sample:

```sh
kubectl config current-context
kubectl apply -k case-03-developer-platform/kubernetes
kubectl -n case-03-pr-42-g1 rollout status statefulset/postgres --timeout=180s
kubectl -n case-03-pr-42-g1 wait --for=condition=complete job/preview-seed --timeout=180s
kubectl -n case-03-pr-42-g1 rollout status deployment/preview --timeout=120s
kubectl -n case-03-pr-42-g1 port-forward service/preview 18421:8000
```

In another terminal, open `http://127.0.0.1:18421/` or `/items`. The response identifies the PR and generation and shows only synthetic seeded records.

## Create another isolated generation

For each environment, copy the sample folder to a distinct Kustomize overlay and change **all** of these together: namespace, PR/generation labels, and `PR_NUMBER`/`GENERATION` environment values. Apply each overlay into a distinct namespace. Each namespace gets its own database and PVC. Wait for and inspect the new generation before deleting the old namespace. Never delete by a broad label selector unless you have checked every matched namespace.

The seed Job has `ttlSecondsAfterFinished: 86400`; Kubernetes removes that completed Job after a day. This does **not** expire or delete the preview Deployment, namespace, or database PVC. Close/merge/TTL cleanup across namespaces requires an external CI workflow or lifecycle controller, which is not included here. Delete one specific environment with `kubectl delete namespace <that-environment-namespace>` after confirming the name; namespace deletion also removes its PVCs and data.

The example Secret contains a dummy local password. Kubernetes Secret values are not automatically encrypted in etcd by every cluster. Do not put production credentials here; use a cluster's secret-management and encryption controls for real workloads.

## Cleanup

```sh
kubectl delete namespace case-03-pr-42-g1
```

This deletes the sample environment and its namespaced storage claim. It does not delete the Kubernetes cluster.

<a id="bahasa-indonesia"></a>

## Jalur deployment Kubernetes

Contoh opsional ini membuat satu preview environment untuk **PR 42, generasi 1** di namespace tersendiri. Namespace memiliki PostgreSQL StatefulSet dan persistent volume sendiri, sehingga PR atau generasi lain bisa memakai namespace serta database terpisah. Manifest ini memperagakan primitive isolasi; tidak ada integrasi GitHub atau controller TTL namespace otomatis. Lab Compose `envctl.py` yang sudah ada memperagakan pengelola siklus hidup otomatis.

## Prasyarat

- Kubernetes cluster lokal seperti kind atau minikube, `kubectl`, dan StorageClass default yang mendukung PVC 1 GiB `ReadWriteOnce`.
- Build image aplikasi dan sediakan image tersebut di cluster. Dengan kind:

  ```sh
  docker build -t case-03-app:local case-03-developer-platform
  kind load docker-image case-03-app:local --name devops-labs
  ```

  Jika belum punya cluster lokal, buat sekali dengan `kind create cluster --name devops-labs`.

## Terapkan dan periksa

Dari root repo, periksa context aktif lalu terapkan contoh:

```sh
kubectl config current-context
kubectl apply -k case-03-developer-platform/kubernetes
kubectl -n case-03-pr-42-g1 rollout status statefulset/postgres --timeout=180s
kubectl -n case-03-pr-42-g1 wait --for=condition=complete job/preview-seed --timeout=180s
kubectl -n case-03-pr-42-g1 rollout status deployment/preview --timeout=120s
kubectl -n case-03-pr-42-g1 port-forward service/preview 18421:8000
```

Di terminal lain, buka `http://127.0.0.1:18421/` atau `/items`. Respons menampilkan PR dan generasi serta record seed sintetis.

## Membuat generasi terisolasi lain

Untuk setiap environment, salin folder contoh ke overlay Kustomize berbeda dan ubah **semua** nilai berikut secara bersamaan: namespace, label PR/generasi, serta nilai environment `PR_NUMBER`/`GENERATION`. Terapkan tiap overlay ke namespace berbeda. Setiap namespace mendapat database dan PVC sendiri. Tunggu dan periksa generasi baru sebelum menghapus namespace lama. Jangan menghapus berdasarkan selector label luas sebelum memeriksa semua namespace yang cocok.

Seed Job memiliki `ttlSecondsAfterFinished: 86400`; Kubernetes menghapus Job yang selesai setelah satu hari. Ini **tidak** menghapus Deployment preview, namespace, atau PVC database. Cleanup ketika PR ditutup/merge atau melewati TTL memerlukan workflow CI atau lifecycle controller eksternal yang tidak disediakan di sini. Untuk menghapus satu environment, jalankan `kubectl delete namespace <namespace-environment>` setelah nama dipastikan; penghapusan namespace ikut menghapus PVC dan datanya.

Secret contoh memakai password dummy lokal. Nilai Kubernetes Secret tidak selalu otomatis terenkripsi di etcd. Jangan masukkan kredensial produksi; gunakan pengelolaan secret dan enkripsi cluster yang sesuai untuk workload nyata.

## Cleanup

```sh
kubectl delete namespace case-03-pr-42-g1
```

Perintah ini menghapus environment contoh dan storage claim di dalamnya, bukan Kubernetes cluster.
