# Project Calendar

A weekly time-resource calendar for ERPNext v16 (Vue 3 + TypeScript + Tailwind + frappe-ui).

Open it at `/project-calendar`, from the **Project Calendar** button on the Project list, or from the
Frappe apps switcher.

## How it works

A **Resource View** is saved configuration, not business data. It says:

- which DocType is the source,
- which Link/Select field defines the resource rows (optionally showing empty/unbooked rows),
- which fields are the card title, start, end and (optionally) colour,
- embedded filter rules (field, operator, value) so the view only shows its own records,
- extra card body fields, in order, each with an optional prefix label and style.

The cards are the real records. Reading goes through `frappe.get_list` and writing through `doc.save()`,
so ERPNext permissions and validation always apply.

On the grid: sticky resource column, one column per day, overlapping cards stack in lanes, rows grow with
their content, rich text is shown as plain text. Click a card to open the record in Desk; drag it to
another day or row, or drag its edges, to save new dates / a new resource.

Views are created, edited, duplicated and deleted from **Manage Views** (needs the Projects Manager or
System Manager role; everyone with Desk access can open views).

A fresh install gets one starter view, **Projects** (projects by customer).

## Development

```bash
cd frontend
npm install
npm run build        # writes to project_calendar/public/frontend
npm run typecheck
```

Backend API: `project_calendar/api.py`. The page is served by `project_calendar/page_renderer.py`.
