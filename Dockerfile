# Use an official lightweight Python image
FROM python:3.10-slim


# Copy the requirements.txt first to leverage Docker cache
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000 for FastAPI app
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "routes:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
