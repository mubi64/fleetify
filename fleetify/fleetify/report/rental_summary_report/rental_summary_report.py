# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"label": _(col), "fieldname": col.lower().replace(" ", "_"), "fieldtype": "Data", "width": 150} 
        for col in ["Rental Agreement", "Customer", "Vehicle", "Status", "Billing Status", "Pickup Date", "Drop-off Date", "Duration", "Total Rental Cost", "Additional Charges", "Total Amount"]
    ]

    data = frappe.db.sql(f"""
        SELECT
            name AS 'rental_agreement', customer, vehicle, status, billing_status,
            pickup_date_and_time AS 'pickup_date', dropoff_date_and_time AS 'drop-off_date', duration, total_rental_cost, total_amount
        FROM `tabRental Agreement`
        WHERE pickup_date_and_time BETWEEN %(from_date)s AND %(to_date)s
        {f"AND status = '{filters.status}'" if filters.get('status') else ''}
        {f"AND billing_status = '{filters.billing_status}'" if filters.get('billing_status') else ''}
    """, filters, as_dict=1)
    
    rental_ids = [row.rental_agreement for row in data]
    

    # Get additional charges in bulk
    if rental_ids:
        charges = frappe.db.sql(f"""
            SELECT parent, description, amount
            FROM `tabAdditional Charge`
            WHERE parent IN %(parents)s
        """, {"parents": rental_ids}, as_dict=1)

        # Group charges by rental_agreement
        from collections import defaultdict
        charges_map = defaultdict(list)
        for c in charges:
            charges_map[c.parent].append(f"{c.description}: {c.amount}")

        # Attach additional charges to each rental row
        for row in data:
            row["additional_charges"] = ", ".join(charges_map.get(row.rental_agreement, []))


    return columns, data
