// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Traffic Fine", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.billed_to_customer || !frm.doc.rental_agreement) {
			return;
		}

		frm.add_custom_button(__("Bill to Customer"), () => {
			frappe.call({
				method: "fleetify.fleetify.doctype.traffic_fine.traffic_fine.rebill",
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
