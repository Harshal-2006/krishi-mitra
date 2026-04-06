# 1. Force Railway to use Python 3.10
FROM python:3.10-slim

# 2. Set the working directory
WORKDIR /app

# 3. Copy your requirements first
COPY requirements.txt .

# 4. Install dependencies (with no cache to save space)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your app (including the .h5 model)
COPY . .

# 6. Start the web server
CMD gunicorn app:app -b 0.0.0.0:$PORT