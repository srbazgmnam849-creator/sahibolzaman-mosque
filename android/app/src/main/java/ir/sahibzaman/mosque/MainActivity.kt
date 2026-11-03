package ir.sahibzaman.mosque

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.webkit.CookieManager
import android.webkit.GeolocationPermissions
import android.webkit.URLUtil
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

/**
 * سامانه مدیریت مسجد صاحب‌الزمان
 * WebView wrapper برای وب‌اپلیکیشن مسجد (Laravel/PHP).
 *
 * - URL از res/values/strings.xml (app_url) خوانده می‌شود.
 * - لینک‌های خارجی (هاست متفاوت / tel / mailto و ...) در مرورگر یا اپ مربوطه باز می‌شوند.
 * - در صورت خطا (قطع اینترنت / سرور در دسترس نیست) یک صفحه خطای فارسی و راست‌به‌چپ
 *   با دکمه «تلاش مجدد» نمایش داده می‌شود.
 * - آپلود فایل (تصویر / PDF) در فرم‌های وب از طریق onShowFileChooser پشتیبانی می‌شود.
 * - دانلود فایل‌ها با DownloadManager انجام می‌شود.
 * - کشیدن از بالا (SwipeRefresh) صفحه را تازه‌سازی می‌کند.
 * - دکمه بازگشت: اگر WebView بتواند عقب برود، عقب می‌رود؛ وگرنه برنامه بسته می‌شود.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var mainUrl: String

    /** آیا آخرین بارگذاری فریم اصلی با خطا مواجه شده است؟ */
    private var isError = false

    /** کال‌بک انتخاب فایل فرم وب (آپلود تصویر/PDF) */
    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    /**
     * لانچر انتخاب فایل — باید قبل از onCreate (به‌صورت فیلد) ثبت شود.
     * با StartActivityForResult و Intent.ACTION_GET_CONTENT کار می‌کند و
     * نتیجه را به ValueCallback<Uri[]> وب‌ویو برمی‌گرداند.
     */
    private val fileChooserLauncher: ActivityResultLauncher<Intent> =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val callback = filePathCallback
            filePathCallback = null
            if (callback != null) {
                val uris: Array<Uri>? =
                    WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
                callback.onReceiveValue(uris ?: arrayOf())
            }
        }

    // ------------------------------------------------------------------ //

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // خروج از حالت اسپلش به تم اصلی برنامه (edge-to-edge معمولی)
        setTheme(R.style.Theme_MosqueApp)
        WindowCompat.setDecorFitsSystemWindows(window, true)
        setContentView(R.layout.activity_main)

        mainUrl = getString(R.string.app_url)
        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)

        setupWebView()
        setupSwipeRefresh()
        setupBackHandling()

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            webView.loadUrl(mainUrl)
        }
    }

    // ------------------------------------------------------------------ //
    // WebView setup
    // ------------------------------------------------------------------ //

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
            mediaPlaybackRequiresUserGesture = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            allowFileAccess = false
            allowContentAccess = true
        }

        // کوکی‌ها برای نگه‌داشتن نشست کاربر
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true)

        webView.setBackgroundColor(ContextCompat.getColor(this, R.color.bg))

        webView.webViewClient = object : WebViewClient() {

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url
                val scheme = url.scheme?.lowercase() ?: return false

                // این‌ها را خود WebView مدیریت می‌کند
                if (scheme in setOf("data", "blob", "about", "javascript")) return false

                // هر چیز غیر http/https (tel:, mailto:, whatsapp:, intent: و ...)
                // در اپلیکیشن مربوطه باز می‌شود
                if (scheme != "http" && scheme != "https") {
                    return openExternally(url)
                }

                // هاست متفاوت از هاست اصلی => لینک خارجی است => خارج از اپ باز شود
                val mainHost = Uri.parse(mainUrl).host
                return if (url.host != mainHost) openExternally(url) else false
            }

            override fun onPageStarted(view: WebView, url: String, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                // شروع بارگذاری جدید => حالت خطا ریست می‌شود
                isError = false
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                // توقف انیمیشن «کشیدن برای تازه‌سازی»
                swipeRefresh.isRefreshing = false
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError
            ) {
                // فقط خطای فریم اصلی (نه تصاویر/اسکریپت‌های فرعی) صفحه خطا را نشان می‌دهد
                if (request.isForMainFrame) {
                    isError = true
                    loadErrorPage(error.description?.toString() ?: "")
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {

            /** آپلود فایل در فرم‌های وب: تصویر یا PDF */
            override fun onShowFileChooser(
                view: WebView,
                callback: ValueCallback<Array<Uri>>,
                params: FileChooserParams
            ): Boolean {
                if (filePathCallback != null) {
                    filePathCallback?.onReceiveValue(null)
                }
                filePathCallback = callback

                val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "*/*"
                    putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("image/*", "application/pdf"))
                    if (params.mode == FileChooserParams.MODE_OPEN_MULTIPLE) {
                        putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
                    }
                    putExtra(Intent.EXTRA_TITLE, params.filenameHint ?: "")
                }

                return try {
                    fileChooserLauncher.launch(Intent.createChooser(intent, params.title))
                    true
                } catch (e: ActivityNotFoundException) {
                    filePathCallback = null
                    false
                }
            }

            /** مجوز موقعیت مکانی: محترمانه رد می‌شود */
            override fun onGeolocationPermissionsShowPrompt(
                origin: String,
                callback: GeolocationPermissions.Callback
            ) {
                callback.invoke(origin, false, false)
            }
        }

        // دانلود فایل‌ها با DownloadManager
        webView.setDownloadListener { url, userAgent, contentDisposition, mimeType, _ ->
            startDownload(url, userAgent, contentDisposition, mimeType)
        }
    }

    // ------------------------------------------------------------------ //
    // Helpers
    // ------------------------------------------------------------------ //

    private fun openExternally(url: Uri): Boolean {
        return try {
            startActivity(Intent(Intent.ACTION_VIEW, url))
            true
        } catch (e: ActivityNotFoundException) {
            false
        }
    }

    private fun startDownload(url: String, userAgent: String, contentDisposition: String, mimeType: String) {
        try {
            val request = DownloadManager.Request(Uri.parse(url)).apply {
                setMimeType(mimeType)
                val cookies = CookieManager.getInstance().getCookie(url)
                if (!cookies.isNullOrBlank()) addRequestHeader("cookie", cookies)
                addRequestHeader("User-Agent", userAgent)
                setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                val fileName = URLUtil.guessFileName(url, contentDisposition, mimeType)
                setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fileName)
                setTitle(fileName)
            }
            val dm = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            dm.enqueue(request)
            Toast.makeText(this, "دانلود آغاز شد", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            // اگر DownloadManager ممکن نبود، در مرورگر باز شود
            openExternally(Uri.parse(url))
        }
    }

    /** صفحه خطای فارسی/RTL با دکمه «تلاش مجدد» */
    private fun loadErrorPage(detail: String) {
        val safeDetail = detail.take(200).replace("<", "&lt;").replace(">", "&gt;")
        val html = """
            <!DOCTYPE html>
            <html dir="rtl" lang="fa">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
              <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body {
                  background: #183D30;
                  color: #FFFFFF;
                  font-family: Tahoma, "Vazirmatn", sans-serif;
                  min-height: 100vh;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  padding: 24px;
                  text-align: center;
                }
                .card { max-width: 420px; width: 100%; }
                .logo {
                  width: 96px; height: 96px; margin: 0 auto 24px auto;
                  border-radius: 24px; background: #FFFFFF;
                  display: flex; align-items: center; justify-content: center;
                  font-size: 48px;
                }
                h1 { font-size: 20px; margin-bottom: 12px; color: #B49A60; }
                p  { font-size: 15px; line-height: 1.9; color: #EDEFEA; margin-bottom: 8px; }
                .detail {
                  direction: ltr; font-size: 12px; color: #9DB5AA;
                  margin-top: 12px; word-break: break-all;
                }
                button {
                  margin-top: 28px;
                  background: #B49A60;
                  color: #183D30;
                  border: none;
                  border-radius: 12px;
                  padding: 14px 40px;
                  font-size: 16px;
                  font-family: inherit;
                  font-weight: bold;
                  cursor: pointer;
                }
                button:active { opacity: 0.85; }
              </style>
            </head>
            <body>
              <div class="card">
                <div class="logo">🕌</div>
                <h1>اتصال برقرار نشد</h1>
                <p>اتصال به سامانه برقرار نشد.<br>لطفاً اتصال اینترنت و آدرس سرور را بررسی کنید.</p>
                <div class="detail">$safeDetail</div>
                <button onclick="location.href='$mainUrl'">تلاش مجدد</button>
              </div>
            </body>
            </html>
        """.trimIndent()
        webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)
    }

    // ------------------------------------------------------------------ //
    // Pull-to-refresh
    // ------------------------------------------------------------------ //

    private fun setupSwipeRefresh() {
        swipeRefresh.setColorSchemeColors(
            ContextCompat.getColor(this, R.color.primary),
            ContextCompat.getColor(this, R.color.accent)
        )
        swipeRefresh.setOnRefreshListener {
            if (isError) {
                // اگر صفحه خطا نمایش داده می‌شود، مستقیماً URL اصلی را بارگذاری کن
                isError = false
                webView.loadUrl(mainUrl)
            } else {
                webView.reload()
            }
        }
    }

    // ------------------------------------------------------------------ //
    // Back handling
    // ------------------------------------------------------------------ //

    private fun setupBackHandling() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    finish()
                }
            }
        })
    }

    // ------------------------------------------------------------------ //

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    override fun onDestroy() {
        // آزادسازی منابع WebView برای جلوگیری از نشت حافظه
        filePathCallback?.onReceiveValue(null)
        filePathCallback = null
        if (::webView.isInitialized) {
            webView.destroy()
        }
        super.onDestroy()
    }
}
