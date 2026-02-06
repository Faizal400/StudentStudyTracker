from django.urls import  path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LowercaseAuthenticationForm


urlpatterns = [
    path('', views.index, name='index'),  # homepage
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html",authentication_form=LowercaseAuthenticationForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(template_name="registration/logout.html"), name="logout"),
    path("focus/", views.focus_view, name="focus"),
    path("api/subjects/add/", views.api_add_subject, name="api_add_subject"),
    path("api/subjects/delete/", views.api_delete_subject, name="api_delete_subject"),
    path("api/sessions/create/", views.api_create_session, name="api_create_session"),
    path("insights/", views.insights_view, name="insights"),

]