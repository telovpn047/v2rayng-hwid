package com.v2ray.ang.patch

import android.os.Build

/**
 * Abonelik başına elle girilen HWID / başlıklar.
 *  - Boş: hiçbir başlık eklenmez (v2rayNG varsayılan davranışı).
 *  - Tek değer (ör. 8697b9cde384fe92): Happ ile aynı set gönderilir:
 *      X-Hwid, X-Device-Os: Android, X-Ver-Os: <sürüm>, X-Device-Model: <model>
 *  - "Ad: değer" satırları: yazılan başlıklar aynen gönderilir (User-Agent dahil).
 */
object SubHeaders {

    fun headersFor(raw: String?): Map<String, String> {
        val t = raw?.trim().orEmpty()
        if (t.isEmpty()) return emptyMap()
        val lines = t.lines().map { it.trim() }.filter { it.isNotEmpty() }
        val out = linkedMapOf<String, String>()
        if (lines.any { it.contains(':') }) {
            for (l in lines) {
                val i = l.indexOf(':')
                if (i <= 0) continue
                val k = l.substring(0, i).trim()
                val v = clean(l.substring(i + 1))
                if (k.isNotEmpty() && k.all { it.isLetterOrDigit() || it == '-' || it == '_' }) out[k] = v
            }
            return out
        }
        out["X-Hwid"] = clean(lines.first())
        out["X-Device-Os"] = "Android"
        out["X-Ver-Os"] = clean(Build.VERSION.RELEASE)
        out["X-Device-Model"] = clean(Build.MODEL)
        return out
    }

    /** OkHttp Request.Builder'a başlıkları ekler; aynı adlı başlık (User-Agent dahil) varsa değiştirir. */
    @JvmStatic
    fun apply(b: okhttp3.Request.Builder, raw: String?) {
        for ((k, v) in headersFor(raw)) b.header(k, v)
    }

    private fun clean(s: String?): String {
        if (s.isNullOrEmpty()) return ""
        val sb = StringBuilder()
        for (ch in s.trim()) sb.append(if (ch.code in 0x20..0x7e) ch else '_')
        return sb.toString()
    }
}
