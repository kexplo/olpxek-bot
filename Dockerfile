FROM python:3.8-slim
WORKDIR /app
COPY . .

ENV PYTHONUNBUFFERED=1
# do not ask any interactive question
ENV POETRY_NO_INTERACTION=1

RUN pip install poetry>=1.0.10
RUN poetry install --no-dev

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
