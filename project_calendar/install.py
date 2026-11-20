import frappe


def after_install():
	seed_default_view()


def seed_default_view():
	"""Give a fresh install one working view (projects by customer) so the calendar isn't empty."""
	if frappe.db.count("Resource View") or not frappe.db.exists("DocType", "Project"):
		return

	meta = frappe.get_meta("Project")
	pick = lambda *names: next((n for n in names if meta.has_field(n)), None)  # noqa: E731

	resource = pick("customer", "department", "status")
	title = pick("project_name")
	start = pick("expected_start_date")
	end = pick("expected_end_date")
	if not all((resource, title, start, end)):
		return

	body = []
	if pick("ep_location"):
		body.append({"field": "ep_location", "label": "Location", "style": "Normal"})
	if pick("status") and resource != "status":
		body.append({"field": "status", "label": "", "style": "Badge"})

	frappe.get_doc(
		{
			"doctype": "Resource View",
			"view_name": "Projects",
			"source_doctype": "Project",
			"resource_field": resource,
			"show_empty_resources": 0,
			"card_title_field": title,
			"start_field": start,
			"end_field": end,
			"card_fields": body,
		}
	).insert(ignore_permissions=True)
