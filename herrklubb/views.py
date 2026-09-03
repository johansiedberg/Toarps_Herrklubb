import os
import datetime
import calendar
import json
import re
from functools import wraps
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.signing import TimestampSigner
from django.conf import settings

from .models import (
    UserProfile, BucketCategory, BucketItem, BucketVote, BucketDream,
    UserUnavailability, HerrklubbEvent
)
from .forms import CustomLoginForm

User = get_user_model()

def herrklubb_member_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.is_herrklubb_member and not request.user.is_superuser:
            return redirect('predictions_sso_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class CustomLoginView(LoginView):
    template_name = 'herrklubb/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.is_herrklubb_member or user.is_superuser:
                return '/hub/'
        return '/predictions/login/'


@login_required
@require_POST
def update_account_settings_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        data = request.POST

    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email:
        return JsonResponse({'success': False, 'error': 'E-postadress kan inte vara tom.'}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'success': False, 'error': 'Ange en giltig e-postadress.'}, status=400)

    User = get_user_model()
    existing_user = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exclude(pk=request.user.pk).first()
    if existing_user:
        return JsonResponse({'success': False, 'error': 'E-postadressen används redan av en annan användare.'}, status=400)

    if password:
        if len(password) < 5:
            return JsonResponse({'success': False, 'error': 'Lösenordet måste vara minst 5 tecken långt.'}, status=400)
        if not re.search(r'\d', password):
            return JsonResponse({'success': False, 'error': 'Lösenordet måste innehålla minst en siffra.'}, status=400)

    user = request.user
    user.email = email
    user.username = email
    if password:
        user.set_password(password)
    user.save()

    nickname = data.get('nickname')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if nickname is not None:
        profile.nickname = nickname.strip()
        profile.save()

    if password:
        update_session_auth_hash(request, user)

    return JsonResponse({
        'success': True,
        'message': 'Dina kontoinställningar har sparats!',
        'email': user.email,
        'username': user.username,
        'nickname': profile.get_nickname() if nickname is not None else None
    })


# --- SSO SIGNED LOGIN REDIRECT ---

@login_required
def predictions_sso_login(request):
    """Generates a cryptographically signed token and redirects the user to the Prediction Engine."""
    payload = {
        'email': request.user.email,
        'username': request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }
    signer = TimestampSigner(key=settings.HERRKLUBB_SSO_SECRET, salt='sso-salt')
    token = signer.sign_object(payload)

    # Determine Prediction Engine destination (env override or dynamic host resolution on port 2028)
    if getattr(settings, 'PREDICTION_ENGINE_URL', ''):
        target_base = settings.PREDICTION_ENGINE_URL.rstrip('/')
    else:
        scheme = 'https' if request.is_secure() else 'http'
        host_name = request.get_host().split(':')[0]
        target_base = f"{scheme}://{host_name}:2028"

    return redirect(f"{target_base}/sso/login/?token={token}")


# --- HERRKLUBBEN VIEWS ---

