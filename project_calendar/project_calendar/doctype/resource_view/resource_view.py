from frappe.model.document import Document


class ResourceView(Document):
	def validate(self):
		from project_calendar.api import validate_view

		validate_view(self)
