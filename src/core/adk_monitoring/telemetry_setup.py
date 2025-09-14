import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

def setup_opentelemetry(app_name: str = "mds7-rebuild", app_version: str = "0.2.0"):
    """
    Configures OpenTelemetry for the application, setting up the Cloud Trace Exporter.
    """
    # Set up a resource for your service
    resource = Resource.create({
        "service.name": app_name,
        "service.version": app_version,
    })

    # Configure the Cloud Trace exporter
    cloud_trace_exporter = CloudTraceSpanExporter()

    # Configure the TracerProvider
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(cloud_trace_exporter)
    provider.add_span_processor(processor)

    # Set the global TracerProvider
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry configured with Cloud Trace Exporter.")

