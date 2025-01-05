# Use official Python image as base
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install necessary packages, apt-utils, and Microsoft ODBC Driver for SQL Server
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-utils \
        curl \
        apt-transport-https \
        gnupg2 \
        lsb-release \
        unixodbc \
        unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/mssql-release.list

# Set the working directory in the container
WORKDIR /app

# Install dependencies directly in the system Python environment
COPY ./app/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose the port your Streamlit app will run on
EXPOSE 9206

# Command to run the Streamlit app
CMD ["streamlit", "run", "--server.port", "9206", "app.py"]
