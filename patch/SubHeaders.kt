package com.v2ray.ang.patch

import android.os.Build
import java.net.URLConnection

/**
 * Abonelik başına elle girilen HWID ve ek başlıklar.
 * Değer boşsa ilgili başlık hiç gönderilmez (v2rayNG varsayılan davranışı korunur).
 * HWID girilmişse Remnawave'in beklediği başlık seti gönderilir: x-hwid, x-device-os, x-ver-os, x-device-model.
 */
object SubHeaders {

    /** "x-hwid: abc" ya da "x-hwid=abc" satırlarını da destekler; sade bir değer de kabul edilir. */
    fun parseHwid(raw: String?): String {
        val t = raw?.trim().orEmpty()
        if (t.isEmpty()) return ""
        val m = Regex("(?i)x-hwid\\s*[:=]\\s*(.+)").find(t)
        return (m?.groupValues?.get(1) ?: t).trim()
    }

    fun headersFor(hwid: String?): Map<String, String> {
        val id = parseHwid(hwid)
        if (id.isEmpty()) return emptyMap()
        return linkedMapOf(
            "x-hwid" to id,
            "x-device-os" to "Android",
            "x-ver-os" to clean(Build.VERSION.RELEASE),
            "x-device-model" to clean(Build.MANUFACTURER + " " + Build.MODEL),
        )
    }

    /** HttpURLConnection'a HWID başlıklarını ekler (User-Agent'a dokunmaz). */
    @JvmStatic
    fun inject(c: URLConnection?, hwid: String?) {
        try {
            if (c == null) return
            for ((k, v) in headersFor(hwid)) c.setRequestProperty(k, v)
        } catch (_: Throwable) {}
    }

    private fun clean(s: String?): String {
        if (s.isNullOrEmpty()) return ""
        val b = StringBuilder()
        for (ch in s.trim()) b.append(if (ch.code in 0x20..0x7e) ch else '_')
        return b.toString()
    }
}
