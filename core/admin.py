from django.contrib import admin
from .models import Subject, Module, SubModule, StudySession

admin.site.register(Subject)
admin.site.register(Module)
admin.site.register(SubModule)
admin.site.register(StudySession)