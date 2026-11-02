# Case 04 — Approval, policy, rollback, and sandbox evidence

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Scope

The OPA service uses image `openpolicyagent/opa:1.0.0`.

Before the run, the local mock target was at release `v2-migration`, the plan volume contained the `demo-secret-scope-denial` fixture, and the audit volume had eight existing records. These values were captured first. At the end, the initial plan and target state were restored; the audit volume was preserved and the new test decisions appended.

## Results: target vs actual

| Check | Target | Actual result |
| --- | --- | --- |
| Old approval after proposal changes | A high-risk plan change invalidates the previous SHA-256 approval; target does not change | Original `demo-migration-change` hash `2cd7a212…cfff223d` deployed `v2-migration`. The revised high-risk plan hash was `5f183007…4440f399`; applying with the old hash exited 2 with `human approval required`. Target remained `v2-migration` with the original artifact hash. |
| OPA stopped | Missing policy decision fails closed; target does not change | With OPA stopped and the safe plan active, controller exited 2 with `policy service unavailable or invalid; deployment stopped`. Target state before and after was identical. Audit recorded `policy_unavailable`. OPA was restarted and healthy afterward. |
| Health check failure | Failed deployment rolls back to the previous release, and restored health is checked | Applying `v2-bad` returned a 503 health result; controller output was `rolled_back`, `restored_release: v2-migration`, `rollback_healthy: true`, then exited 2 to report the deployment failure. Target state afterward was `v2-migration`; `/health` returned 200/`ok`; audit recorded `rolled_back`. |
| Agent sandbox claims | Effective container config matches declared restrictions | Docker inspect confirmed network `none`, read-only root, UID/GID 10001, all capabilities dropped, `no-new-privileges`, 16 MiB `noexec,nosuid` `/tmp`, 128 MiB memory, 0.5 CPU, and 64 PID limit. Its only mounts were the plan volume read/write and fixture directory read-only. The agent had no secret, controller URL, or Docker socket mount. |
| Controller boundary | Controller is separated from the agent and has only the access it needs | Controller runs on the Compose network to reach OPA and target, with read-only root, UID/GID 10001, all capabilities dropped, `no-new-privileges`, 16 MiB `noexec,nosuid` `/tmp`, 160 MiB memory, 0.5 CPU, and 64 PID limit. It mounts plans read-only and audit read/write, and receives only the local dummy deploy token. |

The agent is deterministic fixture code, not an AI model. Container controls are the observed local Docker settings; they share the host kernel and are not a production isolation boundary for arbitrary malicious code.

## Raw output excerpts

### Changed proposal rejects the old approval

```text
{"task_id": "demo-migration-change", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d", "target": "local-demo"}
{"result": "deployed", "release": "v2-migration", "health": {"status": "ok", "release": "v2-migration"}}
{"task_id": "demo-migration-change-revised", "artifact_sha256": "5f1830079af93b68966e8cbc0708d1370c2784ea39af8c5fc1feeb7c4440f399", "target": "local-demo"}
deployment stopped: human approval required; approve this exact artifact hash: 5f1830079af93b68966e8cbc0708d1370c2784ea39af8c5fc1feeb7c4440f399
exit=2
{"release": "v2-migration", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d"}
```

### OPA unavailable fails closed

```text
deployment stopped: policy service unavailable or invalid; deployment stopped
exit=2
before: {"release": "v2-migration", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d"}
after:  {"release": "v2-migration", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d"}
audit decision: policy_unavailable
```

### Health failure rolls back

```text
deployment stopped: deployment health check failed; previous release restored
{"result": "rolled_back", "failed_release": "v2-bad", "restored_release": "v2-migration", "rollback_healthy": true}
exit=2
{"release": "v2-migration", "artifact_sha256": "rollback"}
{"status": "ok", "release": "v2-migration"}
audit decision: rolled_back; rollback_healthy: true
```

### Effective Docker sandbox settings

```text
Agent: NetworkMode=none ReadonlyRootfs=true User=10001:10001
Tmpfs={"/tmp":"rw,noexec,nosuid,size=16m"} CapDrop=["ALL"] SecurityOpt=["no-new-privileges:true"]
Memory=134217728 NanoCpus=500000000 PidsLimit=64
Mounts: /out plan volume (rw); /scenarios (ro bind)
Env: PLAN_FILE=/out/plan.json; SCENARIO=safe; no DUMMY_DEPLOY_TOKEN, OPA_URL, or TARGET_URL

Controller: NetworkMode=case-04-safe-ai-deployment_default ReadonlyRootfs=true User=10001:10001
Tmpfs={"/tmp":"rw,noexec,nosuid,size=16m"} CapDrop=["ALL"] SecurityOpt=["no-new-privileges:true"]
Memory=167772160 NanoCpus=500000000 PidsLimit=64
Mounts: /plans plan volume (ro); /audit volume (rw)
Env: OPA_URL=http://opa:8181; TARGET_URL=http://target:8080; DUMMY_DEPLOY_TOKEN=local-only-demo-token
```

