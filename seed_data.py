import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studytracker.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Subject, Module, SubModule, StudySession
from django.utils import timezone
from datetime import timedelta
from dotenv import load_dotenv
import random

load_dotenv()

# ── Config ──────────────────────────────────────────────
OVERRIDE_TODAY    = True
BEGIN_TIME_24H    = 8
END_TIME_24H      = 20
MAX_SESSION_HOURS = 2.0
VARIATION         = 0.25
BREAK_RATIO       = 0.30

# ── User ────────────────────────────────────────────────
username = os.environ.get('SEED_USERNAME')
user = User.objects.get(username=username)
print(f"Seeding for: {user.username}")

# ── Seed helper ─────────────────────────────────────────
def seed_items(model, names, **parent):
    """
    Creates (or gets) a list of named items under a given parent.
    Returns list of the created/fetched objects.
    """
    items = []
    for name in names:
        obj, created = model.objects.get_or_create(name=name, **parent)
        items.append(obj)
        status = "created" if created else "exists"
        print(f"  [{status}] {model.__name__}: {name}")
    return items

# ── Seed structure ───────────────────────────────────────
print("\nSeeding subjects...")
subjects = seed_items(Subject, ["Computer Science", "Mathematics", "Physics"], user=user)

cs, maths, physics = subjects[0], subjects[1], subjects[2]

print("\nSeeding modules...")
cs_modules     = seed_items(Module, ["Algorithms", "Databases", "Networks"], subject=cs)
maths_modules  = seed_items(Module, ["Calculus", "Statistics"],              subject=maths)
physics_modules= seed_items(Module, ["Mechanics", "Thermodynamics"],         subject=physics)

print("\nSeeding submodules...")
seed_items(SubModule, ["Sorting", "Searching", "Graph Theory"], module=cs_modules[0])
seed_items(SubModule, ["SQL", "ORM", "Indexing"],               module=cs_modules[1])
seed_items(SubModule, ["TCP/IP", "DNS"],                        module=cs_modules[2])

# ── Override today's data ────────────────────────────────
today = timezone.now().date()
if OVERRIDE_TODAY:
    deleted, _ = StudySession.objects.filter(user=user, started_at__date=today).delete()
    print(f"\nDeleted {deleted} session(s) for today.")

# ── Setup ────────────────────────────────────────────────
user_subjects = list(Subject.objects.filter(user=user))
random.shuffle(user_subjects)
TOTAL_SUBJECTS = len(user_subjects)

if TOTAL_SUBJECTS == 0:
    print("No subjects found. Exiting.")
    exit()

total_time  = END_TIME_24H - BEGIN_TIME_24H
break_pool  = total_time * BREAK_RATIO
study_pool  = total_time - break_pool
avg_study   = min(study_pool / TOTAL_SUBJECTS, MAX_SESSION_HOURS)
num_breaks  = TOTAL_SUBJECTS - 1
avg_break   = (break_pool / num_breaks) if num_breaks > 0 else 0

# ── Section subjects ─────────────────────────────────────
above_s = TOTAL_SUBJECTS // 2
below_s = TOTAL_SUBJECTS // 2
avg_s   = TOTAL_SUBJECTS % 2
subject_types = ["above"] * above_s + ["below"] * below_s + ["avg"] * avg_s
random.shuffle(subject_types)

# ── Section breaks ───────────────────────────────────────
if num_breaks > 0:
    break_types = ["above"] * (num_breaks // 2) + ["below"] * (num_breaks // 2) + ["avg"] * (num_breaks % 2)
    random.shuffle(break_types)
else:
    break_types = []

# ── Build schedule ───────────────────────────────────────
schedule = []
for i in range(TOTAL_SUBJECTS):
    schedule.append(("subject", subject_types[i]))
    if i < num_breaks:
        schedule.append(("break", break_types[i]))

# ── Duration calculator ──────────────────────────────────
def get_duration(avg, slot_type, surplus):
    base = avg * (1 + VARIATION if slot_type == "above" else (1 - VARIATION if slot_type == "below" else 1))
    return max(0.1, base + (-surplus * 0.1))

# ── Create sessions ──────────────────────────────────────
current_time  = float(BEGIN_TIME_24H)
surplus_study = 0.0
surplus_break = 0.0
subject_index = 0

print("\nSchedule:")
for slot_kind, slot_type in schedule:
    if slot_kind == "subject":
        subject    = user_subjects[subject_index]
        duration_h = get_duration(avg_study, slot_type, surplus_study)
        surplus_study += (duration_h - avg_study)

        start_h = int(current_time)
        start_m = int((current_time % 1) * 60)
        end_t   = current_time + duration_h
        end_h   = int(end_t)
        end_m   = int((end_t % 1) * 60)

        started_at = timezone.now().replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        ended_at   = timezone.now().replace(hour=end_h,   minute=end_m,   second=0, microsecond=0)

        StudySession.objects.create(
            user=user,
            subject=subject,
            duration_seconds=int(duration_h * 3600),
            started_at=started_at,
            ended_at=ended_at,
        )
        print(f"  {subject.name}: {start_h:02d}:{start_m:02d} → {end_h:02d}:{end_m:02d} ({slot_type})")
        current_time = end_t
        subject_index += 1
    else:
        break_h = get_duration(avg_break, slot_type, surplus_break)
        surplus_break += (break_h - avg_break)
        print(f"  [break {slot_type}: {break_h * 60:.0f} mins]")
        current_time += break_h

print(f"\nDay ends at: {current_time:.2f}h (target {END_TIME_24H}h)")
print("Done.")