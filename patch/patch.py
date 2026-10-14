#!/usr/bin/env python3
"""v2rayNG'ye abonelik başına elle HWID girme özelliği ekler. Markalama/değişiklik yapmaz.
Kullanım: python3 patch/patch.py <v2rayNG-kök-dizini>"""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(sys.argv[1])
app = os.path.join(root, "V2rayNG", "app")
main = os.path.join(app, "src", "main")
kt = os.path.join(main, "kotlin")
if not os.path.isdir(kt):
    kt = os.path.join(main, "java")
assert os.path.isdir(kt), f"kaynak bulunamadı: {kt}"

def read(p): return open(p, encoding="utf-8").read()
def write(p, s): open(p, "w", encoding="utf-8").write(s)
def find(name):
    for dp, _, fs in os.walk(kt):
        if name in fs: return os.path.join(dp, name)
    return None

def rx_sub(pat, repl, s, n=0, flags=0):
    return re.subn(pat, repl, s, count=n, flags=flags)

changed = []

# 0) Yardımcı sınıfı kopyala
dst = os.path.join(kt, "com", "v2ray", "ang", "patch")
os.makedirs(dst, exist_ok=True)
write(os.path.join(dst, "SubHeaders.kt"), read(os.path.join(HERE, "SubHeaders.kt")))
print("[0] SubHeaders.kt eklendi")

# 1) Veri modeli: SubscriptionItem'a customHwid alanı ekle
f = find("SubscriptionItem.kt")
assert f, "SubscriptionItem.kt yok"
s = read(f)
if "customHwid" not in s:
    # customUserAgent zaten varsa onun yanına; yoksa enabled'dan sonra ekle
    if "customUserAgent" in s:
        s, k = rx_sub(r'(var\s+customUserAgent\s*:\s*String\s*=\s*"")',
                      r'\1,\n    var customHwid: String = ""', s, 1)
    else:
        s, k = rx_sub(r'(var\s+enabled\s*:\s*Boolean\s*=\s*true)',
                      r'\1,\n    var customUserAgent: String = "",\n    var customHwid: String = ""', s, 1)
    assert k, "SubscriptionItem alanı eklenemedi"
    write(f, s); changed.append(f); print("[1] SubscriptionItem.customHwid eklendi")

# 2) Abonelik güncellemesinde HWID başlığını enjekte et
#    v2rayNG aboneliği AngConfigManager / SubscriptionUpdater içinde HttpURLConnection ile çeker.
inject_done = 0
for cand in ("AngConfigManager.kt", "SubscriptionUpdater.kt", "SpeedtestManager.kt"):
    f = find(cand)
    if not f: continue
    s = read(f)
    if "openConnection()" not in s or "SubHeaders.inject" in s:
        continue
    # abonelik nesnesinin değişken adını yakalamaya çalış (customUserAgent kullanılan yerden)
    hwid_expr = None
    m = re.search(r'(\w+)\.customUserAgent', s)
    if m:
        hwid_expr = f"{m.group(1)}.customHwid"
    # her openConnection sonrası inject ekle
    def add_inject(mm):
        global inject_done
        indent = mm.group(1)
        var = mm.group(2)
        expr = hwid_expr or '""'
        inject_done += 1
        return f"{mm.group(0)}\n{indent}com.v2ray.ang.patch.SubHeaders.inject({var}, {expr})"
    s2, k = rx_sub(r'(?m)^(\s*)(?:val|var)\s+(\w+)\s*=\s*[^\n]*openConnection\(\)[^\n]*$',
                   add_inject, s)
    if k:
        write(f, s2); changed.append(f); print(f"[2] {cand}: {k} yerde HWID enjekte edildi")

if inject_done == 0:
    print("[2] UYARI: openConnection bulunamadı; manuel kontrol gerek")

# 3) Abonelik düzenleme ekranına HWID alanı (layout + Activity)
#    layout: activity_sub_edit.xml içine customUserAgent alanının benzeri bir alan ekle
lay = None
for p in glob.glob(os.path.join(main, "res", "layout", "*sub*edit*.xml")) + \
         glob.glob(os.path.join(main, "res", "layout", "*edit*sub*.xml")):
    lay = p; break
if lay:
    s = read(lay)
    if "et_custom_hwid" not in s:
        # customUserAgent (et_custom_... ya da benzeri) bloğunu kopyalayıp hwid'e çevir
        m = re.search(r'(<com\.google\.android\.material\.textfield\.TextInputLayout[\s\S]*?et_[a-zA-Z_]*(?:agent|Agent)[\s\S]*?</com\.google\.android\.material\.textfield\.TextInputLayout>)', s)
        if not m:
            m = re.search(r'(<EditText[\s\S]*?et_[a-zA-Z_]*(?:agent|Agent)[\s\S]*?/>)', s)
        if m:
            block = m.group(1)
            nb = block
            nb = re.sub(r'et_[a-zA-Z_]*[aA]gent', 'et_custom_hwid', nb)
            nb = re.sub(r'(android:hint="?)[^"\n]*', r'\1HWID (boş = otomatik)', nb, count=1)
            s = s.replace(block, block + "\n" + nb, 1)
            write(lay, s); changed.append(lay); print("[3] layout: HWID alanı eklendi")
        else:
            print("[3] UYARI: layout'ta User-Agent alanı bulunamadı")
    # Activity: oku/yaz
    act = find("SubEditActivity.kt") or find("SubEditActivity.java")
    if act:
        s = read(act)
        if "et_custom_hwid" not in s and "customHwid" not in s:
            # binding ya da findViewById biçimini customUserAgent'tan türet
            mu = re.search(r'(\w+)\.customUserAgent\s*=\s*([^\n]+)', s)   # yazma
            ru = re.search(r'([\w.]*(?:etCustom\w*Agent|et_custom\w*agent)[\w.]*)\.text', s, re.I)
            if mu:
                var, rhs = mu.group(1), mu.group(2).strip()
                rhs_h = re.sub(r'(etCustom\w*Agent|et_custom\w*agent)', 'etCustomHwid', rhs, flags=re.I)
                s = s.replace(mu.group(0), mu.group(0) + f"\n        {var}.customHwid = {rhs_h}")
            # okuma: setText(... customUserAgent) benzeri
            mr = re.search(r'([\w.]*(?:etCustom\w*Agent)[\w.]*)\.(?:setText|text\s*=)\s*\(?[^\n]*customUserAgent', s, re.I)
            if mr:
                line = mr.group(0)
                nl = re.sub(r'(etCustom\w*Agent)', 'etCustomHwid', line, flags=re.I).replace("customUserAgent", "customHwid")
                s = s.replace(line, line + "\n        " + nl)
            write(act, s); changed.append(act); print("[3] Activity: HWID oku/yaz eklendi (kontrol et)")
else:
    print("[3] UYARI: abonelik düzenleme layout'u bulunamadı — view binding sürümü farklı olabilir")

print(f"\nTOPLAM değişen dosya: {len(set(changed))}")
print("Not: [2] ve [3] adımları v2rayNG sürümüne göre elle doğrulama isteyebilir.")
