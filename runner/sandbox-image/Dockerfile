# Sandbox image for learner submissions (runner protocol §3).
# Contains only Python, pytest and academy_sim. Pin by digest in production (RUNNER_SANDBOX_IMAGE).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml /opt/academy_sim/pyproject.toml
COPY academy_sim /opt/academy_sim/academy_sim
# Optional build secret "pip_ca": a CA bundle for builds behind a TLS-intercepting proxy.
# It is only mounted during this step and never stored in the image.
RUN --mount=type=secret,id=pip_ca,required=false \
    if [ -f /run/secrets/pip_ca ]; then export PIP_CERT=/run/secrets/pip_ca; fi; \
    pip install --no-compile /opt/academy_sim \
    && rm -rf /opt/academy_sim /root/.cache \
    && python -c "import academy_sim, pytest"

USER 65534:65534
WORKDIR /tmp
ENTRYPOINT ["python", "-m", "academy_sim.run", "/work", "/out"]
