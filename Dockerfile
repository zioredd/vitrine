FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir \
  pytest==8.3.4 \
  pytest-cov==6.0.0 \
  pytest-django==4.9.0 \
  django==5.1.5 \
  djangorestframework==3.15.2 \
  django-cors-headers==4.6.0 \
  pydantic==2.10.4 \
  && pip wheel --no-deps -w /wheels \
    packages/types packages/core packages/catalog packages/mix packages/crowd \
    packages/graph packages/parser packages/rebalance packages/sync packages/events \
    packages/queue packages/scheduler packages/retry packages/pipeline packages/worker \
    packages/ingest packages/rules packages/ops packages/enterprise packages/ai \
  && pip install --no-cache-dir \
    vitrine-types==0.1.0 vitrine-core==0.1.0 vitrine-catalog==0.1.0 \
    vitrine-mix==0.1.0 vitrine-crowd==0.1.0 vitrine-graph==0.1.0 \
    vitrine-parser==0.1.0 vitrine-rebalance==0.1.0 vitrine-sync==0.1.0 \
    vitrine-events==0.1.0 vitrine-queue==0.1.0 vitrine-scheduler==0.1.0 \
    vitrine-retry==0.1.0 vitrine-pipeline==0.1.0 vitrine-worker==0.1.0 \
    vitrine-ingest==0.1.0 vitrine-rules==0.1.0 vitrine-ops==0.1.0 \
    vitrine-enterprise==0.1.0 vitrine-ai==0.1.0 \
    --find-links /wheels --no-index
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PYTHONPATH=/app/apps/api
CMD ["pytest"]
