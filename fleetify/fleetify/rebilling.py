# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

"""Shared helpers for charges that a rental company recovers from the renter.

Traffic fines and tolls are incurred against a *vehicle*, but they are owed by
whoever held the agreement at the time — so both doctypes carry the same VAT
arithmetic and the same push into `Rental Agreement.additional_charges`.
"""

import frappe
from frappe import _
from frappe.utils import flt

VAT_RATE = 0.05


def calculate_vat(doc):
	doc.vat_amount = flt(doc.amount) * VAT_RATE if doc.add_vat else 0
	doc.total_cost = flt(doc.amount) + flt(doc.vat_amount)


def rebill_to_agreement(doc, description):
	"""Append `doc`'s total onto its agreement as an additional charge.

	Returns the agreement name. Raises if there is nothing to bill against or
	the charge has already been pushed.
	"""
	if not doc.rental_agreement:
		frappe.throw(_("Set a Contract ID before rebilling {0}").format(doc.name))

	if doc.billed_to_customer:
		frappe.throw(_("{0} has already been billed to the customer").format(doc.name))

	agreement = frappe.get_doc("Rental Agreement", doc.rental_agreement)
	agreement.append(
		"additional_charges", {"description": description, "amount": flt(doc.total_cost)}
	)
	# Totals are rebuilt by validate() on a draft and by on_update_after_submit()
	# once the agreement is submitted.
	agreement.save()

	doc.db_set("billed_to_customer", 1)

	return agreement.name
