from datetime import datetime, timedelta

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.http import JsonResponse
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.contrib import messages

from .forms import AppointmentForm
from .models import (
    Appointment,
    Service,
    Gallery,
    SalonInfo,
    Staff,
    SalonClosedDate,
)


# ==========================================
# HOME
# ==========================================

def home(request):

    services = Service.objects.filter(is_active=True)

    gallery_images = Gallery.objects.filter(is_active=True)

    salon_info = SalonInfo.objects.first()

    staff_members = Staff.objects.filter(is_active=True)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    appointment = form.save()

                return redirect(
                    'booking_success',
                    booking_reference=appointment.booking_reference
                )

            except IntegrityError:
                form.add_error(
                    'appointment_time',
                    (
                        'This appointment time was just '
                        'booked by another customer. '
                        'Please choose another time.'
                    )
                )

    else:
        form = AppointmentForm()

    return render(
        request,
        'website/home.html',
        {
            'form': form,
            'services': services,
            'gallery_images': gallery_images,
            'salon_info': salon_info,
            'staff_members': staff_members,
        }
    )


# ==========================================
# BOOKING SUCCESS
# ==========================================

def booking_success(request, booking_reference):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'service',
            'staff'
        ),
        booking_reference=booking_reference
    )

    return render(
        request,
        'website/booking_success.html',
        {
            'appointment': appointment,
            'salon_info': SalonInfo.objects.first(),
        }
    )


# ==========================================
# CHECK BOOKING
# ==========================================

def check_booking(request):

    appointment = None
    error_message = None
    booking_reference = ''

    if request.method == 'POST':

        booking_reference = request.POST.get(
            'booking_reference',
            ''
        ).strip()

        if not booking_reference:
            error_message = (
                'Please enter your booking reference.'
            )

        else:
            try:
                appointment = (
                    Appointment.objects
                    .select_related(
                        'service',
                        'staff'
                    )
                    .get(
                        booking_reference=booking_reference
                    )
                )

            except (
                Appointment.DoesNotExist,
                ValueError,
            ):
                error_message = (
                    'No appointment was found with '
                    'this booking reference. '
                    'Please check the reference '
                    'and try again.'
                )

    can_cancel = False

    if appointment:

        today = timezone.localdate()

        current_time = (
            timezone.localtime()
            .time()
            .replace(
                second=0,
                microsecond=0
            )
        )

        appointment_time = (
            appointment.appointment_time
            .replace(
                second=0,
                microsecond=0
            )
        )

        if appointment.status in [
            'Pending',
            'Confirmed',
        ]:

            if appointment.appointment_date > today:
                can_cancel = True

            elif (
                appointment.appointment_date == today
                and appointment_time > current_time
            ):
                can_cancel = True

    return render(
        request,
        'website/check_booking.html',
        {
            'appointment': appointment,
            'error_message': error_message,
            'booking_reference': booking_reference,
            'salon_info': SalonInfo.objects.first(),
            'can_cancel': can_cancel,
        }
    )


# ==========================================
# CANCEL BOOKING
# ==========================================

def cancel_booking(request, booking_reference):

    if request.method != 'POST':
        return redirect('check_booking')

    appointment = get_object_or_404(
        Appointment,
        booking_reference=booking_reference
    )

    today = timezone.localdate()

    current_time = (
        timezone.localtime()
        .time()
        .replace(
            second=0,
            microsecond=0
        )
    )

    appointment_time = (
        appointment.appointment_time
        .replace(
            second=0,
            microsecond=0
        )
    )

    if appointment.status == 'Cancelled':
        messages.info(
            request,
            'This appointment is already cancelled.'
        )
        return redirect('check_booking')

    if appointment.status == 'Completed':
        messages.error(
            request,
            'Completed appointments cannot be cancelled.'
        )
        return redirect('check_booking')

    if appointment.appointment_date < today:
        messages.error(
            request,
            'Past appointments cannot be cancelled.'
        )
        return redirect('check_booking')

    if (
        appointment.appointment_date == today
        and appointment_time <= current_time
    ):
        messages.error(
            request,
            (
                'This appointment time has already '
                'passed and cannot be cancelled.'
            )
        )
        return redirect('check_booking')

    if appointment.status not in [
        'Pending',
        'Confirmed',
    ]:
        messages.error(
            request,
            'This appointment cannot be cancelled.'
        )
        return redirect('check_booking')

    appointment.status = 'Cancelled'

    appointment.save(
        update_fields=['status']
    )

    messages.success(
        request,
        (
            'Your appointment has been cancelled '
            'successfully. The time slot is now '
            'available for booking again.'
        )
    )

    return redirect('check_booking')


# ==========================================
# SMART AVAILABLE SLOTS
# ==========================================

