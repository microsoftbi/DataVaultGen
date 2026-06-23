# System Introduction

## Overview

This system is designed to assist in building data warehouses following the Data Vault 2.0 methodology.

It is a modernized port of the original tool: https://github.com/microsoftbi/DWH-Generator

## Assumptions

Assume there is an OLTP database: `TEST_STORE`

The OLTP database contains the tables we need to load into the data warehouse.

This tool reads table/column metadata from the OLTP database, lets you configure it, and then auto-generates:
- DDL scripts for STAGE tables
- Stored procedures in STAGE for loading data from OLTP (full load by default)
- Views over STAGE tables that compute hash keys (for downstream CDC logic)
- DDL scripts for CORE (Data Vault) tables
- Stored procedures in CORE for loading data from STAGE into Data Vault objects

Our data warehouse consists of two databases (which must be created manually):
- `STAGE`
- `CORE`

After creating the STAGE and CORE databases manually, you can start the system.

Backend startup:

```
cd backend
python main.py
```

Frontend startup:

```
cd frontend
npm run dev
```

## How to Use

### Manually create the data warehouse databases

- `STAGE`
- `CORE`

### Configure database connections

Open the system and click "Connections" on the left.

Create the server connections. We recommend creating two: typically the OLTP server and the data warehouse server are different machines; if they share the same server, one connection is enough.

After creating the server connections, configure the database role binding at the bottom of the page. The system uses three roles:
- `OLTP`
- `STAGE`
- `CORE`

For each role, specify which server connection to use and the corresponding database name.

### Metadata Import

Once the database connections are set up, click "Metadata Import" on the left.

Step by step, choose the OLTP source, which tables to import, and which columns within each table to import.

## STAGE Layer

The STAGE layer contains the following objects:
- **STG table**: a 1-to-1 image of the source table.
- **CDC table**: stores change data captured by comparing the STG and LOG tables.
- **LOG table**: stores all historical data.
- **MTA view**: derived from STG, adds supporting fields.
- **LOG_CURRENT view**: derived from LOG, returns only the latest row per HK (LOG self-joined on HK with MAX LOAD_DTS).
- **CDC stored procedures**
- **Orchestration scripts**
