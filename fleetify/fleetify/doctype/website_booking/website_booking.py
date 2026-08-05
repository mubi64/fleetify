# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import get_datetime, nowdate


class WebsiteBooking(Document):
	def autoname(self):
		year, month, _day = nowdate().split("-")
		self.name = make_autoname(f"FL-WB-{year}-{month}-.######")

	def validate(self):
		self.validate_dates()
		self.fetch_rent_from_vehicle()

	def validate_dates(self):
		if self.start_date_time and self.end_date_time:
			if get_datetime(self.end_date_time) <= get_datetime(self.start_date_time):
				frappe.throw(_("End Date Time must be after Start Date Time"))

	def fetch_rent_from_vehicle(self):
		if self.rent or not self.vehicle:
			return

		rate_field = {
			"Daily": "daily_rate",
			"Weekly": "weekly_rate",
			"Monthly": "monthly_rate",
		}.get(self.date_type or "Daily")

		self.rent = frappe.db.get_value("Rental Vehicle", self.vehicle, rate_field)
