from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/schedule/', views.meeting_schedule, name='meeting_schedule'),
    path('meetings/join/', views.join_meeting, name='join_meeting'),
    path('meetings/<uuid:pk>/', views.meeting_detail, name='meeting_detail'),
    path('meetings/<uuid:pk>/start/', views.meeting_start, name='meeting_start'),
    path('meetings/<uuid:pk>/conference/', views.meeting_conference, name='meeting_conference'),
    path('meetings/<uuid:pk>/end/', views.meeting_end, name='meeting_end'),
    path('meetings/<uuid:pk>/minutes/', views.meeting_minutes, name='meeting_minutes'),
    path('meetings/<uuid:pk>/cancel/', views.meeting_cancel, name='meeting_cancel'),

    # Calendar export
    path('meetings/<uuid:pk>/export.ics', views.export_ical, name='export_ical'),

    # AI endpoints
    path('meetings/<uuid:pk>/ai/minutes/', views.ai_generate_minutes, name='ai_generate_minutes'),
    path('meetings/ai/agenda/', views.ai_suggest_agenda, name='ai_suggest_agenda'),

    # Transcription (local Faster-Whisper model)
    path('meetings/<uuid:pk>/transcribe/', views.transcribe_audio, name='transcribe_audio'),
]
