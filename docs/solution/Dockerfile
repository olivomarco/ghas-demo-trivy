# Hardened reference Dockerfile (the "after" state of the demo).
# - Multi-stage build: dependencies installed in a builder stage
# - Minimal distroless runtime: no shell, no package manager, tiny attack surface
# - Runs as a non-root user, COPY instead of ADD, HEALTHCHECK defined

FROM node:24-alpine AS build
WORKDIR /usr/src/app
COPY app/package.json app/package-lock.json ./
RUN npm ci --omit=dev
COPY app/ .

FROM gcr.io/distroless/nodejs24-debian13:nonroot
WORKDIR /usr/src/app
COPY --from=build --chown=nonroot:nonroot /usr/src/app ./
USER nonroot
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["/nodejs/bin/node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"]
CMD ["server.js"]
