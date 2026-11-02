# Case 03 — Environment isolation and cleanup evidence

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

## Scope

The Case 03 app image uses Python 3.12.8, and PostgreSQL is 17.2-alpine.

An unrelated PR 42 preview was already running on port 18421 before this test. The test used PR IDs 98001 and 98002 and ports 18501–18503. PR 42 was left intact and checked before and after cleanup.

## Results: target vs actual

| Check | Target | Actual result |
| --- | --- | --- |
| Two previews run concurrently | Separate port, Compose project, network, volume, and database per PR | `pr-98001-g1` on 18501 and `pr-98002-g1` on 18502 were both ready. Networks were `pr-98001-g1_default` and `pr-98002-g1_default`; volumes were `pr-98001-g1_db-data` and `pr-98002-g1_db-data`. |
| Data is isolated | A write in one preview must not appear in another | Changed item 1 in PR 98001 to `isolated-pr-98001`. Its API returned that label; PR 98002 still returned `synthetic-basic`. |
| New generation replaces old safely | New generation reaches readiness first; stale generation cannot replace it | PR 98001 generation 2 became ready on port 18503. The manager then removed generation 1: 0 old containers and 0 old project volumes. Generation 1 provision subsequently exited 2 with `stale generation 1; current generation is 2`; generation 2 stayed current and healthy. PR 98002 stayed ready throughout. |
| TTL sweep is project-scoped | Expired resources are removed; other active previews remain | For the isolated test record only, `expires_at` was set to current time minus one second (the configured one-hour TTL was not allowed to elapse in real time). `sweep` printed `expired pr-98002-g1`; its container and volume counts became 0. PR 98001 generation 2 and existing PR 42 both remained ready. |
| Explicit cleanup is scoped | Cleanup removes the selected PR without touching unrelated previews | `cleanup --pr 98001` removed generation 2; its container and volume counts were 0. PR 42 still returned ready on port 18421, and it was the only tracked state record afterward. |

The TTL result verifies expiration handling after the state record is expired; it is not a measurement of waiting for one hour. The exact test state was created for these checks and removed afterward. The pre-existing PR 42 state and containers were retained.

## Raw output excerpts

```text
{"status": "ready", "synthetic_items": 3, "pr": "98001", "generation": "1"}
{"status": "ready", "synthetic_items": 3, "pr": "98002", "generation": "1"}
```

After mutating only the first database:

```text
{"pr": "98001", "generation": "1", "items": [{"id": 1, "label": "isolated-pr-98001", "amount": 10}, ...]}
{"pr": "98002", "generation": "1", "items": [{"id": 1, "label": "synthetic-basic", "amount": 10}, ...]}
```

Generation and stale-job outcomes:

```text
{"health": {"status": "ready", "synthetic_items": 3, "pr": "98001", "generation": "2"}, "smoke_items": 3}
old-project-containers=0
old-project-volumes=0
environment operation failed: stale generation 1; current generation is 2
stale_exit=2
```

TTL sweep and scoped cleanup:

```text
expired pr-98002-g1
expired_project_containers=0
expired_project_volumes=0
cleaned pr-98001-g2
pr-98001-containers=0
pr-98001-volumes=0
{"status": "ready", "synthetic_items": 3, "pr": "42", "generation": "1"}
```

## Reproduction commands

Run from `case-03-developer-platform`. Use unused PR IDs and ports in another run.

### Create two independent previews and change one database

```sh
python3 envctl.py provision --pr 98001 --generation 1 --port 18501 --ttl-hours 1
python3 envctl.py provision --pr 98002 --generation 1 --port 18502 --ttl-hours 1
curl -fsS http://127.0.0.1:18501/health
curl -fsS http://127.0.0.1:18502/health
docker compose -p pr-98001-g1 exec -T db psql -U preview -d preview \
  -c "UPDATE preview_items SET label='isolated-pr-98001' WHERE item_id=1"
curl -fsS http://127.0.0.1:18501/items
curl -fsS http://127.0.0.1:18502/items
```

### Replace a generation and reject a stale run

```sh
python3 envctl.py provision --pr 98001 --generation 2 --port 18503 --ttl-hours 1
python3 envctl.py status --pr 98001
curl -fsS http://127.0.0.1:18503/health
python3 envctl.py provision --pr 98001 --generation 1 --port 18501 --ttl-hours 1
```

The final command is expected to exit 2 and must leave generation 2 current.

### Expire one test record and sweep

For a quick local verification, expire only the test preview's state record; this simulates an elapsed TTL rather than waiting one hour:

```sh
python3 - <<'PY'
import json, time
from pathlib import Path
p = Path('.lab-state/pr-98002-g1.json')
record = json.loads(p.read_text())
record['expires_at'] = int(time.time()) - 1
p.write_text(json.dumps(record, indent=2) + '\n')
PY
python3 envctl.py sweep
curl -fsS http://127.0.0.1:18503/health
curl -fsS http://127.0.0.1:18421/health
```

### Explicit cleanup

```sh
python3 envctl.py cleanup --pr 98001
curl -fsS http://127.0.0.1:18421/health
python3 envctl.py status
```

The local raw logs and responses are under ignored `artifacts/local/`. The evidence records enough output to compare resource counts and API identity without committing generated database or container data.

<a id="bahasa-indonesia"></a>

## Ruang lingkup

Image app Case 03 menggunakan Python 3.12.8 dan PostgreSQL 17.2-alpine.

Sebelum pengujian, preview PR 42 yang tidak terkait sudah aktif di port 18421. Pengujian memakai ID PR 98001 dan 98002 serta port 18501–18503. PR 42 dibiarkan utuh dan diperiksa sebelum serta setelah cleanup.

