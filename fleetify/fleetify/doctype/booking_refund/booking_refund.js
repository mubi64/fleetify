// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Booking Refund", {
	rental_agreement(frm) {
		if (!frm.doc.rental_agreement) {
			return;
		}

		frappe.call({
			method: "fleetify.fleetify.doctype.booking_refund.booking_refund.pull_charges",
			args: { rental_agreement: frm.doc.rental_agreement },
			callback: (r) => {
				if (r.message) {
					frm.set_value(r.message);
				}
			},
		});
	},
});
