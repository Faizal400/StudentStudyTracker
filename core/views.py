from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.utils import timezone
from .forms import RegisterForm
from .models import Subject
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Subject, Module, SubModule, StudySession
from django.db.models import Sum, Count
from datetime import timedelta, date
from collections import defaultdict


@login_required
def index(request):
    subjects = Subject.objects.filter(user=request.user).prefetch_related("modules__submodules")
    return render(request, "index.html", {"subjects": subjects})

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the user in right away
            return redirect("focus")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})




@login_required
@ensure_csrf_cookie
def focus_view(request):
    subjects = Subject.objects.filter(user=request.user).order_by("name") #Subject.objects.filter(user=request.user).prefetch_related("modules__submodules")
    return render(request, "focus.html", {"subjects": subjects})

@login_required
def insights_view(request):
    subjects = Subject.objects.filter(user=request.user).order_by("name")

    qs = StudySession.objects.filter(user=request.user)

    # Insight 1: Total Time
    total_seconds = qs.aggregate(total=Sum("duration_seconds"))["total"] or 0
    total_hours = round(total_seconds / 3600.0, 2)

    # Insight 2: Last 7 days time
    week_ago = timezone.now() - timedelta(days=7)
    week_seconds = (
        qs
        .filter(created_at__gte=week_ago)
        .aggregate(total=Sum("duration_seconds"))["total"] or 0
    )
    week_hours = round(week_seconds / 3600.0, 2)

    # Insight 3: By subject breakdown
    by_subject = (
        qs
        .filter(subject__isnull=False)
        .values("subject__name")
        .annotate(
            total_seconds=Sum("duration_seconds"),
            sessions=Count("id"),
        )
        .order_by("-total_seconds")
    )
    by_subject = list(by_subject)
    for row in by_subject:
        row["total_hours"] = round((row["total_seconds"] or 0) / 3600.0, 2)

    # Insight 4: Current streak
    session_dates = sorted(set(
        session.started_at.date() for session in qs
    ))

    if not session_dates:
        session_streak = 0
    else:
        session_streak = 1
        previous = session_dates[0]

        for session_date in session_dates[1:]:
            gap = session_date - previous
            if gap.days == 1:
                session_streak += 1
            else:
                session_streak = 1
            previous = session_date

        today = date.today()
        if (today - session_dates[-1]).days > 1:
            session_streak = 0
    # Insight 5: Best day of the week (0=Monday, 6=Sunday)
    day_names = ["Monday", "Tuesday", "Wednesday","Thursday", "Friday", "Saturday", "Sunday"]
    day_seconds = defaultdict(int)  # any missing key defaults to 0
    for session in qs:
        day = session.started_at.weekday()  # 0-6
        day_seconds[day] += session.duration_seconds
    best_day = max(day_seconds, key=day_seconds.get) if day_seconds else None
    best_day_name = day_names[best_day] if best_day is not None else "N/A"
    # Insight 6: Total sessions + average length
    total_sessions = qs.count()
    avg_session_minutes = round((total_seconds / total_sessions) / 60, 1) if total_sessions > 0 else 0
    # Insight 7: 24 hour clock
    today = timezone.now().date()
    today_sessions = qs.filter(started_at__date=today).select_related("subject")

    clock_data = []
    for session in today_sessions:
        clock_data.append({
            "subject": session.subject.name if session.subject else "General",
            "start_minutes": session.started_at.hour * 60 + session.started_at.minute,
            "end_minutes": session.ended_at.hour * 60 + session.ended_at.minute,
        })
    
    context = {
        "subjects": subjects,
        "all_time_hours": total_hours,
        "week_hours": week_hours,
        "by_subject": by_subject,
        "session_streak": session_streak,
        "best_day": best_day_name,
        "total_sessions": total_sessions,
        "avg_session_minutes": avg_session_minutes,
        "clock_data": json.dumps(clock_data),
    }
    return render(request, "insights.html", context)