@login_required
@herrklubb_member_required
def hub_view(request):
    """Startsida for Herrklubben members after login."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_nickname = profile.get_nickname()

    context = {
        'profile': profile,
        'user': request.user,
        'user_nickname': user_nickname,
    }
    return render(request, 'herrklubb/hub.html', context)


@login_required
@herrklubb_member_required
def herrklubb_view(request):
    """Herrklubbssidan Bucket list ranking & voting page."""
    categories = BucketCategory.objects.prefetch_related('items__votes', 'items__dreams').all()
    all_uncompleted_items = list(BucketItem.objects.filter(is_completed=False).select_related('category', 'created_by').prefetch_related('votes__user', 'dreams__user'))
    completed_items = BucketItem.objects.filter(is_completed=True).select_related('category', 'created_by').order_by('-completed_date')

    # All items ordered for dropdown selectors
    all_open_items_sorted = sorted(all_uncompleted_items, key=lambda x: (x.category.order, x.title))

    user_votes = BucketVote.objects.filter(user=request.user, item__is_completed=False)
    user_placed_svart = user_votes.filter(marker='SVART').first()
    user_placed_gron = user_votes.filter(marker='GRON').first()
    user_placed_rod = user_votes.filter(marker='ROD').first()
    user_dream = BucketDream.objects.filter(user=request.user, item__is_completed=False).first()

    planerade_items = []
    idebanken_items = []

    for item in all_uncompleted_items:
        if item.vote_count >= 6:
            planerade_items.append(item)
        else:
            idebanken_items.append(item)

    planerade_items.sort(key=lambda x: (x.total_points, x.count_svart, x.count_gron), reverse=True)
    idebanken_items.sort(key=lambda x: (x.vote_count, x.total_points), reverse=True)

    context = {
        'categories': categories,
        'all_open_items': all_open_items_sorted,
        'planerade_items': planerade_items,
        'idebanken_items': idebanken_items,
        'completed_items': completed_items,
        'user_placed_svart': user_placed_svart,
        'user_placed_gron': user_placed_gron,
        'user_placed_rod': user_placed_rod,
        'user_dream': user_dream,
        'total_members_count': 11,
        'all_members': User.objects.filter(is_active=True, profile__is_herrklubb_member=True).exclude(username__iexact='john').exclude(username__iexact='admin').order_by('first_name', 'last_name', 'username'),
        'next_event': HerrklubbEvent.objects.filter(is_active=True).prefetch_related('coordinators', 'bucket_items__category', 'bucket_items__dreams__user', 'bucket_items__votes').first(),
    }
    context.update(build_calendar_context(request))
    return render(request, 'herrklubb/herrklubb.html', context)


@login_required
@herrklubb_member_required
@require_POST
def save_user_bucket_votes(request):
    """Saves structured dropdown selections for Bucket/Dream, Svart, Grön, and Röd markers at once."""
    dream_item_id = request.POST.get('dream_item_id')
    svart_item_id = request.POST.get('svart_item_id')
    gron_item_id = request.POST.get('gron_item_id')
    rod_item_id = request.POST.get('rod_item_id')

    # 1. Update Högsta Dröm (Bucket)
    BucketDream.objects.filter(user=request.user, item__is_completed=False).delete()
    if dream_item_id and dream_item_id.isdigit():
        d_item = BucketItem.objects.filter(id=int(dream_item_id), is_completed=False).first()
        if d_item:
            BucketDream.objects.create(user=request.user, item=d_item)

    # Clear current marker votes
    BucketVote.objects.filter(user=request.user, item__is_completed=False).delete()

    # 2. Svart Marker (100)
    if svart_item_id and svart_item_id.isdigit():
        s_item = BucketItem.objects.filter(id=int(svart_item_id), is_completed=False).first()
        if s_item:
            BucketVote.objects.create(user=request.user, item=s_item, marker='SVART')

    # 3. Grön Marker (50)
    if gron_item_id and gron_item_id.isdigit() and gron_item_id != svart_item_id:
        g_item = BucketItem.objects.filter(id=int(gron_item_id), is_completed=False).first()
        if g_item:
            BucketVote.objects.create(user=request.user, item=g_item, marker='GRON')

    # 4. Röd Marker (25)
    if rod_item_id and rod_item_id.isdigit() and rod_item_id != svart_item_id and rod_item_id != gron_item_id:
        r_item = BucketItem.objects.filter(id=int(rod_item_id), is_completed=False).first()
        if r_item:
            BucketVote.objects.create(user=request.user, item=r_item, marker='ROD')

    messages.success(request, "Dina marker-röster och val har sparats!")
    return redirect('herrklubb')


@login_required
@herrklubb_member_required
@require_POST
def vote_bucket_item(request):
    """Places or toggles a Pokermarker vote (SVART/GRON/ROD) on an item."""
    item_id = request.POST.get('item_id')
    marker = request.POST.get('marker')

    if marker not in ['SVART', 'GRON', 'ROD']:
        return JsonResponse({'success': False, 'error': 'Ogiltig marker.'})

    item = get_object_or_404(BucketItem, id=item_id, is_completed=False)

    existing_vote_on_item = BucketVote.objects.filter(user=request.user, item=item, marker=marker).first()
    if existing_vote_on_item:
        existing_vote_on_item.delete()
        action = 'removed'
    else:
        BucketVote.objects.filter(user=request.user, marker=marker, item__is_completed=False).delete()
        BucketVote.objects.filter(user=request.user, item=item).delete()
        BucketVote.objects.create(user=request.user, item=item, marker=marker)
        action = 'added'

    return JsonResponse({
        'success': True,
        'action': action,
        'item_id': item.id,
        'total_points': item.total_points,
        'vote_count': item.vote_count,
        'count_svart': item.count_svart,
        'count_gron': item.count_gron,
        'count_rod': item.count_rod,
        'is_planerad': item.is_planerad,
    })


@login_required
@herrklubb_member_required
@require_POST
def toggle_bucket_dream(request):
    """Toggles Högsta Dröm marker on a bucket item."""
    item_id = request.POST.get('item_id')
    item = get_object_or_404(BucketItem, id=item_id, is_completed=False)

    existing_dream = BucketDream.objects.filter(user=request.user, item=item).first()
    if existing_dream:
        existing_dream.delete()
        action = 'removed'
    else:
        BucketDream.objects.filter(user=request.user, item__is_completed=False).delete()
        BucketDream.objects.create(user=request.user, item=item)
        action = 'added'

    return JsonResponse({
        'success': True,
        'action': action,
        'item_id': item.id,
        'dream_users_count': len(item.dream_users),
    })


@login_required
@herrklubb_member_required
@require_POST
def add_bucket_item(request):
    """Allows members to submit a new proposal to the Bucket list."""
    title = request.POST.get('title', '').strip()
    category_id = request.POST.get('category_id')
    description = request.POST.get('description', '').strip()

    if not title or not category_id:
        messages.error(request, "Titel och kategori måste fyllas i.")
        return redirect('herrklubb')

    category = get_object_or_404(BucketCategory, id=category_id)
    BucketItem.objects.create(
        title=title,
        category=category,
        description=description,
        created_by=request.user
    )
    messages.success(request, f"Förslaget '{title}' har lagts till i Idébanken!")
    return redirect('herrklubb')


@login_required
@herrklubb_member_required
@require_POST
def edit_bucket_item(request, item_id):
    """Allows staff or creator to edit a bucket item's details."""
    item = get_object_or_404(BucketItem, id=item_id)
    if not (request.user.is_staff or item.created_by == request.user):
        messages.error(request, "Du har inte behörighet att ändra detta förslag.")
        return redirect('herrklubb')

    title = request.POST.get('title', '').strip()
    category_id = request.POST.get('category_id')
    description = request.POST.get('description', '').strip()

    if title and category_id:
        category = get_object_or_404(BucketCategory, id=category_id)
        item.title = title
        item.category = category
        item.description = description
        item.save()
        messages.success(request, f"Förslaget '{item.title}' har uppdaterats!")
    else:
        messages.error(request, "Titel och kategori måste fyllas i.")

    return redirect('herrklubb')


