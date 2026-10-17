#!/usr/bin/env python3
"""v2rayNG'ye abonelik başına elle HWID / başlık ekler. Akış, User-Agent'ın gerçek yolunu birebir izler:
SubscriptionItem.hwid -> AngConfigManager -> UrlContentRequest.hwid -> HttpUtil (abonelik isteği, OkHttp).
Her adım hedefini bulamazsa açık hata ile durur.  Kullanım: python3 patch/patch.py <v2rayNG-kökü>"""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(sys.argv[1])
app = os.path.join(root, "V2rayNG", "app")
main = os.path.join(app, "src", "main")
SRC = os.path.join(main, "java")
if not os.path.isdir(SRC):
    SRC = os.path.join(main, "kotlin")
if not os.path.isdir(SRC):
    sys.exit(f"✗ kaynak klasörü yok: {SRC}")

def read(p): return open(p, encoding="utf-8").read()
def write(p, s): open(p, "w", encoding="utf-8").write(s)
def must(ok, msg):
    if not ok: sys.exit("✗ " + msg)
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

def append_ctor_param(src, class_name, decl):
    """`class <ad>(...)` kurucusunun SONUNA parametre ekler (konumsal çağrılar bozulmaz)."""
    m = re.search(r'class\s+' + class_name + r'\s*\(', src)
    if not m: return src, 0
    i = m.end(); depth = 1
    while i < len(src) and depth:
        c = src[i]
        if c == '(': depth += 1
        elif c == ')': depth -= 1
        i += 1
    close = i - 1
    body = src[m.end():close].rstrip()
    sep = "" if body.endswith(",") else ","
    return src[:m.end()] + body + sep + "\n    " + decl + ",\n" + src[close:], 1

# 0) Yardımcı sınıf
dst = os.path.join(SRC, "com", "v2ray", "ang", "patch")
os.makedirs(dst, exist_ok=True)
write(os.path.join(dst, "SubHeaders.kt"), read(os.path.join(HERE, "SubHeaders.kt")))
print("[0] SubHeaders.kt eklendi")

# 1) Model: SubscriptionItem.hwid (sona)
f = find_file("SubscriptionItem.kt"); s = read(f)
if "hwid" not in s:
    s, k = append_ctor_param(s, "SubscriptionItem", "var hwid: String? = null")
    must(k, "SubscriptionItem sınıfı bulunamadı")
    write(f, s)
print("[1] SubscriptionItem.hwid eklendi")

# 2) İstek modeli: UrlContentRequest.hwid (sona)
f = find_containing("class UrlContentRequest"); s = read(f)
if "val hwid" not in s:
    s, k = append_ctor_param(s, "UrlContentRequest", "val hwid: String? = null")
    must(k, "UrlContentRequest sınıfı bulunamadı")
    write(f, s)
print(f"[2] UrlContentRequest.hwid eklendi ({os.path.basename(f)})")

# 3) AngConfigManager: yalnız abonelik güncelleme bölümünde
f = find_file("AngConfigManager.kt"); s = read(f)
anchor = "val userAgent = it.subscription.userAgent"
must(anchor in s, "AngConfigManager'da 'val userAgent = it.subscription.userAgent' yok")
a = s.index(anchor)
s = s[:a] + anchor + "\n            val hwid = it.subscription.hwid" + s[a + len(anchor):]
a = s.index(anchor)
lines_after = s[a:].split("\n")
region = "\n".join(lines_after[:80]); rest = "\n".join(lines_after[80:])
region, k = re.subn(r'(userAgent\s*=\s*userAgent\s*,)', r'\1\n                        hwid = hwid,', region)
must(k, "abonelik isteğinde 'userAgent = userAgent,' yok")
s = s[:a] + region + ("\n" + rest if rest else "")
write(f, s); print(f"[3] AngConfigManager: {k} abonelik isteğine hwid eklendi")

