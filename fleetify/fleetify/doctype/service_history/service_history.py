# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, getdate, nowdate

VAT_RATE = 0.05


class ServiceHistory(Document):
	def autoname(self):
		year, month, _day = nowdate().split("-")
		self.name = make_autoname(f"FL-SH-{year}-{month}-.######")

	def validate(self):
		self.validate_next_service()
		self.calculate_cost()

	def validate_next_service(self):
		if self.next_service_date and self.service_date:
			if getdate(self.next_service_date) <= getdate(self.service_date):
				frappe.throw(_("Next Service Date must be after the Current Service Date"))

		if self.next_service_mileage and flt(self.next_service_mileage) <= flt(self.current_mileage):
			frappe.throw(_("Next Service Mileage must be higher than the Current Mileage"))

	def calculate_cost(self):
		self.vat_amount = flt(self.amount) * VAT_RATE if self.add_vat else 0
		self.total_cost = flt(self.amount) + flt(self.vat_amount)

	def on_update(self):
		self.update_vehicle_mileage()

	def update_vehicle_mileage(self):
		"""Keep the vehicle's odometer in step with the latest service reading."""
		if not (self.vehicle and self.current_mileage):
			return

		if flt(self.current_mileage) > flt(frappe.db.get_value("Rental Vehicle", self.vehicle, "mileage")):
			frappe.db.set_value("Rental Vehicle", self.vehicle, "mileage", flt(self.current_mileage))


def get_service_reminders(overdue=True):
	"""Vehicles whose next service is past due (or coming up within 30 days).

	Backs the `overdue-service-reminders` / `due-soon-reminders` views.
	"""
	latest = frappe.db.sql(
		"""
		select sh.vehicle, sh.next_service_date, sh.next_service_mileage, v.mileage
		from `tabService History` sh
		inner join (
			select vehicle, max(service_date) as service_date
			from `tabService History` group by vehicle
		) last on last.vehicle = sh.vehicle and last.service_date = sh.service_date
		left join `tabRental Vehicle` v on v.name = sh.vehicle
		where sh.next_service_date is not null
		""",
		as_dict=True,
	)

	today = getdate(nowdate())
	rows = []
	for row in latest:
		days_left = (getdate(row.next_service_date) - today).days
		km_left = flt(row.next_service_mileage) - flt(row.mileage) if row.next_service_mileage else None
		is_overdue = days_left < 0 or (km_left is not None and km_left < 0)

		if is_overdue is overdue and (overdue or days_left <= 30):
			row.days_left = days_left
			row.km_left = km_left
			rows.append(row)

	return rows
