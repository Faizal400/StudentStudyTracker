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
from datetime import timedelta


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
    # Insight 1: Total Time
    qs = StudySession.objects.filter(user=request.user)
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
    context = {
        "subjects": subjects,
        "all_time_hours": total_hours,
        "week_hours": week_hours,
        "by_subject": by_subject,
    }
    return render(request, "insights.html", context)

def sendPrintStatement(message):
    #console.log(message)
    print(message)
# API: ADD OR DELETE [SUBJECTS // MODULES // SUB MODULES]
def isDataValid(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        return True, data
    except json.JSONDecodeError:
        sendPrintStatement("isDataValid - module creation not allowed, invalid JSON")
        return False, JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
def isNameandDatatypeValid(data):
    """
    3 dataTypes:
    - Subject
    - Module
    - Sub Module
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
def getJsonResponse(dataTypeName, createdData, created):
    """
    3 dataTypes:
    - Subject
    - Module
    - Sub Module
    """
    data = {
        "ok": True,
        dataTypeName: {"id": createdData.id, "name": createdData.name},
        "created": created
    }
    jsR = JsonResponse(data)
    sendPrintStatement(json.dumps(data, indent = 4))
    return jsR

@login_required
@require_POST
def api_add_subject(request):
    DataValid, data = isDataValid(request)
    sendPrintStatement(request.body)
    sendPrintStatement(json.dumps(data, indent = 4))
    if not isDataValid:
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
            parent_subject = Subject.objects.get(id=ParentId, user=request.user)
            module, created = Module.objects.get_or_create(subject=parent_subject, name=name)
            return getJsonResponse(dataTypeName=dataType, createdData= module, created=created)
        elif dataType == "submodule":
            parent_module = Module.objects.get(id=ParentId, subject__user=request.user)
            submodule, created = SubModule.objects.get_or_create(module=parent_module, name=name)
            return getJsonResponse(dataTypeName=dataType, createdData=submodule, created=created)

@login_required
@require_POST
def api_delete_subject(request):
    print("Delete API called")
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
    print(data)
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

@login_required
@require_POST
def api_create_session(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
    subject_id = data.get("subject_id")
    session_type = data.get("session_type")
    sendPrintStatement(json.dumps(data, indent = 4))
    print(f"Session Type: {session_type}")
    duration_seconds = data.get("duration_seconds")

    # Validate duration
    try:
        duration_seconds = int(duration_seconds)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "duration_seconds must be an integer."}, status=400)

    if duration_seconds <= 0:
        return JsonResponse({"ok": False, "error": "Session duration must be > 0."}, status=400)

    # Validate subject belongs to this user
    
    if session_type == "subject":
        try:
            subject_id = int(subject_id)
            subject = Subject.objects.get(id=subject_id, user=request.user)
        except (TypeError, ValueError, Subject.DoesNotExist):
            return JsonResponse({"ok": False, "error": "Invalid subject."}, status=400)
        session = StudySession.objects.create(
            user=request.user,
            subject=subject,
            duration_seconds=duration_seconds,
            started_at=timezone.now(),   # simple for now
            ended_at=timezone.now(),
            )
    elif session_type == "module":
        try:
            module_id = int(subject_id)
            module = Module.objects.get(id=module_id, subject__user=request.user)
        except (TypeError, ValueError, Module.DoesNotExist):
            return JsonResponse({"ok": False, "error": "Invalid module."}, status=400)
        session = StudySession.objects.create(
            user=request.user,
            module=module,
            duration_seconds=duration_seconds,
            started_at=timezone.now(),   # simple for now
            ended_at=timezone.now(),
            )
    elif session_type == "submodule":
        try:
            submodule_id = int(subject_id)
            submodule = SubModule.objects.get(id=submodule_id, module__subject__user=request.user)
        except (TypeError, ValueError, SubModule.DoesNotExist):
            return JsonResponse({"ok": False, "error": "Invalid submodule."}, status=400)
        session = StudySession.objects.create(
            user=request.user,
            submodule=submodule,
            duration_seconds=duration_seconds,
            started_at=timezone.now(),   # simple for now
            ended_at=timezone.now(),
            )

    return JsonResponse({"ok": True, "session_id": session.id})
