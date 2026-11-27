# ⚠️ Intentionally insecure Dockerfile used for the GHAS + Trivy demo.
# - Old, end-of-life base image full of OS and runtime CVEs
# - Outdated npm dependencies (see app/package.json)
# - Runs as root, no HEALTHCHECK, uses ADD instead of COPY
FROM node:16

WORKDIR /usr/src/app

ADD app/package.json app/package-lock.json ./
RUN npm ci --omit=dev

COPY app/ .

EXPOSE 3000
CMD ["node", "server.js"]
