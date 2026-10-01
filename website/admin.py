from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Appointment,
    Service,
    Gallery,
    SalonInfo,
    Staff,
    SalonClosedDate,
)


# ==========================================
# APPOINTMENT ADMIN
# ==========================================

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        'customer_name',
        'phone',
        'service',
        'service_duration',
        'staff',
        'appointment_date',
        'appointment_time',
        'colored_status',
        'short_booking_reference',
        'created_at',
    )

    list_filter = (
        'status',
        'appointment_date',
        'service',
        'staff',
        'created_at',
    )

    search_fields = (
        'name',
        'phone',
        'service__name',
        'staff__name',
        'booking_reference',
    )

    ordering = (
        '-appointment_date',
        '-appointment_time',
    )

    date_hierarchy = 'appointment_date'

    list_per_page = 25

    readonly_fields = (
        'booking_reference',
        'created_at',
    )

    fieldsets = (

        (
            'Customer Information',
            {
                'fields': (
                    'name',
                    'phone',
                )
            }
        ),

        (
            'Appointment Details',
            {
                'fields': (
                    'service',
                    'staff',
                    'appointment_date',
                    'appointment_time',
                    'message',
                )
            }
        ),

        (
            'Appointment Status',
            {
                'fields': (
                    'status',
                )
            }
        ),

        (
            'Booking Information',
            {
                'fields': (
                    'booking_reference',
                    'created_at',
                )
            }
        ),

    )

    actions = (
        'mark_as_pending',
        'mark_as_confirmed',
        'mark_as_completed',
        'mark_as_cancelled',
    )

    # ======================================
    # CUSTOMER NAME
    # ======================================

    @admin.display(
        description='Customer',
        ordering='name'
    )
    def customer_name(self, obj):
        return obj.name

    # ======================================
    # SERVICE DURATION
    # ======================================

    @admin.display(description='Duration')
    def service_duration(self, obj):
        return f"{obj.service.duration_minutes} min"

    # ======================================
    # SHORT BOOKING REFERENCE
    # ======================================

    @admin.display(description='Booking Ref')
    def short_booking_reference(self, obj):

        reference = str(obj.booking_reference)

        return reference[:8] + "..."

    # ======================================
    # COLORED STATUS
    # ======================================

    @admin.display(
        description='Status',
        ordering='status'
    )
    def colored_status(self, obj):

        status_styles = {
            'Pending': {
                'background': '#f59e0b',
                'color': '#000000',
            },
            'Confirmed': {
                'background': '#22c55e',
                'color': '#000000',
            },
            'Completed': {
                'background': '#3b82f6',
                'color': '#ffffff',
            },
            'Cancelled': {
                'background': '#ef4444',
                'color': '#ffffff',
            },
        }

        style = status_styles.get(
            obj.status,
            {
                'background': '#6b7280',
                'color': '#ffffff',
            }
        )

        return format_html(
            '<span style="'
            'background:{};'
            'color:{};'
            'padding:5px 10px;'
            'border-radius:12px;'
            'font-weight:600;'
            'display:inline-block;'
            '">'
            '{}'
            '</span>',
            style['background'],
            style['color'],
            obj.status,
        )

    # ======================================
    # BULK ACTION - PENDING
    # ======================================

    @admin.action(
        description='Mark selected appointments as Pending'
    )
    def mark_as_pending(self, request, queryset):

        updated = queryset.update(
            status='Pending'
        )

        self.message_user(
            request,
            f"{updated} appointment(s) marked as Pending."
        )

    # ======================================
    # BULK ACTION - CONFIRMED
    # ======================================

    @admin.action(
        description='Mark selected appointments as Confirmed'
    )
    def mark_as_confirmed(self, request, queryset):

        updated = queryset.update(
            status='Confirmed'
        )

        self.message_user(
            request,
            f"{updated} appointment(s) marked as Confirmed."
        )

    # ======================================
    # BULK ACTION - COMPLETED
    # ======================================

    @admin.action(
        description='Mark selected appointments as Completed'
    )
    def mark_as_completed(self, request, queryset):

        updated = queryset.update(
            status='Completed'
        )

        self.message_user(
            request,
            f"{updated} appointment(s) marked as Completed."
        )

    # ======================================
    # BULK ACTION - CANCELLED
    # ======================================

    @admin.action(
        description='Mark selected appointments as Cancelled'
    )
    def mark_as_cancelled(self, request, queryset):

        updated = queryset.update(
            status='Cancelled'
        )

        self.message_user(
            request,
            f"{updated} appointment(s) marked as Cancelled."
        )


# ==========================================
# SERVICE ADMIN
# ==========================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'price',
        'duration_minutes',
        'is_active',
    )

    list_editable = (
        'price',
        'duration_minutes',
        'is_active',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
    )

    ordering = (
        'name',
    )


# ==========================================
# GALLERY ADMIN
# ==========================================

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'is_active',
        'created_at',
    )

    list_editable = (
        'is_active',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'title',
    )

    ordering = (
        '-created_at',
    )


# ==========================================
# SALON INFORMATION ADMIN
# ==========================================

@admin.register(SalonInfo)
class SalonInfoAdmin(admin.ModelAdmin):

    list_display = (
        'salon_name',
        'phone',
        'opening_days',
        'weekly_closed_day',
        'opening_time',
        'closing_time',
    )

    fieldsets = (

        (
            'Salon Details',
            {
                'fields': (
                    'salon_name',
                    'phone',
                    'whatsapp_number',
                    'email',
                    'address',
                )
            }
        ),

        (
            'Opening Hours',
            {
                'fields': (
                    'opening_days',
                    'weekly_closed_day',
                    'opening_time',
                    'closing_time',
                )
            }
        ),

    )

    def has_add_permission(self, request):

        if SalonInfo.objects.exists():
            return False

        return super().has_add_permission(request)


# ==========================================
# STAFF ADMIN
# ==========================================

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'specialization',
        'experience_years',
        'is_active',
    )

    list_editable = (
        'is_active',
    )

    search_fields = (
        'name',
        'specialization',
    )

    list_filter = (
        'is_active',
    )

    ordering = (
        'name',
    )


# ==========================================
# CLOSED DATE / HOLIDAY ADMIN
# ==========================================

@admin.register(SalonClosedDate)
class SalonClosedDateAdmin(admin.ModelAdmin):

    list_display = (
        'date',
        'reason',
        'is_active',
    )

    list_editable = (
        'is_active',
    )

    list_filter = (
        'is_active',
        'date',
    )

    search_fields = (
        'reason',
    )

    ordering = (
        'date',
    )

    date_hierarchy = 'date'