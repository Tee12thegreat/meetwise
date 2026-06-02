from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from meetings import views as meeting_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='meetings/login.html'), name='login'),
    path('accounts/logout/', meeting_views.logout_view, name='logout'),
    path('', include('meetings.urls')),
]
