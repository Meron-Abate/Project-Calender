"""Whitelisted API behind the Weekly Resource Calendar.

A *Resource View* is saved configuration only (which DocType, which fields play which role, which filters
apply). The cards on the calendar are the real records of that DocType. Reads go through
``frappe.get_list`` and writes through ``doc.save()``, so ERPNext role permissions, user permissions and
server-side validation all apply.
"""

import html
import json
import re

import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate, strip_html_tags
from frappe.utils.formatters import format_value

VIEW_DOCTYPE = "Resource View"
MAX_CARDS = 2000
MAX_EMPTY_ROWS = 500

LAYOUT_TYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"HTML",
	"Button",
	"Image",
	"Fold",
	"Heading",
	"Table",
	"Table MultiSelect",
	"Attach",
	"Attach Image",
	"Signature",
	"Geolocation",
	"Barcode",
	"Password",
	"JSON",
}
EXCLUDED_MODULES = ("Core", "Custom", "Email", "Integrations", "Printing", "Website", "Social", "Automation")

TEXT = {"Data", "Small Text", "Text", "Long Text", "Text Editor", "Select", "Link", "Read Only", "Dynamic Link"}
NUMBERS = {"Int", "Float", "Currency", "Percent", "Long Int"}
DATES = {"Date", "Datetime"}

RESOURCE_TYPES = {"Link", "Select"}
TITLE_TYPES = TEXT | NUMBERS
COLOR_TYPES = {"Color", "Select", "Data", "Link"}

OPERATORS = ["=", "!=", ">", "<", ">=", "<=", "like", "not like", "in", "not in", "is set", "is not set"]
STYLES = ["Normal", "Bold", "Muted", "Italic", "Badge"]

STANDARD_FIELDS = [
	("name", "ID", "Data", None),
	("creation", "Created On", "Datetime", None),
	("modified", "Last Modified", "Datetime", None),
	("owner", "Created By", "Link", "User"),
	("docstatus", "Document Status", "Int", None),
]

UNASSIGNED = ""


# ----------------------------------------------------------------------------------------------
# Metadata
# ----------------------------------------------------------------------------------------------


def field_defs(doctype):
	"""``{fieldname: {fieldname, label, fieldtype, options, choices}}`` for every usable field."""
	meta = frappe.get_meta(doctype)
	defs = {}
	for fieldname, label, fieldtype, options in STANDARD_FIELDS:
		defs[fieldname] = {
			"fieldname": fieldname,
			"label": _(label),
			"fieldtype": fieldtype,
			"options": options,
			"choices": [],
		}
	for df in meta.fields:
		if df.fieldtype in LAYOUT_TYPES or not df.fieldname or df.get("is_virtual"):
			continue
		choices = [c for c in (df.options or "").split("\n") if c] if df.fieldtype == "Select" else []
		defs[df.fieldname] = {
			"fieldname": df.fieldname,
			"label": _(df.label or df.fieldname),
			"fieldtype": df.fieldtype,
			"options": df.options if df.fieldtype in ("Link", "Dynamic Link") else None,
			"choices": choices,
		}
	return defs


def _check_source(doctype):
	if not doctype or not frappe.db.exists("DocType", doctype):
		frappe.throw(_("{0} is not a DocType.").format(frappe.bold(doctype or "")))
	meta = frappe.get_meta(doctype)
	if meta.issingle or meta.istable:
		frappe.throw(_("{0} can't be used as a source: pick a regular DocType.").format(frappe.bold(doctype)))
	frappe.has_permission(doctype, "read", throw=True)
	return meta


