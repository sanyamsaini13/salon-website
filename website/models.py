import uuid

from django.db import models
from django.db.models import Q


# ==========================================
# SERVICE MODEL
# ==========================================

class Service(models.Model):

    name = models.CharField(max_length=100)

    description = models.TextField()

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Service duration in minutes. Example: 30, 60, 90"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==========================================
# STAFF / BARBER MODEL
# ==========================================

class Staff(models.Model):

    name = models.CharField(max_length=100)

    specialization = models.CharField(max_length=150)

    experience_years = models.PositiveIntegerField(default=0)

    photo = models.ImageField(
        upload_to='staff/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Staff Member"
        verbose_name_plural = "Staff Members"
        ordering = ['name']


# ==========================================
# APPOINTMENT MODEL
# ==========================================

class Appointment(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    booking_reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name='appointments',
        blank=True,
        null=True
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    message = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.service.name} - "
            f"{self.appointment_date} "
            f"{self.appointment_time}"
        )

    class Meta:
        ordering = [
            '-appointment_date',
            '-appointment_time',
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'staff',
                    'appointment_date',
                    'appointment_time',
                ],
                condition=~Q(status='Cancelled'),
                name='unique_active_staff_slot',
            )
        ]


# ==========================================
# GALLERY MODEL
# ==========================================

class Gallery(models.Model):

    title = models.CharField(max_length=100)

    image = models.ImageField(upload_to='gallery/')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Gallery"
        ordering = ['-created_at']


# ==========================================
# SALON INFORMATION MODEL
# ==========================================

class SalonInfo(models.Model):

    WEEKDAY_CHOICES = [
        ('', 'No Weekly Closed Day'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    salon_name = models.CharField(
        max_length=100,
        default="Elite Salon"
    )

    phone = models.CharField(max_length=20)

    whatsapp_number = models.CharField(max_length=20)

    address = models.TextField()

    opening_days = models.CharField(
        max_length=100,
        default="Monday - Sunday"
    )

    weekly_closed_day = models.CharField(
        max_length=10,
        choices=WEEKDAY_CHOICES,
        blank=True,
        default='',
        help_text="Choose the salon's regular weekly closed day, if any."
    )

    opening_time = models.TimeField()

    closing_time = models.TimeField()

    email = models.EmailField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.salon_name

    class Meta:
        verbose_name = "Salon Information"
        verbose_name_plural = "Salon Information"


# ==========================================
# SPECIAL CLOSED DATE / HOLIDAY MODEL
# ==========================================

class SalonClosedDate(models.Model):

    date = models.DateField(unique=True)

    reason = models.CharField(
        max_length=200,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.reason:
            return f"{self.date} - {self.reason}"
        return str(self.date)

    class Meta:
        verbose_name = "Salon Closed Date"
        verbose_name_plural = "Salon Closed Dates"
        ordering = ['date']
