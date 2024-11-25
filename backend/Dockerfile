ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim

# Working directory
WORKDIR /app

# Copy requirements and install dependences
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code to the container
COPY ./app /app/

# Expose the port for FastAPI
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]