# 4) HttpUtil: başlıklar YALNIZ abonelik indiren fonksiyona ('val finalUserAgent' olan fonksiyon).
#    'applyEmbeddedBasicAuthHeader(...)' dosyada birden çok fonksiyonda geçer; doğru olan
#    'val finalUserAgent' tanımından SONRA, bir sonraki 'fun' tanımından ÖNCE gelen çağrıdır.
f = find_file("HttpUtil.kt"); s = read(f)
fu = s.find("val finalUserAgent")
must(fu >= 0, "HttpUtil'de 'val finalUserAgent' (abonelik isteği) bulunamadı")
call = s.find("applyEmbeddedBasicAuthHeader(", fu)
must(call >= 0, "abonelik isteğinde applyEmbeddedBasicAuthHeader çağrısı bulunamadı")
nxt = re.search(r"\n\s*(?:private\s+|internal\s+|public\s+)?fun\s", s[fu:])
must(nxt is None or call < fu + nxt.start(), "applyEmbeddedBasicAuthHeader abonelik fonksiyonunun dışında kaldı")
eol = s.index("\n", call)
line_start = s.rfind("\n", 0, call) + 1
indent = re.match(r"[ \t]*", s[line_start:]).group(0)
s = s[:eol] + "\n" + indent + "com.v2ray.ang.patch.SubHeaders.apply(requestBuilder, request.hwid)" + s[eol:]
must(s.count("SubHeaders.apply(") == 1, "SubHeaders.apply birden fazla yere eklendi")
write(f, s); print("[4] HttpUtil: başlıklar abonelik isteğine (finalUserAgent fonksiyonu) eklendi")

# 5) Arayüz: et_user_agent bloğunun kopyası -> et_hwid (çok satırlı)
lay = os.path.join(main, "res", "layout", "activity_sub_edit.xml"); s = read(lay)
if "et_hwid" not in s:
    m = re.search(r'<LinearLayout\b(?:(?!</LinearLayout>).)*?@\+id/et_user_agent(?:(?!</LinearLayout>).)*?</LinearLayout>', s, re.S)
    must(m, "layout'ta et_user_agent bloğu bulunamadı")
    block = m.group(0)
    nb = block.replace("@+id/et_user_agent", "@+id/et_hwid").replace("@string/sub_setting_user_agent", "@string/sub_setting_hwid")
    nb = re.sub(r'android:inputType="[^"]*"', 'android:inputType="textMultiLine"', nb)
    if 'android:inputType' not in nb:
        nb = nb.replace('android:id="@+id/et_hwid"', 'android:id="@+id/et_hwid"\n                    android:inputType="textMultiLine"')
    nb = nb.replace('android:id="@+id/et_hwid"', 'android:id="@+id/et_hwid"\n                    android:minLines="1"\n                    android:maxLines="8"', 1)
    s = s.replace(block, block + "\n\n            " + nb, 1)
    write(lay, s)
must(s.count('@+id/et_hwid"') == 1, "layout'ta et_hwid sayısı 1 değil")
print("[5] layout: HWID alanı eklendi")

# 5b) Etiket (tüm dil dosyaları)
n = 0
for strf in glob.glob(os.path.join(main, "res", "values*", "*.xml")):
    t = read(strf)
    if '<string name="sub_setting_user_agent"' in t and "sub_setting_hwid" not in t:
        t = re.sub(r'(<string name="sub_setting_user_agent"[^>]*>.*?</string>)',
                   lambda mm: mm.group(1) + '\n    <string name="sub_setting_hwid">HWID ya da başlıklar (Ad: değer, satır satır · boş = gönderilmez)</string>',
                   t, count=1, flags=re.S)
        write(strf, t); n += 1
must(n, "values*/*.xml içinde sub_setting_user_agent bulunamadı")
print(f"[5b] HWID etiketi {n} dil dosyasına eklendi")

# 6) SubEditActivity: oku / yaz
f = find_file("SubEditActivity.kt"); s = read(f)
r_old = "binding.etUserAgent.text = Utils.getEditable(subItem.userAgent)"
w_old = "subItem.userAgent = binding.etUserAgent.text.toString()"
must(r_old in s, "Activity okuma satırı bulunamadı")
must(w_old in s, "Activity yazma satırı bulunamadı")
if "etHwid" not in s:
    s = s.replace(r_old, r_old + "\n        binding.etHwid.text = Utils.getEditable(subItem.hwid)", 1)
    s = s.replace(w_old, w_old + "\n        subItem.hwid = binding.etHwid.text.toString()", 1)
    write(f, s)
print("[6] SubEditActivity: HWID oku/yaz eklendi")

# 7) Ayrı paket adı + uygulama adı
gp = os.path.join(app, "build.gradle.kts"); s = read(gp)
s, k = re.subn(r'(applicationId\s*=\s*)"com\.v2ray\.ang"', r'\1"com.v2ray.ang.hwid"', s, count=1)
must(k, "applicationId bulunamadı")
write(gp, s)
for strf in glob.glob(os.path.join(main, "res", "values*", "*.xml")):
    t = read(strf)
    t2 = re.sub(r'(<string name="app_name"[^>]*>)[^<]*(</string>)', r'\1v2rayNG HWID\2', t)
    if t2 != t: write(strf, t2)
print("[7] paket: com.v2ray.ang.hwid · ad: v2rayNG HWID")
print("✓ YAMA TAMAM")
