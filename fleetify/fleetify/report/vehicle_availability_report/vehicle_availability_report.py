# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime


def execute(filters=None):
    from frappe import _
    import frappe
    from datetime import datetime

    columns = [
        {"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Rental Vehicle", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "HTML", "width": 120},
        {"label": "Available From", "fieldname": "available_from", "fieldtype": "Datetime", "width": 180}
    ]

    selected_date = filters.get("date")
    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d")

    all_vehicles = frappe.get_all("Rental Vehicle", fields=["name"])
    vehicle_data = {}

    for v in all_vehicles:
        vehicle_data[v.name] = {
            "vehicle": v.name,
            "status": '<span style="color:green;font-weight:bold">Available</span>',
            "available_from": selected_date  # assume available unless overridden
        }

    bookings = frappe.db.sql("""
        SELECT vehicle, pickup_date_and_time, dropoff_date_and_time
        FROM `tabRental Agreement`
        WHERE
            status IN ('Confirmed', 'Active')
            AND dropoff_date_and_time >= %(date)s
    """, {"date": selected_date}, as_dict=True)

    for b in bookings:
        v = b.vehicle
        pickup = b.pickup_date_and_time
        dropoff = b.dropoff_date_and_time
        if isinstance(pickup, str):
            pickup = datetime.strptime(pickup, "%Y-%m-%d %H:%M:%S")
        if isinstance(dropoff, str):
            dropoff = datetime.strptime(dropoff, "%Y-%m-%d %H:%M:%S")

        if v in vehicle_data:
            if pickup <= selected_date <= dropoff:
                vehicle_data[v]["status"] = '<span style="color:red;font-weight:bold">Not Available</span>'
                vehicle_data[v]["available_from"] = dropoff
            elif selected_date < pickup and 'Not Available' not in vehicle_data[v]["status"]:
                vehicle_data[v]["available_from"] = ""

    sorted_data = sorted(vehicle_data.values(), key=lambda d: ('Not Available' in d['status'], d['available_from']))

    return columns, sorted_data
