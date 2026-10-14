package com.v2ray.ang.patch

import android.os.Build

/**
 * Abonelik başına elle girilen HWID.
 * Boşsa hiçbir başlık eklenmez (v2rayNG'nin varsayılan davranışı aynen kalır).
 * Doluysa Remnawave'in beklediği başlıklar: x-hwid, x-device-os, x-ver-os, x-device-model.
 */
object SubHeaders {

    /** Sade değer ya da "x-hwid: değer" / "x-hwid=değer" biçimi kabul edilir. */
    fun parseHwid(raw: String?): String {
        val t = raw?.trim().orEmpty()
        if (t.isEmpty()) return ""
        val m = Regex("(?i)^x-hwid\\s*[:=]\\s*(.+)$").find(t)
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

    /** OkHttp Request.Builder'a HWID başlıklarını ekler. */
    @JvmStatic
    fun apply(b: okhttp3.Request.Builder, hwid: String?) {
        for ((k, v) in headersFor(hwid)) b.header(k, v)
    }

    private fun clean(s: String?): String {
        if (s.isNullOrEmpty()) return ""
        val sb = StringBuilder()
        for (ch in s.trim()) sb.append(if (ch.code in 0x20..0x7e) ch else '_')
        return sb.toString()
    }
}
