# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate, date_diff, nowdate, get_datetime, ceil


class RentalAgreement(Document):
	def autoname(self):
		date = nowdate()  # gives '2025-07-10'
		year, month, _ = date.split('-')
		prefix = f"FL-RA-{year}-{month}"

		self.name = make_autoname(f"{prefix}-.######")
            
	def validate(self):
        # Server-side validation to prevent double booking
		self.check_vehicle_availability()
		self.calculate_duration()

		self.calculate_total_rental_cost()
		self.populate_billing_items()
		self.calculate_total_amount()

	def before_update_after_submit(self):
		# Tolls and fines land on the agreement after it is submitted, so the
		# billing table has to be rebuilt outside the normal validate() path.
		# This runs before update_children(), so stale rows are cleaned up for us.
		self.calculate_total_rental_cost()
		self.populate_billing_items()
		self.calculate_total_amount()

	def before_submit(self):
		self.status = "Confirmed"
		
	def on_submit(self):
		self.update_vehicle_status("Rented")

	def on_cancel(self):
		self.update_vehicle_status("Available")

	def check_vehicle_availability(self):
		if not (self.vehicle and self.pickup_date_and_time and self.dropoff_date_and_time):
			return

		# Find other rental agreements for the same vehicle that overlap with the current one
		overlapping_rentals = frappe.db.sql("""
			SELECT name
			FROM `tabRental Agreement`
			WHERE
				vehicle = %(vehicle)s AND
				docstatus = 1 AND
				name != %(current_doc)s AND
				(
					(pickup_date_and_time < %(dropoff)s AND dropoff_date_and_time > %(pickup)s)
				)
		""", {
			'vehicle': self.vehicle,
			'pickup': self.pickup_date_and_time,
			'dropoff': self.dropoff_date_and_time,
			'current_doc': self.name
		})

		if overlapping_rentals:
			frappe.throw(f"Vehicle <b>{self.vehicle}</b> is already booked for the selected period.")

	def calculate_duration(self):
		if self.pickup_date_and_time and self.dropoff_date_and_time:
			pickup = get_datetime(self.pickup_date_and_time)
			dropoff = get_datetime(self.dropoff_date_and_time)
			diff_hours = (dropoff - pickup).total_seconds() / 3600

			# Round up to the next full day
			self.duration = ceil(diff_hours / 24)

   
	@frappe.whitelist()
	def get_vehicle_rate(self):
		if self.vehicle:
			self.daily_rate = frappe.db.get_value("Rental Vehicle", self.vehicle, "daily_rate")

	def calculate_total_rental_cost(self):
		if self.daily_rate and self.duration:
			days = self.duration
			self.total_rental_cost = self.daily_rate * days

	@frappe.whitelist()
	def populate_billing_items(self):
		# This method will populate the billing items table based on the rental cost
		self.billing_items = [] # Clear existing items
		if self.total_rental_cost:
		
			settings = frappe.get_doc("Fleetify Settings")
			
			if not settings:
				frappe.throw("Fleetify Settings not found. Please create it first.")
			if not settings.rental_item:
				frappe.throw("Please set the Rental Item in Fleetify Settings.")
			if not settings.additional_charge_item:
				frappe.throw("Please set the Additional Charge Item in Fleetify Settings.")
			
			rental_item = settings.rental_item
			days = self.duration
			self.append("billing_items", {
				"item_code": rental_item,
				"item_name": frappe.db.get_value("Item", rental_item, "item_name"),
				"qty": days,
				"rate": self.daily_rate,
				"amount": self.total_rental_cost,
			})
			
			additional_charge_item = settings.additional_charge_item
			for charge in self.additional_charges:
				self.append("billing_items", {
					"item_code": additional_charge_item,
					"item_name": frappe.db.get_value("Item", additional_charge_item, "item_name"),
					"qty": 1,
					"rate": charge.amount,
					"amount": charge.amount,
					"description": charge.description
				})

	def calculate_total_amount(self):
		total_billing_items = sum(item.amount for item in self.billing_items)
		# total_additional_charges = sum(charge.amount for charge in self.additional_charges)
		self.total_amount = total_billing_items

	def update_vehicle_status(self, status):
		if self.vehicle:
			if status == "Available":
				other_rentals = frappe.get_all("Rental Agreement", filters={
					"vehicle": self.vehicle,
					"status": "Rented",
					"name": ["!=", self.name]
				})
				if other_rentals:
					return

			vehicle = frappe.get_doc("Rental Vehicle", self.vehicle)
			vehicle.status = status
			vehicle.save()

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    
    from frappe.model.mapper import get_mapped_doc

    def postprocess(source_doc, target_doc):
        target_doc.due_date = frappe.utils.nowdate()
        target_doc.set_posting_time = 1
        target_doc.custom_rental_agreement = source_doc.name
        target_doc.set_missing_values()  # ← this fills in UOM, item names, etc.
        target_doc.calculate_taxes_and_totals()
    
    doc = get_mapped_doc(
        "Rental Agreement", source_name,
        {
            "Rental Agreement": {
                "doctype": "Sales Invoice",
                "field_map": {
                    "customer": "customer"
                }
            },
            "Rental Agreement Item": {
                "doctype": "Sales Invoice Item",
                "field_map": {
					"item_code": "item_code",
                    "item_name": "item_name",
                    "qty": "qty",
                    "rate": "rate",
                    "amount": "amount",
                    "description": "description"
                }
            }
        },
        postprocess=postprocess
    )

    return doc


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_available_vehicles(doctype, txt, searchfield, start, page_len, filters=None):
    if not filters:
        filters = {}

    start_date = filters.get('start_date')
    end_date = filters.get('end_date')

    # If dates are not provided, no vehicles will be shown.
    if not start_date or not end_date:
        frappe.throw("Please select Pickup and Drop-off dates first.")

    # Find vehicles that are already booked (submitted agreements) during the requested period.
    booked_vehicles = frappe.db.sql_list("""
        SELECT DISTINCT vehicle
        FROM `tabRental Agreement`
        WHERE
            docstatus = 1 AND
            (
                (pickup_date_and_time < %(end_date)s AND dropoff_date_and_time > %(start_date)s)
            )
    """, {
        'start_date': start_date,
        'end_date': end_date
    })

    # Define conditions for the vehicle query
    vehicle_conditions = [
        ("{key}".format(key=searchfield), "like", f"%%{txt}%%")
    ]
    
    if booked_vehicles:
        vehicle_conditions.append(
            ("{key}".format(key=searchfield), "not in", booked_vehicles)
		)			

    print("vehicle_conditions", vehicle_conditions)

    # Return vehicles that are not in the booked list
    return frappe.get_list(
        "Rental Vehicle",
        filters=vehicle_conditions,
        fields=["name", "license_plate", "vehicle_make", "vehicle_model"],
        as_list=True
    )
