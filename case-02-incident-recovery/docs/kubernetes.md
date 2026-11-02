# Case 02 — Kubernetes manifests

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Purpose and parity

The Compose lab is the default local path. This optional Kubernetes variant gives learners a second way to run the same incident-recovery scenario using Kubernetes Deployments, Services, a PostgreSQL StatefulSet, probes, resource requests/limits, Prometheus, and a k6 Job. Both Compose and Kubernetes configuration are YAML, but their schemas and controllers differ.

The intended workflow is equivalent: route requests between stable and canary, measure both releases, hold or promote using the same `labctl.py` gate, roll traffic back to stable, and observe load shedding. Results are not expected to be numerically identical. Cluster networking, scheduling, CPU limits, storage, replica counts, and node capacity change latency and throughput. The manifests provide one replica per app release for a small learning cluster; record the cluster details alongside any benchmark.

`labctl.py rollback` changes the router's canary percentage to zero. It does not revert a Kubernetes Deployment image. The current lab simulates a faulty canary with `APP_FAULT`; a real image rollback is a separate operation such as `kubectl rollout undo deployment/canary`.

## Requirements

- A Kubernetes cluster and `kubectl` configured to use it. Docker Desktop Kubernetes, kind, or minikube are suitable for this learning setup.
- For the step-by-step local path below: Docker running, [`kubectl`](https://kubernetes.io/docs/tasks/tools/) installed, and [`kind`](https://kind.sigs.k8s.io/docs/user/quick-start/) installed.
- A cluster with a default `ReadWriteOnce` StorageClass for PostgreSQL's 1 GiB claim.
- Docker to build the local app image. For kind, load the image into the cluster; for minikube, use its image-loading command. A remote cluster needs the image pushed to a registry it can access.
- Approximately 1.5 GiB of pod memory limits, plus Kubernetes and node overhead. The k6 Job adds up to 256 MiB.

## Build and deploy

First create a local kind cluster. Run this command from any directory. It creates Kubernetes locally using Docker and does not provision cloud resources:

```sh
kind create cluster --name case02 --wait 2m
kubectl config current-context
kubectl get nodes -o wide
```

Confirm the current context is `kind-case02` before continuing. If you already use a different Kubernetes cluster, do not run the apply commands until you have confirmed that it is the intended learning cluster. To use Docker Desktop's built-in Kubernetes instead, enable it in Docker Desktop settings, confirm its context, and follow the image-availability note below.

Now run these commands from `case-02-incident-recovery/`. The secret values are disposable demo credentials. Kubernetes Secrets are not encrypted merely because they are stored as Secret objects; use cluster encryption and a secret manager for real credentials.

```sh
docker build -t case-02-app:local .
# Make the locally built image available to the kind cluster:
kind load docker-image case-02-app:local --name case02
# For minikube instead, use: minikube image load case-02-app:local

kubectl apply -f kubernetes/namespace.yaml
kubectl create secret generic case-02-demo-secrets -n case-02 \
  --from-literal=postgres-password=lab-local-only \
  --from-literal=admin-token=local-demo-token \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -k kubernetes/
kubectl rollout status statefulset/postgres -n case-02 --timeout=180s
kubectl rollout status deployment/stable -n case-02 --timeout=180s
kubectl rollout status deployment/canary -n case-02 --timeout=180s
kubectl rollout status deployment/router -n case-02 --timeout=180s
kubectl rollout status deployment/prometheus -n case-02 --timeout=180s
kubectl get pods,services,pvc -n case-02
```

For minikube, omit the `kind load` line and use `minikube image load case-02-app:local`. With Docker Desktop Kubernetes, build through Docker Desktop's Docker daemon; if the cluster cannot see that image, check Docker Desktop's current image-loading instructions. Never push the dummy image or demo credentials to a public registry.

## Run the lab

In separate terminals, forward the two ClusterIP services. The applications are not exposed with a NodePort or public LoadBalancer:

```sh
kubectl port-forward -n case-02 service/router 8082:8000
kubectl port-forward -n case-02 service/prometheus 9093:9090
```

From the case directory, use the existing local controller against those forwarded ports:

```sh
export LAB_ROUTER_URL=http://127.0.0.1:8082
export LAB_PROMETHEUS_URL=http://127.0.0.1:9093
export LAB_ADMIN_TOKEN=local-demo-token
python3 labctl.py status
curl -s 'http://127.0.0.1:8082/api/work?priority=critical'
```

Set a synthetic fault or change the canary weight with the same lab controls. To remove the latency fault:

```sh
kubectl set env deployment/canary -n case-02 APP_FAULT=none
kubectl rollout status deployment/canary -n case-02
python3 labctl.py canary 50
```

The 50% share is for meeting this lab's unchanged served-canary sample floor under a small local load generator; it is not a production rollout recommendation. See the [Compose guide](build-and-run.md) for the gate conditions and interpretation. You can run `python3 labctl.py gate`, `promote`, and `rollback` after starting enough traffic. Router weight changes are held in memory and return to the manifest's initial 5% after a router restart.

## Run k6 in the cluster

Create a ConfigMap from the existing script and start the optional Job. Delete the prior Job before repeating it so the new run gets a fresh summary:

```sh
kubectl create configmap k6-script -n case-02 \
  --from-file=load.js=scripts/load.js \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl delete job/k6-load -n case-02 --ignore-not-found
kubectl apply -f kubernetes/k6-job.yaml
kubectl wait --for=condition=complete job/k6-load -n case-02 --timeout=10m
kubectl logs -n case-02 job/k6-load
```

The Job defaults to 40 offered requests/second for 130 seconds. Tune `RATE`, `DURATION`, `MAX_VUS`, and `PREALLOCATED_VUS` in `k6-job.yaml` when running a different profile, and record the actual values and cluster/node conditions. The k6 summary distinguishes successful requests, controlled load-shed responses, unexpected failures, p95/p99, and dropped iterations.

## Cleanup

Delete the lab namespace when finished. This removes its workloads, Secret, and PVC; whether the underlying storage asset is also deleted depends on the cluster StorageClass reclaim policy.

```sh
kubectl delete namespace case-02
```

To also remove the local kind cluster created above, run this after namespace cleanup:

```sh
kind delete cluster --name case02
```

<a id="bahasa-indonesia"></a>

## Bahasa Indonesia

### Tujuan dan kesetaraan

Compose tetap menjadi cara default untuk menjalankan lab lokal. Varian Kubernetes ini opsional dan memberi cara belajar kedua menggunakan Deployment, Service, StatefulSet PostgreSQL, probe, batas resource, Prometheus, dan Job k6. Compose dan Kubernetes sama-sama memakai YAML, tetapi skema dan controller-nya berbeda.

Alur yang ingin dicapai setara: merutekan request antara stable dan canary, mengukur kedua release, menahan atau mempromosikan berdasarkan gate `labctl.py`, mengembalikan traffic ke stable, dan mengamati load shedding. Angka hasilnya tidak akan selalu sama. Jaringan cluster, penjadwalan, batas CPU, storage, jumlah replika, dan kapasitas node memengaruhi latensi serta throughput. Manifest menyediakan satu replika per release aplikasi untuk cluster belajar kecil; catat kondisi cluster saat melakukan benchmark.

`labctl.py rollback` mengubah persentase canary pada router menjadi nol. Perintah itu tidak mengembalikan image Deployment Kubernetes. Lab ini mensimulasikan canary bermasalah dengan `APP_FAULT`; rollback image sungguhan merupakan operasi terpisah, misalnya `kubectl rollout undo deployment/canary`.

### Persyaratan

- Kubernetes cluster dan `kubectl` yang sudah dikonfigurasi. Jalur langkah demi langkah di bawah menggunakan Docker, `kubectl`, dan `kind` lokal.
- Cluster dengan StorageClass default `ReadWriteOnce` untuk PVC PostgreSQL sebesar 1 GiB.
- Docker untuk membangun image aplikasi lokal. Untuk kind, muat image ke cluster; untuk minikube gunakan perintah pemuatan image-nya. Cluster remote memerlukan image di registry yang dapat diakses.
- Batas memori Pod sekitar 1,5 GiB, ditambah overhead Kubernetes dan node. Job k6 menambah batas hingga 256 MiB.

### Build, deploy, dan jalankan

Untuk jalur kind lokal, buat cluster dari direktori mana pun dengan `kind create cluster --name case02 --wait 2m`, lalu pastikan `kubectl config current-context` menampilkan `kind-case02` dan `kubectl get nodes -o wide` menunjukkan node siap. `kind` menjalankan Kubernetes di Docker secara lokal tanpa resource cloud.

Lanjutkan perintah pada bagian English dari folder `case-02-incident-recovery/`. Jika memakai cluster Kubernetes lain, periksa context yang aktif dengan teliti sebelum menjalankan perintah apply. Nilai secret contoh hanya kredensial demo. Objek Secret Kubernetes tidak otomatis terenkripsi hanya karena jenisnya Secret; gunakan enkripsi cluster dan secret manager untuk kredensial sungguhan.

Forward service `router` dan `prometheus` ke localhost, lalu set `LAB_ROUTER_URL`, `LAB_PROMETHEUS_URL`, dan `LAB_ADMIN_TOKEN` agar `labctl.py` memakai service dalam cluster. Aplikasi tetap tidak dipaparkan sebagai NodePort atau LoadBalancer publik.

Gunakan `kubectl set env deployment/canary -n case-02 APP_FAULT=none` untuk menghapus fault latensi. Jalankan gate dan perintah traffic yang sama seperti di Compose. Persentase 50% hanya membantu memenuhi sample floor pada beban lokal dan bukan rekomendasi produksi. Angka beban Kubernetes perlu dicatat terpisah karena tidak dijamin sama dengan hasil Compose.

Job k6 memakai skrip yang sama seperti Compose. Setelah run selesai, baca output dengan `kubectl logs`; hapus Job sebelum menjalankan ulang. Namespace cleanup menghapus workload, Secret, dan PVC, sedangkan penghapusan aset storage mengikuti kebijakan reclaim StorageClass cluster. Jika membuat cluster kind seperti di atas, hapus juga dengan `kind delete cluster --name case02` setelah membersihkan namespace.

Lihat [panduan Compose](build-and-run.md) untuk definisi gate dan interpretasi metrik.
