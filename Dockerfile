# 1. Use an official lightweight Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker caching
COPY requirements.txt .

# 4. Install the specified packages (Pandas, Numpy, Matplotlib)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the source code and create the data directory
COPY src/ ./src/
RUN mkdir -p /app/data

# 6. Define the command to run the data ingestion pipeline when the container starts
CMD ["python", "src/data_ingestion.py"]