def validate_view(doc):
	"""Called from the Resource View controller: every mapped field must really exist with a fitting type."""
	_check_source(doc.source_doctype)
	defs = field_defs(doc.source_doctype)

	def check(fieldname, label, kinds, required=True):
		value = (doc.get(fieldname) or "").strip()
		doc.set(fieldname, value)
		if not value:
			if required:
				frappe.throw(_("{0} is required.").format(_(label)))
			return
		field = defs.get(value)
		if not field:
			frappe.throw(
				_("{0}: {1} is not a field of {2}.").format(_(label), frappe.bold(value), doc.source_doctype)
			)
		if field["fieldtype"] not in kinds:
			frappe.throw(
				_("{0}: {1} is a {2} field; expected one of {3}.").format(
					_(label), frappe.bold(value), field["fieldtype"], ", ".join(sorted(kinds))
				)
			)

	check("resource_field", "Resource Row Field", RESOURCE_TYPES, required=False)
	check("card_title_field", "Card Title Field", TITLE_TYPES)
	check("start_field", "Start Date/Time Field", DATES)
	check("end_field", "End Date/Time Field", DATES)
	check("color_field", "Color Field", COLOR_TYPES, required=False)

	for rule in doc.filters:
		rule.field = (rule.field or "").strip()
		if rule.field not in defs:
			frappe.throw(_("Filter row {0}: {1} is not a field of {2}.").format(rule.idx, rule.field, doc.source_doctype))
		if rule.operator not in OPERATORS:
			frappe.throw(_("Filter row {0}: unknown operator {1}.").format(rule.idx, rule.operator))
		if rule.operator not in ("is set", "is not set") and (rule.value or "") == "":
			frappe.throw(_("Filter row {0}: a value is required.").format(rule.idx))

	for row in doc.card_fields:
		row.field = (row.field or "").strip()
		if row.field not in defs:
			frappe.throw(_("Body field row {0}: {1} is not a field of {2}.").format(row.idx, row.field, doc.source_doctype))
		if row.style and row.style not in STYLES:
			frappe.throw(_("Body field row {0}: unknown style {1}.").format(row.idx, row.style))


def _view_dict(doc):
	return {
		"name": doc.name,
		"view_name": doc.view_name,
		"source_doctype": doc.source_doctype,
		"resource_field": doc.resource_field,
		"show_empty_resources": cint(doc.show_empty_resources),
		"card_title_field": doc.card_title_field,
		"start_field": doc.start_field,
		"end_field": doc.end_field,
		"color_field": doc.color_field or "",
		"sort_order": cint(doc.sort_order),
		"filters": [{"field": f.field, "operator": f.operator, "value": f.value or ""} for f in doc.filters],
		"fields": [
			{
				"field": f.field,
				"label": f.label or "",
				"style": f.style or "Normal",
				"show_in_detail": cint(f.show_in_detail),
			}
			for f in doc.card_fields
		],
	}


# ----------------------------------------------------------------------------------------------
# Saved views
# ----------------------------------------------------------------------------------------------


@frappe.whitelist()
def list_views():
	frappe.has_permission(VIEW_DOCTYPE, "read", throw=True)
	names = frappe.get_list(
		VIEW_DOCTYPE, pluck="name", order_by="sort_order asc, view_name asc", limit_page_length=0
	)
	return {
		"views": [_view_dict(frappe.get_doc(VIEW_DOCTYPE, n)) for n in names],
		"can_write": bool(frappe.has_permission(VIEW_DOCTYPE, "write")),
		"can_create": bool(frappe.has_permission(VIEW_DOCTYPE, "create")),
		"is_admin": "System Manager" in frappe.get_roles(),
	}


