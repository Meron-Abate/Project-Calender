app_name = "project_calendar"
app_title = "Project Calendar"
app_publisher = "EMC"
app_description = "Weekly time-resource calendar: saved views over any ERPNext DocType"
app_email = "girum@eternal-media.com"
app_license = "mit"

required_apps = ["erpnext"]

after_install = "project_calendar.install.after_install"

# Adds a "Project Calendar" button to the Project list.
doctype_list_js = {"Project": "public/js/project_list.js"}

# Serves the SPA at /project-calendar.
page_renderer = ["project_calendar.page_renderer.ProjectCalendarPage"]

# Lists the calendar in the Frappe apps switcher.
add_to_apps_screen = [
	{
		"name": "project_calendar",
		"logo": "/assets/erpnext/images/erpnext-logo.svg",
		"title": "Project Calendar",
		"route": "/project-calendar",
	}
]
