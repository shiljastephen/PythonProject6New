from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import login, authenticate
from .models import Event, Registration, Feedback, Venue, Profile, NotificationLog
from .forms import EventForm, FeedbackForm, SignUpForm
from django.contrib.auth.models import User
from .utils import send_notification

#profile-role(student/teacher)
def is_student(user):
    return hasattr(user, "profile") and user.profile.role == "student"
def is_teacher(user):
    return hasattr(user, "profile") and user.profile.role == "teacher"
#list all the events at home page
def event_list(request):
    events = Event.objects.filter(approved=True).order_by('date_time')
    return render(request, 'event_list.html', {'events': events})
#detail of events:only students can register and give feedback for events
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registrations = Registration.objects.filter(event=event)
    feedbacks = Feedback.objects.filter(event=event)
    # check if current user already registered
    user_registered = False
    if request.user.is_authenticated:
        user_registered = Registration.objects.filter(event=event, user=request.user).exists()

    return render(request, 'event_detail.html', {
        'event': event,
        'registrations': registrations,
        'feedbacks': feedbacks,
        'user_registered': user_registered,
    })
# registration for students and teachers
def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data.get('email')
            user.save()
            role = form.cleaned_data.get('role')
            parent_email = form.cleaned_data.get('parent_email') or None
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.parent_email = parent_email
            profile.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user:
                login(request, user)

            messages.success(request, "Account created successfully.")
            return redirect('event_list')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})
#only teachers can create events
@login_required
@user_passes_test(is_teacher)
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.approved = False
            event.save()
            form.save_m2m()
            messages.success(request, "Event submitted for approval.")
            return redirect('event_list')
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})

# only admin can approve events
@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_event(request, event_id):
    if request.method != "POST":
        return HttpResponseForbidden("Approval must be POST request.")
    event = get_object_or_404(Event, id=event_id)
    event.approved = True
    event.save()

    # # notify students who might be interested? (we send on registration only)
    # messages.success(request, "Event approved successfully.")
    # return redirect('pending_events')
#only teacher can view pending events
def pending_events(request):
    events = Event.objects.filter(approved=False)
    return render(request, 'pending_events.html', {'events': events})

#student can register for events and notification sent to parent and student email
@login_required
@user_passes_test(is_student)
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, approved=True)
    if event.venue and Registration.objects.filter(event=event).count() >= event.venue.capacity:
        messages.error(request, "Venue is full. Registration closed.")
        return redirect('event_detail', event_id=event.id)

    reg, created = Registration.objects.get_or_create(event=event, user=request.user)
    if not created:
        messages.info(request, "You have already registered for this event.")
    else:
        messages.success(request, "You have successfully registered.")

        # student email
        if request.user.email:
            send_notification(
                subject=f"Registration confirmed: {event.name}",
                template_name='emails/registration_confirmation.txt',
                context={'user': request.user, 'event': event},
                to_emails=[request.user.email],
                event=event
            )

        # parent email (if provided in student's profile)
        parent_email = request.user.profile.parent_email
        if parent_email:
            send_notification(
                subject=f"Your child registered: {event.name}",
                template_name='emails/parent_registration_notification.txt',
                context={'student': request.user, 'event': event},
                to_emails=[parent_email],
                event=event
            )
    return redirect('event_detail', event_id=event.id)

#cancel event registration (student)
@login_required
@user_passes_test(is_student)
def cancel_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id, approved=True)
    reg = Registration.objects.filter(event=event, user=request.user).first()
    if not reg:
        messages.error(request, "You are not registered for this event.")
        return redirect('event_detail', event_id=event.id)
    reg.delete()
    messages.success(request,"Your registration has been cancelled.")
    # student email
    if request.user.email:
        send_notification(
            subject=f"Registration cancelled: {event.name}",
            template_name='emails/registration_cancelled.txt',
            context={'user': request.user, 'event': event},
            to_emails=[request.user.email],
            event=event
        )
    # parent email
    parent_email = request.user.profile.parent_email
    if parent_email:
        send_notification(
            subject=f"Your child cancelled registration: {event.name}",
            template_name='emails/parent_registration_cancelled.txt',
            context={'student': request.user, 'event': event},
            to_emails=[parent_email],
            event=event
        )

    return redirect('event_detail', event_id=event.id)

#feedback
@login_required
@user_passes_test(is_student)
def submit_feedback(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if Feedback.objects.filter(event=event, user=request.user).exists():
        messages.error(request, "You already submitted feedback.")
        return redirect('event_detail', event_id=event.id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.user = request.user
            fb.event = event
            fb.save()

            messages.success(request, "Thanks! Your feedback has been submitted.")

            # notify parent about feedback
            parent_email = request.user.profile.parent_email
            if parent_email:
                send_notification(
                    subject=f"Your child submitted feedback for {event.name}",
                    template_name='emails/parent_feedback_notification.txt',
                    context={'student': request.user, 'event': event, 'feedback': fb},
                    to_emails=[parent_email],
                    event=event
                )
            return redirect('event_detail', event_id=event.id)
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'event': event, 'form': form})

#teacher can manage the list of participants(add/remove)
@login_required
@user_passes_test(is_teacher)
def manage_participants(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    participants = Registration.objects.filter(event=event).select_related('user')
    remove_id = request.GET.get("remove")
    if remove_id:
        reg = Registration.objects.filter(event=event, user_id=remove_id).first()
        if reg:
            reg.delete()
            messages.success(request, "Participant removed successfully.")
        return redirect("manage_participants", event_id=event.id)
    if request.method == "POST":
        username = request.POST.get("username")

        if not username:
            messages.error(request, "Please enter a username.")
            return redirect("manage_participants", event_id=event.id)

        user = User.objects.filter(username=username).first()
        if not user:
            messages.error(request, "User not found.")
            return redirect("manage_participants", event_id=event.id)
        if Registration.objects.filter(event=event, user=user).exists():
            messages.info(request, "This user is already registered.")
            return redirect("manage_participants", event_id=event.id)

        Registration.objects.create(event=event, user=user)
        messages.success(request, f"{user.username} added successfully.")
        return redirect("manage_participants", event_id=event.id)

    return render(request, 'manage_participants.html', {
        'event': event,
        'participants': participants,
    })
