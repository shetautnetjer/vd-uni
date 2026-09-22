FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-tk ffmpeg vlc-bin vlc-plugin-base xvfb xauth nodejs ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PYTHONPATH=/work/src HOME=/tmp
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /work
USER 65534:65534
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
