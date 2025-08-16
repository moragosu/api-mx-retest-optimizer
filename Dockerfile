FROM hqdev-sep.redii.net/metafactory/base-uv:latest

ARG PY_INDEX_URL
ARG PY_TRUSTED_HOST
ARG FCT_NAME
ARG AUTH_KEY

ENV INSTALL_HOME /
ENV NO_PROXY bart.sec.samsung.net
ENV FCT_NAME ${FCT_NAME}

COPY . ${INSTALL_HOME}
WORKDIR ${INSTALL_HOME}

RUN /root/.local/bin/uv sync --index-url https://bart.sec.samsung.net/artifactory/api/pypi/pypi-remote/simple

EXPOSE 8000

CMD ["/root/.local/bin/uv", "run", "-m", "retest_optimizer"]