from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from .models import (
    Appointment,
    Service,
    Staff,
    SalonInfo,
    SalonClosedDate,
)


class AppointmentForm(forms.ModelForm):

    appointment_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date'}
        )
    )

    appointment_time = forms.TimeField(
        input_formats=['%H:%M'],
        widget=forms.Select()
    )

    class Meta:
        model = Appointment

        fields = [
            'name',
            'phone',
            'service',
            'staff',
            'appointment_date',
            'appointment_time',
            'message',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your Name',
                'autocomplete': 'name',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '10-digit mobile number',
                'maxlength': '10',
                'inputmode': 'numeric',
                'autocomplete': 'tel',
            }),
            'service': forms.Select(),
            'staff': forms.Select(),
            'message': forms.Textarea(attrs={
                'placeholder': 'Any special request...',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['service'].queryset = Service.objects.filter(
            is_active=True
        )
        self.fields['service'].empty_label = "Select Service"

        self.fields['staff'].queryset = Staff.objects.filter(
            is_active=True
        )
        self.fields['staff'].required = True
        self.fields['staff'].empty_label = "Select Barber / Stylist"

        self.fields['appointment_date'].widget.attrs['min'] = (
            timezone.localdate().isoformat()
        )

        self.fields['appointment_time'].widget.choices = [
            ('', 'Select service, barber and date first')
        ]

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if len(name) < 2:
            raise forms.ValidationError(
                "Please enter a valid name."
            )

        return name

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()

        if not phone.isdigit():
            raise forms.ValidationError(
                "Phone number must contain only numbers."
            )

        if len(phone) != 10:
            raise forms.ValidationError(
                "Please enter a valid 10-digit mobile number."
            )

        if phone[0] not in ['6', '7', '8', '9']:
            raise forms.ValidationError(
                "Please enter a valid Indian mobile number."
            )

        return phone

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data['appointment_date']

        if appointment_date < timezone.localdate():
            raise forms.ValidationError(
                "Please select today or a future date."
            )

        salon_info = SalonInfo.objects.first()

        if (
            salon_info
            and salon_info.weekly_closed_day
            and appointment_date.strftime('%A')
            == salon_info.weekly_closed_day
        ):
            raise forms.ValidationError(
                f"Salon is closed every "
                f"{salon_info.weekly_closed_day}. "
                "Please select another date."
            )

        closed_date = SalonClosedDate.objects.filter(
            date=appointment_date,
            is_active=True
        ).first()

        if closed_date:
            if closed_date.reason:
                raise forms.ValidationError(
                    f"Salon is closed on this date: "
                    f"{closed_date.reason}. "
                    "Please select another date."
                )

            raise forms.ValidationError(
                "Salon is closed on this date. "
                "Please select another date."
            )

        return appointment_date

    def clean(self):
        cleaned_data = super().clean()

        service = cleaned_data.get('service')
        staff = cleaned_data.get('staff')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        if (
            not service
            or not staff
            or not appointment_date
            or not appointment_time
        ):
            return cleaned_data

        salon_info = SalonInfo.objects.first()

        if not salon_info:
            self.add_error(
                'appointment_time',
                'Salon opening hours are not configured.'
            )
            return cleaned_data

        opening_time = salon_info.opening_time.replace(
            second=0,
            microsecond=0
        )

        closing_time = salon_info.closing_time.replace(
            second=0,
            microsecond=0
        )

        appointment_time = appointment_time.replace(
            second=0,
            microsecond=0
        )

        opening_datetime = datetime.combine(
            appointment_date,
            opening_time
        )

        closing_datetime = datetime.combine(
            appointment_date,
            closing_time
        )

        appointment_start = datetime.combine(
            appointment_date,
            appointment_time
        )

        appointment_end = (
            appointment_start
            + timedelta(minutes=service.duration_minutes)
        )

        if appointment_start < opening_datetime:
            self.add_error(
                'appointment_time',
                (
                    'Salon opens at '
                    f'{opening_time.strftime("%I:%M %p")}.'
                )
            )

        if appointment_end > closing_datetime:
            self.add_error(
                'appointment_time',
                (
                    f'{service.name} takes '
                    f'{service.duration_minutes} minutes. '
                    'Please select an earlier time.'
                )
            )

        opening_minutes = (
            opening_time.hour * 60
            + opening_time.minute
        )

        selected_minutes = (
            appointment_time.hour * 60
            + appointment_time.minute
        )

        difference_minutes = (
            selected_minutes
            - opening_minutes
        )

        if (
            difference_minutes < 0
            or difference_minutes % 30 != 0
        ):
            self.add_error(
                'appointment_time',
                'Please select a valid appointment time slot.'
            )

        if appointment_date == timezone.localdate():
            current_time = (
                timezone.localtime()
                .time()
                .replace(
                    second=0,
                    microsecond=0
                )
            )

            if appointment_time <= current_time:
                self.add_error(
                    'appointment_time',
                    (
                        'This time has already passed. '
                        'Please select another time.'
                    )
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

        if self.instance.pk:
            existing_appointments = (
                existing_appointments.exclude(
                    pk=self.instance.pk
                )
            )

        for existing in existing_appointments:
            existing_start = datetime.combine(
                appointment_date,
                existing.appointment_time.replace(
                    second=0,
                    microsecond=0
                )
            )

            existing_end = (
                existing_start
                + timedelta(
                    minutes=existing.service.duration_minutes
                )
            )

            if (
                appointment_start < existing_end
                and appointment_end > existing_start
            ):
                self.add_error(
                    'appointment_time',
                    (
                        f'{staff.name} is busy during '
                        'this service time. '
                        'Please select another available time.'
                    )
                )
                break

        cleaned_data['appointment_time'] = appointment_time

        return cleaned_data
