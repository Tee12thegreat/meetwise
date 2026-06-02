from django.db import models
from django.contrib.auth.models import User
import uuid


class Meeting(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_meetings')
    attendees = models.ManyToManyField(User, related_name='attending_meetings', blank=True)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    room_code = models.CharField(max_length=64, unique=True, blank=True)
    agenda = models.TextField(blank=True, help_text="Meeting agenda items, one per line")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = f"meetwise-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    @property
    def agenda_items(self):
        return [item.strip() for item in self.agenda.split('\n') if item.strip()]

    @property
    def attendee_count(self):
        return self.attendees.count()


class MeetingMinutes(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='minutes')
    content = models.TextField(blank=True)
    action_items = models.TextField(blank=True, help_text="Action items, one per line")
    decisions = models.TextField(blank=True, help_text="Key decisions made")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Minutes: {self.meeting.title}"

    @property
    def action_item_list(self):
        return [item.strip() for item in self.action_items.split('\n') if item.strip()]