## Reproduction commands

Run from `case-04-safe-ai-deployment`. The old and revised proposals both remain high-risk so OPA requires an exact approval for each one.

### Stale approval

```sh
SCENARIO=high-risk docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller hash
docker compose run --rm --no-deps controller apply --approval-hash OLD_SHA256

SCENARIO=high-risk-revised docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller hash
docker compose run --rm --no-deps controller apply --approval-hash OLD_SHA256
curl -fsS http://127.0.0.1:18084/state
```

The first `apply` succeeds with its matching hash. The last `apply` is expected to exit 2 and leave the target state unchanged.

### OPA stopped

```sh
SCENARIO=safe docker compose run --rm --no-deps agent
curl -fsS http://127.0.0.1:18084/state
docker compose stop opa
docker compose run --rm --no-deps controller apply
curl -fsS http://127.0.0.1:18084/state
docker compose up -d --wait opa
docker compose run --rm --no-deps controller audit
```

The controller command is expected to exit 2; compare the target state before and after.

### Health failure and rollback

```sh
SCENARIO=health-fail docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller apply
curl -fsS http://127.0.0.1:18084/state
curl -fsS http://127.0.0.1:18084/health
docker compose run --rm --no-deps controller audit
```

The controller exits 2 to report the unsuccessful new release after the rollback result has been recorded.

### Inspect the effective agent config

```sh
docker compose create agent
AGENT_CID=$(docker compose ps -q -a agent)
docker inspect "$AGENT_CID" --format '{{.HostConfig.NetworkMode}} {{.HostConfig.ReadonlyRootfs}} {{.Config.User}} {{json .HostConfig.Tmpfs}} {{json .HostConfig.CapDrop}} {{json .HostConfig.SecurityOpt}} {{.HostConfig.Memory}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}} {{json .Mounts}} {{json .Config.Env}}'
docker compose rm -f agent
```

Local logs and inspection output are saved under ignored `artifacts/local/`. The initial plan and target state were restored after this run; the audit history was preserved with the new test records appended.

<a id="bahasa-indonesia"></a>

## Ruang lingkup

Service OPA menggunakan image `openpolicyagent/opa:1.0.0`.

Sebelum run, target mock lokal berada di release `v2-migration`, volume plan berisi fixture `demo-secret-scope-denial`, dan volume audit memiliki delapan record. Nilai ini disimpan terlebih dahulu. Di akhir pengujian, plan dan target dipulihkan; volume audit dipertahankan dan keputusan baru ditambahkan.

## Hasil: target dibanding aktual

| Pemeriksaan | Target | Hasil aktual |
| --- | --- | --- |
| Approval lama setelah proposal berubah | Perubahan plan berisiko tinggi membatalkan approval SHA-256 lama; target tidak berubah | Hash `demo-migration-change` awal `2cd7a212…cfff223d` berhasil deploy `v2-migration`. Hash plan high-risk revisi `5f183007…4440f399`; apply memakai hash lama exit 2 dengan `human approval required`. Target tetap `v2-migration` dengan hash artefak awal. |
| OPA dihentikan | Keputusan policy yang tidak tersedia fail-closed; target tidak berubah | Dengan OPA stop dan plan safe aktif, controller exit 2: `policy service unavailable or invalid; deployment stopped`. State target sebelum/sesudah sama. Audit mencatat `policy_unavailable`. OPA kemudian dinyalakan kembali dan sehat. |
| Health check gagal | Deployment gagal rollback ke release sebelumnya dan health hasil pemulihan diperiksa | Apply `v2-bad` mendapat health 503; output controller `rolled_back`, `restored_release: v2-migration`, `rollback_healthy: true`, lalu exit 2 untuk menandai deployment gagal. State target kembali ke `v2-migration`; `/health` memberi 200/`ok`; audit mencatat `rolled_back`. |
| Klaim sandbox agent | Konfigurasi container efektif cocok dengan deklarasi | Docker inspect mengonfirmasi network `none`, root read-only, UID/GID 10001, semua capability di-drop, `no-new-privileges`, `/tmp` 16 MiB `noexec,nosuid`, memori 128 MiB, CPU 0,5, batas 64 PID. Mount hanya volume plan read/write dan folder fixture read-only. Agent tidak menerima secret, URL controller, atau Docker socket. |
| Batas controller | Controller terpisah dari agent dan hanya punya akses yang diperlukan | Controller berada di network Compose untuk mengakses OPA dan target, dengan root read-only, UID/GID 10001, semua capability di-drop, `no-new-privileges`, `/tmp` 16 MiB `noexec,nosuid`, memori 160 MiB, CPU 0,5, batas 64 PID. Plan di-mount read-only, audit read/write, dan hanya token deploy dummy lokal diberikan. |

Agent adalah fixture deterministik, bukan model AI. Kontrol container di atas adalah setting Docker lokal yang teramati; container tetap berbagi kernel host dan bukan batas isolasi produksi untuk kode berbahaya.

