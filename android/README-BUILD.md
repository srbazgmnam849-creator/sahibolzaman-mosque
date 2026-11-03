# اپلیکیشن اندروید سامانه مدیریت مسجد صاحب‌الزمان 🕌

این پروژه یک **پوسته اندروید (WebView Wrapper)** برای سامانه مدیریت مسجد است؛ یعنی وب‌اپلیکیشن شما (مثلاً Laravel/PHP) داخل یک WebView بومی اندروید نمایش داده می‌شود و کاربر آن را مثل یک اپ معمولی از فروشگاه یا فایل APK نصب می‌کند.

- نام اپلیکیشن: **سامانه مدیریت مسجد صاحب‌الزمان**
- شناسه پکیج (Application ID): `ir.sahibzaman.mosque`
- زبان برنامه‌نویسی: Kotlin
- حداقل نسخه اندروید: **Android 7.0 (API 24)** — هدف: **Android 14 (API 34)**
- پشتیبانی کامل راست‌به‌چپ (RTL) و زبان فارسی
- امکانات: اسپلش‌اسکرین با لوگو، کشیدن برای تازه‌سازی (Pull-to-Refresh)، آپلود فایل (تصویر/PDF) در فرم‌ها، دانلود فایل با DownloadManager، صفحه خطای فارسی با دکمه «تلاش مجدد»، باز شدن لینک‌های خارجی در مرورگر/اپ مربوطه

---

## ۱) پیش‌نیازها

| مورد | حداقل نسخه |
|---|---|
| Android Studio | **Hedgehog (2023.1.1) یا جدیدتر** |
| JDK | 17 (همراه Android Studio نصب است) |
| Gradle | 8.7+ (خودکار توسط Wrapper/استودیو دانلود می‌شود) |
| Android Gradle Plugin | 8.5.2 |
| Kotlin | 1.9.24 |
| اینترنت | برای دانلود وابستگی‌ها در اولین Build لازم است |

> نیازی به نصب جداگانه Gradle یا Kotlin ندارید؛ Android Studio همه‌چیز را خودکار دانلود می‌کند.

---

## ۲) نحوه باز کردن پروژه در Android Studio

1. پوشه `MosqueSahibZaman-Android` را روی رایانه خود کپی کنید.
2. Android Studio را باز کنید و از منو:
   **File → Open** (در صفحه خوش‌آمد: **Open**)
3. پوشه `MosqueSahibZaman-Android` را انتخاب و **OK** کنید.
4. اولین بار همگام‌سازی (Gradle Sync) چند دقیقه طول می‌کشد؛ منتظر بمانید تا پیام
   `BUILD SUCCESSFUL` یا نوار پیشرفت تمام شود.
   - اگر خطای «SDK not found» دیدید، از **File → Settings → Languages & Frameworks → Android SDK** نسخه **Android 14 (API 34)** را نصب کنید.
5. برای تست، یک دستگاه/شبیه‌ساز وصل کنید و دکمه ▶ (Run) را بزنید.

> ⚠️ **توجه:** در این محیط، ابزار ساخت اندروید موجود نیست؛ Build باید روی سیستم خودتان با Android Studio انجام شود.

---

## ۳) تغییر آدرس سرور (مهم!)

آدرس سامانه در فایل زیر نگه‌داری می‌شود:

```
app/src/main/res/values/strings.xml
```

خط زیر را پیدا کنید و به آدرس سرور خودتان تغییر دهید:

```xml
<string name="app_url">http://10.0.2.2:8000</string>
```

مثال برای سرور واقعی:

```xml
<string name="app_url">https://mosque.example.com</string>
```

نکات:
- مقدار `http://10.0.2.2:8000` فقط برای **تست روی شبیه‌ساز** است (`10.0.2.2` از داخل شبیه‌ساز به `localhost` رایانه شما اشاره می‌کند).
- در نسخه نهایی حتماً از **HTTPS** استفاده کنید.
- گزینه `android:usesCleartextTraffic="true"` در `AndroidManifest.xml` فقط برای تست با HTTP است؛ در تولید (production) با HTTPS می‌توانید آن را `false` کنید.

---

## ۴) ساخت فایل APK

در Android Studio:

1. از منو: **Build → Build Bundle(s) / APK(s) → Build APK(s)**
2. صبر کنید تا Build تمام شود.
3. روی اعلان پایین سمت راست، **locate** را بزنید یا مسیر زیر را باز کنید:

```
app/build/outputs/apk/debug/app-debug.apk
```

این فایل **APK دیباگ** است و مستقیماً روی گوشی قابل نصب است (کافیست در گوشی گزینه «نصب از منابع ناشناس» را مجاز کنید).

برای ساخت نسخه **Release** (شکسته/امضاشده) به بخش بعد بروید.

---

