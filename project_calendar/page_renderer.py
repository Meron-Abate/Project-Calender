"""Serves the Vue app at /project-calendar.

The page is the `index.html` that Vite builds (hashed asset names, so a rebuild is picked up at once)
with the session's CSRF token injected. Guests are sent to the login page.
"""

import json
import os

import frappe
from frappe.website.page_renderers.base_renderer import BaseRenderer
from werkzeug.wrappers import Response

ROUTE = "project-calendar"


class ProjectCalendarPage(BaseRenderer):
	def can_render(self):
		return self.path == ROUTE

	def render(self):
		if frappe.session.user == "Guest":
			return Response(status=302, headers={"Location": f"/login?redirect-to=/{ROUTE}"})

		index = frappe.get_app_path("project_calendar", "public", "frontend", "index.html")
		if not os.path.exists(index):
			return self.build_response(
				"<h1>Project Calendar has not been built yet.</h1><p>Run <code>npm run build</code> in the app's frontend folder.</p>",
				503,
			)

		with open(index, encoding="utf-8") as f:
			html = f.read()
		token = json.dumps(frappe.sessions.get_csrf_token()).replace("</", "<\/")
		html = html.replace("<head>", f"<head><script>window.csrf_token = {token};</script>", 1)
		return self.build_response(html, headers={"Cache-Control": "no-store"})