@login_required
@herrklubb_member_required
@require_POST
def delete_bucket_item(request, item_id):
    """Allows staff or creator to delete a bucket item."""
    item = get_object_or_404(BucketItem, id=item_id)
    if not (request.user.is_staff or item.created_by == request.user):
        messages.error(request, "Du har inte behörighet att ta bort detta förslag.")
        return redirect('herrklubb')

    title = item.title
    item.delete()
    messages.success(request, f"Förslaget '{title}' har tagits bort från Bucketlisten.")
    return redirect('herrklubb')


@login_required
@herrklubb_member_required
@require_POST
def complete_bucket_item(request, item_id):
    """Marks a bucket item as completed, archiving it and freeing up active votes."""
    item = get_object_or_404(BucketItem, id=item_id)
    item.is_completed = True
    item.completed_date = timezone.now()
    item.save()
    messages.success(request, f"🎉 Grattis! '{item.title}' har markerats som genomförd! Alla röster har frigjorts.")
    return redirect('herrklubb')


# --- HINDERKALENDER (UNAVAILABILITY CALENDAR) VIEWS ---

def build_calendar_context(request):
    """Helper function to build calendar heatmap and Golden Weekend data."""
    import datetime
    today = datetime.date.today()
    try:
        req_year = int(request.GET.get('year', today.year))
        req_month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        req_year = today.year
        req_month = today.month

    total_members = UserProfile.objects.filter(is_herrklubb_member=True).count()
    if total_members == 0:
        total_members = 11

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(req_year, req_month)

    unavailabilities = list(UserUnavailability.objects.select_related('user').all())
    user_unavailabilities = UserUnavailability.objects.filter(user=request.user, end_date__gte=today).order_by('start_date')
    planned_events = list(HerrklubbEvent.objects.filter(is_active=True))

    swedish_months = [
        "", "Januari", "Februari", "Mars", "April", "Maj", "Juni",
        "Juli", "Augusti", "September", "Oktober", "November", "December"
    ]
    swedish_weekdays = ["Mån", "Tis", "Ons", "Tor", "Fre", "Lör", "Sön"]

    days_data = []
    for week in month_days:
        for day in week:
            is_other_month = (day.month != req_month)

            blocked_users = []
            if not is_other_month:
                for u in unavailabilities:
                    if u.start_date <= day <= u.end_date:
                        if u.user not in blocked_users:
                            blocked_users.append(u.user)

            unavailable_count = len(blocked_users)
            available_count = max(0, total_members - unavailable_count)

            is_weekend = day.weekday() in [4, 5, 6]
            is_golden = (available_count == total_members) and is_weekend and not is_other_month

            day_events = [
                ev for ev in planned_events
                if ev.event_date and (
                    (ev.end_date and ev.event_date <= day <= ev.end_date) or
                    (not ev.end_date and ev.event_date == day)
                )
            ]
            is_planned_event = len(day_events) > 0
            planned_event = day_events[0] if day_events else None

            days_data.append({
                'date': day,
                'day_num': day.day,
                'weekday_name': swedish_weekdays[day.weekday()],
                'is_weekend': is_weekend,
                'is_today': (day == today),
                'is_other_month': is_other_month,
                'available_count': available_count,
                'unavailable_count': unavailable_count,
                'blocked_users': blocked_users,
                'is_user_blocked': (request.user in blocked_users),
                'is_golden': is_golden,
                'is_planned_event': is_planned_event,
                'planned_event': planned_event,
            })

    golden_weekends = []
    scan_start = today
    scan_end = today + datetime.timedelta(days=90)
    current = scan_start
    while current <= scan_end:
        if current.weekday() == 4: # Friday
            sat = current + datetime.timedelta(days=1)
            sun = current + datetime.timedelta(days=2)

            fr_blocked = {u.user_id for u in unavailabilities if u.start_date <= current <= u.end_date}
            sa_blocked = {u.user_id for u in unavailabilities if u.start_date <= sat <= u.end_date}
            su_blocked = {u.user_id for u in unavailabilities if u.start_date <= sun <= u.end_date}

            if not fr_blocked and not sa_blocked and not su_blocked:
                golden_weekends.append({
                    'start': current,
                    'end': sun,
                    'days_count': 3
                })
        current += datetime.timedelta(days=1)

    all_upcoming = UserUnavailability.objects.filter(end_date__gte=today).select_related('user').order_by('start_date')

    prev_month = req_month - 1
    if prev_month < 1:
        prev_month = 12

    next_month = req_month + 1
    if next_month > 12:
        next_month = 1

    prev_year = req_year - 1
    next_year = req_year + 1

    # Build 12-month structured data for 6-row half-year views (Jan-June / July-Dec)
    yearly_months = []
    for m in range(1, 13):
        m_days = cal.monthdatescalendar(req_year, m)
        m_days_data = []
        for week in m_days:
            for day in week:
                if day.month != m:
                    continue
                blocked_users = []
                for u in unavailabilities:
                    if u.start_date <= day <= u.end_date:
                        if u.user not in blocked_users:
                            blocked_users.append(u.user)

                unavailable_count = len(blocked_users)
                available_count = max(0, total_members - unavailable_count)
                is_weekend = day.weekday() in [4, 5, 6]
                is_golden = (available_count == total_members) and is_weekend

                day_events = [
                    ev for ev in planned_events
                    if ev.event_date and (
                        (ev.end_date and ev.event_date <= day <= ev.end_date) or
                        (not ev.end_date and ev.event_date == day)
                    )
                ]
                is_planned_event = len(day_events) > 0
                planned_event = day_events[0] if day_events else None

                m_days_data.append({
                    'date': day,
                    'day_num': day.day,
                    'weekday_name': swedish_weekdays[day.weekday()],
                    'is_weekend': is_weekend,
                    'is_today': (day == today),
                    'available_count': available_count,
                    'unavailable_count': unavailable_count,
                    'blocked_users': blocked_users,
                    'is_user_blocked': (request.user in blocked_users),
                    'is_golden': is_golden,
                    'is_planned_event': is_planned_event,
                    'planned_event': planned_event,
                })
        yearly_months.append({
            'month_num': m,
            'month_name': swedish_months[m],
            'days': m_days_data,
        })

    half1_months = yearly_months[0:6]   # Jan - June
    half2_months = yearly_months[6:12]  # July - Dec
    half_param = request.GET.get('half')
    if half_param in ['1', '2']:
        active_half = int(half_param)
    elif req_year == today.year:
        active_half = 1 if today.month <= 6 else 2
    else:
        active_half = 1

    return {
        'req_year': req_year,
        'req_month': req_month,
        'month_name_sv': swedish_months[req_month],
        'days_data': days_data,
        'yearly_months': yearly_months,
        'half1_months': half1_months,
        'half2_months': half2_months,
        'active_half': active_half,
        'total_members': total_members,
        'golden_weekends': golden_weekends,
        'user_unavailabilities': user_unavailabilities,
        'all_upcoming': all_upcoming,
        'today': today,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }


