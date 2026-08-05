# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate

from fleetify.fleetify.rebilling import calculate_vat, rebill_to_agreement


class TrafficFine(Document):
	def autoname(self):
		year, month, _day = nowdate().split("-")
		self.name = make_autoname(f"FL-TF-{year}-{month}-.######")

	def validate(self):
		calculate_vat(self)
		self.link_agreement()

	def link_agreement(self):
		"""Match the fine to whichever agreement held the vehicle at the time."""
		if self.rental_agreement or not (self.vehicle and self.date_time):
			return

		self.rental_agreement = frappe.db.get_value(
			"Rental Agreement",
			{
				"vehicle": self.vehicle,
				"pickup_date_and_time": ("<=", self.date_time),
				"dropoff_date_and_time": (">=", self.date_time),
				"docstatus": 1,
			},
			"name",
		)


@frappe.whitelist()
def rebill(name):
	"""Push this fine onto its agreement's additional charges."""
	fine = frappe.get_doc("Traffic Fine", name)
	label = f"Traffic Fine {fine.ticket_number or fine.name} - {fine.date_time}"
	return rebill_to_agreement(fine, label)
