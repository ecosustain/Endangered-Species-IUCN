# Use a Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /endangered-species

# Copy the project files to the container
COPY . .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to start the application
CMD ["python", "src/dashboard/app.py"]
