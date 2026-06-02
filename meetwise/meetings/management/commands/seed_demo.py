from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from meetings.models import Meeting, MeetingMinutes
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed demo data for MeetWise'

    def handle(self, *args, **kwargs):
        # Create users
        admin, _ = User.objects.get_or_create(username='admin', defaults={
            'first_name': 'Alex', 'last_name': 'Morgan',
            'email': 'alex@company.com', 'is_staff': True, 'is_superuser': True
        })
        admin.set_password('admin123')
        admin.save()

        sarah, _ = User.objects.get_or_create(username='sarah', defaults={
            'first_name': 'Sarah', 'last_name': 'Chen',
            'email': 'sarah@company.com'
        })
        sarah.set_password('sarah123')
        sarah.save()

        james, _ = User.objects.get_or_create(username='james', defaults={
            'first_name': 'James', 'last_name': 'Park',
            'email': 'james@company.com'
        })
        james.set_password('james123')
        james.save()

        now = timezone.now()

        # Upcoming meeting
        m1, created = Meeting.objects.get_or_create(
            title='Q4 Strategy Review',
            defaults={
                'description': 'Quarterly review of strategic goals and roadmap for Q4.',
                'organizer': admin,
                'scheduled_at': now + timedelta(hours=2),
                'duration_minutes': 60,
                'status': 'scheduled',
                'agenda': 'Review Q3 performance metrics\nAlign on Q4 priorities\nBudget allocation discussion\nTeam capacity planning\nAOB',
            }
        )
        if created:
            m1.attendees.set([sarah, james])

        # In-progress meeting
        m2, created = Meeting.objects.get_or_create(
            title='Product Design Sync',
            defaults={
                'description': 'Weekly design sync with the product and engineering teams.',
                'organizer': sarah,
                'scheduled_at': now - timedelta(minutes=15),
                'duration_minutes': 45,
                'status': 'in_progress',
                'agenda': 'Sprint review\nUI feedback on new dashboard\nHandoff checklist\nNext sprint planning',
            }
        )
        if created:
            m2.attendees.set([admin, james])

        # Completed with minutes
        m3, created = Meeting.objects.get_or_create(
            title='Engineering Standup',
            defaults={
                'description': 'Daily engineering standup.',
                'organizer': james,
                'scheduled_at': now - timedelta(days=1, hours=3),
                'duration_minutes': 15,
                'status': 'completed',
                'agenda': 'What did you do yesterday?\nWhat are you doing today?\nAny blockers?',
            }
        )
        if created:
            m3.attendees.set([admin, sarah])
            MeetingMinutes.objects.create(
                meeting=m3,
                recorded_by=james,
                content=(
                    'James completed the authentication refactor and pushed to staging. '
                    'Sarah finished the new chart components. Alex reviewed and approved the '
                    'API contract changes. No major blockers reported.'
                ),
                decisions='Agreed to merge authentication changes to main after QA sign-off.',
                action_items=(
                    'James — Write unit tests for auth module by Thursday\n'
                    'Sarah — Share component library updates in Figma\n'
                    'Alex — Schedule QA review session for Friday'
                )
            )

        # Another upcoming meeting
        m4, created = Meeting.objects.get_or_create(
            title='Client Onboarding — Acme Corp',
            defaults={
                'description': 'Kickoff call with Acme Corp to walk through onboarding process.',
                'organizer': admin,
                'scheduled_at': now + timedelta(days=1, hours=4),
                'duration_minutes': 90,
                'status': 'scheduled',
                'agenda': 'Introductions\nProject scope walkthrough\nTimeline and milestones\nAccess provisioning\nNext steps and Q&A',
            }
        )
        if created:
            m4.attendees.set([sarah])

        self.stdout.write(self.style.SUCCESS(
            '\n✓ Demo data seeded successfully!\n'
            '\nLogin credentials:\n'
            '  admin  / admin123  (superuser)\n'
            '  sarah  / sarah123\n'
            '  james  / james123\n'
        ))
