FROM python:3.12-slim

# Set directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

#permissions
RUN chmod -R 777 /app

# HF port
EXPOSE 7860
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:7860", "--timeout", "120"]