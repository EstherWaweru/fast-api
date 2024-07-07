FROM python:3.9-slim
WORKDIR /home/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev && \
    apt-get clean && \
    apt-get install -y build-essential && \
    apt-get install -y pkg-config

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /home/app/

# Install deps
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code to the necessary path
COPY . /home/app/

EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
