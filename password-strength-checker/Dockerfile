# ── Base image ──────────────────────────────────────────────────────────────
# Node.js 20 LTS slim image — required so the gg --runtime node target
# has a Node.js interpreter available at runtime.
FROM node:20-slim

# ── Install Graftcode Gateway (`gg`) ────────────────────────────────────────
# Same download pattern as sdn-currency-converter and stock portfolio tracker.
RUN mkdir -p /usr/app \
    && apt-get update \
    && apt-get install -y wget \
    && wget -O /usr/app/gg.deb \
       https://github.com/grft-dev/graftcode-gateway/releases/latest/download/gg_linux_amd64.deb \
    && dpkg -i /usr/app/gg.deb \
    && rm /usr/app/gg.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Copy service module ──────────────────────────────────────────────────────
COPY password_checker /usr/app/password_checker

# ── Launch gg ────────────────────────────────────────────────────────────────
# `gg` introspects PasswordChecker's public methods and exposes them as
# remotely callable Grafts — no HTTP server code required in our JS class.
CMD ["gg", "--runtime", "node", "--modules", "/usr/app/password_checker/checker.js", "--port", "5002"]
