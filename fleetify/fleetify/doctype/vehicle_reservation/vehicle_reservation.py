# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import nowdate
import frappe


class VehicleReservation(Document):
	def autoname(self):
		date = nowdate()  # gives '2025-07-10'
		year, month, _ = date.split('-')
		prefix = f"FL-VR-{year}-{month}"

		self.name = make_autoname(f"{prefix}-.######")
