from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import threading

from .models import Meeting, MeetingMinutes
from .forms import MeetingForm, MinutesForm


# ─────────────────────────────────────────
# Auth
# ─────────────────────────────────────────

def logout_view(request):
    auth_logout(request)
    return redirect('login')


# ─────────────────────────────────────────
# Email — runs in background thread so it
# never blocks or crashes the request
# ─────────────────────────────────────────

def send_meeting_email(meeting, subject, template_name, extra_context=None):
    """
    Fire-and-forget email. Runs in a daemon thread so the view
    returns immediately whether email succeeds or fails.
    If email credentials are not configured, skips silently.
    """
    # Skip entirely if no email credentials configured
    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        return

    recipients = list(meeting.attendees.values_list('email', flat=True))
    if meeting.organizer.email and meeting.organizer.email not in recipients:
        recipients.append(meeting.organizer.email)
    recipients = [e for e in recipients if e]

    if not recipients:
        return

    context = {
        'meeting': meeting,
        'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
    }
    if extra_context:
        context.update(extra_context)

    def _send():
        try:
            import re
            html_body = render_to_string(template_name, context)
            plain_body = re.sub(r'<[^>]+>', '', html_body).strip()
            send_mail(
                subject=subject,
                message=plain_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@meetwise.app'),
                recipient_list=recipients,
                html_message=html_body,
                fail_silently=True,
            )
        except Exception:
            pass  # never crash the app over email

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# ─────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────

@login_required
def dashboard(request):
    now = timezone.now()
    upcoming = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user),
        scheduled_at__gte=now,
        status__in=['scheduled', 'in_progress']
    ).distinct()[:5]

    past = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user),
        scheduled_at__lt=now
    ).distinct()[:5]

    total_meetings = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user)
    ).distinct().count()

    return render(request, 'meetings/dashboard.html', {
        'upcoming': upcoming,
        'past': past,
        'total_meetings': total_meetings,
        'now': now,
    })


# ─────────────────────────────────────────
# Meeting list
# ─────────────────────────────────────────

@login_required
def meeting_list(request):
    meetings = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user)
    ).distinct()

    status_filter = request.GET.get('status', '')
    if status_filter:
        meetings = meetings.filter(status=status_filter)

    return render(request, 'meetings/meeting_list.html', {
        'meetings': meetings,
        'status_filter': status_filter,
    })


# ─────────────────────────────────────────
# Schedule
# ─────────────────────────────────────────

