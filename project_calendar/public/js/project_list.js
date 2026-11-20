frappe.listview_settings["Project"] = frappe.listview_settings["Project"] || {};

const previous_onload = frappe.listview_settings["Project"].onload;
frappe.listview_settings["Project"].onload = function (listview) {
	if (previous_onload) previous_onload.call(this, listview);
	listview.page.add_inner_button(__("Project Calendar"), () => {
		window.location.href = "/project-calendar";
	});
};
