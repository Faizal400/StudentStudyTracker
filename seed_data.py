import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studytracker.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Subject, StudySession
from django.utils import timezone
from datetime import timedelta
import random
from dotenv import load_dotenv

load_dotenv()

# ||| Config  ----------------------------------------------
OVERRIDE_TODAY    = True    # wipe today's sessions before seeding
BEGIN_TIME_24H    = 8       # 8am
END_TIME_24H      = 20      # 8pm
MAX_SESSION_HOURS = 2.0     # cap per session (handles 1–2 subject edge case)
VARIATION         = 0.25    # plus or minus 25% variation from avg
BREAK_RATIO       = 0.30    # 30% of total time reserved for breaks

# ||| User ----------------------------------------------
username = os.environ.get('SEED_USERNAME')
user = User.objects.get(username=username)
print(f"Seeding for: {user.username}")

# ||| Seed subjects if they don't exist ----------------------------------------------
Subject.objects.get_or_create(user=user, name="Computer Science")
Subject.objects.get_or_create(user=user, name="Mathematics")
Subject.objects.get_or_create(user=user, name="Physics")

# ||| Override today's data ----------------------------------------------
today = timezone.now().date()
if OVERRIDE_TODAY:
    deleted, _ = StudySession.objects.filter(user=user, started_at__date=today).delete()
    print(f"Deleted {deleted} session(s) for today.")

# ||| Setup ----------------------------------------------
user_subjects = list(Subject.objects.filter(user=user))
random.shuffle(user_subjects)
TOTAL_SUBJECTS = len(user_subjects)

if TOTAL_SUBJECTS == 0:
    print("No subjects found. Exiting.")
    exit()

total_time  = END_TIME_24H - BEGIN_TIME_24H             # hours
break_pool  = total_time * BREAK_RATIO                  # hours for breaks
study_pool  = total_time - break_pool                   # hours for study

# Cap avg to avoid unrealistic sessions with very few subjects
avg_study   = min(study_pool / TOTAL_SUBJECTS, MAX_SESSION_HOURS)
num_breaks  = TOTAL_SUBJECTS - 1
avg_break   = (break_pool / num_breaks) if num_breaks > 0 else 0

# ||| Section subjects: above / below / avg ----------------------------------------------
above_s = TOTAL_SUBJECTS // 2
below_s = TOTAL_SUBJECTS // 2
avg_s   = TOTAL_SUBJECTS % 2       # 1 if odd, 0 if even

subject_types = ["above"] * above_s + ["below"] * below_s + ["avg"] * avg_s
random.shuffle(subject_types)

# ||| Section breaks: above / below / avg ----------------------------------------------
if num_breaks > 0:
    above_b = num_breaks // 2
    below_b = num_breaks // 2
    avg_b   = num_breaks % 2
    break_types = ["above"] * above_b + ["below"] * below_b + ["avg"] * avg_b
    random.shuffle(break_types)
else:
    break_types = []

# ||| Build interleaved schedule ----------------------------------------------
# [subject, break, subject, break, ..., subject]
"""
Example:
[
    ("subject", "above"),
    ("break", "below"),
    ("subject", "below"),
    ("break", "avg"),
    ("subject", "avg"),
]
"""
schedule = []
for i in range(TOTAL_SUBJECTS):
    schedule.append(("subject", subject_types[i]))
    if i < num_breaks:
        schedule.append(("break", break_types[i]))

# ||| Duration calculator with surplus nudging ----------------------------------------------
def get_duration(avg, slot_type, surplus):
    if slot_type == "avg":
        base = avg
    elif slot_type == "above":
        base = avg * (1 + VARIATION)
    else:
        base = avg * (1 - VARIATION)
    # nudge back toward avg if surplus drifts too far
    nudge = -surplus * 0.1
    return max(0.1, base + nudge)

# ||| Loop & create sessions ----------------------------------------------
current_time   = float(BEGIN_TIME_24H)
surplus_study  = 0.0
surplus_break  = 0.0
subject_index  = 0

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

    else:  # break
        break_h = get_duration(avg_break, slot_type, surplus_break)
        surplus_break += (break_h - avg_break)
        print(f"  [break {slot_type}: {break_h * 60:.0f} mins]")
        current_time += break_h

print(f"\nDay ends at: {current_time:.2f}h (target {END_TIME_24H}h)")
print("Done.")