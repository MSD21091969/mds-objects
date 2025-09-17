import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

def setup_opentelemetry(app_name: str = "mds7-rebuild", app_version: str = "0.2.0", project_id: str | None = None):
    """
    Configures OpenTelemetry for the application, setting up the Cloud Trace Exporter.
    """
    if project_id is None:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id is None:
            logger.warning("GOOGLE_CLOUD_PROJECT environment variable not set. Cloud Trace Exporter may not function correctly.")

    # Set up a resource for your service
    resource = Resource.create({
        "service.name": app_name,
        "service.version": app_version,
    })

    # Configure the Cloud Trace exporter
    cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)

    # Configure the TracerProvider
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(cloud_trace_exporter)
    provider.add_span_processor(processor)

    # Set the global TracerProvider
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry configured with Cloud Trace Exporter.")

