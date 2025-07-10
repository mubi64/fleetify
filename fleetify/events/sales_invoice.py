import frappe

def validate(doc, method):
    if doc.custom_rental_agreement:
        agreement = frappe.get_doc("Rental Agreement", doc.custom_rental_agreement)
        agreement.db_set("billing_status", "Billed")
        agreement.db_set("sales_invoice", doc.name)
        frappe.msgprint(f"Sales Invoice {doc.name} has been created. Rental Agreement {agreement.name} status updated to Billed.")

def on_trash(doc, method):
    if doc.custom_rental_agreement:
        agreement = frappe.get_doc("Rental Agreement", doc.custom_rental_agreement)
        agreement.db_set("billing_status", "Unbilled")
        agreement.db_set("sales_invoice", "")
        frappe.msgprint(f"Sales Invoice {doc.name} has been deleted. Rental Agreement {agreement.name} status updated to Unbilled.")