@login_required
@herrklubb_member_required
def calendar_view(request):
    """Monthly heatmap calendar showing member availability and Golden Weekends."""
    context = build_calendar_context(request)
    return render(request, 'herrklubb/calendar.html', context)


@login_required
@herrklubb_member_required
@require_POST
def add_unavailability_view(request):
    """Adds a date block of unavailability for the logged-in member."""
    import datetime
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')
    reason = request.POST.get('reason', '').strip()
    next_url = request.META.get('HTTP_REFERER') or 'herrklubb'

    if not start_date_str or not end_date_str:
        messages.error(request, "Både start- och slutdatum måste anges.")
        return redirect(next_url)

    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Ogiltigt datumformat.")
        return redirect(next_url)

    if end_date < start_date:
        messages.error(request, "Slutdatum kan inte vara före startdatum.")
        return redirect(next_url)

    UserUnavailability.objects.create(
        user=request.user,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )
    messages.success(request, f"Hinder har registrerats ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')})!")
    return redirect(next_url)


@login_required
@herrklubb_member_required
@require_POST
def delete_unavailability_view(request, item_id):
    """Deletes an unavailability period owned by the logged-in member."""
    item = get_object_or_404(UserUnavailability, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Hindret har tagits bort från kalendern.")
    next_url = request.META.get('HTTP_REFERER') or 'herrklubb'
    return redirect(next_url)


@login_required
@herrklubb_member_required
@require_POST
def save_herrklubb_event_view(request):
    """Creates or updates the Next Event for Herrklubben."""
    import datetime
    title = request.POST.get('title', '').strip()
    category_id = request.POST.get('category_id')
    description = request.POST.get('description', '').strip()
    event_date_str = request.POST.get('event_date')
    end_date_str = request.POST.get('end_date')
    location = request.POST.get('location', '').strip()

    if not title:
        messages.error(request, "Aktivitetsnamn måste fyllas i.")
        return redirect('herrklubb')

    category = None
    if category_id and category_id.isdigit():
        category = BucketCategory.objects.filter(id=int(category_id)).first()

    event_date = None
    if event_date_str:
        try:
            event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    end_date = None
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    linked_bucket_items = request.POST.getlist('linked_bucket_items')
    coordinator_ids = request.POST.getlist('coordinators')

    event = HerrklubbEvent.objects.filter(is_active=True).first()
    if not event:
        event = HerrklubbEvent.objects.create(
            title=title,
            category=category,
            description=description,
            event_date=event_date,
            end_date=end_date,
            location=location,
            created_by=request.user,
            is_active=True
        )
    else:
        event.title = title
        event.category = category
        event.description = description
        event.event_date = event_date
        event.end_date = end_date
        event.location = location
        event.save()

    if coordinator_ids:
        valid_coordinators = User.objects.filter(id__in=coordinator_ids, is_active=True)
        event.coordinators.set(valid_coordinators)
    else:
        event.coordinators.clear()

    if linked_bucket_items:
        valid_items = BucketItem.objects.filter(id__in=linked_bucket_items, is_completed=False)
        event.bucket_items.set(valid_items)
    else:
        event.bucket_items.clear()

    messages.success(request, f"Nästa Event '{event.title}' har uppdaterats!")
    return redirect('herrklubb')


@login_required
@herrklubb_member_required
@require_POST
def delete_herrklubb_event_view(request, event_id):
    """Deletes or deactivates the Next Event."""
    event = get_object_or_404(HerrklubbEvent, id=event_id)
    event.delete()
    messages.success(request, "Nästa Event har tagits bort.")
    return redirect('herrklubb')


@login_required
@herrklubb_member_required
@require_POST
def toggle_event_coordinator_view(request, event_id):
    """Adds or removes the logged-in member as a coordinator for the event."""
    event = get_object_or_404(HerrklubbEvent, id=event_id)
    if request.user in event.coordinators.all():
        event.coordinators.remove(request.user)
        messages.info(request, "Du har gått ur som samordnare för eventet.")
    else:
        event.coordinators.add(request.user)
        messages.success(request, "🎉 Du har lagts till som samordnare för eventet!")
    return redirect('herrklubb')


@login_required
def upload_avatar_view(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Din profilbild har uppdaterats!')
    return redirect(request.META.get('HTTP_REFERER', 'hub'))
@login_required
@herrklubb_member_required
@require_POST
def toggle_event_participation_view(request, event_id, status):
    """Toggles participation for the logged-in user in the event."""
    event = get_object_or_404(HerrklubbEvent, id=event_id)
    
    if status == 'yes':
        if request.user in event.participants.all():
            event.participants.remove(request.user)
            messages.info(request, "Deltagande nollställt.")
        else:
            event.participants.add(request.user)
            event.participants_no.remove(request.user)
            messages.success(request, "✅ Du deltar i eventet!")
    elif status == 'no':
        if request.user in event.participants_no.all():
            event.participants_no.remove(request.user)
            messages.info(request, "Deltagande nollställt.")
        else:
            event.participants_no.add(request.user)
            event.participants.remove(request.user)
            messages.info(request, "❌ Du deltar ej i eventet.")
            
    return redirect('herrklubb')


def generate_event_ics(event):
    """
    Generates standard RFC 5545 iCalendar (.ics) string for a HerrklubbEvent.
    """
    now_utc = timezone.now().strftime("%Y%m%dT%H%M%SZ")
    uid = f"herrklubb-event-{event.id}@toarpsherrklubb.se"
    
    def escape_ics_text(text):
        if not text:
            return ""
        return str(text).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\r\n', '\\n').replace('\n', '\\n')
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Toarps Herrklubb//Herrklubb Event//SV",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc}",
    ]
    
    if event.event_date:
        if event.event_time:
            # Timed event
            start_dt = datetime.datetime.combine(event.event_date, event.event_time)
            lines.append(f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}")
            if event.end_date:
                end_dt = datetime.datetime.combine(event.end_date, event.event_time)
                lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}")
            else:
                end_dt = start_dt + datetime.timedelta(hours=3)
                lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}")
        else:
            # All-day / Multi-day event (dates formatted as YYYYMMDD, DTEND is exclusive per RFC 5545)
            start_str = event.event_date.strftime("%Y%m%d")
            end_date = (event.end_date or event.event_date) + datetime.timedelta(days=1)
            end_str = end_date.strftime("%Y%m%d")
            lines.append(f"DTSTART;VALUE=DATE:{start_str}")
            lines.append(f"DTEND;VALUE=DATE:{end_str}")
            
    lines.append(f"SUMMARY:{escape_ics_text(f'Toarps Herrklubb: {event.title}')}")
    
    desc_parts = []
    if event.category:
        desc_parts.append(f"Kategori: {event.category.name}")
    if event.description:
        desc_parts.append(event.description)
    if event.coordinators.exists():
        coords = ", ".join([c.get_full_name() or c.username for c in event.coordinators.all()])
        desc_parts.append(f"Ansvariga: {coords}")
        
    full_desc = "\n\n".join(desc_parts)
    if full_desc:
        lines.append(f"DESCRIPTION:{escape_ics_text(full_desc)}")
        
    if event.location:
        lines.append(f"LOCATION:{escape_ics_text(event.location)}")
        
    lines.append("STATUS:CONFIRMED")
    lines.append("TRANSP:OPAQUE")
    lines.append("X-MICROSOFT-CDO-BUSYSTATUS:BUSY")
    lines.append("X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY")
    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    
    return "\r\n".join(lines) + "\r\n"


