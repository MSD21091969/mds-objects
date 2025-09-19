# Use the official Prefect image
FROM prefecthq/prefect:2-python3.12

# The PREFECT_API_DATABASE_CONNECTION_URL will be set as an
# environment variable in the Google Cloud Run service configuration.

# Expose the Prefect server port. Cloud Run will map its own PORT to this.
EXPOSE 4200

# Use a shell form ENTRYPOINT to be able to reference the PORT env var.
# This is the standard way to make a container work on Cloud Run.
# It will use the PORT variable provided by Cloud Run, and fall back to 4200 if not set.
ENTRYPOINT ["sh", "-c", "prefect server start --host 0.0.0.0 --port ${PORT:-4200}"]

# The CMD is not strictly needed with this ENTRYPOINT, but can be useful for local testing.
CMD ["prefect", "server", "start", "--host", "0.0.0.0", "--port", "4200"]
