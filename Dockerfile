# Step 1: Base Image
# Use an official Python runtime as the base. Choose a version that matches
# your development environment if possible (e.g., 3.10, 3.11).
# Using a 'slim' variant reduces the final image size.
FROM python:3.10-slim

# Step 2: Set Working Directory
# Define the directory inside the container where your application code will live.
WORKDIR /app

# Step 3: Copy Dependencies File First
# Copy only the requirements file. This allows Docker to cache the installed
# dependencies layer unless requirements.txt changes, speeding up builds.
COPY requirements.txt .

# Step 4: Install Dependencies
# Upgrade pip and install the packages listed in requirements.txt.
# --no-cache-dir reduces image size by not storing the pip cache.
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Step 5: Copy Application Code
# Copy the rest of your application files (app.py, models.py, templates folder,
# static folder, etc.) into the working directory inside the container.
COPY . .

# Step 6: Expose Port
# Inform Docker that the container will listen on port 5000 at runtime.
# This matches the port specified in your app.py (app.run(..., port=5000)).
# Replit typically handles mapping this internal port to the outside world.
EXPOSE 5000

# Step 7: Define Run Command
# Specify the command to run when the container starts.
# This executes your Flask application using the Python interpreter.
# Your app.py should be configured to listen on host '0.0.0.0' to be accessible
# within Replit's network environment, which it already is.
CMD ["python", "app.py"]