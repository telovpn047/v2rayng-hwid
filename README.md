# v2rayNG — Elle HWID Yaması

Saf v2rayNG'ye tek özellik ekler: her abonelik için **elle HWID** ve (v2rayNG'de zaten olan)
**User-Agent** girilebilir. Boş bırakılırsa v2rayNG'nin varsayılan davranışı kullanılır
(HWID başlığı hiç gönderilmez, User-Agent v2rayNG'nin kendi değeri olur).

Markalama, reklam, izleme yok. Sadece abonelik çekerken şu başlıklar eklenir (HWID doluysa):
`x-hwid`, `x-device-os`, `x-ver-os`, `x-device-model`.

## Kullanım
Abonelik ekle/düzenle ekranında **HWID** alanına değeri yaz (ya da `x-hwid: değer` satırı).
Boş = otomatik/varsayılan. Abonelik güncellendiğinde bu başlıklarla çekilir.

## Derleme
`main` dalına push → GitHub Actions v2rayNG kaynağını çeker, yamayı uygular, `v2rayNG-hwid.apk` üretir.

## Yama dosyaları
- `patch/SubHeaders.kt` — HWID başlık mantığı (boşsa başlık yok)
- `patch/patch.py` — SubscriptionItem'a `customHwid` alanı, abonelik çekme kodu ve düzenleme ekranı yaması
