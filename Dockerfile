# Project Python version
FROM python:3.11

# Install uv (옵션, 필요 없으면 생략 가능)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . /app

# Install the application dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
