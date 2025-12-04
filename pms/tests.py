from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from pms.models import Booking, Room, Customer, Room_type
from django.urls import reverse
from django.db.models import Sum
from django.utils.timezone import now
from .forms import *
from unittest.mock import patch

from datetime import datetime, timedelta, date, time


def global_setUp(self):
    today = date.today()
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
        checkout=today + timedelta(days=2),
        created=now(),
        state="NEW",
        guests=1,
        customer_id=self.customer1.id,
        room=self.room1,
        total=40,
        code="ABC123",
    )
    Booking.objects.create(
        checkin=today - timedelta(days=1),
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
        checkin=today - timedelta(days=1),
        checkout=today + timedelta(days=3),
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

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_dashboard_view(self, mock_static_url):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        dashboard = response.context["dashboard"]

        today = date.today()
        today_min = datetime.combine(today, time.min)
        today_max = datetime.combine(today, time.max)
        expected_new_bookings = (
            Booking.objects.filter(created__range=(today_min, today_max))
            .values("id")
            .count()
        )
        self.assertEqual(dashboard["new_bookings"], expected_new_bookings)
        expected_incoming = (
            Booking.objects.filter(checkin=today)
            .exclude(state="DEL")
            .values("id")
            .count()
        )
        self.assertEqual(dashboard["incoming_guests"], expected_incoming)

        expected_outcoming = (
            Booking.objects.filter(checkout=today)
            .exclude(state="DEL")
            .values("id")
            .count()
        )
        self.assertEqual(dashboard["outcoming_guests"], expected_outcoming)

        expected_occupancy = (
            Booking.objects.filter(checkin__lte=today, checkout__gte=today)
            .exclude(state="DEL")
            .count()
            / Room.objects.all().count()
        ) * 100
        self.assertEqual(dashboard["occupancy"], expected_occupancy)

        expected_invoiced = (
            Booking.objects.filter(created__range=(today_min, today_max))
            .exclude(state="DEL")
            .aggregate(Sum("total"))
        )
        self.assertEqual(dashboard["invoiced"], expected_invoiced)


class BookingSearchViewTest(TestCase):
    setUp = global_setUp

    def setUp(self):
        global_setUp(self)
        self.url = reverse("booking_search")

    def test_redirect_when_no_filter(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_filter_matches_code(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"
        response = self.client.get(self.url, {"filter": "ABC"})
        self.assertEqual(response.status_code, 200)
        bookings = response.context["bookings"]
        self.assertEqual(len(bookings), 3)
        self.assertIn("ABC123", [b.code for b in bookings])
        self.assertIn("ABC124X", [b.code for b in bookings])

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_filter_matches_customer_name(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"
        response = self.client.get(self.url, {"filter": "test customer 1"})
        self.assertEqual(response.status_code, 200)

        bookings = response.context["bookings"]
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0].customer.name, "test customer 1")

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_filter_no_matches(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"
        response = self.client.get(self.url, {"filter": "NOPE"})
        self.assertEqual(response.status_code, 200)

        bookings = response.context["bookings"]
        self.assertEqual(len(bookings), 0)

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_uses_correct_template(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"
        response = self.client.get(self.url, {"filter": "ABC"})
        self.assertTemplateUsed(response, "home.html")

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_context_contains_expected_items(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"
        response = self.client.get(self.url, {"filter": "ABC"})

        self.assertIn("bookings", response.context)
        self.assertIn("form", response.context)
        self.assertIn("filter", response.context)
        self.assertIsInstance(response.context["form"], RoomSearchForm)
        self.assertTrue(response.context["filter"])


class HomeViewTest(TestCase):
    def setUp(self):
        global_setUp(self)
        self.url = reverse("home")

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_home_view_status_code_and_template(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_home_view_context_contains_bookings(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"

        response = self.client.get(self.url)
        self.assertIn("bookings", response.context)
        bookings = response.context["bookings"]
        self.assertEqual(len(bookings), 3)

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_home_view_empty_bookings(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"
        Booking.objects.all().delete()
        response = self.client.get(self.url)
        bookings = response.context["bookings"]
        self.assertEqual(len(bookings), 0)


class RoomSearchViewTest(TestCase):
    def setUp(self):
        global_setUp(self)
        self.url = reverse("search")

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    def test_get_returns_form(self, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "booking_search_form.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], RoomSearchForm)

    @patch("django.contrib.staticfiles.storage.staticfiles_storage.url")
    @patch("pms.models.Room.objects")
    def test_post_returns_search_results(self, mock_rooms_objects, mock_static_url):
        mock_static_url.side_effect = lambda path: f"/static/{path}"

        mock_room_instance = MagicMock()
        mock_room_instance.name = "Room 101"
        mock_room_instance.room_type__max_guests = 2
        mock_room_instance.room_type__price = 100

        mock_qs = MagicMock()
        mock_qs.exclude.return_value.annotate.return_value.order_by.return_value = [
            mock_room_instance
        ]
        mock_rooms_objects.filter.return_value = mock_qs

        mock_total_qs = MagicMock()
        mock_total_qs.exclude.return_value.annotate.return_value.order_by.return_value = [
            {"room_type__name": "Standard", "room_type": 1, "total": 2}
        ]
        mock_rooms_objects.filter.return_value = mock_total_qs

        checkin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        guests = "2"

        post_data = {"checkin": checkin, "checkout": checkout, "guests": guests}
        response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search.html")

        self.assertIn("rooms", response.context)
        self.assertIn("total_rooms", response.context)
        self.assertIn("query", response.context)
        self.assertIn("url_query", response.context)
        self.assertIn("data", response.context)

        self.assertEqual(response.context["query"], post_data)
        self.assertEqual(response.context["data"]["total_days"], 2)
