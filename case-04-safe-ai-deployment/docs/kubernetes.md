# Kubernetes deployment path

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This optional path runs the deterministic proposal fixture, OPA, controller, and mock target as Kubernetes resources. It does not call an AI model or deploy a real workload. The agent Job has no network access under the included NetworkPolicy; the controller can reach only OPA, the target, and cluster DNS. NetworkPolicy enforcement requires a CNI plugin that supports it. Check your cluster's CNI before treating these rules as an enforced boundary.

## Prerequisites and local image

Use a local kind/minikube cluster, `kubectl`, and a default StorageClass supporting 1 GiB `ReadWriteOnce` PVCs. Build and load the lab image (kind example):

```sh
docker build -t case-04-app:local case-04-safe-ai-deployment
kind load docker-image case-04-app:local --name devops-labs
```

Create a local cluster once if needed: `kind create cluster --name devops-labs`.

## Prepare and apply

From the repository root, check the current context first. Create the namespace and ConfigMaps from the checked-in policy and fixed scenarios, then apply the base resources:

```sh
kubectl config current-context
kubectl apply -f case-04-safe-ai-deployment/kubernetes/namespace.yaml
kubectl -n case-04 create configmap case-04-policy \
  --from-file=deployment.rego=case-04-safe-ai-deployment/policy/deployment.rego
kubectl -n case-04 create configmap case-04-scenarios \
  --from-file=case-04-safe-ai-deployment/scenarios/
kubectl apply -k case-04-safe-ai-deployment/kubernetes
kubectl -n case-04 rollout status deployment/opa --timeout=120s
kubectl -n case-04 rollout status deployment/target --timeout=120s
```

The example Secret contains only a dummy local token. Keep it for this local lab; do not replace it with a real deployment credential. Kubernetes Secret storage may require separate etcd encryption configuration.

## Run the scenario Jobs

Run the fixture agent, inspect its proposal file, then run the guarded controller:

```sh
kubectl apply -f case-04-safe-ai-deployment/kubernetes/agent-job.yaml
kubectl -n case-04 wait --for=condition=complete job/proposal-agent --timeout=120s
kubectl -n case-04 logs job/proposal-agent
kubectl apply -f case-04-safe-ai-deployment/kubernetes/controller-job.yaml
kubectl -n case-04 wait --for=condition=complete job/deployment-controller --timeout=120s
kubectl -n case-04 logs job/deployment-controller
```

The default `safe` proposal should pass the policy gate and update the mock target. The target endpoint can be inspected locally with `kubectl -n case-04 port-forward service/target 18084:8080`, then `curl http://127.0.0.1:18084/state`.

To try a different checked-in fixture, change `SCENARIO` in `agent-job.yaml`, delete the old `proposal-agent` Job, and apply it again. Before each rerun, delete the completed Job with the same name. High-risk proposals need the exact hash printed by the controller's `hash` command and a human approval. To obtain it, first edit `controller-job.yaml` so its command is `["python", "controller.py", "hash"]`, run that Job, and review its hash. Then delete the Job, change the command to `["python", "controller.py", "apply", "--approval-hash", "<reviewed-hash>"]`, and apply again. If the proposal changes, the previously approved hash must be rejected. The `health-fail` fixture uses release `v2-bad`; its controller Job is expected to fail after printing a rollback result. Check the result with `kubectl -n case-04 logs job/deployment-controller` and verify `/state` reports `v1-stable`. The target readiness probe checks `/state` so a failed release remains reachable for the controller's rollback call. To observe fail-closed behavior, scale OPA to zero before starting a fresh controller Job; the controller must fail without changing the target. Scale OPA back to one afterward.

Audit records and plan files use PVCs during the lab. Delete the namespace to discard both PVCs and all demo state. Job TTL removes completed Job objects after an hour; it does not clean the namespace or PVCs.

## Cleanup and limits

```sh
kubectl delete namespace case-04
```

The Kubernetes restrictions mirror selected Compose controls, but are not a production sandbox. A NetworkPolicy only takes effect with a supporting CNI; Kubernetes Secret encryption, RBAC, image provenance, persistent volume permissions, and node isolation depend on cluster configuration. Review these separately before adapting the pattern to a real deployment.

<a id="bahasa-indonesia"></a>

## Jalur deployment Kubernetes

Jalur opsional ini menjalankan fixture proposal deterministik, OPA, controller, dan target mock sebagai resource Kubernetes. Lab ini tidak memanggil model AI atau mendeploy workload sungguhan. Agent Job tidak memiliki akses jaringan menurut NetworkPolicy yang disertakan; controller hanya dapat mengakses OPA, target, dan DNS cluster. Enforcement NetworkPolicy memerlukan plugin CNI yang mendukungnya. Periksa CNI cluster sebelum menganggap aturan ini sebagai batas keamanan yang diterapkan.

