# Use modern Python to match your local setup
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (fixed the typo here!)
COPY . .

# Give Hugging Face permission to write to the uploads folder
RUN chmod -R 777 /app

# Hugging Face Spaces MUST use port 7860
EXPOSE 7860
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:7860", "--timeout", "120"]