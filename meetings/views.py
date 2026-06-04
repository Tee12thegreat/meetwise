from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import json

from .models import Meeting, MeetingMinutes
from .forms import MeetingForm, MinutesForm


# ── Auth ──────────────────────────────────────────────────────

def logout_view(request):
    auth_logout(request)
    return redirect('login')


# ── Dashboard ─────────────────────────────────────────────────

@login_required
def dashboard(request):
    now = timezone.now()
    upcoming = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user),
        scheduled_at__gte=now,
        status__in=['scheduled', 'in_progress']
    ).distinct().order_by('scheduled_at')[:5]

    past = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user),
        scheduled_at__lt=now
    ).distinct().order_by('-scheduled_at')[:5]

    total_meetings = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user)
    ).distinct().count()

    return render(request, 'meetings/dashboard.html', {
        'upcoming': upcoming,
        'past': past,
        'total_meetings': total_meetings,
        'now': now,
    })


# ── Meeting list ──────────────────────────────────────────────

@login_required
def meeting_list(request):
    meetings = Meeting.objects.filter(
        Q(organizer=request.user) | Q(attendees=request.user)
    ).distinct().order_by('-scheduled_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        meetings = meetings.filter(status=status_filter)

    return render(request, 'meetings/meeting_list.html', {
        'meetings': meetings,
        'status_filter': status_filter,
    })


# ── Schedule ──────────────────────────────────────────────────

@login_required
def meeting_schedule(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.organizer = request.user
            meeting.save()
            form.save_m2m()
            messages.success(request, 'Meeting scheduled successfully.')
            return redirect('meeting_detail', pk=meeting.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = MeetingForm()

    form.fields['attendees'].queryset = User.objects.exclude(pk=request.user.pk)
    return render(request, 'meetings/schedule.html', {'form': form})


# ── Detail ────────────────────────────────────────────────────

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


# ── Conference ────────────────────────────────────────────────

@login_required
def meeting_start(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if meeting.organizer == request.user and meeting.status == 'scheduled':
        meeting.status = 'in_progress'
        meeting.save()
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
        messages.success(request, 'Meeting ended. Add minutes below.')
    return redirect('meeting_minutes', pk=pk)


# ── Minutes ───────────────────────────────────────────────────

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
            messages.success(request, 'Minutes saved.')
            return redirect('meeting_detail', pk=pk)
    else:
        form = MinutesForm(instance=minutes)

    return render(request, 'meetings/minutes.html', {
        'meeting': meeting,
        'form': form,
        'minutes': minutes,
    })


# ── Cancel ────────────────────────────────────────────────────

@login_required
def meeting_cancel(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if meeting.organizer == request.user and meeting.status not in ['cancelled', 'completed']:
        meeting.status = 'cancelled'
        meeting.save()
        messages.info(request, 'Meeting cancelled.')
    return redirect('dashboard')


# ── Join ──────────────────────────────────────────────────────

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
            error = 'No meeting found with that code.'
    return render(request, 'meetings/join.html', {'error': error})


# ── Calendar export ───────────────────────────────────────────

@login_required
def export_ical(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    from icalendar import Calendar, Event as IEvent
    from datetime import timedelta

    cal = Calendar()
    cal.add('prodid', '-//MeetWise//')
    cal.add('version', '2.0')

    event = IEvent()
    event.add('uid', str(meeting.pk))
    event.add('summary', meeting.title)
    event.add('description', meeting.agenda or '')
    event.add('dtstart', meeting.scheduled_at)
    event.add('dtend', meeting.scheduled_at + timedelta(minutes=meeting.duration))
    event.add('dtstamp', timezone.now())
    cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="meeting.ics"'
    return response


# ── AI: Agenda (local model, no API key needed) ───────────────

@login_required
@require_POST
def ai_suggest_agenda(request):
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if not title:
        return JsonResponse({'error': 'Title required.'}, status=400)

    agenda = _local_agenda_model(title)
    return JsonResponse({'success': True, 'agenda': agenda})


def _local_agenda_model(title):
    t = title.lower()
    templates = [
        (['standup', 'stand-up', 'daily', 'scrum', 'sync'],
         ['• What did each member complete yesterday?',
          '• What is each member working on today?',
          '• Any blockers or impediments?',
          '• Team announcements or updates']),

        (['sprint', 'retrospective', 'retro', 'iteration'],
         ['• Sprint goals review and completion status',
          '• Demo of completed deliverables',
          '• What went well this sprint?',
          '• What needs improvement?',
          '• Action items and owners',
          '• Priorities for next sprint']),

        (['planning', 'plan', 'roadmap', 'strategy', 'strategic', 'quarterly', 'q1', 'q2', 'q3', 'q4'],
         ['• Review current status and progress',
          '• Key priorities and objectives ahead',
          '• Resource allocation and capacity',
          '• Risks and mitigation plans',
          '• Timeline and milestones',
          '• Next steps and owners']),

        (['review', 'feedback', 'evaluation', 'assessment'],
         ['• Overview of work under review',
          '• Strengths and what is working well',
          '• Areas for improvement',
          '• Recommendations and action items',
          '• Follow-up schedule']),

        (['budget', 'finance', 'financial', 'cost', 'forecast', 'revenue'],
         ['• Current budget status and variances',
          '• Income, expenses, and cash flow',
          '• Key financial risks and opportunities',
          '• Budget adjustments needed',
          '• Approvals required',
          '• Next reporting period']),

        (['kickoff', 'kick-off', 'launch', 'onboarding', 'project start'],
         ['• Project overview and success criteria',
          '• Team roles and responsibilities',
          '• Scope and deliverables',
          '• Timeline and key milestones',
          '• Tools and ways of working',
          '• Open questions and next steps']),

        (['design', 'ux', 'ui', 'wireframe', 'prototype', 'mockup'],
         ['• Presentation of current designs',
          '• Review against user requirements',
          '• Feedback on usability and direction',
          '• Open design decisions needed',
          '• Revisions required',
          '• Next review date']),

        (['technical', 'engineering', 'architecture', 'backend', 'frontend', 'api', 'deployment', 'release'],
         ['• Current technical status and open issues',
          '• Architecture decisions needed',
          '• Blockers and dependencies',
          '• Testing and security considerations',
          '• Deployment plan',
          '• Action items and owners']),

        (['sales', 'client', 'customer', 'account', 'proposal', 'pitch'],
         ['• Account overview and context',
          '• Current pipeline status',
          '• Customer needs and pain points',
          '• Proposed solution and value',
          '• Objections and how to address them',
          '• Next steps and follow-up']),

        (['hr', 'hiring', 'recruitment', 'performance', 'people', 'team'],
         ['• Team updates and changes',
          '• Open roles and hiring pipeline',
          '• Performance updates',
          '• Team wellbeing check-in',
          '• Training and development',
          '• HR decisions required']),

        (['marketing', 'campaign', 'brand', 'content', 'launch', 'promotion'],
         ['• Campaign performance review',
          '• Upcoming campaigns and content',
          '• Channel metrics',
          '• Creative approvals needed',
          '• Budget status',
          '• Next deadlines']),

        (['update', 'status', 'progress', 'weekly', 'monthly', 'check-in'],
         ['• Progress against goals and KPIs',
          '• Completed items',
          '• Work in progress',
          '• Blockers and risks',
          '• Upcoming deadlines',
          '• Decisions needed']),

        (['brainstorm', 'ideation', 'ideas', 'creative', 'workshop'],
         ['• Problem statement and context',
          '• Constraints and success criteria',
          '• Silent idea generation',
          '• Group sharing and building',
          '• Voting and prioritising',
          '• Next steps for top ideas']),
    ]

    best_score, best_items = 0, None
    for keywords, items in templates:
        score = sum(1 for kw in keywords if kw in t)
        if score > best_score:
            best_score, best_items = score, items

    if not best_items:
        best_items = [
            '• Welcome and introductions',
            f'• Purpose and objectives: {title}',
            '• Main discussion points',
            '• Key considerations and options',
            '• Decisions and agreements',
            '• Action items, owners, and next steps',
        ]

    return '\n'.join(best_items)


# ── AI: Generate minutes ──────────────────────────────────────

@login_required
@require_POST
def ai_generate_minutes(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    try:
        body = json.loads(request.body)
        raw_notes = body.get('notes', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if not raw_notes:
        return JsonResponse({'error': 'No notes provided.'}, status=400)

    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'ANTHROPIC_API_KEY not set in environment.'}, status=503)

    try:
        import anthropic, re
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1500,
            messages=[{'role': 'user', 'content': f'''You are a meeting secretary. Structure these raw notes.

Meeting: {meeting.title}
Agenda: {meeting.agenda or 'Not specified'}
Notes: {raw_notes}

Return ONLY a JSON object with keys:
- "summary": 2-3 sentence summary
- "decisions": list of strings
- "action_items": list of {{"task": "...", "owner": "..."}}
- "notes": cleaned professional notes'''}]
        )
        text = re.sub(r'^```json\s*|\s*```$', '', message.content[0].text.strip())
        return JsonResponse({'success': True, 'result': json.loads(text)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Transcription ─────────────────────────────────────────────

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
        return JsonResponse({'error': 'No audio received.'}, status=400)

    import tempfile, os

    # Write to temp file — try webm first, fall back to generic
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        model = _get_whisper()
        segments, info = model.transcribe(
            tmp_path,
            beam_size=1,
            language='en',
            vad_filter=True,           # skip silent sections
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        text = ' '.join(s.text.strip() for s in segments).strip()
        return JsonResponse({'success': True, 'text': text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
