# --- Build Stage ---
# This stage installs dependencies into a virtual environment.
FROM python:3.12-slim as builder

WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the requirements file to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
# This stage creates the final, lean image.
FROM prefecthq/prefect:2-python3.12

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY . /app
WORKDIR /app

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# The CMD is inherited from the base prefect image, 
# which is `prefect worker start`
