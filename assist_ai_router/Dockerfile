ARG BUILD_FROM=ghcr.io/berriai/litellm:v1.106.4@sha256:c169fb3adc514fcf210377c203f3de406d54f10bfdacf13948a4a839db9af7de
FROM ${BUILD_FROM}

ARG BUILD_VERSION=1.0.3
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
