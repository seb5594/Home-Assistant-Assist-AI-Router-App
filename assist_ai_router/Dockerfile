ARG BUILD_FROM=ghcr.io/berriai/litellm:v1.106.6@sha256:37e2dafb088a7723beb998590682957386dfc83ffea1848486f8e0e5cfac0b06
FROM ${BUILD_FROM}

ARG BUILD_VERSION=1.0.4
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
