FROM node:22-alpine AS build

WORKDIR /app

# Vite inlines VITE_* env vars into the built JS at build time, so the API
# base URL has to be a build arg rather than a runtime environment variable.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine

WORKDIR /app
RUN npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 4173

CMD ["serve", "-s", "dist", "-l", "4173"]
