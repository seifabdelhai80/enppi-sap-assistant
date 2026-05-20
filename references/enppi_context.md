# ENPPI-Specific SAP Context

This file is loaded by `prompts/system_prompts.py` to inject ENPPI-specific knowledge into
the assistant. Fill in the sections below with your actual landscape details.

---

## Company & System Landscape

- **Company**: ENPPI (Engineering for the Petroleum & Process Industries)
- **Industry**: Oil & Gas EPC
- **SAP Release**: S/4HANA 2022 On-Premise
- **Company Code**: *(e.g. 1000)*
- **Controlling Area**: *(e.g. 1000)*
- **Plants**: *(e.g. 1001 – Cairo HQ, 1002 – Site)*
- **Purchasing Org**: *(e.g. 1000)*
- **Sales Org / Distribution Channel / Division**: *(fill in)*

---

## Chart of Accounts

- **Chart of Accounts ID**: *(e.g. ENPP)*
- Key GL accounts to know:
  | GL Account | Description |
  |---|---|
  | *(e.g. 400000)* | *(e.g. Raw Materials Consumption)* |

---

## Custom Z-Objects Catalog

List your team's Z-programs, Z-classes, Z-tables, and Z-function modules here so the
assistant can reference them by name.

| Object Name | Type | Module | Description |
|---|---|---|---|
| *(e.g. Z_MM_OPEN_PO)* | Program | MM | *(Lists open POs for a vendor)* |
| *(e.g. ZCL_FI_POSTING)* | Class | FI | *(Wrapper for FI document posting)* |
| *(e.g. ZT_VENDOR_MAP)* | Table | MM | *(Custom vendor mapping table)* |

---

## Authorization Roles & Profiles

| Role Name | Description |
|---|---|
| *(e.g. Z_MM_BUYER)* | *(MM purchasing user — create/change POs)* |
| *(e.g. Z_FI_APPROVER)* | *(FI document approver)* |

---

## Integration Partners & Interfaces

| System | Interface Type | Direction | Description |
|---|---|---|---|
| *(e.g. Oracle Primavera)* | IDoc / RFC | Inbound | *(Project data sync)* |
| *(e.g. DMS)* | OData | Outbound | *(Document attachments)* |

---

## ENPPI-Specific Standards & Conventions

- *(e.g. All custom reports must include a selection screen with company code and date range)*
- *(e.g. Transport requests must be approved by the BASIS team before import to production)*
- *(e.g. BAPI error handling must log to table ZT_ERROR_LOG)*