## Hasil: target dibanding aktual

| Pemeriksaan | Target | Hasil aktual |
| --- | --- | --- |
| Dua preview aktif bersamaan | Port, Compose project, network, volume, dan database terpisah per PR | `pr-98001-g1` di 18501 dan `pr-98002-g1` di 18502 sama-sama ready. Network bernama `pr-98001-g1_default` dan `pr-98002-g1_default`; volume `pr-98001-g1_db-data` dan `pr-98002-g1_db-data`. |
| Data terisolasi | Perubahan pada satu preview tidak terlihat di preview lain | Item 1 di database PR 98001 diubah menjadi `isolated-pr-98001`. API-nya mengembalikan label tersebut; PR 98002 tetap mengembalikan `synthetic-basic`. |
| Generasi baru menggantikan generasi lama dengan aman | Generasi baru lulus readiness lebih dulu; generasi lama tidak bisa menggantikannya | Generasi 2 PR 98001 ready di port 18503. Manager lalu menghapus generasi 1: 0 container lama dan 0 volume project lama. Provision generation 1 sesudah itu exit 2 dengan `stale generation 1; current generation is 2`; generation 2 tetap current dan sehat. PR 98002 tetap ready. |
| TTL sweep scoped | Resource kedaluwarsa dihapus; preview aktif lain tetap ada | Hanya untuk state test terisolasi, `expires_at` diatur menjadi waktu sekarang dikurangi satu detik (TTL satu jam tidak ditunggu sampai habis). `sweep` mencetak `expired pr-98002-g1`; jumlah container dan volume menjadi 0. PR 98001 generation 2 dan PR 42 yang sudah ada tetap ready. |
| Cleanup eksplisit scoped | Cleanup menghapus PR terpilih tanpa menyentuh preview lain | `cleanup --pr 98001` menghapus generation 2; jumlah container dan volumenya 0. PR 42 masih ready di port 18421 dan menjadi satu-satunya state record setelahnya. |

Hasil TTL menguji mekanisme saat record sudah dinyatakan kedaluwarsa; ini bukan pengukuran menunggu satu jam. State test dibuat khusus lalu dihapus. State dan container PR 42 yang sudah ada tetap dipertahankan.

## Cuplikan output mentah

```text
{"status": "ready", "synthetic_items": 3, "pr": "98001", "generation": "1"}
{"status": "ready", "synthetic_items": 3, "pr": "98002", "generation": "1"}
```

Setelah hanya database pertama yang diubah:

```text
{"pr": "98001", "generation": "1", "items": [{"id": 1, "label": "isolated-pr-98001", "amount": 10}, ...]}
{"pr": "98002", "generation": "1", "items": [{"id": 1, "label": "synthetic-basic", "amount": 10}, ...]}
```

Hasil penggantian generasi dan penolakan job lama:

```text
{"health": {"status": "ready", "synthetic_items": 3, "pr": "98001", "generation": "2"}, "smoke_items": 3}
old-project-containers=0
old-project-volumes=0
environment operation failed: stale generation 1; current generation is 2
stale_exit=2
```

Hasil TTL sweep dan cleanup scoped:

```text
expired pr-98002-g1
expired_project_containers=0
expired_project_volumes=0
cleaned pr-98001-g2
pr-98001-containers=0
pr-98001-volumes=0
{"status": "ready", "synthetic_items": 3, "pr": "42", "generation": "1"}
```

## Perintah reproduksi

Jalankan dari `case-03-developer-platform`. Pakai ID PR dan port yang belum terpakai.

### Buat dua preview terpisah dan ubah satu database

```sh
python3 envctl.py provision --pr 98001 --generation 1 --port 18501 --ttl-hours 1
python3 envctl.py provision --pr 98002 --generation 1 --port 18502 --ttl-hours 1
curl -fsS http://127.0.0.1:18501/health
curl -fsS http://127.0.0.1:18502/health
docker compose -p pr-98001-g1 exec -T db psql -U preview -d preview \
  -c "UPDATE preview_items SET label='isolated-pr-98001' WHERE item_id=1"
curl -fsS http://127.0.0.1:18501/items
curl -fsS http://127.0.0.1:18502/items
```

### Ganti generasi dan tolak job lama

```sh
python3 envctl.py provision --pr 98001 --generation 2 --port 18503 --ttl-hours 1
python3 envctl.py status --pr 98001
curl -fsS http://127.0.0.1:18503/health
python3 envctl.py provision --pr 98001 --generation 1 --port 18501 --ttl-hours 1
```

Perintah terakhir diharapkan exit 2 dan generation 2 harus tetap current.

### Kedaluwarsakan satu record test dan jalankan sweep

Untuk pemeriksaan lokal cepat, kedaluwarsakan hanya state preview test ini; langkah ini menyimulasikan TTL yang lewat dan tidak menunggu satu jam:

```sh
python3 - <<'PY'
import json, time
from pathlib import Path
p = Path('.lab-state/pr-98002-g1.json')
record = json.loads(p.read_text())
record['expires_at'] = int(time.time()) - 1
p.write_text(json.dumps(record, indent=2) + '\n')
PY
python3 envctl.py sweep
curl -fsS http://127.0.0.1:18503/health
curl -fsS http://127.0.0.1:18421/health
```

### Cleanup eksplisit

```sh
python3 envctl.py cleanup --pr 98001
curl -fsS http://127.0.0.1:18421/health
python3 envctl.py status
```

Log dan respons mentah tersimpan lokal di `artifacts/local/` yang diabaikan Git. Dokumen ini menyimpan cuplikan cukup untuk membandingkan jumlah resource dan identitas API tanpa memasukkan data database/container hasil generate ke repo.