def available_slots(request):

    service_id = request.GET.get('service')
    staff_id = request.GET.get('staff')
    selected_date = request.GET.get('date')

    if (
        not service_id
        or not staff_id
        or not selected_date
    ):
        return JsonResponse({
            'slots': [],
            'message': (
                'Please select a service, '
                'barber and appointment date.'
            ),
        })

    try:
        service = Service.objects.get(
            id=service_id,
            is_active=True
        )

    except (
        Service.DoesNotExist,
        ValueError,
        TypeError,
    ):
        return JsonResponse({
            'slots': [],
            'message': 'Invalid service selected.',
        }, status=400)

    try:
        staff = Staff.objects.get(
            id=staff_id,
            is_active=True
        )

    except (
        Staff.DoesNotExist,
        ValueError,
        TypeError,
    ):
        return JsonResponse({
            'slots': [],
            'message': 'Invalid barber selected.',
        }, status=400)

    try:
        appointment_date = datetime.strptime(
            selected_date,
            '%Y-%m-%d'
        ).date()

    except ValueError:
        return JsonResponse({
            'slots': [],
            'message': 'Invalid date.',
        }, status=400)

    today = timezone.localdate()

    if appointment_date < today:
        return JsonResponse({
            'slots': [],
            'message': (
                'Appointments cannot be booked '
                'for past dates.'
            ),
        }, status=400)

    salon_info = SalonInfo.objects.first()

    if not salon_info:
        return JsonResponse({
            'slots': [],
            'message': (
                'Salon opening hours '
                'are not configured.'
            ),
        }, status=400)

    # ======================================
    # WEEKLY CLOSED DAY
    # ======================================

    if (
        salon_info.weekly_closed_day
        and appointment_date.strftime('%A')
        == salon_info.weekly_closed_day
    ):
        return JsonResponse({
            'slots': [],
            'message': (
                f'Salon is closed every '
                f'{salon_info.weekly_closed_day}. '
                'Please select another date.'
            ),
        })

    # ======================================
    # SPECIAL CLOSED DATE / HOLIDAY
    # ======================================

    closed_date = SalonClosedDate.objects.filter(
        date=appointment_date,
        is_active=True
    ).first()

    if closed_date:

        if closed_date.reason:
            message = (
                f'Salon is closed on this date: '
                f'{closed_date.reason}. '
                'Please select another date.'
            )
        else:
            message = (
                'Salon is closed on this date. '
                'Please select another date.'
            )

        return JsonResponse({
            'slots': [],
            'message': message,
        })

    opening_time = (
        salon_info.opening_time
        .replace(
            second=0,
            microsecond=0
        )
    )

    closing_time = (
        salon_info.closing_time
        .replace(
            second=0,
            microsecond=0
        )
    )

    opening_datetime = datetime.combine(
        appointment_date,
        opening_time
    )

    closing_datetime = datetime.combine(
        appointment_date,
        closing_time
    )

    existing_appointments = (
        Appointment.objects
        .filter(
            staff=staff,
            appointment_date=appointment_date,
        )
        .exclude(status='Cancelled')
        .select_related('service')
    )

    occupied_periods = []

    for appointment in existing_appointments:

        existing_start = datetime.combine(
            appointment_date,
            appointment.appointment_time.replace(
                second=0,
                microsecond=0
            )
        )

        existing_end = (
            existing_start
            + timedelta(
                minutes=appointment.service.duration_minutes
            )
        )

        occupied_periods.append(
            (
                existing_start,
                existing_end
            )
        )

    slots = []

    current_slot = opening_datetime

    slot_step = timedelta(minutes=30)

    service_duration = timedelta(
        minutes=service.duration_minutes
    )

    while current_slot < closing_datetime:

        candidate_start = current_slot

        candidate_end = (
            candidate_start
            + service_duration
        )

        if candidate_end > closing_datetime:
            break

        is_past = False

        if appointment_date == today:

            now = timezone.localtime()

            current_local_datetime = datetime.combine(
                appointment_date,
                now.time().replace(
                    second=0,
                    microsecond=0
                )
            )

            if candidate_start <= current_local_datetime:
                is_past = True

        has_overlap = False

        for (
            existing_start,
            existing_end
        ) in occupied_periods:

            if (
                candidate_start < existing_end
                and candidate_end > existing_start
            ):
                has_overlap = True
                break

        if (
            not is_past
            and not has_overlap
        ):
            slots.append({
                'value': candidate_start.strftime('%H:%M'),
                'label': candidate_start.strftime('%I:%M %p'),
            })

        current_slot += slot_step

    if not slots:
        return JsonResponse({
            'slots': [],
            'message': (
                'No available time slots for '
                f'{service.name} with {staff.name} '
                'on the selected date.'
            ),
        })

    return JsonResponse({
        'slots': slots,
        'message': '',
        'service_duration': service.duration_minutes,
    })
