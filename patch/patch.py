#!/usr/bin/env python3
"""v2rayNG'ye abonelik başına elle HWID ekler. Akış, User-Agent'ın gerçek yolunu birebir izler:
SubscriptionItem.hwid -> AngConfigManager -> UrlContentRequest.hwid -> HttpUtil (OkHttp başlıkları).
Her adım hedefini bulamazsa açık hata ile durur."""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(sys.argv[1])
app = os.path.join(root, "V2rayNG", "app")
main = os.path.join(app, "src", "main")
SRC = os.path.join(main, "java")
if not os.path.isdir(SRC):
    SRC = os.path.join(main, "kotlin")
assert os.path.isdir(SRC), f"kaynak yok: {SRC}"

def read(p): return open(p, encoding="utf-8").read()
def write(p, s): open(p, "w", encoding="utf-8").write(s)
def find_file(name):
    for dp, _, fs in os.walk(SRC):
        if name in fs: return os.path.join(dp, name)
    sys.exit(f"✗ {name} bulunamadı")
def find_containing(text):
    for dp, _, fs in os.walk(SRC):
        for fn in fs:
            if fn.endswith(".kt"):
                p = os.path.join(dp, fn)
                if text in read(p): return p
    sys.exit(f"✗ '{text}' içeren dosya yok")
def must(k, msg):
    if not k: sys.exit("✗ " + msg)

# 0) Yardımcı sınıf
dst = os.path.join(SRC, "com", "v2ray", "ang", "patch")
os.makedirs(dst, exist_ok=True)
write(os.path.join(dst, "SubHeaders.kt"), read(os.path.join(HERE, "SubHeaders.kt")))
print("[0] SubHeaders.kt eklendi")

# 1) Model: SubscriptionItem.hwid
f = find_file("SubscriptionItem.kt"); s = read(f)
s, k = re.subn(r'(var\s+userAgent\s*:\s*String\?\s*=\s*null)(\s*,)?', r'\1,\n    var hwid: String? = null,', s, count=1)
must(k, "SubscriptionItem.userAgent bulunamadı")
s = s.replace(",,", ",")
write(f, s); print("[1] SubscriptionItem.hwid eklendi")

# 2) İstek modeli: UrlContentRequest.hwid
f = find_containing("class UrlContentRequest"); s = read(f)
s, k = re.subn(r'(val\s+userAgent\s*:\s*String\?\s*(?:=\s*null)?)(\s*,)?', r'\1,\n    val hwid: String? = null,', s, count=1)
must(k, "UrlContentRequest.userAgent bulunamadı")
s = s.replace(",,", ",")
write(f, s); print(f"[2] UrlContentRequest.hwid eklendi ({os.path.basename(f)})")

# 3) AngConfigManager: her UrlContentRequest(userAgent = userAgent, ...) çağrısına hwid
f = find_file("AngConfigManager.kt"); s = read(f)
s, k = re.subn(r'(userAgent\s*=\s*userAgent\s*,)', r'\1\n                        hwid = it.subscription.hwid,', s)
must(k, "AngConfigManager'da 'userAgent = userAgent,' bulunamadı")
write(f, s); print(f"[3] AngConfigManager: {k} çağrıya hwid eklendi")

# 4) HttpUtil: getUrlContentWithUserAgent içinde OkHttp başlıkları
f = find_file("HttpUtil.kt"); s = read(f)
anchor = "applyEmbeddedBasicAuthHeader(currentUrl, requestBuilder)"
must(anchor in s, "HttpUtil'de abonelik isteği kurulumu bulunamadı")
s = s.replace(anchor, anchor + "\n            com.v2ray.ang.patch.SubHeaders.apply(requestBuilder, request.hwid)", 1)
write(f, s); print("[4] HttpUtil: HWID başlıkları eklendi")

# 5) Arayüz: layout'a et_hwid (et_user_agent bloğunun kopyası)
lay = os.path.join(main, "res", "layout", "activity_sub_edit.xml"); s = read(lay)
m = re.search(r'<LinearLayout\b(?:(?!</LinearLayout>).)*?@\+id/et_user_agent(?:(?!</LinearLayout>).)*?</LinearLayout>', s, re.S)
must(m, "layout'ta et_user_agent bloğu bulunamadı")
block = m.group(0)
nb = block.replace("@+id/et_user_agent", "@+id/et_hwid").replace("@string/sub_setting_user_agent", "@string/sub_setting_hwid")
s = s.replace(block, block + "\n\n            " + nb, 1)
write(lay, s); print("[5] layout: HWID alanı eklendi")

# 5b) Etiket metni
n = 0
for strf in glob.glob(os.path.join(main, "res", "values*", "strings.xml")):
    t = read(strf)
    if "sub_setting_user_agent" in t and "sub_setting_hwid" not in t:
        t = re.sub(r'(<string name="sub_setting_user_agent">.*?</string>)',
                   lambda mm: mm.group(1) + '\n    <string name="sub_setting_hwid">HWID (boş = gönderilmez)</string>', t, count=1, flags=re.S)
        write(strf, t); n += 1
must(n, "strings.xml'de sub_setting_user_agent bulunamadı")
print(f"[5b] HWID etiketi {n} dil dosyasına eklendi")

# 6) SubEditActivity: oku / yaz
f = find_file("SubEditActivity.kt"); s = read(f)
r_old = "binding.etUserAgent.text = Utils.getEditable(subItem.userAgent)"
w_old = "subItem.userAgent = binding.etUserAgent.text.toString()"
must(r_old in s, "Activity okuma satırı bulunamadı")
must(w_old in s, "Activity yazma satırı bulunamadı")
s = s.replace(r_old, r_old + "\n        binding.etHwid.text = Utils.getEditable(subItem.hwid)", 1)
s = s.replace(w_old, w_old + "\n        subItem.hwid = binding.etHwid.text.toString()", 1)
write(f, s); print("[6] SubEditActivity: HWID oku/yaz eklendi")

# 7) Ayrı paket adı + ad: orijinal v2rayNG ile yan yana kurulabilsin
gp = os.path.join(app, "build.gradle.kts"); s = read(gp)
s, k = re.subn(r'(applicationId\s*=\s*)"com\.v2ray\.ang"', r'\1"com.v2ray.ang.hwid"', s, count=1)
must(k, "applicationId bulunamadı")
write(gp, s)
for strf in glob.glob(os.path.join(main, "res", "values*", "strings.xml")):
    t = read(strf)
    t2 = re.sub(r'(<string name="app_name"[^>]*>)[^<]*(</string>)', r'\1v2rayNG HWID\2', t)
    if t2 != t: write(strf, t2)
print("[7] paket: com.v2ray.ang.hwid · ad: v2rayNG HWID")

print("✓ YAMA TAMAM")
