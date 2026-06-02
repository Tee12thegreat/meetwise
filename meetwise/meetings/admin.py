from django.contrib import admin
from .models import Meeting, MeetingMinutes


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'scheduled_at', 'status', 'attendee_count']
    list_filter = ['status', 'scheduled_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'room_code', 'created_at', 'updated_at']
    filter_horizontal = ['attendees']


@admin.register(MeetingMinutes)
class MeetingMinutesAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'recorded_by', 'updated_at']
    search_fields = ['meeting__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