## Cuplikan output mentah

### Proposal berubah menolak approval lama

```text
{"task_id": "demo-migration-change", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d", "target": "local-demo"}
{"result": "deployed", "release": "v2-migration", "health": {"status": "ok", "release": "v2-migration"}}
{"task_id": "demo-migration-change-revised", "artifact_sha256": "5f1830079af93b68966e8cbc0708d1370c2784ea39af8c5fc1feeb7c4440f399", "target": "local-demo"}
deployment stopped: human approval required; approve this exact artifact hash: 5f1830079af93b68966e8cbc0708d1370c2784ea39af8c5fc1feeb7c4440f399
exit=2
{"release": "v2-migration", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d"}
```

### OPA tidak tersedia, deployment fail-closed

```text
deployment stopped: policy service unavailable or invalid; deployment stopped
exit=2
before: {"release": "v2-migration", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d"}
after:  {"release": "v2-migration", "artifact_sha256": "2cd7a212038e5f6f07d98197c23fb407d4560f12db3a2e660a8aa661cfff223d"}
audit decision: policy_unavailable
```

### Health check gagal memicu rollback

```text
deployment stopped: deployment health check failed; previous release restored
{"result": "rolled_back", "failed_release": "v2-bad", "restored_release": "v2-migration", "rollback_healthy": true}
exit=2
{"release": "v2-migration", "artifact_sha256": "rollback"}
{"status": "ok", "release": "v2-migration"}
audit decision: rolled_back; rollback_healthy: true
```

### Setting sandbox efektif dari Docker

```text
Agent: NetworkMode=none ReadonlyRootfs=true User=10001:10001
Tmpfs={"/tmp":"rw,noexec,nosuid,size=16m"} CapDrop=["ALL"] SecurityOpt=["no-new-privileges:true"]
Memory=134217728 NanoCpus=500000000 PidsLimit=64
Mounts: /out plan volume (rw); /scenarios (ro bind)
Env: PLAN_FILE=/out/plan.json; SCENARIO=safe; tanpa DUMMY_DEPLOY_TOKEN, OPA_URL, atau TARGET_URL

Controller: NetworkMode=case-04-safe-ai-deployment_default ReadonlyRootfs=true User=10001:10001
Tmpfs={"/tmp":"rw,noexec,nosuid,size=16m"} CapDrop=["ALL"] SecurityOpt=["no-new-privileges:true"]
Memory=167772160 NanoCpus=500000000 PidsLimit=64
Mounts: /plans plan volume (ro); /audit volume (rw)
Env: OPA_URL=http://opa:8181; TARGET_URL=http://target:8080; DUMMY_DEPLOY_TOKEN=local-only-demo-token
```

## Perintah reproduksi

Jalankan dari `case-04-safe-ai-deployment`. Kedua proposal tetap berisiko tinggi sehingga OPA meminta approval tepat untuk setiap hash.

### Approval lama

```sh
SCENARIO=high-risk docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller hash
docker compose run --rm --no-deps controller apply --approval-hash OLD_SHA256

SCENARIO=high-risk-revised docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller hash
docker compose run --rm --no-deps controller apply --approval-hash OLD_SHA256
curl -fsS http://127.0.0.1:18084/state
```

`apply` pertama sukses dengan hash yang cocok. `apply` terakhir diharapkan exit 2 dan state target harus tetap sama.

### OPA dihentikan

```sh
SCENARIO=safe docker compose run --rm --no-deps agent
curl -fsS http://127.0.0.1:18084/state
docker compose stop opa
docker compose run --rm --no-deps controller apply
curl -fsS http://127.0.0.1:18084/state
docker compose up -d --wait opa
docker compose run --rm --no-deps controller audit
```

Perintah controller diharapkan exit 2; bandingkan state target sebelum dan sesudah.

### Health check gagal dan rollback

```sh
SCENARIO=health-fail docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller apply
curl -fsS http://127.0.0.1:18084/state
curl -fsS http://127.0.0.1:18084/health
docker compose run --rm --no-deps controller audit
```

Controller exit 2 untuk melaporkan release baru yang gagal, setelah hasil rollback dicatat.

### Periksa konfigurasi efektif agent

```sh
docker compose create agent
AGENT_CID=$(docker compose ps -q -a agent)
docker inspect "$AGENT_CID" --format '{{.HostConfig.NetworkMode}} {{.HostConfig.ReadonlyRootfs}} {{.Config.User}} {{json .HostConfig.Tmpfs}} {{json .HostConfig.CapDrop}} {{json .HostConfig.SecurityOpt}} {{.HostConfig.Memory}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}} {{json .Mounts}} {{json .Config.Env}}'
docker compose rm -f agent
```

Log lokal dan output inspect disimpan di `artifacts/local/` yang diabaikan Git. Plan dan target awal dipulihkan setelah run; histori audit dipertahankan dengan record pengujian baru.
