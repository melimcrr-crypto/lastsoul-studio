#!/usr/bin/env python3
"""
assemble.py — بسته‌بندی خروجی‌ها: کانتکت‌شیت + ریلِ مقایسه + گرین سینمایی.

کار می‌کند با ffmpeg و Pillow. هیچ وابستگی دیگری لازم ندارد.

usage:
  python edit/assemble.py <artifacts_dir> <out_dir>
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (11, 13, 18)
INK = (242, 239, 233)
DIM = (150, 156, 166)
AMBER = (232, 185, 106)


def sh(args: list[str]) -> None:
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(args)[:200])
        print(r.stderr[-1500:])
        raise SystemExit(1)


def font(sz: int):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def contact_sheet(stills: list[tuple[str, str]], out: Path) -> None:
    """یک شیت تیره با برچسب زیر هر تصویر."""
    cols = 2 if len(stills) <= 4 else 3
    tw, th = 620, 349                      # 16:9
    pad, cap = 26, 46
    rows = (len(stills) + cols - 1) // cols
    W = cols * tw + pad * (cols + 1)
    H = rows * (th + cap) + pad * (rows + 1) + 90

    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 30), "LAST SOUL — TOOL SHOOTOUT", font=font(34), fill=INK)
    d.text((pad, 70), "Blender Cycles (headless)  ·  Manim 0.22  ·  ffmpeg 7",
           font=font(20), fill=DIM)

    for i, (path, label) in enumerate(stills):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = 100 + pad + r * (th + cap + pad)
        im = Image.open(path).convert("RGB")
        im.thumbnail((tw, th), Image.LANCZOS)
        sheet.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        d.text((x + 4, y + th + 10), label.upper(), font=font(20), fill=AMBER)

    sheet.save(out, quality=94, optimize=True)
    print(f"contact sheet → {out}  ({sheet.width}×{sheet.height})")


def grade_and_grain(src: Path, dst: Path) -> None:
    """گرین ۳۵mm سبک + کنتراست ملایم — همان بافتِ فینال فیلم."""
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
        "-vf", "eq=contrast=1.06:saturation=1.04,"
               "noise=alls=9:allf=t+u,"
               "vignette=PI/5",
        "-c:v", "libx264", "-crf", "20", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-an", str(dst)])
    print(f"graded → {dst}")


def reel(clips: list[Path], out: Path) -> None:
    """همهٔ کلیپ‌ها را با هم می‌چسباند (اگر اختلاف رزولوشن داشت، اسکیل می‌کند)."""
    if not clips:
        return
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(lst),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
               "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x0B0D12,fps=24",
        "-c:v", "libx264", "-crf", "21", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-an", str(out)])
    print(f"reel → {out}")


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts")
    outd = Path(sys.argv[2] if len(sys.argv) > 2 else "dist")
    outd.mkdir(parents=True, exist_ok=True)

    pngs = sorted(root.rglob("*.png"))
    mp4s = sorted(root.rglob("*.mp4"))
    print(f"found {len(pngs)} png, {len(mp4s)} mp4")

    labels = {
        "wide": "Blender · wide — window key, haze, seated figure",
        "close": "Blender · close — faceless head, rim light, bokeh",
        "low": "Blender · low angle — window eclipse",
        "anim": "Blender · camera push (48f)",
        "Card": "Manim · text card 2 lines",
        "Title": "Manim · channel title",
        "EndCard": "Manim · end card",
    }

    stills = [(str(p), labels.get(p.stem, p.stem)) for p in pngs if "anim_" not in p.stem][:6]
    if stills:
        contact_sheet(stills, outd / "contact_sheet.jpg")

    # یک نمونهٔ گرین‌خورده، برای قضاوت بافت
    anim = [p for p in pngs if p.stem.startswith("anim_")]
    if anim:
        adir = anim[0].parent
        digits = sum(1 for ch in "".join(
            ch for ch in anim[0].stem if ch.isdigit()))
        sh(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24",
            "-i", str(adir / ("anim_%0" + str(max(digits, 1)) + "d.png")),
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
            str(outd / "_raw_anim.mp4")])
        grade_and_grain(outd / "_raw_anim.mp4", outd / "blender_anim_graded.mp4")
        (outd / "_raw_anim.mp4").unlink(missing_ok=True)

    reel(mp4s + ([outd / "blender_anim_graded.mp4"] if (outd / "blender_anim_graded.mp4").exists() else []),
         outd / "reel_all_tools.mp4")


if __name__ == "__main__":
    main()