@login_required
@herrklubb_member_required
def event_ics_export_view(request, event_id):
    """Exports an event as an RFC 5545 .ics file for download / calendar import."""
    event = get_object_or_404(HerrklubbEvent, id=event_id)
    ics_data = generate_event_ics(event)
    filename = f"toarps_herrklubb_event_{event.id}.ics"
    response = HttpResponse(ics_data, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ==============================================================================
# PHOTO SHARING & GALLERY VIEWS
# ==============================================================================

import io
import zipfile
import mimetypes
from django.utils.text import slugify
from .models import PhotoAlbum, Photo, PhotoLike


@login_required
@herrklubb_member_required
def photo_gallery_view(request):
    """Overview of all photo albums/folders with search, filters, and stats."""
    albums_qs = PhotoAlbum.objects.select_related('created_by', 'category', 'event', 'cover_photo').prefetch_related('photos', 'photos__uploader')
    
    # Query filters
    category_id = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()
    
    # Harmonize member_filter and legacy filter parameter
    raw_filter = (request.GET.get('member') or request.GET.get('filter', '')).strip()
    member_filter = ''
    if raw_filter in ('tagged_me', 'me'):
        member_filter = 'me'
        albums_qs = albums_qs.filter(photos__tagged_members=request.user).distinct()
    elif raw_filter.isdigit():
        member_filter = raw_filter
        albums_qs = albums_qs.filter(photos__tagged_members__id=member_filter).distinct()
        
    if category_id:
        albums_qs = albums_qs.filter(category_id=category_id)
        
    if search_query:
        albums_qs = albums_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(event__title__icontains=search_query)
        )
        
    albums = list(albums_qs)
    
    # Statistics
    total_albums = PhotoAlbum.objects.count()
    total_photos = Photo.objects.count()
    user_uploaded_count = Photo.objects.filter(uploader=request.user).count()
    user_tagged_count = Photo.objects.filter(tagged_members=request.user).count()
    
    categories = BucketCategory.objects.all().order_by('order', 'name')
    events = HerrklubbEvent.objects.all().order_by('-event_date')
    all_members = User.objects.filter(profile__is_herrklubb_member=True).select_related('profile').order_by('first_name', 'username')
    
    selected_member = None
    if member_filter and member_filter.isdigit():
        selected_member = all_members.filter(id=int(member_filter)).first()
    
    context = {
        'albums': albums,
        'categories': categories,
        'events': events,
        'all_members': all_members,
        'members': all_members,
        'member_filter': member_filter,
        'filter_type': member_filter,
        'selected_member': selected_member,
        'search_query': search_query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'total_albums': total_albums,
        'total_photos': total_photos,
        'user_uploaded_count': user_uploaded_count,
        'user_tagged_count': user_tagged_count,
    }
    return render(request, 'herrklubb/photo_gallery.html', context)


