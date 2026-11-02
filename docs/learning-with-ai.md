# Learning with AI

[English](#english) | [Bahasa Indonesia](#bahasa-indonesia)

<a id="english"></a>

AI is optional. These labs do not include an AI assistant, and Case 04 uses fixed proposal fixtures rather than calling an AI model. You can use your preferred AI tool as a study helper, while keeping command execution and change approval under your control.

## Good ways to use an AI helper

- Ask it to explain one Compose service, Kubernetes resource, command, metric, or error at a time.
- Share the case name, operating system, the exact command, what you expected, and a short sanitized error excerpt.
- Ask for a read-only diagnostic step first, and ask it to explain what each command does before you run it.
- Compare suggestions with the case guide and official tool documentation. Check file paths, namespaces, context, ports, image names, and cleanup scope.
- Ask the assistant to identify assumptions and uncertainty instead of inventing a successful result.

## Keep private information out of prompts

Do not paste access tokens, passwords, `.env` files, kubeconfig contents, private keys, customer data, or unredacted logs. Replace sensitive values with placeholders such as `<REDACTED_TOKEN>` and use only the synthetic data in these labs. Review the privacy and data-retention settings of whichever AI service you use.

Treat commands that change or delete resources as proposals. Read them first, verify the active Docker context or Kubernetes context, namespace, and target, then decide whether to run them. In particular, inspect commands containing `kubectl apply/delete`, `docker compose down --volumes`, `kind delete cluster`, or database reset operations. Do not let an AI assistant apply changes or clean up resources without your review.

## Copyable prompt

```text
I am learning the [case name] lab in this repository.
Environment: [OS, Docker/Compose or Kubernetes, versions if known]
What I ran: [exact command]
Expected result: [what I expected]
Observed result: [sanitized output; secrets and personal data removed]

Please explain the likely cause in beginner-friendly steps. Start with a read-only
diagnostic command. Explain what it checks and what output to expect. If a change
is needed, show the smallest proposed diff and wait for my review before suggesting
any command that changes or deletes resources. Do not assume the lab succeeded;
help me verify the result from actual output.
```

## Verify before trusting an answer

1. Check whether the suggested command is read-only, mutating, or destructive.
2. Verify it targets the local lab rather than another Docker/Kubernetes context.
3. Check generated YAML with `docker compose config` or `kubectl kustomize` before applying it.
4. Confirm the result from real command output, logs, metrics, and the case's documented evidence. An AI explanation is not a test result.

<a id="bahasa-indonesia"></a>

## Belajar dengan AI

AI bersifat opsional. Lab ini tidak menyertakan asisten AI, dan Case 04 menggunakan fixture proposal tetap, bukan memanggil model AI. Kamu dapat memakai AI pilihanmu sebagai teman belajar, sambil tetap mengendalikan eksekusi perintah dan persetujuan perubahan.

## Cara memakai AI sebagai pendamping belajar

- Minta penjelasan satu service Compose, resource Kubernetes, perintah, metrik, atau error dalam satu waktu.
- Sertakan nama case, sistem operasi, perintah persis yang dijalankan, hasil yang diharapkan, dan cuplikan error yang sudah disamarkan.
- Minta langkah diagnosis read-only lebih dulu. Minta AI menjelaskan fungsi perintah sebelum kamu menjalankannya.
- Bandingkan saran dengan panduan case dan dokumentasi resmi. Periksa path file, namespace, context, port, nama image, dan cakupan cleanup.
- Minta AI menyebutkan asumsi dan hal yang belum pasti, bukan mengarang seolah-olah pengujian berhasil.

## Jangan kirim informasi privat

Jangan tempel access token, password, file `.env`, isi kubeconfig, private key, data pengguna, atau log yang belum disamarkan. Ganti nilai sensitif dengan placeholder seperti `<TOKEN_DISAMARKAN>` dan gunakan data sintetis lab saja. Periksa pengaturan privasi dan retensi data dari layanan AI yang kamu pakai.

Anggap perintah yang mengubah atau menghapus resource sebagai usulan. Baca perintahnya, pastikan Docker context atau Kubernetes context, namespace, dan targetnya benar, lalu putuskan sendiri apakah akan dijalankan. Periksa khusus perintah yang berisi `kubectl apply/delete`, `docker compose down --volumes`, `kind delete cluster`, atau reset database. Jangan biarkan asisten AI menerapkan perubahan atau cleanup tanpa pemeriksaanmu.

## Prompt yang bisa disalin

```text
Saya sedang belajar lab [nama case] di repo ini.
Environment: [OS, Docker/Compose atau Kubernetes, versi jika tahu]
Perintah yang dijalankan: [perintah persis]
Hasil yang diharapkan: [yang saya harapkan]
Hasil aktual: [output yang sudah disamarkan; hapus secret dan data pribadi]

Jelaskan kemungkinan penyebabnya dengan langkah sederhana. Mulai dengan satu
perintah diagnosis read-only. Jelaskan apa yang diperiksa dan output yang mungkin
muncul. Jika perlu perubahan, tunjukkan diff terkecil dan tunggu pemeriksaan saya
sebelum memberi perintah yang mengubah atau menghapus resource. Jangan menganggap
lab berhasil; bantu saya memverifikasinya dari output aktual.
```

## Verifikasi sebelum mempercayai jawaban

1. Periksa apakah perintah hanya membaca, mengubah, atau menghapus resource.
2. Pastikan targetnya lab lokal, bukan Docker/Kubernetes context lain.
3. Validasi YAML usulan dengan `docker compose config` atau `kubectl kustomize` sebelum menerapkannya.
4. Cocokkan hasil dengan output perintah, log, metrik, dan bukti yang didokumentasikan. Penjelasan AI bukan hasil pengujian.
