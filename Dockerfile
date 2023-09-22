# Use the Python 3.8 base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container (excluding venv)
COPY . /app

# Install the required packages from requirements.txt
RUN pip install -r requirements.txt

# Expose port 3000
EXPOSE 3000

# Specify the command to run the application
CMD ["python", "main.py"]
