FROM python:alpine

ENV PYTHONUNBUFFERED 1

# Эти переменные передаются через build.args в compose
ARG UNAME=docker
ARG UID=1000
ARG GID=1000

# Тут доставляет все что может понадобитьсярина
RUN apk update && apk --no-cache add shadow \
  bash \
  git \
  curl \
  netcat-openbsd \
  postgresql-client \
  python3-dev

RUN groupadd -g ${GID} -o ${UNAME} && \
  useradd -m -u ${UID} -g ${GID} -o -s /bin/bash ${UNAME}

WORKDIR /code

COPY --chown=${UNAME} pyproject.toml src ./

VOLUME ["/code"]

# Без зависимостей для разработчика
# RUN pip install --upgrade pip .
RUN pip install --upgrade pip '.[dev]'

# Если вызвать раньше, то питоновские зависимости будут установлены в $HOME
# и не будут работать бинарники, тк путей до них нет в $PATH
USER ${UNAME}

EXPOSE 8000
CMD uvicorn --host 0.0.0.0 ripe_db_search:app
