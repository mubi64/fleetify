# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, get_datetime, nowdate

VAT_RATE = 0.05


class FuelHistory(Document):
	def autoname(self):
		year, month, _day = nowdate().split("-")
		self.name = make_autoname(f"FL-FH-{year}-{month}-.######")

	def validate(self):
		self.calculate_usage()
		self.calculate_fuel_economy()
		self.calculate_cost()

	def calculate_usage(self):
		"""Usage is the distance covered since this vehicle's previous entry."""
		previous_meter = self.get_previous_meter_entry()
		if previous_meter is None:
			self.usage = 0
			return

		if flt(self.meter_entry) < flt(previous_meter):
			frappe.throw(
				_("Meter Entry {0} is lower than the previous reading {1} for this vehicle").format(
					flt(self.meter_entry), flt(previous_meter)
				)
			)

		self.usage = flt(self.meter_entry) - flt(previous_meter)

	def get_previous_meter_entry(self):
		if not (self.vehicle and self.date):
			return None

		return frappe.db.get_value(
			"Fuel History",
			{
				"vehicle": self.vehicle,
				"date": ("<", get_datetime(self.date)),
				"name": ("!=", self.name),
			},
			"meter_entry",
			order_by="date desc",
		)

	def calculate_fuel_economy(self):
		self.fuel_economy = flt(self.usage) / flt(self.volume) if flt(self.volume) else 0

	def calculate_cost(self):
		if not flt(self.amount) and flt(self.cost_per_meter) and flt(self.usage):
			self.amount = flt(self.cost_per_meter) * flt(self.usage)

		self.vat_amount = flt(self.amount) * VAT_RATE if self.add_vat else 0
		self.total_cost = flt(self.amount) + flt(self.vat_amount)
