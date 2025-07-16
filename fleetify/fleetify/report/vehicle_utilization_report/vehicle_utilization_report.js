// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle Utilization Report"] = {
	"filters": [
        { "fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": frappe.datetime.month_start(), "reqd": 1 },
        { "fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": frappe.datetime.month_end(), "reqd": 1 }
    ]
};
