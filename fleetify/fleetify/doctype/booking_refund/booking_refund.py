# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, nowdate

DEDUCTION_FIELDS = (
	"salik",
	"fine",
	"fuel_charges",
	"extra_km_charges",
	"damage",
	"other_charges",
	"rent_adjusted",
)


class BookingRefund(Document):
	def autoname(self):
		year, month, _day = nowdate().split("-")
		self.name = make_autoname(f"FL-BR-{year}-{month}-.######")

	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		self.total_deductions = sum(flt(self.get(f)) for f in DEDUCTION_FIELDS)

		balance = flt(self.deposit) - flt(self.total_deductions)
		self.refund = balance if balance > 0 else 0
		self.payable_by_client = -balance if balance < 0 else 0
		self.pending_refund = 0 if self.is_settled else flt(self.refund)


@frappe.whitelist()
def pull_charges(rental_agreement):
	"""Sum the unbilled tolls and fines sitting against an agreement."""
	def total(doctype):
		rows = frappe.get_all(
			doctype,
			filters={"rental_agreement": rental_agreement, "billed_to_customer": 0},
			fields=["total_cost"],
		)
		return sum(flt(r.total_cost) for r in rows)

	return {"salik": total("Toll Charge"), "fine": total("Traffic Fine")}
