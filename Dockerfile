FROM docker.io/astral/uv:python3.12-bookworm-slim
ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    git jq yq curl wget nano unzip tk8.6 \
    binutils libproj-dev gdal-bin geos-bin libsqlite3-mod-spatialite

RUN mkdir /src
COPY ./ /src
# RUN uv pip install -r /app/requirements.txt --system
WORKDIR /src