@login_required
def meeting_schedule(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.organizer = request.user
            meeting.save()
            form.save_m2m()

            # Email runs in background — will not block or crash this view
            send_meeting_email(
                meeting,
                subject=f'Meeting Invitation: {meeting.title}',
                template_name='meetings/email_invite.html',
            )

            messages.success(request, 'Meeting scheduled successfully.')
            return redirect('meeting_detail', pk=meeting.pk)
    else:
        form = MeetingForm()

    form.fields['attendees'].queryset = User.objects.exclude(pk=request.user.pk)
    return render(request, 'meetings/schedule.html', {'form': form})


# ─────────────────────────────────────────
# Detail
# ─────────────────────────────────────────

@login_required
def meeting_detail(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    try:
        minutes = meeting.minutes
    except MeetingMinutes.DoesNotExist:
        minutes = None

    return render(request, 'meetings/detail.html', {
        'meeting': meeting,
        'minutes': minutes,
    })


# ─────────────────────────────────────────
# Start / Conference / End
# ─────────────────────────────────────────

@login_required
def meeting_start(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if meeting.organizer == request.user and meeting.status == 'scheduled':
        meeting.status = 'in_progress'
        meeting.save()
        send_meeting_email(
            meeting,
            subject=f'Meeting Starting Now: {meeting.title}',
            template_name='meetings/email_starting.html',
        )
    return redirect('meeting_conference', pk=pk)


@login_required
def meeting_conference(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    return render(request, 'meetings/conference.html', {
        'meeting': meeting,
        'user_name': request.user.get_full_name() or request.user.username,
    })


@login_required
def meeting_end(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if meeting.organizer == request.user:
        meeting.status = 'completed'
        meeting.save()
        send_meeting_email(
            meeting,
            subject=f'Meeting Completed: {meeting.title}',
            template_name='meetings/email_completed.html',
        )
        messages.success(request, 'Meeting ended. Add minutes below.')
    return redirect('meeting_minutes', pk=pk)


# ─────────────────────────────────────────
# Minutes
# ─────────────────────────────────────────

@login_required
def meeting_minutes(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    try:
        minutes = meeting.minutes
    except MeetingMinutes.DoesNotExist:
        minutes = None

    if request.method == 'POST':
        form = MinutesForm(request.POST, instance=minutes)
        if form.is_valid():
            m = form.save(commit=False)
            m.meeting = meeting
            m.recorded_by = request.user
            m.save()
            messages.success(request, 'Minutes saved successfully.')
            return redirect('meeting_detail', pk=pk)
    else:
        form = MinutesForm(instance=minutes)

    return render(request, 'meetings/minutes.html', {
        'meeting': meeting,
        'form': form,
        'minutes': minutes,
    })


# ─────────────────────────────────────────
# Cancel
# ─────────────────────────────────────────

@login_required
def meeting_cancel(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if meeting.organizer == request.user and request.method == 'POST':
        meeting.status = 'cancelled'
        meeting.save()
        send_meeting_email(
            meeting,
            subject=f'Meeting Cancelled: {meeting.title}',
            template_name='meetings/email_cancelled.html',
        )
        messages.info(request, 'Meeting cancelled.')
    return redirect('dashboard')


# ─────────────────────────────────────────
# Join
# ─────────────────────────────────────────

@login_required
def join_meeting(request):
    error = None
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        meeting = (
            Meeting.objects.filter(room_code__iexact=token).first()
            or Meeting.objects.filter(pk=token).first()
        )
        if meeting:
            if meeting.status == 'cancelled':
                error = 'This meeting has been cancelled.'
            else:
                if meeting.organizer == request.user and meeting.status == 'scheduled':
                    meeting.status = 'in_progress'
                    meeting.save()
                return redirect('meeting_conference', pk=meeting.pk)
        else:
            error = 'No meeting found with that ID or room code.'

    return render(request, 'meetings/join.html', {'error': error})


# ─────────────────────────────────────────
# Calendar export (.ics)
# ─────────────────────────────────────────

@login_required
def export_ical(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)

    from icalendar import Calendar, Event as IEvent
    from datetime import timedelta

    cal = Calendar()
    cal.add('prodid', '-//MeetWise//meetwise.app//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'REQUEST')

    event = IEvent()
    event.add('uid', str(meeting.pk))
    event.add('summary', meeting.title)
    event.add('description', meeting.agenda or '')
    event.add('dtstart', meeting.scheduled_at)
    event.add('dtend', meeting.scheduled_at + timedelta(minutes=meeting.duration))
    event.add('dtstamp', timezone.now())

    cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{meeting.title}.ics"'
    return response


# ─────────────────────────────────────────
# AI — Generate minutes (Claude)
# ─────────────────────────────────────────

@login_required
@require_POST
def ai_generate_minutes(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)

    try:
        body = json.loads(request.body)
        raw_notes = body.get('notes', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body.'}, status=400)

    if not raw_notes:
        return JsonResponse({'error': 'No notes provided.'}, status=400)

    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'AI not configured. Add ANTHROPIC_API_KEY to your environment variables on Render.'}, status=503)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a professional meeting secretary. Given raw meeting notes, produce a clean structured summary.

Meeting title: {meeting.title}
Agenda: {meeting.agenda or 'Not specified'}
Raw notes:
{raw_notes}

Return a JSON object with exactly these keys:
- "summary": 2-4 sentence executive summary
- "decisions": list of decisions made (strings)
- "action_items": list of action items, each with "task" and "owner" (use "TBD" if unknown)
- "notes": cleaned professional version of the notes

Return ONLY the JSON object, no markdown, no explanation."""

        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1500,
            messages=[{'role': 'user', 'content': prompt}]
        )

        import re
        text = message.content[0].text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        return JsonResponse({'success': True, 'result': result})

    except Exception as e:
        return JsonResponse({'error': f'AI generation failed: {str(e)}'}, status=500)


# ─────────────────────────────────────────
# AI — Suggest agenda
# ─────────────────────────────────────────

@login_required
@require_POST
def ai_suggest_agenda(request):
    try:
        body = json.loads(request.body)
        title = body.get('title', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if not title:
        return JsonResponse({'error': 'No title provided.'}, status=400)

    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'AI not configured.'}, status=503)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=400,
            messages=[{
                'role': 'user',
                'content': f'Write a concise professional meeting agenda for a meeting titled "{title}". '
                           f'Return 4-6 bullet points only, each on a new line starting with "• ".'
            }]
        )

        return JsonResponse({'success': True, 'agenda': message.content[0].text.strip()})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────
# Transcription — Faster-Whisper (local model)
# Runs entirely on your server, no external API
# ─────────────────────────────────────────

_whisper_model = None

def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel('tiny', device='cpu', compute_type='int8')
    return _whisper_model


@login_required
@require_POST
def transcribe_audio(request, pk):
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'No audio file received.'}, status=400)

    import tempfile, os

    suffix = '.webm'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        model = _get_whisper()
        segments, _ = model.transcribe(tmp_path, beam_size=1, language='en')
        text = ' '.join(seg.text.strip() for seg in segments).strip()
        return JsonResponse({'success': True, 'text': text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        os.unlink(tmp_path)