---
# === BASIC INFO ===
name: Jane Doe
role: Senior Software Engineer

# === OPTIONAL ===
# Filename of your headshot, or delete this line to skip the photo entirely.
photo: headshot.svg

# A short intro paragraph. The "|" keeps line breaks; use ">" instead if
# you want one flowing paragraph regardless of how you wrap the lines.
summary: |
  Backend engineer with 9+ years of experience building distributed
  systems and data platforms. Comfortable across the stack — from
  low-level performance work to leading small teams. Based in London;
  previously in Berlin and Stockholm.

# === CONTACT ROW ===
# One item per line. Use Markdown link syntax for clickable items.
# The double quotes are needed because lines that start with "[" are
# special in YAML.
contact:
  - "London, UK"
  - "+44 7700 900123"
  - "[jane@example.com](mailto:jane@example.com)"
  - "[LinkedIn](https://www.linkedin.com/in/janedoe/)"
  - "[GitHub](https://github.com/janedoe)"
---

## Skills

| | |
|---|---|
| **Languages** | Go, Rust, Python, TypeScript |
| **Infrastructure** | Kubernetes, Terraform, AWS, GitHub Actions |
| **Data & Streaming** | Kafka, Flink, ClickHouse, Spark |
| **Databases** | PostgreSQL, Redis, DynamoDB |
| **Observability** | Prometheus, Grafana, OpenTelemetry |
| **APIs & Protocols** | gRPC, GraphQL, REST, Protobuf |

## Experience

### Northwind Data — Jan 2022 – Present

*Senior Software Engineer (previously Engineer II)*

Tech lead for the ingestion platform team — owns the pipeline that ingests, normalizes, and routes 8 TB/day of customer event data into the warehouse.

- Cut average ingestion latency from 90s to under 4s by replacing a polling-based architecture with a streaming one (Kafka + Flink).
- Designed and shipped a multi-tenant rate-limiting layer that handles 25k req/s with sub-millisecond overhead, unblocking the team to onboard self-serve customers.
- Reduced on-call paging volume by ~70% over a quarter by introducing SLO-based alerting and removing noisy threshold alerts.
- Mentor for two junior engineers; led the hiring loop for three senior backend hires.

**Stack:** Go, Rust, Kafka, Flink, PostgreSQL, ClickHouse, Kubernetes, Terraform, AWS

### Bramble Health — Mar 2020 – Jan 2022

*Senior Software Engineer*

Worked on the clinician-facing application platform at a Series-B digital health startup.

- Led the migration from a Rails monolith to a set of Go services behind a GraphQL gateway, reducing p99 API latency by 60% without changing the frontend contract.
- Built the audit-logging pipeline used to demonstrate HIPAA compliance during the company's SOC 2 Type II audit.
- Owned the feature-flag system, which became the primary mechanism for safe rollouts across the engineering org (~40 engineers).

**Stack:** Go, TypeScript, GraphQL, PostgreSQL, Redis, Kubernetes, AWS

### Lumiform — Aug 2017 – Feb 2020

*Software Engineer*

Early backend engineer at an industrial-IoT startup. Wore a lot of hats; everything from production firmware updates to billing.

- Built the device-firmware OTA-update service, which has shipped tens of thousands of updates without a rollback to date.
- Implemented the billing integration with Stripe and the in-product subscription management UI.
- Established the engineering team's CI/CD baseline (test pyramid, branch protection, automated previews).

**Stack:** Python, Django, PostgreSQL, Redis, Docker, AWS

### Helix Robotics — Sep 2015 – Jul 2017

*Junior Software Engineer*

First job out of university. Worked on the control-plane software for industrial robotic arms.

- Wrote the Python wrapper SDK used by all customer-facing automation scripts.
- Reduced cycle time on the integration test suite from 45 to 9 minutes.

**Stack:** Python, C++, Linux, Jenkins

## Education

### MSc Computer Science — Sep 2013 – Jun 2015

*University of Edinburgh*

Thesis: Streaming algorithms for approximate distinct-count over unbounded keyspaces.

### BSc Computer Science — Sep 2010 – Jun 2013

*University of Edinburgh*

## Side Projects

### Tinydash

Open-source dashboarding tool for self-hosted SQLite databases. Single binary, no dependencies, ~3k GitHub stars.

**Stack:** Go, SQLite, htmx

### Drift

Time-series anomaly detection library focused on small datasets where statistical methods outperform ML.

**Stack:** Python, NumPy, SciPy

## Languages

English (native), German (conversational), Swedish (basic).
