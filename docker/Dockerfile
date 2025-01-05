# Use official Python image as base
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install ODBC library and its dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl apt-transport-https gnupg2 lsb-release && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm /etc/apt/sources.list.d/mssql-release.list
    
# Set the working directory in the container
WORKDIR /app

# Install virtualenv
RUN pip install virtualenv

# Create a virtual environment
RUN virtualenv venv

# Activate the virtual environment
RUN /bin/bash -c "source venv/bin/activate"

# Copy the dependencies file to the working directory
COPY ./app/requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose the port streamlit runs on
EXPOSE 8501

# Command to run the streamlit app
CMD ["streamlit", "run", "app.py"]