# API: ADD OR DELETE [SUBJECTS // MODULES // SUB MODULES]
def isDataValid(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        return True, data
    except json.JSONDecodeError:
        return False, JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
def isNameandDatatypeValid(data):
    """
    3 dataTypes:
    - Subject
    - Module
    - Sub Module
    Checks if any of the 3 (dataType, name, parentId) are missing or invalid. 
    ParentId is only needed for module and submodule, but we can ignore it for subject since it won't be used.
    """
    name = (data.get("name") or "").strip()
    dataTypeName = (data.get("dataType") or "").strip()
    ParentId = (data.get("ParentId") or "").strip()
    if not dataTypeName:
        return False, JsonResponse({"ok": False, "error": f"dataTypeName cannot be empty."}, status=400), "None", "None"
    if not name:
        return False, JsonResponse({"ok": False, "error": f"{dataTypeName} name cannot be empty."}, status=400), "None", "None"
    if len(name) > 80:
        return False, JsonResponse({"ok": False, "error": f"{dataTypeName} name too long (max 80)."}, status=400), "None", "None"
    return True, name, dataTypeName, ParentId

def getJsonResponse(dataTypeName, createdData, created, parent_id=None):
    data = {
        "ok": True,
        "type": dataTypeName,  # "subject" | "module" | "submodule"
        "item": {"id": createdData.id, "name": createdData.name},
        "created": created,
        "parent_id": parent_id
    }
    return JsonResponse(data)


@login_required
@require_POST
def api_add_subject(request):
    DataValid, data = isDataValid(request)
    if not DataValid:
        return data

    validNaming, name, dataType, ParentId = isNameandDatatypeValid(data)
    if not validNaming:
        return name # name in this case is a JsonResponse
    # Avoid duplicates per user
    dataTypes = ["subject", "module", "submodule"]
    if dataType in dataTypes:
        if dataType == "subject":
            subject, created = Subject.objects.get_or_create(user=request.user, name=name)
            return getJsonResponse(dataTypeName= dataType, createdData= subject, created=created)
        elif dataType == "module":
            try:
                parent_subject = Subject.objects.get(id=ParentId, user=request.user)
            except Subject.DoesNotExist:
                return JsonResponse({"ok": False, "error": "Parent subject not found."}, status=404)
            module, created = Module.objects.get_or_create(subject=parent_subject, name=name)
            return getJsonResponse(dataTypeName=dataType, createdData= module, created=created, parent_id=ParentId)
        elif dataType == "submodule":
            try:
                parent_module = Module.objects.get(id=ParentId, subject__user=request.user)
            except Module.DoesNotExist:
                return JsonResponse({"ok": False, "error": "Parent module not found."}, status=404)
            submodule, created = SubModule.objects.get_or_create(module=parent_module, name=name)
            return getJsonResponse(dataTypeName=dataType, createdData=submodule, created=created, parent_id=ParentId)
    return JsonResponse({"ok": False, "error": "Invalid dataType."}, status=400)

@login_required
@require_POST
def api_delete_subject(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
    option_id = data.get("id")
    option_type = data.get("type") # subject, module, or submodule
    if option_type not in ["subject", "module", "submodule"]:
        return JsonResponse({"ok": False, "error": "Invalid type."}, status=400)
    try:
        isInteger = int(option_id)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": f"Invalid {option_type} id."}, status=400)
    if option_type == "subject":
        subject_id = option_id
        deleted_count, _ = Subject.objects.filter(id=subject_id, user=request.user).delete()
        if deleted_count == 0:
            return JsonResponse({"ok": False, "error": f"{option_type} not found."}, status=404)
    elif option_type == "module":
        deleted_count, _ = Module.objects.filter(id=option_id, subject__user=request.user).delete()
        if deleted_count == 0:
            return JsonResponse({"ok": False, "error": f"{option_type} not found."}, status=404)
    elif option_type == "submodule":
        deleted_count, _ = SubModule.objects.filter(id=option_id, module__subject__user=request.user).delete()
        if deleted_count == 0:
            return JsonResponse({"ok": False, "error": f"{option_type} not found."}, status=404)
    return JsonResponse({"ok": True, "deleted_id": option_id})

def create_session_object(user, session_type, the_object, duration_seconds):
    ended_at = timezone.now()
    started_at = ended_at - timedelta(seconds=duration_seconds)
    kwargs = {
        "user": user,
        "duration_seconds": duration_seconds,
        "started_at": started_at, # simple since it doesn't consider tiny delays such as user clicking start and stop, or network time. We can improve later if needed.
        "ended_at": ended_at,
        session_type: the_object
    }
    session = StudySession.objects.create(**kwargs)
    return session

@login_required
@require_POST
def api_create_session(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
    session_type = data.get("session_type")
    duration_seconds = data.get("duration_seconds")

    # Validate duration
    try:
        duration_seconds = int(duration_seconds)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "duration_seconds must be an integer."}, status=400)

    if duration_seconds <= 0:
        return JsonResponse({"ok": False, "error": "Session duration must be > 0."}, status=400)

    # Validate subject belongs to this user
    item_id = data.get("item_id")
    if session_type == "subject":
        try:
            item_id = int(item_id)
            subject = Subject.objects.get(id=int(item_id), user=request.user)
        except (TypeError, ValueError, Subject.DoesNotExist):
            return JsonResponse({"ok": False, "error": "Invalid subject."}, status=400)
        session = create_session_object(user=request.user, session_type=session_type, the_object=subject, duration_seconds=duration_seconds)
    elif session_type == "module":
        try:
            module = Module.objects.get(id=int(item_id), subject__user=request.user)
        except (TypeError, ValueError, Module.DoesNotExist):
            return JsonResponse({"ok": False, "error": "Invalid module."}, status=400)
        session = create_session_object(user=request.user, session_type=session_type, the_object=module, duration_seconds=duration_seconds)
    elif session_type == "submodule":
        try:
            submodule = SubModule.objects.get(id=int(item_id), module__subject__user=request.user)
        except (TypeError, ValueError, SubModule.DoesNotExist):
            return JsonResponse({"ok": False, "error": "Invalid submodule."}, status=400)
        session = create_session_object(user=request.user, session_type=session_type, the_object=submodule, duration_seconds=duration_seconds)

    return JsonResponse({"ok": True, "session_id": session.id})
