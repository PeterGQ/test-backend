# --- Stage 1: The Builder ---
# This stage installs Poetry and converts pyproject.toml into a requirements.txt file.
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry
# Install the poetry-plugin-export to enable exporting dependencies
RUN poetry self add poetry-plugin-export

# Copy only the dependency files to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Export the dependencies to a requirements.txt file
# This is the modern equivalent of `pip freeze` for Poetry projects
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# --- Stage 2: The Final Image ---
# This stage builds the final, lightweight image for production.
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security best practices
RUN addgroup --system app && adduser --system --group app

# Copy the generated requirements.txt from the builder stage
COPY --from=builder /app/requirements.txt .

# Install the production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint for the container
ENTRYPOINT ["/app/entrypoint.sh"]