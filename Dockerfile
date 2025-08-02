FROM python:3.10-slim
SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential \
    curl \
    apt-utils \
    gnupg2 &&\
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update
RUN env ACCEPT_EULA=Y apt-get install -y msodbcsql18
WORKDIR /app
COPY . .
RUN pip install uv
RUN uv sync --extra postgres --extra sqldb
ENV PATH="/app/.venv/bin:$PATH"
# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT [] 
CMD ["uvicorn", "datu.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
