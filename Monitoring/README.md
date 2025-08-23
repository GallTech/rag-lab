# Monitoring (lab-1-monitoring01)

This module provides observability for the RAG lab environment.

## Scope
- **Prometheus** for metrics collection (scraping system + service exporters).
- **Grafana** for dashboards and visualizations.
- **Alertmanager** for alert routing.
- **Filebeat → Elasticsearch** (optional) for log shipping and centralized search.

No application logic or data lives here — only monitoring & alerting.

---

## Canonical paths (planned)
- Prometheus data: /var/lib/prometheus
- Grafana data: /var/lib/grafana
- Alertmanager config: /etc/alertmanager/alertmanager.yml
- Prometheus config: /etc/prometheus/prometheus.yml
- Dashboards/templates (this repo): /opt/rag-lab/Monitoring/dashboards
- Logs: /var/log/monitoring

---

## Repository layout
- config/ — example Prometheus, Grafana, and Alertmanager configs (templates only)
- dashboards/ — Grafana JSON dashboards
- docs/ — runbooks and notes
- scripts/ — setup and maintenance helpers
- alerts/ — alert definitions and routing templates
- tests/ — health checks for monitoring stack
- .gitignore — excludes local state (logs, data dirs)
- README.md — this file
