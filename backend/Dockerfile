ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app



# Copy requirements and install dependences
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt

# Download dependencies as a separate step to take advantage of Docker's caching.
#RUN --mount=type=cache,target=/root/.cache/pip \
 #   --mount=type=bind,source=requirements.txt,target=requirements.txt \
  #  python -m pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code to the container #COPY ./app /app/
#COPY ./app /app/

#ENV PYTHONPATH=/app

# Expose the port for FastAPI
#EXPOSE 8000

# Command to run the application
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --reload"]

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/main.py", "backend"]
