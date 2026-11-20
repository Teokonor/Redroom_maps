# Build the Vue application.
FROM node:22-alpine AS frontend-build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build-only


# Serve it through nginx.
FROM nginx:1.27-alpine

ENV BACKEND_UPSTREAM=host.docker.internal:8652

RUN rm -f /etc/nginx/conf.d/default.conf

COPY deploy/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY deploy/nginx/proxy_params /etc/nginx/proxy_params
COPY deploy/nginx/security_headers /etc/nginx/security_headers
COPY --from=frontend-build /app/dist /usr/share/nginx/html

EXPOSE 80
