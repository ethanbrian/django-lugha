# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Gunicorn
RUN pip install gunicorn

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV DJANGO_SETTINGS_MODULE=translation.settings

# Run Gunicorn when the container launches
CMD ["gunicorn", "translation.wsgi:application", "--bind", "0.0.0.0:8000", "--certfile", "/etc/letsencrypt/live/djangoapi.drlugha.com/fullchain.pem", "--keyfile", "/etc/letsencrypt/live/djangoapi.drlugha.com/privkey.pem", "--workers", "3", "--preload"]

