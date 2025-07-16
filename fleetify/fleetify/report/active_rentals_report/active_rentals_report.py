# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"label": _(col), "fieldname": col.lower().replace(" ", "_"), "fieldtype": "Data", "width": 150}
        for col in ["Rental Agreement", "Customer", "Vehicle", "Pickup Date", "Drop-off Date", "Duration", "Daily Rate", "Total Rental Cost", "Total Amount"]
    ]

    data = frappe.db.sql("""
        SELECT
            name AS 'rental_agreement', customer, vehicle, pickup_date_and_time AS 'pickup_date', dropoff_date_and_time AS 'drop-off_date',
            duration, daily_rate, total_rental_cost, total_amount
        FROM `tabRental Agreement`
        WHERE status = 'Confirmed' AND dropoff_date_and_time > CURDATE()
    """, as_dict=1)

    return columns, data

