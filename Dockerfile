FROM python:3.11

WORKDIR /app

# Install R
RUN apt-get update && apt-get install -y r-base

# Copy requirements first
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
