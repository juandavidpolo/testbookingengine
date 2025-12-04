from django.test import TestCase, Client
from pms.models import Booking, Room, Customer, Room_type
from pms.views import DashboardView
from django.db.models import Sum
from django.utils.timezone import now
import datetime

# TODO
# Comment line when STATICFILES_STORAGE is defined in
# chapp/settings.py To able to run the tests successfully


def global_setUp(self):
    today = datetime.date.today()
    self.client = Client()
    # create room types
    Room_type.objects.create(id=1, name="Simple", price=20, max_guests=1)
    Room_type.objects.create(id=2, name="Doble", price=30, max_guests=2)
    Room_type.objects.create(id=3, name="Tripe", price=40, max_guests=3)
    Room_type.objects.create(id=4, name="Cuadruple", price=50, max_guests=4)

    # Create rooms
    self.room1 = Room.objects.create(
        id=1, description="", name="Room 1.1", room_type_id=1
    )
    self.room2 = Room.objects.create(
        id=2, description="", name="Room 1.2", room_type_id=1
    )
    self.room3 = Room.objects.create(
        id=3, description="", name="Room 1.3", room_type_id=1
    )
    self.room4 = Room.objects.create(
        id=4, description="", name="Room 2.1", room_type_id=2
    )
    self.room5 = Room.objects.create(
        id=5, description="", name="Room 2.2", room_type_id=2
    )
    self.room6 = Room.objects.create(
        id=6, description="", name="Room 3.1", room_type_id=3
    )
    self.room7 = Room.objects.create(
        id=7, description="", name="Room 4.1", room_type_id=4
    )

    # Create customers
    self.customer1 = Customer.objects.create(
        id=1, name="test customer 1", email="customer1@test.com", phone="1231233223"
    )
    self.customer2 = Customer.objects.create(
        id=2, name="test customer 2", email="customer2@test.com", phone="1231233223"
    )
    self.customer3 = Customer.objects.create(
        id=3, name="test customer 3", email="customer3@test.com", phone="1231233223"
    )

    # Create bookings
    Booking.objects.create(
        checkin=today,
        checkout=today + datetime.timedelta(days=2),
        created=now(),
        state="NEW",
        guests=1,
        customer_id=self.customer1.id,
        room=self.room1,
        total=40,
        code="ABC123",
    )
    Booking.objects.create(
        checkin=today - datetime.timedelta(days=1),
        checkout=today,
        created=now(),
        state="DEL",
        guests=1,
        customer_id=self.customer2.id,
        room=self.room2,
        total=20,
        code="ABC124A",
    )
    Booking.objects.create(
        checkin=today - datetime.timedelta(days=1),
        checkout=today + datetime.timedelta(days=3),
        created=now(),
        state="NEW",
        guests=1,
        customer_id=self.customer3.id,
        room=self.room3,
        total=80,
        code="ABC124X",
    )


class DashboardViewTest(TestCase):
    setUp = global_setUp

    def test_dashboard_view(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        dashboard = response.context["dashboard"]

        today = datetime.date.today()
        today_min = datetime.datetime.combine(today, datetime.time.min)
        today_max = datetime.datetime.combine(today, datetime.time.max)

        # check new bookings
        expected_new_bookings = (
            Booking.objects.filter(created__range=(today_min, today_max))
            .values("id")
            .count()
        )
        self.assertEqual(dashboard["new_bookings"], expected_new_bookings)

        # check incoming guests
        expected_incoming = (
            Booking.objects.filter(checkin=today)
            .exclude(state="DEL")
            .values("id")
            .count()
        )
        self.assertEqual(dashboard["incoming_guests"], expected_incoming)

        # check outcoming guests
        expected_outcoming = (
            Booking.objects.filter(checkout=today)
            .exclude(state="DEL")
            .values("id")
            .count()
        )
        self.assertEqual(dashboard["outcoming_guests"], expected_outcoming)

        # check occupancy
        expected_occupancy = (
            Booking.objects.filter(checkin__lte=today, checkout__gte=today)
            .exclude(state="DEL")
            .count()
            / Room.objects.all().count()
        ) * 100
        self.assertEqual(dashboard["occupancy"], expected_occupancy)

        # check invoiced
        expected_invoiced = (
            Booking.objects.filter(created__range=(today_min, today_max))
            .exclude(state="DEL")
            .aggregate(Sum("total"))
        )
        self.assertEqual(dashboard["invoiced"], expected_invoiced)