## Prasyarat dan image lokal

Gunakan cluster kind/minikube lokal, `kubectl`, dan StorageClass default yang mendukung PVC 1 GiB `ReadWriteOnce`. Build dan muat image lab (contoh kind):

```sh
docker build -t case-04-app:local case-04-safe-ai-deployment
kind load docker-image case-04-app:local --name devops-labs
```

Jika belum memiliki cluster, buat sekali dengan `kind create cluster --name devops-labs`.

## Siapkan dan terapkan

Dari root repo, periksa context aktif terlebih dahulu. Buat namespace dan ConfigMap dari policy serta skenario tetap yang ada di repo, lalu terapkan resource dasar:

```sh
kubectl config current-context
kubectl apply -f case-04-safe-ai-deployment/kubernetes/namespace.yaml
kubectl -n case-04 create configmap case-04-policy \
  --from-file=deployment.rego=case-04-safe-ai-deployment/policy/deployment.rego
kubectl -n case-04 create configmap case-04-scenarios \
  --from-file=case-04-safe-ai-deployment/scenarios/
kubectl apply -k case-04-safe-ai-deployment/kubernetes
kubectl -n case-04 rollout status deployment/opa --timeout=120s
kubectl -n case-04 rollout status deployment/target --timeout=120s
```

Secret contoh hanya berisi token dummy lokal. Gunakan hanya untuk lab; jangan menggantinya dengan kredensial deployment sungguhan. Penyimpanan Secret Kubernetes mungkin memerlukan konfigurasi enkripsi etcd tersendiri.

## Jalankan Job skenario

Jalankan agent fixture, lihat file proposal, lalu jalankan controller dengan guardrail:

```sh
kubectl apply -f case-04-safe-ai-deployment/kubernetes/agent-job.yaml
kubectl -n case-04 wait --for=condition=complete job/proposal-agent --timeout=120s
kubectl -n case-04 logs job/proposal-agent
kubectl apply -f case-04-safe-ai-deployment/kubernetes/controller-job.yaml
kubectl -n case-04 wait --for=condition=complete job/deployment-controller --timeout=120s
kubectl -n case-04 logs job/deployment-controller
```

Proposal `safe` bawaan seharusnya lolos policy gate dan memperbarui target mock. Periksa endpoint target dengan `kubectl -n case-04 port-forward service/target 18084:8080`, lalu `curl http://127.0.0.1:18084/state`.

Untuk mencoba fixture lain yang tersedia, ubah `SCENARIO` di `agent-job.yaml`, hapus Job `proposal-agent` lama, lalu terapkan ulang. Hapus Job selesai dengan nama yang sama sebelum menjalankan ulang. Proposal berisiko tinggi memerlukan hash persis dari perintah `hash` controller dan persetujuan manusia. Untuk mendapatkan hash, ubah command di `controller-job.yaml` menjadi `["python", "controller.py", "hash"]`, jalankan Job, lalu review hash. Hapus Job tersebut, ubah command menjadi `["python", "controller.py", "apply", "--approval-hash", "<hash-yang-sudah-direview>"]`, lalu terapkan kembali. Jika proposal berubah, hash lama yang disetujui harus ditolak. Fixture `health-fail` memakai release `v2-bad`; Job controller memang diharapkan gagal setelah mencetak hasil rollback. Periksa dengan `kubectl -n case-04 logs job/deployment-controller` dan pastikan `/state` menampilkan `v1-stable`. Probe readiness target memeriksa `/state` agar target dengan release gagal tetap dapat diakses saat controller melakukan rollback. Untuk melihat perilaku fail-closed, scale OPA menjadi nol sebelum menjalankan Job controller baru; controller harus gagal tanpa mengubah target. Setelahnya kembalikan OPA ke satu replica.

Record audit dan file rencana menggunakan PVC selama lab berjalan. Hapus namespace untuk membuang kedua PVC dan seluruh state demo. TTL Job menghapus object Job yang selesai setelah satu jam; TTL ini tidak membersihkan namespace atau PVC.

## Cleanup dan batasan

```sh
kubectl delete namespace case-04
```

Pembatasan Kubernetes meniru sebagian kontrol Compose, tetapi tidak menjadi sandbox produksi. NetworkPolicy hanya berlaku dengan CNI pendukung; enkripsi Secret Kubernetes, RBAC, asal image, izin persistent volume, dan isolasi node bergantung pada konfigurasi cluster. Tinjau kontrol tersebut secara terpisah sebelum memakai pola ini untuk deployment nyata.