## ۵) امضای APK (Signed APK) — خلاصه

برای انتشار رسمی، APK باید با کلید امضا شود:

1. منو: **Build → Generate Signed Bundle / APK**
2. گزینه **APK** را انتخاب و **Next** بزنید.
3. زیر **Key store path** روی **Create new…** بزنید و یک Keystore جدید بسازید:
   - مسیر فایل و یک رمز (Keystore password) انتخاب کنید.
   - نام مستعار (Alias)، رمز Alias و مشخصات (نام، سازمان، کشور) را پر کنید.
   - ⚠️ فایل Keystore و رمزها را **در جای امن نگه‌دارید**؛ برای همه به‌روزرسانی‌های بعدی به همان کلید نیاز دارید.
4. Build Variant را **release** انتخاب و **Finish** بزنید.
5. فایل خروجی این‌جا ساخته می‌شود:

```
app/release/app-release.apk
```

(همین مسیر در حالت Android App Bundle: `app/build/outputs/bundle/release/app-release.aab`)

---

## ۶) ساختار پروژه

```
MosqueSahibZaman-Android/
├── settings.gradle                    ← تنظیمات پروژه و مخازن
├── build.gradle                       ← پلاگین‌ها (AGP 8.5.2, Kotlin 1.9.24)
├── gradle.properties                  ← تنظیمات Gradle/AndroidX
├── README-BUILD.md                    ← همین راهنما
└── app/
    ├── build.gradle                   ← پیکربندی ماژول (minSdk 24, targetSdk 34)
    ├── proguard-rules.pro             ← قوانین ProGuard
    └── src/main/
        ├── AndroidManifest.xml        ← دسترسی‌ها، تم اسپلش، اکتیویتی
        ├── java/ir/sahibzaman/mosque/
        │   └── MainActivity.kt        ← منطق WebView (کامل)
        └── res/
            ├── layout/activity_main.xml        ← WebView + SwipeRefresh
            ├── values/strings.xml              ← نام اپ + آدرس سرور (app_url)
            ├── values/colors.xml               ← پالت سبز/طلایی مسجد
            ├── values/themes.xml               ← تم اسپلش و تم اصلی
            ├── xml/file_paths.xml              ← مسیرهای FileProvider
            ├── drawable/splash_background.xml  ← پس‌زمینه اسپلش
            ├── drawable-nodpi/splash_logo.png  ← لوگوی اسپلش (512×512)
            ├── mipmap-xxhdpi/ic_launcher.png   ← آیکون لانچر (192×192)
            └── mipmap-hdpi/ic_launcher.png     ← آیکون لانچر (72×72)
```

---

## ۷) روش جایگزین بدون اندروید استودیو: PWA

اگر موقتاً نمی‌خواهید APK بسازید، می‌توانید همین سامانه را مثل یک «اپ» روی صفحه اصلی گوشی نصب کنید (PWA / میان‌بر وب‌اپ):

1. در گوشی اندروید، **Chrome** را باز کنید و آدرس سامانه را وارد کنید
   (مثلاً `https://mosque.example.com`).
2. از منوی سه‌نقطه‌ای ⋮ بالای مرورگر:
   **افزودن به صفحه اصلی / Add to Home Screen** را بزنید.
3. یک نام انتخاب کنید (مثلاً «مسجد صاحب‌الزمان») و تأیید کنید.
4. حالا آیکون سامانه روی صفحه اصلی گوشی قرار می‌گیرد و مثل اپ تمام‌صفحه باز می‌شود.

مزیت این روش: بدون کامپایل و بدون نیاز به هیچ ابزاری، در چند دقیقه.
محدودیت: آیکون و تجربه نصب به وب‌اپلیکیشن شما بستگی دارد (اگر `manifest.json` و Service Worker داشته باشید، تجربه PWA کامل‌تری خواهید داشت).

---

## ۸) پرسش‌های رایج

**سوال: صفحه «اتصال برقرار نشد» می‌بینم.**
- آدرس `app_url` در `strings.xml` را بررسی کنید؛ روی گوشی واقعی باید آدرس در دسترس از اینترنت باشد (نه `10.0.2.2`).
- اتصال اینترنت گوشی و روشن بودن سرور را بررسی کنید و با دکمه «تلاش مجدد» دوباره امتحان کنید.

**سوال: آپلود فایل کار نمی‌کند.**
- روی برخی گوشی‌های قدیمی، نبودِ اپ «Files/فایل‌ها» باعث می‌شود انتخاب‌گر فایل باز نشود. یک مدیر فایل نصب کنید.

**سوال: می‌خواهم هنگام انتشار، نسخه را بالا ببرم.**
- در `app/build.gradle` مقادیر `versionCode` (عدد صحیح، همیشه +۱) و `versionName` (مثلاً "1.1.0") را تغییر دهید.