@frappe.whitelist()
def save_view(data):
	"""Create a view, or update it when ``data.name`` already exists."""
	data = frappe.parse_json(data) or {}
	scalars = (
		"view_name",
		"source_doctype",
		"resource_field",
		"show_empty_resources",
		"card_title_field",
		"start_field",
		"end_field",
		"color_field",
		"sort_order",
	)
	values = {k: data.get(k) for k in scalars if k in data}

	if data.get("name") and frappe.db.exists(VIEW_DOCTYPE, data["name"]):
		doc = frappe.get_doc(VIEW_DOCTYPE, data["name"])
		doc.check_permission("write")
		new_name = (values.get("view_name") or doc.name).strip()
		doc.update(values)
		doc.set("filters", [])
		doc.set("card_fields", [])
	else:
		doc = frappe.new_doc(VIEW_DOCTYPE)
		doc.check_permission("create")
		doc.update(values)
		new_name = None

	for rule in data.get("filters") or []:
		doc.append("filters", {"field": rule.get("field"), "operator": rule.get("operator") or "=", "value": rule.get("value") or ""})
	for row in data.get("fields") or []:
		doc.append(
			"card_fields",
			{
				"field": row.get("field"),
				"label": row.get("label") or "",
				"style": row.get("style") or "Normal",
				"show_in_detail": cint(row.get("show_in_detail")),
			},
		)

	if doc.is_new():
		doc.insert()
	else:
		doc.save()
		if new_name and new_name != doc.name:
			frappe.rename_doc(VIEW_DOCTYPE, doc.name, new_name)
			doc = frappe.get_doc(VIEW_DOCTYPE, new_name)
	return _view_dict(doc)


@frappe.whitelist()
def duplicate_view(name):
	source = frappe.get_doc(VIEW_DOCTYPE, name)
	source.check_permission("read")
	frappe.has_permission(VIEW_DOCTYPE, "create", throw=True)

	copy = frappe.copy_doc(source)
	base = f"{source.view_name} (Copy)"
	candidate, n = base, 2
	while frappe.db.exists(VIEW_DOCTYPE, candidate):
		candidate, n = f"{base} {n}", n + 1
	copy.view_name = candidate
	copy.insert()
	return _view_dict(copy)


@frappe.whitelist()
def delete_view(name):
	frappe.delete_doc(VIEW_DOCTYPE, name)
	return {"name": name}


@frappe.whitelist()
def list_doctypes(txt="", limit=40):
	"""Regular DocTypes the user may read, for the Source DocType picker."""
	limit = min(cint(limit) or 40, 100)
	filters = [
		["DocType", "issingle", "=", 0],
		["DocType", "istable", "=", 0],
		["DocType", "is_virtual", "=", 0],
		["DocType", "module", "not in", EXCLUDED_MODULES],
	]
	if txt:
		filters.append(["DocType", "name", "like", f"%{txt}%"])
	rows = frappe.get_all(
		"DocType", filters=filters, fields=["name", "module"], order_by="name asc", limit_page_length=300
	)
	result = [r for r in rows if frappe.has_permission(r.name, "read")]
	return result[:limit]


@frappe.whitelist()
def get_doctype_fields(doctype):
	"""Real fields of a DocType, for the view editor's pickers."""
	_check_source(doctype)
	return {
		"doctype": doctype,
		"fields": list(field_defs(doctype).values()),
		"operators": OPERATORS,
		"styles": STYLES,
		"resource_types": sorted(RESOURCE_TYPES),
		"title_types": sorted(TITLE_TYPES),
		"date_types": sorted(DATES),
		"color_types": sorted(COLOR_TYPES),
	}


# ----------------------------------------------------------------------------------------------
# Calendar data
# ----------------------------------------------------------------------------------------------


def _plain(text):
	"""Rich text to plain text: tags removed, block ends kept as line breaks, entities decoded."""
	text = re.sub(r"<\s*br\s*/?>|</\s*(p|div|li|h[1-6]|tr)\s*>", "\n", str(text), flags=re.I)
	text = html.unescape(strip_html_tags(text))
	return re.sub(r"[ \t]*\n[ \t\n]*", "\n", text).strip()


def _stamp(value):
	"""'YYYY-MM-DD' for a date and 'YYYY-MM-DD HH:MM:SS' for a datetime."""
	if not value:
		return None
	text = str(value)
	return text[:19] if len(text) > 10 else text[:10]


