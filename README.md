# v2rayNG — Elle HWID / Başlık Yaması

Saf v2rayNG'ye tek özellik ekler: abonelik ekleme/düzenleme ekranında **HWID ya da başlıklar** alanı.

- **Boş:** hiçbir başlık eklenmez (normal v2rayNG).
- **Tek değer** (`8697b9cde384fe92`): Happ ile aynı set: `X-Hwid`, `X-Device-Os`, `X-Ver-Os`, `X-Device-Model`.
- **`Ad: değer` satırları:** yazılan başlıklar aynen gönderilir (User-Agent dahil).

User-Agent alanı v2rayNG'nin kendi alanıdır; boşsa `v2rayNG/<sürüm>` kullanılır.

## Akış (User-Agent'ın gerçek yolu)
SubscriptionItem.hwid → AngConfigManager → UrlContentRequest.hwid → HttpUtil.getUrlContentWithUserAgent (OkHttp)

Paket `com.v2ray.ang.hwid`, ad "v2rayNG HWID": orijinal v2rayNG ile yan yana kurulur.
`patch/patch.py` hedefini bulamazsa açık hata (✗) ile durur; iş akışı ayrıca başlık satırının doğru fonksiyonda olduğunu doğrular.
