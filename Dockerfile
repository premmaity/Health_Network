# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Prevent Python from writing .pyc files to disc and enable stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container
COPY . .


# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expose the port (Render.com will pass the PORT env variable at runtime)
EXPOSE 5000

# Run the application. Make sure your app file is named app.py.
CMD ["python", "app.py"]
