# =============================================================================
# Time / Stamina System
# -----------------------------------------------------------------------------
# - Default action drains 20 stamina (4 actions per hour at base 80 stamina).
# - Max stamina is upgradable: max = base_stamina + Agility * 5.
# - When stamina hits 0 (or below), one in-game hour passes and stamina refills.
# =============================================================================

default base_stamina = 80
default stamina = 80
default time = 8   # Starting hour (24h, 0-23). 8 = 8 AM.
default day = 1
default _pending_stamina_cost = 0
default stamina_cost_multiplier = 1.0

# -----------------------------------------------------------------------------
# Hour-advance hooks. Other systems (mood decay, world events, NPC schedules)
# can subscribe with `on_hour_advance(fn)` - each fn(hours_advanced) is called
# every time advance_hour() runs.
# Lives at init time (not `default`) because the listener list is rebuilt
# each init pass and shouldn't be saved (functions aren't picklable).
# -----------------------------------------------------------------------------
init python:

    _hour_listeners = []

    def on_hour_advance(fn):
        if fn not in _hour_listeners:
            _hour_listeners.append(fn)
        return fn

    def get_max_stamina():
        try:
            agi = Agility
        except NameError:
            agi = 0
        return base_stamina + agi * 5

    def convert_to_12hr_format(t):
        if t == 0:
            return "12 AM"
        if t == 12:
            return "12 PM"
        if t < 12:
            return "%d AM" % t
        return "%d PM" % (t - 12)

    def weekday_name(d=None):
        if d is None:
            d = day
        names = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        return names[(int(d) - 1) % len(names)]

    def advance_hour(hours=1, force=False):
        global time, day
        if not force:
            try:
                if not system_enabled("time") or not game_action_allowed("time"):
                    renpy.notify(time_sensitive_lock_message())
                    return False
            except Exception:
                pass
        time += hours
        prev_day = day
        while time >= 24:
            time -= 24
            day += 1
        for cb in list(_hour_listeners):
            try:
                cb(hours)
            except Exception as _e:
                renpy.log("hour listener error: %r" % _e)
        try:
            emit("hour_advanced", hours)
            if day != prev_day:
                emit("day_advanced", day)
        except NameError:
            pass
        return True

    def set_stamina_cost_multiplier(value=1.0):
        global stamina_cost_multiplier
        try:
            stamina_cost_multiplier = max(0.0, float(value))
        except Exception:
            stamina_cost_multiplier = 1.0
        return stamina_cost_multiplier

    def reset_stamina_cost_multiplier():
        return set_stamina_cost_multiplier(1.0)

    def adjusted_stamina_cost(amount):
        try:
            amount = int(amount or 0)
        except Exception:
            amount = 0
        if amount <= 0:
            return 0
        try:
            return max(1, int(round(amount * float(stamina_cost_multiplier))))
        except Exception:
            return amount

    def decrease_stamina(amount=20):
        global stamina
        try:
            if not system_enabled("stamina") or not game_action_allowed("stamina"):
                return
        except Exception:
            pass
        amount = adjusted_stamina_cost(amount)
        if amount <= 0:
            return
        stamina -= amount
        max_s = get_max_stamina()
        if stamina <= 0:
            stamina = 0
            advance_hour(1, force=True)
            stamina = max_s
        if stamina > max_s:
            stamina = max_s

    def queue_stamina_cost(amount=20):
        global _pending_stamina_cost
        try:
            if not system_enabled("stamina") or not game_action_allowed("stamina"):
                return
        except Exception:
            pass
        amount = int(amount or 0)
        if amount > 0:
            _pending_stamina_cost += amount

    def flush_stamina_cost():
        global _pending_stamina_cost
        if _pending_stamina_cost <= 0:
            return
        cost = _pending_stamina_cost
        _pending_stamina_cost = 0
        decrease_stamina(cost)

    def refill_stamina():
        global stamina
        stamina = get_max_stamina()

    def can_skip_time():
        try:
            return system_enabled("time") and game_action_allowed("time")
        except Exception:
            return True

    def sleep_until_morning():
        if not can_skip_time():
            renpy.notify(time_sensitive_lock_message())
            return False
        hours = (24 - time) + time_skip_wake_hour if time >= time_skip_wake_hour else time_skip_wake_hour - time
        advanced = advance_hour(hours, force=True)
        refill_stamina()
        return advanced

    def skip_hour():
        if not can_skip_time():
            renpy.notify(time_sensitive_lock_message())
            return False
        if time_skip_sleep_hour <= time < time_skip_wake_hour:
            return sleep_until_morning()
        advanced = advance_hour(1, force=True)
        refill_stamina()
        return advanced
