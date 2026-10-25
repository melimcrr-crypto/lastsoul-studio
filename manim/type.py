"""
Last Soul — typographic layer (Manim Community 0.22).

Rules taken from the channel's own 5 videos:
  · huge caps, 2-5 words per card, max 2 lines
  · dark plate + one warm accent word
  · slow scale push, no bounce, no spin
  · silence is the default; the type carries the narration

render:  manim -qh --format=mp4 manim/type.py Card Title EndCard
"""
from manim import *

BG     = "#0B0D12"
INK    = "#F2EFE9"
AMBER  = "#E8B96A"
DIM    = "#6E7480"

config.background_color = BG
config.frame_rate = 24


def plate(*lines, size=0.62, accent_last=False, accent_color=AMBER):
    """۲ تا ۳ خط تایپ درشت، وسط‌چین، با کلمهٔ آخر به‌رنگ تأکید."""
    grp = VGroup()
    for i, ln in enumerate(lines):
        col = accent_color if (accent_last and i == len(lines) - 1) else INK
        grp.add(Text(ln, font="DejaVu Sans", weight=BOLD, color=col).scale(size))
    grp.arrange(DOWN, buff=0.30, aligned_edge=LEFT)
    # وسط‌چین افقی با توجه به پهن‌ترین خط
    for t in grp:
        t.align_to(grp, LEFT)
    return grp.move_to(ORIGIN)


class Card(Scene):
    """یک کارت متن با پوش آرام و فیدِ بالا."""
    def construct(self):
        halo = VGroup(
            Circle(radius=3.2).set_fill(AMBER, 0.045).set_stroke(width=0),
            Circle(radius=1.7).set_fill(AMBER, 0.055).set_stroke(width=0),
        )
        self.add(halo)

        t = plate("HE BOUGHT", "THE PENCILS.", accent_last=True)
        t.scale(0.96).set_opacity(0)
        self.add(t)
        self.play(t.animate.set_opacity(1).scale(1.02), run_time=0.7, rate_func=smooth)
        self.play(t.animate.scale(1.055), halo.animate.scale(1.12),
                  run_time=2.6, rate_func=linear)
        self.play(t.animate.set_opacity(0).shift(UP * 0.22), run_time=0.6, rate_func=rush_into)


class Title(Scene):
    """تیترِ کانال — تک‌کلمهٔ درشت با خطِ زیرِ نازک."""
    def construct(self):
        word = Text("1 MINUTE", font="DejaVu Sans", weight=BOLD, color=INK).scale(1.5)
        rule = Line(LEFT * 2.4, RIGHT * 2.4, stroke_width=1.6,
                    color=AMBER).set_opacity(0.0)
        rule.next_to(word, DOWN, buff=0.55)
        sub = Text("AN ANIMATED SHORT FILM", font="DejaVu Sans",
                   color=DIM).scale(0.30).next_to(rule, DOWN, buff=0.34)

        self.play(FadeIn(word, shift=UP * 0.15), run_time=0.9, rate_func=smooth)
        self.play(Create(rule), FadeIn(sub), run_time=0.8)
        self.play(word.animate.scale(1.04), run_time=2.4, rate_func=linear)


class EndCard(Scene):
    """کارت پایانی: یک جملهٔ قصاری + رده‌بندی."""
    def construct(self):
        a = plate("READY IS NOT", "A FEELING.", accent_last=True, size=0.58)
        b = Text("IT'S THE SECOND LINE.", font="DejaVu Sans", weight=BOLD,
                 color=INK).scale(0.52)
        b.next_to(a, DOWN, buff=0.62).align_to(a, LEFT)
        tag = Text("2D ANIMATED SHORT · STYLE SAMPLE · NO NARRATION",
                   font="DejaVu Sans", color=DIM).scale(0.22)
        tag.next_to(b, DOWN, buff=0.90).align_to(a, LEFT)

        self.play(FadeIn(a, shift=UP * 0.12), run_time=0.8)
        self.play(FadeIn(b, shift=UP * 0.12), run_time=0.8)
        self.play(FadeIn(tag), run_time=0.6)
        self.wait(3.0)
