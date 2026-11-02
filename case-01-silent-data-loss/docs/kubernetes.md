# Kubernetes deployment path

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This optional Kubernetes version runs a single-node Kafka broker, PostgreSQL, Prometheus, and short-lived Jobs for the producer and workers. It demonstrates the same synthetic schema-drift scenario as Compose. It is a local learning setup, not a resilient Kafka/PostgreSQL production topology.

## Prerequisites

- A local kind/minikube cluster, `kubectl`, and a default StorageClass that supports 1 GiB `ReadWriteOnce` PVCs.
- Build and load the Python lab image. With kind:

  ```sh
  docker build -t case-01-lab:local case-01-silent-data-loss
  kind load docker-image case-01-lab:local --name devops-labs
  ```

  Create the cluster once if needed: `kind create cluster --name devops-labs`. The Kafka pod requests 512 MiB and may need more memory headroom from the local cluster.

## Deploy services

From the repository root, confirm the active Kubernetes context, then apply the resources:

```sh
kubectl config current-context
kubectl apply -k case-01-silent-data-loss/kubernetes
kubectl -n case-01 rollout status statefulset/postgres --timeout=180s
kubectl -n case-01 rollout status statefulset/kafka --timeout=300s
kubectl -n case-01 rollout status deployment/metrics --timeout=120s
kubectl -n case-01 rollout status deployment/prometheus --timeout=120s
```

`secret.example.yaml` contains a dummy local password. Do not replace it with production credentials. Kubernetes Secret values may need separate etcd encryption configuration.

## Run the data-loss scenario

Run each Job once in the order below and inspect its logs. Jobs are separate so the broken and hardened consumers use independent Kafka consumer groups.

```sh
kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/seed-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-seed --timeout=300s
kubectl -n case-01 logs job/case-01-seed

kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/broken-worker-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-broken-worker --timeout=300s
kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/report-broken-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-report-broken --timeout=120s
kubectl -n case-01 logs job/case-01-report-broken

kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/hardened-worker-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-hardened-worker --timeout=300s
kubectl -n case-01 logs job/case-01-hardened-worker
kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/report-broken-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-report-hardened --timeout=120s
kubectl -n case-01 logs job/case-01-report-hardened

kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/replay-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-replay --timeout=120s
kubectl -n case-01 logs job/case-01-replay
```

The 20-event fixture includes three schema-v2 events. The broken worker advances offsets while silently dropping unsupported events; reconciliation should show unaccounted IDs. The hardened worker persists supported rows and quarantines unsupported ones before committing offsets. Replay applies the reviewed adapter idempotently. For a clean repetition, delete the named Jobs and reset the namespace PVC data by deleting/recreating the namespace, then apply the base resources and rerun in order.

Prometheus is available through `kubectl -n case-01 port-forward service/prometheus 9090:9090`. The metrics exporter exposes the reconciliation gap and quarantine metrics.

## Cleanup and limits

```sh
kubectl delete namespace case-01
```

This removes the lab's PVCs and synthetic data. The example has a single Kafka broker, one PostgreSQL replica, no TLS/authentication, and a dummy Secret; it is not suitable as a production template without hardening and HA design.

<a id="bahasa-indonesia"></a>

## Jalur deployment Kubernetes

Versi Kubernetes opsional ini menjalankan satu broker Kafka, PostgreSQL, Prometheus, dan Job sementara untuk producer serta worker. Skenario schema drift sintetisnya sama dengan Compose. Ini setup belajar lokal, bukan topologi Kafka/PostgreSQL production yang tahan gangguan.

## Prasyarat

- Kubernetes cluster lokal kind/minikube, `kubectl`, dan StorageClass default yang mendukung PVC 1 GiB `ReadWriteOnce`.
- Build dan muat image Python lab. Dengan kind:

  ```sh
  docker build -t case-01-lab:local case-01-silent-data-loss
  kind load docker-image case-01-lab:local --name devops-labs
  ```

  Buat cluster satu kali jika belum ada: `kind create cluster --name devops-labs`. Pod Kafka meminta memori 512 MiB; siapkan ruang memori lokal cluster yang cukup.

## Deploy service

Dari root repo, pastikan context Kubernetes yang aktif, lalu terapkan resource:

```sh
kubectl config current-context
kubectl apply -k case-01-silent-data-loss/kubernetes
kubectl -n case-01 rollout status statefulset/postgres --timeout=180s
kubectl -n case-01 rollout status statefulset/kafka --timeout=300s
kubectl -n case-01 rollout status deployment/metrics --timeout=120s
kubectl -n case-01 rollout status deployment/prometheus --timeout=120s
```

`secret.example.yaml` berisi password dummy lokal. Jangan menggantinya dengan kredensial production. Nilai Secret Kubernetes mungkin memerlukan konfigurasi enkripsi etcd tersendiri.

## Jalankan skenario kehilangan data

Jalankan setiap Job satu kali sesuai urutan dan lihat log-nya. Job dipisahkan agar consumer rusak dan hardened memakai Kafka consumer group yang berbeda.

```sh
kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/seed-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-seed --timeout=300s
kubectl -n case-01 logs job/case-01-seed

kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/broken-worker-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-broken-worker --timeout=300s
kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/report-broken-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-report-broken --timeout=120s
kubectl -n case-01 logs job/case-01-report-broken

kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/hardened-worker-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-hardened-worker --timeout=300s
kubectl -n case-01 logs job/case-01-hardened-worker
kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/report-broken-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-report-hardened --timeout=120s
kubectl -n case-01 logs job/case-01-report-hardened

kubectl apply -f case-01-silent-data-loss/kubernetes/jobs/replay-job.yaml
kubectl -n case-01 wait --for=condition=complete job/case-01-replay --timeout=120s
kubectl -n case-01 logs job/case-01-replay
```

Fixture 20 event memiliki tiga event schema v2. Worker rusak memajukan offset sambil diam-diam membuang event yang tidak didukung; rekonsiliasi seharusnya menemukan ID yang belum tercatat. Worker hardened menyimpan row yang didukung dan mengarantina sisanya sebelum commit offset. Replay menjalankan adapter yang sudah direview secara idempotent. Untuk mengulang dari kondisi bersih, hapus Job terkait dan reset data PVC dengan menghapus/membuat ulang namespace, lalu terapkan ulang resource dasar dan jalankan urutannya.

Prometheus dapat diakses dengan `kubectl -n case-01 port-forward service/prometheus 9090:9090`. Metrics exporter menampilkan gap rekonsiliasi dan metrik karantina.

## Cleanup dan batasan

```sh
kubectl delete namespace case-01
```

Perintah ini menghapus PVC lab dan data sintetisnya. Contoh hanya memakai satu broker Kafka, satu replica PostgreSQL, tanpa TLS/authentication, serta Secret dummy; jangan jadikan ini template production tanpa hardening dan desain HA.