@login_required
@herrklubb_member_required
@require_POST
def create_photo_album_view(request):
    """Create a new photo album/folder, optionally linking to an event."""
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, "Vänligen ange ett albumnamn.")
        return redirect('photo_gallery')
        
    description = request.POST.get('description', '').strip()
    category_id = request.POST.get('category_id')
    event_id = request.POST.get('event_id')
    folder_date_str = request.POST.get('folder_date', '').strip()
    
    category = BucketCategory.objects.filter(id=category_id).first() if category_id else None
    event = HerrklubbEvent.objects.filter(id=event_id).first() if event_id else None
    
    folder_date = None
    if folder_date_str:
        try:
            folder_date = datetime.datetime.strptime(folder_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    elif event and event.event_date:
        folder_date = event.event_date
        
    album = PhotoAlbum.objects.create(
        title=title,
        description=description,
        category=category,
        event=event,
        folder_date=folder_date,
        created_by=request.user
    )
    
    # Handle initial photos if uploaded together with album creation
    files = request.FILES.getlist('photos')
    if files:
        for f in files:
            photo = Photo(album=album, image=f, uploader=request.user)
            photo.save()
            photo.generate_thumbnail_and_metadata()
            photo.save()
            
    messages.success(request, f"Albumet '{album.title}' har skapats!")
    return redirect('album_detail', album_id=album.id)


@login_required
@herrklubb_member_required
def album_detail_view(request, album_id):
    """Detailed album view with masonry gallery, lightbox, member tagging and upload modal."""
    album = get_object_or_404(
        PhotoAlbum.objects.select_related('created_by', 'category', 'event', 'cover_photo'),
        id=album_id
    )
    
    photos_qs = album.photos.select_related('uploader', 'uploader__profile').prefetch_related('tagged_members', 'tagged_members__profile', 'likes')
    
    # Filters within album
    member_filter = request.GET.get('member')
    if member_filter:
        if member_filter == 'me':
            photos_qs = photos_qs.filter(tagged_members=request.user).distinct()
        elif member_filter.isdigit():
            photos_qs = photos_qs.filter(tagged_members__id=member_filter).distinct()
            
    photos = list(photos_qs)
    
    # Mark if current user liked each photo
    user_liked_photo_ids = set(
        PhotoLike.objects.filter(user=request.user, photo__album=album).values_list('photo_id', flat=True)
    )
    for p in photos:
        p.is_liked = p.id in user_liked_photo_ids
        
    all_members = User.objects.filter(profile__is_herrklubb_member=True).select_related('profile').order_by('first_name', 'username')
    categories = BucketCategory.objects.all().order_by('order', 'name')
    events = HerrklubbEvent.objects.all().order_by('-event_date')

    my_tagged_count = album.photos.filter(tagged_members=request.user).count()
    
    context = {
        'album': album,
        'photos': photos,
        'all_members': all_members,
        'categories': categories,
        'events': events,
        'member_filter': member_filter,
        'total_in_album': album.photos.count(),
        'my_tagged_count': my_tagged_count,
    }
    return render(request, 'herrklubb/album_detail.html', context)


@login_required
@herrklubb_member_required
@require_POST
def edit_photo_album_view(request, album_id):
    """Edit album metadata (title, description, date, category, cover)."""
    album = get_object_or_404(PhotoAlbum, id=album_id)
    
    title = request.POST.get('title', '').strip()
    if title:
        album.title = title
    album.description = request.POST.get('description', '').strip()
    
    category_id = request.POST.get('category_id')
    album.category = BucketCategory.objects.filter(id=category_id).first() if category_id else None
    
    event_id = request.POST.get('event_id')
    album.event = HerrklubbEvent.objects.filter(id=event_id).first() if event_id else None
    
    folder_date_str = request.POST.get('folder_date', '').strip()
    if folder_date_str:
        try:
            album.folder_date = datetime.datetime.strptime(folder_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    cover_photo_id = request.POST.get('cover_photo_id')
    if cover_photo_id:
        album.cover_photo = Photo.objects.filter(id=cover_photo_id, album=album).first()
        
    album.save()
    messages.success(request, "Albumet har uppdaterats!")
    return redirect('album_detail', album_id=album.id)


@login_required
@herrklubb_member_required
@require_POST
def delete_photo_album_view(request, album_id):
    """Delete an album and its photos."""
    album = get_object_or_404(PhotoAlbum, id=album_id)
    album_title = album.title
    album.delete()
    messages.success(request, f"Albumet '{album_title}' och dess foton har tagits bort.")
    return redirect('photo_gallery')


@login_required
@herrklubb_member_required
@require_POST
def upload_photos_view(request, album_id):
    """Upload one or more photos to an album with EXIF auto-rotation and thumbnailing."""
    album = get_object_or_404(PhotoAlbum, id=album_id)
    files = request.FILES.getlist('photos')
    
    if not files:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Inga bilder valdes.'}, status=400)
        messages.error(request, "Inga bilder valdes för uppladdning.")
        return redirect('album_detail', album_id=album.id)
        
    caption = request.POST.get('caption', '').strip()
    tagged_member_ids = request.POST.getlist('tagged_members')
    
    tagged_users = []
    if tagged_member_ids:
        tagged_users = list(User.objects.filter(id__in=tagged_member_ids))
        
    created_photos = []
    for f in files:
        photo = Photo(
            album=album,
            image=f,
            caption=caption,
            uploader=request.user
        )
        photo.save()
        photo.generate_thumbnail_and_metadata()
        photo.save()
        
        if tagged_users:
            photo.tagged_members.set(tagged_users)
            
        created_photos.append(photo)
        
    count = len(created_photos)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{count} bild(er) har laddats upp!',
            'uploaded_count': count
        })
        
    messages.success(request, f"{count} bild(er) har laddats upp till {album.title}!")
    return redirect('album_detail', album_id=album.id)


