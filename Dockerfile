FROM python:3.10-slim

WORKDIR /app

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/main_batch.py main_batch.py
COPY docker/xgb_model.joblib xgb_model.joblib

COPY app/ app/

CMD ["python", "main_batch.py"]