def _display(meta, defs, fieldname, value, row):
	df = defs.get(fieldname)
	if value in (None, "") or not df:
		return ""
	if df["fieldtype"] == "Check":
		return _("Yes") if cint(value) else ""
	docfield = meta.get_field(fieldname)
	try:
		formatted = format_value(value, docfield, doc=row) if docfield else str(value)
	except Exception:
		formatted = str(value)
	return _plain(formatted)


def _rule_to_filter(doctype, defs, rule):
	field, op, value = rule["field"], rule["operator"], rule.get("value") or ""
	if op == "is set":
		return [doctype, field, "is", "set"]
	if op == "is not set":
		return [doctype, field, "is", "not set"]
	value = {"__user": frappe.session.user, "today": nowdate()}.get(value.strip().lower(), value)
	fieldtype = defs[field]["fieldtype"]
	if op in ("in", "not in"):
		return [doctype, field, op, [v.strip() for v in value.split(",") if v.strip()]]
	if op in ("like", "not like") and "%" not in value:
		value = f"%{value}%"
	if fieldtype == "Check":
		value = 1 if value.strip().lower() in ("1", "yes", "true") else 0
	return [doctype, field, op, value]


def _load_view(view):
	doc = frappe.get_doc(VIEW_DOCTYPE, view)
	doc.check_permission("read")
	return doc


def _link_labels(linked, names):
	"""{name: display label} for a Link target, using its title field when it shows titles in links."""
	lmeta = frappe.get_meta(linked)
	title = lmeta.title_field if lmeta.show_title_field_in_link and lmeta.title_field else None
	if not title or not names:
		return {n: n for n in names}
	rows = frappe.get_all(linked, filters={"name": ["in", list(names)]}, fields=["name", title])
	labels = {r.name: r.get(title) or r.name for r in rows}
	return {n: labels.get(n, n) for n in names}


def _resource_rows(doctype, defs, resource_field, used_values, show_empty):
	"""Row list: every value in use, plus (optionally) every possible value, then 'Unassigned' last."""
	df = defs[resource_field]
	values = {v for v in used_values if v}
	labels = {}

	if df["fieldtype"] == "Link" and df["options"]:
		linked = df["options"]
		if show_empty:
			lmeta = frappe.get_meta(linked)
			title = lmeta.title_field if lmeta.show_title_field_in_link and lmeta.title_field else None
			try:
				for r in frappe.get_list(
					linked,
					fields=["name", *([title] if title else [])],
					order_by="name asc",
					limit_page_length=MAX_EMPTY_ROWS,
				):
					values.add(r.name)
					labels[r.name] = r.get(title) or r.name if title else r.name
			except frappe.PermissionError:
				pass
		labels = {**_link_labels(linked, values), **labels}
	else:
		if show_empty:
			values.update(df["choices"])
		labels = {v: v for v in values}

	rows = sorted(({"value": v, "label": labels.get(v, v)} for v in values), key=lambda r: str(r["label"]).lower())
	if UNASSIGNED in used_values:
		rows.append({"value": UNASSIGNED, "label": _("Unassigned")})
	return rows


