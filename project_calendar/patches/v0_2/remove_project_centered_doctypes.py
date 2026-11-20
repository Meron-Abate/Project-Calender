import frappe

# The first version of the app stored its settings in these DocTypes. The Resource Calendar replaces them
# with Resource View, so they are removed here (their rows only held calendar configuration).
OLD_DOCTYPES = ("Project Calendar Resource", "Project Calendar Settings", "Project Calendar Saved Filter")


def execute():
	for name in OLD_DOCTYPES:
		if frappe.db.exists("DocType", name):
			frappe.delete_doc("DocType", name, force=True, ignore_missing=True)
