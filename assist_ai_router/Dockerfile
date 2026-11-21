ARG BUILD_FROM=ghcr.io/seb5594/home-assistant-base-python:3.14-alpine3.24-2026.11.0
FROM ${BUILD_FROM}

# renovate: datasource=pypi depName=litellm
ARG LITELLM_VERSION=1.110.2

# renovate: datasource=pypi depName=mcp
ARG MCP_VERSION=2.3.0
RUN python -m pip install --no-cache-dir litellm==${LITELLM_VERSION} mcp==${MCP_VERSION}

ARG BUILD_VERSION=2026.11.21
LABEL io.hass.version="${BUILD_VERSION}" \
    io.hass.type="addon" \
    org.opencontainers.image.title="Home Assistant App: Assist AI Router" \
    org.opencontainers.image.version="${BUILD_VERSION}" \
    org.opencontainers.image.source="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LITELLM_LOCAL_MODEL_COST_MAP=True \
    LITELLM_TELEMETRY_DISABLED=true \
    DO_NOT_TRACK=1
WORKDIR /opt/router
COPY app /opt/router/app
COPY --chmod=755 run.sh entrypoint.sh /
EXPOSE 8000 8099 10300
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["/run.sh"]
