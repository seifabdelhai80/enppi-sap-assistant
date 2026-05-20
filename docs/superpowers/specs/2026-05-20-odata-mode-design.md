# OData Developer Mode — Design Spec
**Date:** 2026-05-20
**Status:** Approved

---

## Overview

Add a 6th assistant mode ("OData Developer") to the ENPPI SAP Assistant, covering the full OData lifecycle on S/4HANA on-premise. Alongside the chat mode, a collapsible quick-reference card is rendered in the main content area with two tabs: standard SAP OData APIs and a Z-services placeholder.

---

## 1. New Mode — `prompts/system_prompts.py`

### Mode metadata
| Field | Value |
|---|---|
| Key | `"odata"` |
| Label | `"OData Developer"` |
| Color | `"#0891B2"` |
| Placeholder | `"e.g. How do I create a custom OData service using SEGW? Show me how to call API_PURCHASEORDER_PROCESS_SRV from Python."` |

### System prompt structure

The system prompt is appended after `ENPPI_CONTEXT` and `SAP_STANDARDS` and covers three areas:

**Build**
- SEGW project setup: creating project, entity types, entity sets, associations, function imports
- CDS-based OData: `@OData.publish: true`, `@Semantics` annotations, VDM annotation best practices
- Service activation via `/IWFND/MAINT_SERVICE`
- Always recommend CDS-based over SEGW for new S/4HANA development

**Consume**
- Base URL pattern for on-premise: `https://<host>:<port>/sap/opu/odata/sap/<SERVICE_NAME>/`
- System query options: `$filter`, `$expand`, `$select`, `$top`, `$skip`, `$orderby`, `$format`
- Authentication: basic auth headers + CSRF token fetch (`GET` with `x-csrf-token: Fetch`, then `POST`/`PATCH`/`DELETE` with token)
- Sample requests in three formats: raw HTTP, Python (`requests`), ABAP (`CL_HTTP_CLIENT`)

**Debug**
- `/IWFND/ERROR_LOG` — Gateway error log, how to read payload and HTTP status
- `/IWFND/TRACES` — enable Gateway trace, read request/response
- `ST05` / SQL trace for backend performance issues
- `SICF` — check service node is active
- Common error codes in SAP Gateway context:
  - `401` — missing/wrong credentials or CSRF token
  - `403` — authorization object missing (check SU53)
  - `404` — service not activated in `/IWFND/MAINT_SERVICE` or wrong entity set name
  - `500` — backend ABAP exception; read inner error from response body

---

## 2. Quick Reference Expander — `app.py`

### Placement
Rendered in the main content area, immediately before `st.chat_input`. Conditional: only shown when `st.session_state.active_mode == "odata"`.

### Structure
```
st.expander("📋 OData Quick Reference", expanded=False)
  └── st.tabs(["Standard SAP APIs", "Z-Services"])
        ├── Tab 1: st.dataframe or st.markdown table of standard services
        └── Tab 2: placeholder table + note pointing to references/enppi_context.md
```

### Tab 1 — Standard SAP APIs (pre-filled)
| Service | Base Path | Key Operations |
|---|---|---|
| API_PURCHASEORDER_PROCESS_SRV | `/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV` | Create/Read/Change PO |
| API_SALES_ORDER_SRV | `/sap/opu/odata/sap/API_SALES_ORDER_SRV` | Create/Read SO |
| API_BUSINESS_PARTNER | `/sap/opu/odata/sap/API_BUSINESS_PARTNER` | Read/Create BP |
| API_MATERIAL_STOCK_SRV | `/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV` | Read stock levels |
| API_PROJECT_RESULTS_SRV | `/sap/opu/odata/sap/API_PROJECT_RESULTS_SRV` | PS project data |
| API_FINANCIALPLANDATA_SRV | `/sap/opu/odata/sap/API_FINANCIALPLANDATA_SRV` | FI plan data |

### Tab 2 — Z-Services (placeholder)
A Markdown table with columns: Service Name | Base Path | Description | Activated By.
Rows are placeholders with a caption: *"Add your Z-services to `references/enppi_context.md`"*.

---

## 3. Files Changed

| File | Change |
|---|---|
| `prompts/system_prompts.py` | Add `"odata"` entry to `MODES` dict |
| `app.py` | Add OData quick-reference expander block before `st.chat_input` |

No new files. No new dependencies.

---

## 4. Out of Scope

- Editing Z-services from within the UI (fill via `references/enppi_context.md`)
- OData V4 deep-dive (V2 is primary on S/4HANA on-premise 2022; V4 mentioned where relevant)
- Live service testing / HTTP client built into the app
