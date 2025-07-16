# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"label": _(label), "fieldname": fieldname, "fieldtype": ftype, "options": options, "width": width} 
        for label, fieldname, ftype, options, width in [
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

    # Create bar chart: Total Revenue by Vehicle
    chart = {
        "data": {
            "labels": [d["vehicle"] for d in data],
            "datasets": [
                {
                    "name": "Total Revenue",
                    "values": [float(d["total_amount"] or 0) for d in data]
                }
            ]
        },
        "type": "bar",  # or "pie", "line"
        "colors": ["#34D399"]  # Optional: tailwind green-400
    }

    # Add summary
    summary = [
        {"label": "Total Rentals", "value": sum(d["rental_count"] for d in data), "indicator": "blue"},
        {"label": "Total Duration (Days)", "value": sum(d["total_duration"] for d in data), "indicator": "green"},
        {"label": "Total Revenue", "value": frappe.utils.fmt_money(sum(d["total_amount"] for d in data)), "indicator": "red"},
    ]

    return columns, data, None, chart, summary
