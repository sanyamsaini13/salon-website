from django.urls import path

from . import views


urlpatterns = [

    # =====================================================
    # HOME
    # =====================================================

    path(
        '',
        views.home,
        name='home'
    ),


    # =====================================================
    # AVAILABLE TIME SLOTS
    # =====================================================

    path(
        'available-slots/',
        views.available_slots,
        name='available_slots'
    ),


    # =====================================================
    # BOOKING SUCCESS
    # =====================================================

    path(
        'booking-success/<uuid:booking_reference>/',
        views.booking_success,
        name='booking_success'
    ),


    # =====================================================
    # CHECK BOOKING
    # =====================================================

    path(
        'check-booking/',
        views.check_booking,
        name='check_booking'
    ),


    # =====================================================
    # CANCEL BOOKING
    # =====================================================

    path(
        'cancel-booking/<uuid:booking_reference>/',
        views.cancel_booking,
        name='cancel_booking'
    ),

]