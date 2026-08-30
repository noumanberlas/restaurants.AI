from __future__ import annotations

import logging
import os

from agent_framework.observability import (
    configure_otel_providers,
    create_resource,
    enable_instrumentation,
    enable_sensitive_telemetry,
)

logger = logging.getLogger(__name__)

_configured = False


def setup_observability() -> None:
    """Configure Azure Monitor + AF instrumentation. Call once at startup."""
    global _configured
    if _configured:
        return

    connection_string = os.getenv("AZURE_MONITOR_CONNECTION_STRING", "")
    enable_sensitive = os.getenv("ENABLE_SENSITIVE_DATA", "false").lower() == "true"

    if connection_string:
        _setup_azure_monitor(connection_string, enable_sensitive)
    else:
        _setup_otlp(enable_sensitive)

    _configured = True


def _setup_azure_monitor(connection_string: str, enable_sensitive: bool) -> None:
    """Wire Azure Application Insights as the OTEL exporter."""
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=connection_string,
            # resource identifies the service in App Insights — shows under "Cloud role"
            resource=create_resource(
                service_name=os.getenv("OTEL_SERVICE_NAME", "restaurant-management-system"),
                service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
                deployment_environment=os.getenv("DEPLOYMENT_ENVIRONMENT", "development"),
            ),
        )

        if enable_sensitive:
            # Opt in to capturing message content, tool args, and tool results.
            # Enable only in dev/test — this data goes to App Insights.
            enable_sensitive_telemetry()
        else:
            enable_instrumentation()

        logger.info("Observability: Azure Monitor connected (App Insights)")
    except ImportError:
        logger.warning(
            "azure-monitor-opentelemetry not installed — falling back to OTLP. "
            "Run: pip install azure-monitor-opentelemetry"
        )
        _setup_otlp(enable_sensitive)


def _setup_otlp(enable_sensitive: bool) -> None:
    """Fall back to OTEL_EXPORTER_OTLP_ENDPOINT when App Insights is not configured."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    if not otlp_endpoint:
        logger.info(
            "Observability: no AZURE_MONITOR_CONNECTION_STRING or "
            "OTEL_EXPORTER_OTLP_ENDPOINT set — instrumentation enabled (no exporter)"
        )

    configure_otel_providers(
        service_name=os.getenv("OTEL_SERVICE_NAME", "restaurant-management-system"),
        service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
        resource_attributes={"deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "development")},
        enable_sensitive_data=enable_sensitive,
        enable_console_exporters=os.getenv("ENABLE_CONSOLE_EXPORTERS", "false").lower() == "true",
    )

    logger.info(
        "Observability: OTLP exporter — endpoint=%s | sensitive=%s",
        otlp_endpoint or "(none)",
        enable_sensitive,
    )
