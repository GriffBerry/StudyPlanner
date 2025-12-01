FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src ./src

# Defaults (can be overridden)
ENV FLASK_ENV=production
ENV PORT=8080
ENV MAX_HOURS_PER_DAY=5
ENV PLANNING_HORIZON_DAYS=7
ENV DB_PATH=/app/tasks.db

EXPOSE 8080

CMD ["python", "-m", "src.app"]
