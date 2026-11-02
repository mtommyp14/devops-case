# Case 03 — Build and run

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

This local template provisions one app + PostgreSQL Compose project per PR generation, loads three deterministic synthetic rows, checks `/health` and `/items`, and binds the preview port only to `127.0.0.1`. The manager keeps exact project metadata and removes only the project it created.

Requirements: Docker Desktop with Compose and Python 3.9+ for the host-side manager. From this directory:

```sh
docker compose config
python3 envctl.py provision --pr 42 --generation 1 --port 18421
python3 envctl.py status
```

The provisioning command builds the image, starts the database, seeds synthetic data, starts the app, and waits for readiness plus a three-row API smoke check. Open `http://127.0.0.1:18421` or inspect the rows at `http://127.0.0.1:18421/items`.

Create an independent environment with another PR number and unused local port:

```sh
python3 envctl.py provision --pr 43 --generation 1 --port 18431
```

An updated commit for the same PR uses a higher integer generation and another unused port. The manager holds a per-PR lock, refuses stale generations, waits for the new environment to pass readiness and smoke checks, then switches its recorded current generation and removes the previous exact Compose project. If provisioning fails, it cleans the attempted project and retains the prior current record.

## Cleanup and TTL

```sh
python3 envctl.py cleanup --pr 42
python3 envctl.py sweep
```

Default TTL is 24 hours. Use `--ttl-hours` to change it for a demo. `sweep` checks recorded project state and removes expired projects only. A provisioning record expires after 15 minutes if the command is interrupted. Cleanup uses an exact validated project name and scoped `docker compose down --volumes`; it does not run Docker prune commands.

All database values are synthetic, the password is a local placeholder, and the preview isn't exposed to the network. The host-side manager has Docker control to provision containers; the app container itself has no Docker socket. Do not run untrusted fork code through this local host manager. A production CI implementation needs a disposable isolated runner, authenticated preview, egress controls, and TLS.

Compose creates a separate default network for each project, but this local template does not block outbound egress. It runs only the fixed sample app in this repository; it does not execute pull request code.

See [test evidence](test-evidence.md) for a measured two-environment isolation check, generation replacement, stale-generation rejection, TTL sweep, and cleanup that preserves an unrelated active PR.

<a id="bahasa-indonesia"></a>

## Case 03 — Build dan jalankan

Template lokal ini menyediakan satu project Compose berisi aplikasi dan PostgreSQL untuk setiap generasi PR. Lab mengisi tiga record sintetis, memeriksa `/health` serta `/items`, dan hanya mengikat port preview ke `127.0.0.1`. Manager menyimpan metadata project yang tepat dan menghapus hanya project yang dibuatnya.

Prasyarat: Docker Desktop dengan Compose serta Python 3.9+ untuk manager di host. Dari folder ini:

```sh
docker compose config
python3 envctl.py provision --pr 42 --generation 1 --port 18421
python3 envctl.py status
```

Perintah provisioning membangun image, menjalankan database, mengisi data sintetis, menyalakan aplikasi, lalu menunggu readiness dan smoke check API dengan tiga baris. Buka `http://127.0.0.1:18421` atau periksa data di `http://127.0.0.1:18421/items`.

Buat environment terpisah dengan nomor PR dan port lokal yang belum digunakan:

```sh
python3 envctl.py provision --pr 43 --generation 1 --port 18431
```

Commit baru untuk PR yang sama harus memakai nomor generasi integer lebih tinggi dan port lain. Manager menggunakan lock per PR, menolak generasi lama, menunggu environment baru lulus readiness dan smoke check, kemudian mengganti generasi aktif dan menghapus project Compose sebelumnya yang tepat. Jika provisioning gagal, project yang dicoba dibersihkan dan catatan aktif sebelumnya dipertahankan.

## Cleanup dan TTL

```sh
python3 envctl.py cleanup --pr 42
python3 envctl.py sweep
```

TTL default adalah 24 jam. Gunakan `--ttl-hours` untuk mengubahnya saat demo. `sweep` memeriksa state project tercatat dan hanya menghapus project yang sudah kedaluwarsa. Catatan provisioning kedaluwarsa setelah 15 menit jika perintah terhenti. Cleanup memvalidasi nama project secara persis lalu menjalankan `docker compose down --volumes`; perintah Docker prune tidak digunakan.

Seluruh nilai database sintetis, password adalah placeholder lokal, dan preview tidak terbuka ke jaringan. Manager host memiliki kendali Docker untuk membuat container; container aplikasi sendiri tidak memiliki Docker socket. Jangan jalankan kode dari fork yang tidak tepercaya melalui manager host lokal ini. CI produksi memerlukan runner sementara terisolasi, preview terautentikasi, kontrol egress, dan TLS.

Compose membuat network default terpisah untuk setiap project, tetapi template lokal ini tidak memblokir egress keluar. Template hanya menjalankan aplikasi contoh tetap di repo; ia tidak menjalankan kode pull request.

Lihat [bukti pengujian](test-evidence.md) untuk pemeriksaan isolasi dua environment, penggantian generasi, penolakan generasi lama, TTL sweep, dan cleanup yang mempertahankan PR aktif lain.
