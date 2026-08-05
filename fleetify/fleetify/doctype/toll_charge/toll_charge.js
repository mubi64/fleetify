// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Toll Charge", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.billed_to_customer || !frm.doc.rental_agreement) {
			return;
		}

		frm.add_custom_button(__("Bill to Customer"), () => {
			frappe.call({
				method: "fleetify.fleetify.doctype.toll_charge.toll_charge.rebill",
				args: { name: frm.doc.name },
				freeze: true,
				callback: (r) => {
					if (r.message) {
						frappe.show_alert({
							message: __("Added to {0}", [r.message]),
							indicator: "green",
						});
						frm.reload_doc();
					}
				},
			});
		});
	},
});
