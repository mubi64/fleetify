frappe.ui.form.on('Rental Agreement', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.billing_status === 'Unbilled') {
            frm.add_custom_button(__('Create Sales Invoice'), function() {
                frappe.model.open_mapped_doc({
                    method: 'fleetify.fleetify.doctype.rental_agreement.rental_agreement.make_sales_invoice',
                    frm: frm,
                    freeze_message: __("Creating Sales Invoice ..."),
                });
            }).addClass('btn-primary');
        }
        if (frm.doc.docstatus === 1 && frm.doc.billing_status === 'Billed') {
            frm.add_custom_button(__('View Sales Invoice'), function() {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Sales Invoice',
                        filters: {
                            custom_rental_agreement: frm.doc.name
                        },
                        fields: ['name'],
                        limit_page_length: 1
                    },
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            frappe.set_route('Form', 'Sales Invoice', r.message[0].name);
                        } else {
                            frappe.msgprint(__('Sales Invoice not found for this agreement.'));
                        }
                    }
                });
            }).addClass('btn-default');
        }

    },
    onload: function(frm) {
        // Set a dynamic query for the 'vehicle' field
        frm.set_query("vehicle", function() {
            // This query will only run if both date fields have values
            if (frm.doc.pickup_date_and_time && frm.doc.dropoff_date_and_time) {
                return {
                    // Path to the server-side python method
                    query: "fleetify.fleetify.doctype.rental_agreement.rental_agreement.get_available_vehicles",
                    // Pass the selected dates as filters
                    filters: {
                        'start_date': frm.doc.pickup_date_and_time,
                        'end_date': frm.doc.dropoff_date_and_time
                    }
                };
            } else {
                // If dates are not set, show a message and return no results
                frappe.msgprint(__("Please select Pickup and Drop-off dates to see available vehicles."));
                return {
                    filters: {
                        'name': 'non-existent-vehicle' // Return no vehicles
                    }
                };
            }
        });

    },
    // When the vehicle is selected, fetch its daily rate
    vehicle: function(frm) {
        if (frm.doc.vehicle) {
            // Using the class method defined in the Python script
            frm.call('get_vehicle_rate').then(r => {
                frm.refresh_field('daily_rate');
                frm.trigger('calculate_totals');
            });
        }
    },
    // Recalculate everything if dates change
    pickup_date_and_time: function(frm) {
        frm.set_value('vehicle', ''); // Clear vehicle selection when dates change
        frm.trigger('calculate_totals');
    },

    dropoff_date_and_time: function(frm) {
        frm.set_value('vehicle', ''); // Clear vehicle selection when dates change
        frm.trigger('calculate_totals');
    },
    additional_charges_on_form_rendered: function(frm) {
        frm.fields_dict.additional_charges.grid.get_field('amount').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    // No filters needed for now
                }
            };
        };
    },
    // Trigger for recalculating all costs
    calculate_totals: function(frm) {
        if (frm.doc.pickup_date_and_time && frm.doc.dropoff_date_and_time) {
            let pickup = frappe.datetime.str_to_obj(frm.doc.pickup_date_and_time);
            let dropoff = frappe.datetime.str_to_obj(frm.doc.dropoff_date_and_time);

            if (dropoff > pickup) {
                let duration_in_seconds = (dropoff - pickup) / 1000;  // milliseconds to seconds
                let duration_in_hours = duration_in_seconds / 3600;
                let days = Math.ceil(duration_in_hours / 24);  // Round up partial day

                let total_rental_cost = days * (frm.doc.daily_rate || 0);
                frm.set_value('duration', days);
                frm.set_value('total_rental_cost', total_rental_cost);

                let total_additional_charges = 0;
                if (frm.doc.additional_charges) {
                    frm.doc.additional_charges.forEach(function(charge) {
                        total_additional_charges += (charge.amount || 0);
                    });
                }

                frm.set_value('total_amount', total_rental_cost + total_additional_charges);

                //populate_billing_items
                frm.call('populate_billing_items').then(r => {
                    frm.refresh_field('billing_items');
                });
            } else {
                frm.set_value('duration', 0);
                frm.set_value('total_rental_cost', 0);
                frm.set_value('total_amount', 0);
            }
        } else {
            frm.set_value('duration', 0);
            frm.set_value('total_rental_cost', 0);
            frm.set_value('total_amount', 0);
        }

        frm.refresh_fields(['duration', 'total_rental_cost', 'total_amount']);
    }

});

// Recalculate total when additional charges are changed
frappe.ui.form.on('Additional Charge', {
    amount: function(frm, cdt, cdn) {
        frm.trigger('calculate_totals');
    },
    additional_charges_remove: function(frm) {
        frm.trigger('calculate_totals');
    }
});

// Recalculate amount in billing items table
frappe.ui.form.on('Rental Agreement Item', {
    qty: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        row.amount = row.qty * row.rate;
        frm.refresh_field('billing_items');
        frm.trigger('calculate_totals');
    },
    rate: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        row.amount = row.qty * row.rate;
        frm.refresh_field('billing_items');
        frm.trigger('calculate_totals');
    }
});

