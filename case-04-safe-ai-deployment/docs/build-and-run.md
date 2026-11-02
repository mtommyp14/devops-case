# Case 04 — Build and run

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This is a local policy-gate demonstration. The “agent” copies one deterministic JSON proposal fixture into a shared plan volume; it does not call an AI model. It has no network, secret, Docker socket, or controller access. OPA evaluates the proposal. A separate, restricted controller calls a mock application with a dummy token and appends audit records. No cloud resources or real credentials are used.

From this directory:

```sh
docker compose config
docker compose up -d --build volume-init opa target
```

## Low-risk change

```sh
SCENARIO=safe docker compose run --rm agent
docker compose run --rm controller inspect
docker compose run --rm controller apply
curl -s http://127.0.0.1:18084/state
```

The controller recomputes the canonical plan hash, asks OPA for a decision, applies the allowed change to the local target, and checks health.

## High-risk approval bound to the plan

```sh
SCENARIO=high-risk docker compose run --rm agent
docker compose run --rm controller hash
```

Copy the printed SHA-256 value into the approval command:

```sh
docker compose run --rm controller apply --approval-hash SHA256_VALUE
```

The approval is accepted only when it matches the current plan byte-for-byte after canonical JSON serialization. Re-run the agent with a different proposal and the previous hash no longer authorizes it.

To reproduce a stale-approval rejection, retain the hash from `high-risk`, replace the proposal, then try that old hash:

```sh
SCENARIO=high-risk-revised docker compose run --rm --no-deps agent
docker compose run --rm --no-deps controller hash
docker compose run --rm --no-deps controller apply --approval-hash OLD_SHA256_VALUE
```

The changed proposal remains high-risk and requires its own new hash; the old hash must exit with an error without changing target state.

## Denial and rollback demonstrations

The forbidden fixture attempts privileged mode and must be denied before contacting the target:

```sh
SCENARIO=forbidden docker compose run --rm agent
docker compose run --rm controller inspect
docker compose run --rm controller apply
```

The secret-scope fixture requests a production secret and is denied by policy even though it contains no real credential:

```sh
SCENARIO=secret-scope docker compose run --rm agent
docker compose run --rm controller inspect
```

The health-failure fixture passes policy but asks the mock target to activate `v2-bad`, which is configured to fail health. The controller restores the prior release and exits with a failure status:

```sh
SCENARIO=health-fail docker compose run --rm agent
docker compose run --rm controller apply
curl -s http://127.0.0.1:18084/state
docker compose run --rm controller audit
```

To demonstrate fail-closed behavior when OPA is stopped:

```sh
SCENARIO=safe docker compose run --rm agent
docker compose stop opa
docker compose run --rm --no-deps controller apply
curl -s http://127.0.0.1:18084/state
docker compose up -d --wait opa
```

The policy call must fail closed and leave target state unchanged. See [test evidence](test-evidence.md) for the actual decision, target state comparisons, rollback output, and effective sandbox settings reported by Docker.

The agent container is the network-isolated proposal sandbox. The controller intentionally has network access to OPA and the mock target; inspect both effective configurations in the [test evidence](test-evidence.md).

## Reset and limits

This removes only this Compose project's target, policy service, plan, and audit volumes:

```sh
docker compose down --volumes --remove-orphans
```

Secret values are dummy placeholders. The mock target stores release state in memory and starts at `v1-stable` after restart. OPA policy is a small teaching example. Containers share the host kernel, so this lab is not a production sandbox for arbitrary model output or untrusted code.

<a id="bahasa-indonesia"></a>

## Case 04 — Build dan jalankan

Ini adalah demonstrasi gate policy lokal. “Agent” menyalin satu fixture proposal JSON deterministik ke volume bersama; agent tidak memanggil model AI. Agent tidak memiliki jaringan, secret, Docker socket, atau akses controller. OPA mengevaluasi proposal. Controller terpisah dan dibatasi memanggil aplikasi mock dengan token dummy serta menambahkan catatan audit. Tidak ada resource cloud atau kredensial nyata.

Dari folder ini:

```sh
docker compose config
docker compose up -d --build volume-init opa target
```

## Perubahan berisiko rendah

```sh
SCENARIO=safe docker compose run --rm agent
docker compose run --rm controller inspect
docker compose run --rm controller apply
curl -s http://127.0.0.1:18084/state
```

Controller menghitung ulang hash plan kanonis, meminta keputusan OPA, menerapkan perubahan yang diizinkan ke target lokal, lalu memeriksa health.

## Persetujuan berisiko tinggi yang terikat pada plan

```sh
SCENARIO=high-risk docker compose run --rm agent
docker compose run --rm controller hash
```

Salin nilai SHA-256 yang dicetak ke perintah persetujuan:

```sh
docker compose run --rm controller apply --approval-hash SHA256_VALUE
```

Persetujuan diterima hanya jika hash cocok dengan plan saat ini setelah serialisasi JSON kanonis. Jika agent dijalankan ulang dengan proposal berbeda, hash lama tidak lagi memberi izin.

## Demonstrasi penolakan dan rollback

Fixture forbidden mencoba mengaktifkan privileged mode dan harus ditolak sebelum menghubungi target:

```sh
SCENARIO=forbidden docker compose run --rm agent
docker compose run --rm controller inspect
docker compose run --rm controller apply
```

Fixture secret-scope meminta secret produksi dan ditolak policy meskipun tidak berisi kredensial nyata:

```sh
SCENARIO=secret-scope docker compose run --rm agent
docker compose run --rm controller inspect
```

Fixture health-fail lulus policy, tetapi meminta target mock mengaktifkan `v2-bad` yang health-nya gagal. Controller memulihkan release sebelumnya dan keluar dengan status gagal:

```sh
SCENARIO=health-fail docker compose run --rm agent
docker compose run --rm controller apply
curl -s http://127.0.0.1:18084/state
docker compose run --rm controller audit
```

Untuk menunjukkan perilaku fail-closed saat OPA dihentikan:

```sh
SCENARIO=safe docker compose run --rm agent
docker compose stop opa
docker compose run --rm --no-deps controller apply
curl -s http://127.0.0.1:18084/state
docker compose up -d --wait opa
```

Pemanggilan policy harus fail-closed dan tidak mengubah state target. Lihat [bukti pengujian](test-evidence.md) untuk keputusan aktual, perbandingan state target, output rollback, dan setting sandbox efektif yang dilaporkan Docker.

Container agent adalah sandbox proposal yang tidak memiliki network. Controller sengaja memiliki akses network ke OPA dan target mock; lihat konfigurasi efektif keduanya pada [bukti pengujian](test-evidence.md).

## Reset dan batasan

Perintah ini menghapus target, policy service, plan, dan volume audit milik Compose project ini:

```sh
docker compose down --volumes --remove-orphans
```

Secret yang digunakan adalah placeholder dummy. Target mock menyimpan state release di memori dan kembali ke `v1-stable` setelah restart. Policy OPA adalah contoh untuk pembelajaran. Container berbagi kernel host, sehingga lab ini bukan sandbox produksi untuk output model atau kode tidak tepercaya.
