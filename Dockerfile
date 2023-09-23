# Use the Python 3.8 base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container (excluding venv)
COPY . /app

# Install the required packages from requirements.txt
RUN pip install -r requirements.txt

ARG DEFAULT_EXPOSE_PORT=3000

ENV EXPOSE_PORT $DEFAULT_EXPOSE_PORT

# Expose port
EXPOSE $EXPOSE_PORT

# Specify the command to run the application
CMD ["python", "main.py"]
