# lastsoul-studio

پایپ‌لاین تولید برای کانال **Last Soul** — همه‌چیز روی GitHub Actions اجرا می‌شود.

## چه چیزی اینجا هست

| مسیر | کار |
|---|---|
| `blender/scene.py` | صحنهٔ سه‌بعدی: فیگور بی‌چهره با `join + voxel remesh` (یک سطح پیوسته)، پنجره به‌عنوان تنها منبع نور، غبار حجمی، دوربین با پوش آرام. چهار واریانت: `wide` `close` `low` `anim` |
| `manim/type.py` | لایهٔ تایپوگرافی: `Card` / `Title` / `EndCard` — کپس درشت، پوش آرام، رنگ تأکید کهربایی |
| `edit/assemble.py` | کانتکت‌شیت، گرین و گرید (`noise` + `vignette` + `eq`)، و ریلِ مقایسه |
| `.github/workflows/render.yml` | ۴ جاب موازی: سه استیل بلندر + کلیپ ۴۸ فریمی + سه کلیپ مینیم + بسته‌بندی |

## اجرا

```bash
# بلندر (محلی)
blender -b --factory-startup -P blender/scene.py -- wide 1600 900 96 1 render

# مینیم
manim -qh manim/type.py Card Title EndCard

# بسته‌بندی
python edit/assemble.py artifacts dist
```

روی گیت‌هاب: تب **Actions → Render samples → Run workflow**.
خروجی‌ها در artifact به نام `DIST-samples` هستند.

## تصمیم‌های فنی (و دلیلشان)

- **Metaball استفاده نشد** — در تست ادغام نشد و کره‌های شناور ساخت. `join + voxel remesh + smooth` یک سطح پیوسته می‌دهد.
- **پنجره emissive به‌جای چند نور** — استایل کانال «تک منبع نور» است؛ میله‌های پنجره خودشان الگوی سایه می‌سازند.
- **Cyclex CPU، نه GPU** — روی رانر استاندارد ۴ هسته‌ای جواب می‌دهد؛ رانر GPU لازم نیست.
- **AgX Medium High Contrast** — کنتراست سینمایی، نه فلتِ دیجیتال.
- **هر کارت متن حداکثر ۲ خط / ۵ کلمه** — فید بی‌صدا، خواندن در یک نگاه.