@frappe.whitelist()
def get_resource_data(view, start, end):
	"""Rows and cards of one view for the days ``start``..``end`` (inclusive)."""
	cfg = _load_view(view)
	doctype = cfg.source_doctype
	meta = _check_source(doctype)
	defs = field_defs(doctype)

	start_d, end_d = getdate(start), getdate(end)
	sf, ef, rf = cfg.start_field, cfg.end_field, cfg.resource_field or ""
	for fieldname in (sf, ef, rf, cfg.card_title_field):
		if fieldname and fieldname not in defs:
			frappe.throw(_("The view refers to {0}, which no longer exists on {1}.").format(fieldname, doctype))

	filters = [
		_rule_to_filter(doctype, defs, {"field": f.field, "operator": f.operator, "value": f.value})
		for f in cfg.filters
		if f.field in defs
	]
	upper = f"{end_d} 23:59:59" if defs[sf]["fieldtype"] == "Datetime" else str(end_d)
	filters.append([doctype, sf, "<=", upper])
	lower = f"{start_d} 00:00:00" if defs[ef]["fieldtype"] == "Datetime" else str(start_d)
	or_filters = [[doctype, ef, ">=", lower], [doctype, ef, "is", "not set"]]

	body = [f for f in cfg.card_fields if f.field in defs]
	wanted = ["name", cfg.card_title_field, sf, ef, *([rf] if rf else [])]
	if cfg.color_field and cfg.color_field in defs:
		wanted.append(cfg.color_field)
	wanted += [f.field for f in body]
	wanted = list(dict.fromkeys(wanted))

	records = frappe.get_list(
		doctype,
		fields=wanted,
		filters=filters,
		or_filters=or_filters,
		order_by=f"{sf} asc, creation asc",
		limit_page_length=MAX_CARDS + 1,
	)
	truncated = len(records) > MAX_CARDS
	records = records[:MAX_CARDS]

	cards, used = [], set()
	for r in records:
		begin = r.get(sf)
		if not begin:
			continue
		finish = r.get(ef) or begin
		d1, d2 = getdate(begin), getdate(finish)
		if d2 < d1:
			finish, d2 = begin, d1
		if d1 > end_d or d2 < start_d:
			continue

		resource = (r.get(rf) or UNASSIGNED) if rf else UNASSIGNED
		used.add(resource)
		lines, details = [], []
		for f in body:
			text = _display(meta, defs, f.field, r.get(f.field), r)
			if not text:
				continue
			line = {"label": f.label or "", "value": text, "style": f.style or "Normal"}
			lines.append(line)
			if cint(f.show_in_detail):
				# the side panel names the field even when the card shows it without a prefix
				details.append({**line, "label": f.label or defs[f.field]["label"]})

		cards.append(
			{
				"name": r.name,
				"resource": resource,
				"title": _display(meta, defs, cfg.card_title_field, r.get(cfg.card_title_field), r) or r.name,
				"start": _stamp(begin),
				"end": _stamp(finish),
				"color": (r.get(cfg.color_field) or "") if cfg.color_field and cfg.color_field in defs else "",
				"lines": lines,
				"details": details,
			}
		)

	return {
		"view": _view_dict(cfg),
		"rows": (
			_resource_rows(doctype, defs, rf, used, cint(cfg.show_empty_resources))
			if rf
			else ([{"value": UNASSIGNED, "label": _("All")}] if cards else [])
		),
		"cards": cards,
		"truncated": truncated,
		"meta": {
			"start_type": defs[sf]["fieldtype"],
			"end_type": defs[ef]["fieldtype"],
			"resource_label": defs[rf]["label"] if rf else "",
			"can_create": bool(frappe.has_permission(doctype, "create")),
			"can_write": bool(frappe.has_permission(doctype, "write")),
		},
	}


@frappe.whitelist()
def update_card(view, name, start=None, end=None, resource=None):
	"""Move or resize a card by saving the underlying record. Only the view's own fields can change."""
	cfg = _load_view(view)
	doc = frappe.get_doc(cfg.source_doctype, name)
	doc.check_permission("write")

	if start is not None:
		doc.set(cfg.start_field, start)
	if end is not None:
		doc.set(cfg.end_field, end)
	if resource is not None and cfg.resource_field:
		doc.set(cfg.resource_field, resource or None)
	doc.save()
	return {
		"name": doc.name,
		"start": _stamp(doc.get(cfg.start_field)),
		"end": _stamp(doc.get(cfg.end_field)),
		"resource": (doc.get(cfg.resource_field) or UNASSIGNED) if cfg.resource_field else UNASSIGNED,
	}
