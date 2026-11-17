ARG BUILD_FROM=ghcr.io/seb5594/home-assistant-base-python:3.14-alpine3.24-2026.11.0@sha256:807723c78eeeb57962063875e19b500571a5a6e89423977db6d1123832f1550e
FROM ${BUILD_FROM}

# renovate: datasource=pypi depName=litellm
ARG LITELLM_VERSION=1.106.6
RUN python -m pip install --no-cache-dir litellm[proxy]==${LITELLM_VERSION}

ARG BUILD_VERSION=1.0.5
ARG BUILD_ARCH=amd64
LABEL io.hass.version="${BUILD_VERSION}" \
    io.hass.type="addon" \
    io.hass.arch="${BUILD_ARCH}" \
    org.opencontainers.image.source="https://github.com/seb5594/Home-Assistant-Assist-AI-Router-App"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LITELLM_LOCAL_MODEL_COST_MAP=True \
    LITELLM_TELEMETRY_DISABLED=true \
    DO_NOT_TRACK=1
WORKDIR /opt/router
COPY app /opt/router/app
COPY --chmod=755 run.sh entrypoint.sh /
EXPOSE 8000 8099
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["/run.sh"]
