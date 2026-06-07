# =============================================================================
# Misc/Text_Effects.rpy - opt-in custom text tags
# -----------------------------------------------------------------------------
# Drop-in animated text effects that compose with normal Ren'Py tags. Pure
# additive: doesn't change anything until you actually use a tag.
#
# Tags shipped:
#
#   {bt}...{/bt}            - bouncing wave (good for excitement)
#   {bt=8}                  - amplitude in pixels (default 6)
#
#   {sc}...{/sc}            - shaky / scared text
#   {sc=4}                  - jitter range in pixels (default 3)
#
#   {fi}...{/fi}            - per-letter fade-in slide (calm, dramatic)
#   {fi=0.6}                - fade time per letter in seconds
#
#   {pulse}...{/pulse}      - color/alpha pulse for emphasis
#
#   {glitch}...{/glitch}    - rapid color/style flicker; respects accessibility
#                             toggle persistent.text_glitch_disabled.
#
#   You can MIX any of these inside a normal say-line. Example:
#       a "I'm fine. {sc=4}I'm fine. I'm fine.{/sc}"
#       a "{fi}It's good to see you again.{/fi}"
#       a "{bt=10}Surprise!{/bt}"
#
# Disable everything: set text_effects_enabled = False.
# Disable just the heaviest one: persistent.text_glitch_disabled = True.
# =============================================================================


default persistent.text_glitch_disabled = False
define  text_effects_enabled = True


init python:

    import math as _math
    import random as _trandom


    class _BouncyText(renpy.Displayable):
        def __init__(self, child, idx, amp=6.0, speed=4.0, **kw):
            super(_BouncyText, self).__init__(**kw)
            self.child = child
            self.idx   = idx
            self.amp   = float(amp)
            self.speed = float(speed)

        def render(self, w, h, st, at):
            offset = _math.sin(self.speed * st + self.idx * 0.4) * self.amp
            cr = renpy.render(self.child, w, h, st, at)
            cw, ch = cr.get_size()
            rv = renpy.Render(cw, ch)
            rv.subpixel_blit(cr, (0, offset))
            renpy.redraw(self, 0)
            return rv

        def visit(self):
            return [self.child]


    class _ShakyText(renpy.Displayable):
        def __init__(self, child, jitter=3.0, **kw):
            super(_ShakyText, self).__init__(**kw)
            self.child = child
            self.jitter = float(jitter)

        def render(self, w, h, st, at):
            jx = (_trandom.random() - 0.5) * self.jitter
            jy = (_trandom.random() - 0.5) * self.jitter
            cr = renpy.render(self.child, w, h, st, at)
            cw, ch = cr.get_size()
            rv = renpy.Render(cw, ch)
            rv.subpixel_blit(cr, (jx, jy))
            renpy.redraw(self, 0)
            return rv

        def visit(self):
            return [self.child]


    class _FadeInText(renpy.Displayable):
        def __init__(self, child, idx, fade_time=0.4, slide=40, **kw):
            super(_FadeInText, self).__init__(**kw)
            self.child = child
            self.idx   = idx
            self.fade_time = float(fade_time)
            self.slide = float(slide)

        def render(self, w, h, st, at):
            cps = 1.0 / max(0.0001, preferences.text_cps) if preferences.text_cps else 0.0
            delay = self.idx * cps
            t = max(0.0, st - delay)
            a  = min(1.0, t / max(0.0001, self.fade_time))
            xo = max(0.0, self.slide * (1.0 - a))
            tr = Transform(child=self.child, alpha=a)
            cr = renpy.render(tr, w, h, st, at)
            cw, ch = cr.get_size()
            rv = renpy.Render(cw, ch)
            rv.subpixel_blit(cr, (xo, 0))
            if t < self.fade_time:
                renpy.redraw(self, 0)
            return rv

        def visit(self):
            return [self.child]


    class _PulseText(renpy.Displayable):
        def __init__(self, child, **kw):
            super(_PulseText, self).__init__(**kw)
            self.child = child

        def render(self, w, h, st, at):
            a = 0.6 + 0.4 * (0.5 + 0.5 * _math.sin(st * 4.0))
            tr = Transform(child=self.child, alpha=a)
            cr = renpy.render(tr, w, h, st, at)
            cw, ch = cr.get_size()
            rv = renpy.Render(cw, ch)
            rv.blit(cr, (0, 0))
            renpy.redraw(self, 0)
            return rv

        def visit(self):
            return [self.child]


    class _GlitchText(renpy.Displayable):
        _palette = ["#ffffff", "#ff5fa2", "#7fdf9c", "#ffd27a", "#7fb3ff"]

        def __init__(self, raw, **kw):
            super(_GlitchText, self).__init__(**kw)
            self.raw = raw
            self.child = renpy.text.text.Text(raw)

        def render(self, w, h, st, at):
            if persistent.text_glitch_disabled:
                self.child.set_text(self.raw)
            else:
                col = _trandom.choice(self._palette)
                self.child.set_text("{color=%s}%s{/color}" % (col, self.raw))
            cr = renpy.render(self.child, w, h, st, at)
            cw, ch = cr.get_size()
            rv = renpy.Render(cw, ch)
            rv.subpixel_blit(cr, (0, 0))
            renpy.redraw(self, 0)
            return rv

        def visit(self):
            return [self.child]


    # ---- text-tag wiring ---------------------------------------------------
    def _wrap_each_char(contents, factory):
        out = []
        idx = 0
        for kind, text in contents:
            if kind == renpy.TEXT_TEXT and text_effects_enabled:
                for ch in text:
                    if ch == ' ':
                        out.append((renpy.TEXT_TEXT, ch))
                        continue
                    out.append((renpy.TEXT_DISPLAYABLE, factory(renpy.text.text.Text(ch), idx)))
                    idx += 1
            else:
                out.append((kind, text))
        return out

    def _bt_tag(tag, arg, contents):
        amp = 6.0
        if arg:
            try: amp = float(arg)
            except: pass
        return _wrap_each_char(contents, lambda t, i: _BouncyText(t, i, amp=amp))

    def _sc_tag(tag, arg, contents):
        jitter = 3.0
        if arg:
            try: jitter = float(arg)
            except: pass
        return _wrap_each_char(contents, lambda t, i: _ShakyText(t, jitter=jitter))

    def _fi_tag(tag, arg, contents):
        ft = 0.4
        if arg:
            try: ft = float(arg)
            except: pass
        return _wrap_each_char(contents, lambda t, i: _FadeInText(t, i, fade_time=ft))

    def _pulse_tag(tag, arg, contents):
        out = []
        for kind, text in contents:
            if kind == renpy.TEXT_TEXT and text_effects_enabled:
                out.append((renpy.TEXT_DISPLAYABLE, _PulseText(renpy.text.text.Text(text))))
            else:
                out.append((kind, text))
        return out

    def _glitch_tag(tag, arg, contents):
        out = []
        for kind, text in contents:
            if kind == renpy.TEXT_TEXT and text_effects_enabled:
                out.append((renpy.TEXT_DISPLAYABLE, _GlitchText(text)))
            else:
                out.append((kind, text))
        return out


    config.custom_text_tags = config.custom_text_tags or {}
    config.custom_text_tags["bt"]     = _bt_tag
    config.custom_text_tags["sc"]     = _sc_tag
    config.custom_text_tags["fi"]     = _fi_tag
    config.custom_text_tags["pulse"]  = _pulse_tag
    config.custom_text_tags["glitch"] = _glitch_tag
