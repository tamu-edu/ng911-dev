FROM debian:bullseye-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Python
RUN apt-get update && \
    apt-get install -y \
        git \
        build-essential \
        cmake \
        libpcap-dev \
        libncurses5-dev \
        iputils-ping \
        net-tools \
        curl \
        python3 \
        python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone and build SIPp from source
RUN git clone https://github.com/SIPp/sipp.git && \
    cd sipp && \
    cmake . && \
    make && \
    make install

# Set working directory
WORKDIR /app

# Copy source files
COPY . .

# Install Python requirements if available
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Set entrypoint
CMD ["python3", "docker_entrypoint.py"]