
FROM python:3.10-slim


WORKDIR /app

COPY ./requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy our simulation source code into the container
COPY ./src ./src

ENTRYPOINT ["python", "-u", "src/run_simulation.py"]