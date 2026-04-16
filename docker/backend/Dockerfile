FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libreoffice-core \
    libreoffice-impress \
    fonts-dejavu \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

WORKDIR /workspace

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN grep -Ev '^prefix\s*:' /tmp/environment.yml > /tmp/environment.docker.yml
RUN micromamba create -y -n aluda-whisper -f /tmp/environment.docker.yml && micromamba clean --all --yes

EXPOSE 8000

CMD ["micromamba", "run", "-n", "aluda-whisper", "uvicorn", "src.backend.aluda_backend_fastapi:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
