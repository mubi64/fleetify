# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"label": _(label), "fieldname": fieldname, "fieldtype": ftype, "options": options, "width": width} for label, fieldname, ftype, options, width in [
            ("Vehicle", "vehicle", "Link", "Rental Vehicle", 180),
            ("Number of Rentals", "rental_count", "Int", None, 200),
            ("Total Duration (Days)", "total_duration", "Int", None, 200),
            ("Total Revenue", "total_amount", "Currency", None, 200)
        ]
    ]

    data = frappe.db.sql("""
        SELECT
            vehicle,
            COUNT(name) AS rental_count,
            SUM(duration) AS total_duration,
            SUM(total_amount) AS total_amount
        FROM `tabRental Agreement`
        WHERE pickup_date_and_time BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY vehicle
    """, filters, as_dict=1)

    return columns, data