@login_required
@herrklubb_member_required
@require_POST
def delete_photo_view(request, photo_id):
    """Delete a single photo (allowed by uploader or superuser/admin)."""
    photo = get_object_or_404(Photo, id=photo_id)
    album_id = photo.album_id
    
    if photo.uploader != request.user and not request.user.is_superuser:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Du har inte behörighet att radera detta foto.'}, status=403)
        messages.error(request, "Du kan endast radera dina egna uppladdade bilder.")
        return redirect('album_detail', album_id=album_id)
        
    # Delete thumbnail and image files
    if photo.thumbnail and os.path.isfile(photo.thumbnail.path):
        try:
            os.remove(photo.thumbnail.path)
        except OSError:
            pass
    if photo.image and os.path.isfile(photo.image.path):
        try:
            os.remove(photo.image.path)
        except OSError:
            pass
            
    photo.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Bilden har raderats.'})
        
    messages.success(request, "Bilden har tagits bort.")
    return redirect('album_detail', album_id=album_id)


@login_required
@herrklubb_member_required
@require_POST
def tag_photo_members_view(request, photo_id):
    """Tag or untag members who appear in the photo."""
    photo = get_object_or_404(Photo, id=photo_id)
    
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        action = data.get('action')  # 'toggle', 'add', 'remove'
    except (json.JSONDecodeError, TypeError):
        member_id = request.POST.get('member_id')
        action = request.POST.get('action', 'toggle')
        
    if not member_id:
        return JsonResponse({'success': False, 'error': 'Medlem saknas.'}, status=400)
        
    target_user = get_object_or_404(User, id=member_id)
    
    if action == 'add':
        photo.tagged_members.add(target_user)
        is_tagged = True
    elif action == 'remove':
        photo.tagged_members.remove(target_user)
        is_tagged = False
    else:  # toggle
        if photo.tagged_members.filter(id=target_user.id).exists():
            photo.tagged_members.remove(target_user)
            is_tagged = False
        else:
            photo.tagged_members.add(target_user)
            is_tagged = True
            
    tagged_list = [
        {
            'id': u.id,
            'name': u.profile.get_nickname() if hasattr(u, 'profile') else (u.get_full_name() or u.username),
            'avatar': u.profile.get_avatar_url() if hasattr(u, 'profile') else None
        }
        for u in photo.tagged_members.select_related('profile').all()
    ]
    
    return JsonResponse({
        'success': True,
        'is_tagged': is_tagged,
        'member_id': target_user.id,
        'tagged_members': tagged_list
    })


