ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# Copy application code to the container
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["python", "app/main.py", "backend"]
