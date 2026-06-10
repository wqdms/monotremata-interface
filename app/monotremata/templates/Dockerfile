{% autoescape off %}
FROM docker.io/astral/uv:python3.12-bookworm-slim
ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
{% if project.db_driver == "spatialite" %}
    binutils libproj-dev gdal-bin geos-bin libsqlite3-mod-spatialite \
{% endif %}
    git jq yq curl wget nano unzip tk8.6

RUN mkdir -p /app
COPY ./ /app
WORKDIR /app
RUN uv init
CMD ["/bin/bash","-c",{{ container_command }}]
{% endautoescape %}
