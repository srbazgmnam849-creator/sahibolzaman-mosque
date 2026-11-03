# Rules for the MosqueSahibZaman WebView wrapper.
# Minification is disabled (minifyEnabled false), so these rules are
# mostly a safety net if minification is turned on later.

# Keep the MainActivity entry point
-keep class ir.sahibzaman.mosque.MainActivity { *; }

# Keep JavascriptInterface methods if any are added later
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
