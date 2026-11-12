FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY automation/ /app/automation/
COPY videos/ /app/videos/

ENV PYTHONUTF8=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860
CMD ["python", "automation/cloud_server.py"]
