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

## Yama akışı (User-Agent'ın gerçek yolunu izler)
SubscriptionItem.hwid → AngConfigManager → UrlContentRequest.hwid → HttpUtil (OkHttp başlıkları)

- Paket adı `com.v2ray.ang.hwid`, uygulama adı "v2rayNG HWID": orijinal v2rayNG ile yan yana kurulur.
- `patch/patch.py` her adımda hedefini bulamazsa açık hata ile durur.