@login_required
@herrklubb_member_required
@require_POST
def toggle_photo_like_view(request, photo_id):
    """Toggle a heart reaction on a photo."""
    photo = get_object_or_404(Photo, id=photo_id)
    like_obj = PhotoLike.objects.filter(photo=photo, user=request.user).first()
    
    if like_obj:
        like_obj.delete()
        liked = False
    else:
        PhotoLike.objects.create(photo=photo, user=request.user)
        liked = True
        
    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': photo.likes.count()
    })


@login_required
@herrklubb_member_required
def download_photo_view(request, photo_id):
    """Download single high-res original photo."""
    photo = get_object_or_404(Photo, id=photo_id)
    
    if not photo.image or not os.path.exists(photo.image.path):
        messages.error(request, "Bildfilen kunde inte hittas på servern.")
        return redirect('album_detail', album_id=photo.album_id)
        
    album_slug = slugify(photo.album.title) or "album"
    ext = os.path.splitext(photo.image.name)[1].lower() or ".jpg"
    safe_filename = f"ToarpsHK_{album_slug}_{photo.id}{ext}"
    
    mime_type, _ = mimetypes.guess_type(photo.image.path)
    if not mime_type:
        mime_type = 'application/octet-stream'
        
    with open(photo.image.path, 'rb') as f:
        file_data = f.read()
        
    response = HttpResponse(file_data, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
    return response


@login_required
@herrklubb_member_required
def download_album_zip_view(request, album_id):
    """Pack all original high-resolution photos in an album into a ZIP file and download."""
    album = get_object_or_404(PhotoAlbum, id=album_id)
    photos = album.photos.all()
    
    if not photos.exists():
        messages.warning(request, "Albumet innehåller inga bilder att ladda ner.")
        return redirect('album_detail', album_id=album.id)
        
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, photo in enumerate(photos, start=1):
            if photo.image and os.path.exists(photo.image.path):
                ext = os.path.splitext(photo.image.name)[1].lower() or ".jpg"
                date_prefix = photo.taken_at.strftime('%Y%m%d_') if photo.taken_at else ""
                uploader_name = slugify(photo.uploader.profile.get_nickname() if hasattr(photo.uploader, 'profile') else photo.uploader.username) or "medlem"
                arch_filename = f"{idx:03d}_{date_prefix}{uploader_name}{ext}"
                zip_file.write(photo.image.path, arcname=arch_filename)
                
    buffer.seek(0)
    album_slug = slugify(album.title) or f"album_{album.id}"
    zip_filename = f"ToarpsHK_{album_slug}.zip"
    
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    return response

