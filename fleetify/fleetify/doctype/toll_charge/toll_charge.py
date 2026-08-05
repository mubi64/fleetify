# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate

from fleetify.fleetify.rebilling import calculate_vat, rebill_to_agreement


class TollCharge(Document):
	def autoname(self):
		year, month, _day = nowdate().split("-")
		self.name = make_autoname(f"FL-TC-{year}-{month}-.######")

	def validate(self):
		calculate_vat(self)
		self.link_agreement()

	def link_agreement(self):
		"""Match the crossing to whichever agreement held the vehicle at the time."""
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
	"""Push this toll onto its agreement's additional charges."""
	toll = frappe.get_doc("Toll Charge", name)
	label = f"{toll.toll_type} {toll.date_time}"
	if toll.location:
		label += f" - {toll.location}"

	return rebill_to_agreement(toll, label)
