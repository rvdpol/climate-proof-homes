# Use the base image specified in the compose file
FROM naskio/n8n-python:latest-debian

# Set environment variables
ARG TIMEZONE
ENV GENERIC_TIMEZONE=${TIMEZONE}
ENV TZ=${TIMEZONE}

# Expose the necessary port
EXPOSE 5678

# Set the work directory
WORKDIR /data

# Copy requirements.txt to the container (optional, if you want to install Python packages)
COPY ./requirements.txt /data/requirements.txt

# Install Python packages (if applicable)
RUN pip install -r /data/requirements.txt

# Command to run when the container starts
CMD ["n8n", "start"]