from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('scheduled_at', models.DateTimeField()),
                ('duration_minutes', models.PositiveIntegerField(default=60)),
                ('status', models.CharField(
                    choices=[
                        ('scheduled', 'Scheduled'),
                        ('in_progress', 'In Progress'),
                        ('completed', 'Completed'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='scheduled',
                    max_length=20,
                )),
                ('room_code', models.CharField(blank=True, max_length=64, unique=True)),
                ('agenda', models.TextField(blank=True, help_text='Meeting agenda items, one per line')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organizer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='organized_meetings',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('attendees', models.ManyToManyField(
                    blank=True,
                    related_name='attending_meetings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-scheduled_at'],
            },
        ),
        migrations.CreateModel(
            name='MeetingMinutes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True)),
                ('action_items', models.TextField(blank=True, help_text='Action items, one per line')),
                ('decisions', models.TextField(blank=True, help_text='Key decisions made')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('meeting', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='minutes',
                    to='meetings.meeting',
                )),
                ('recorded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
