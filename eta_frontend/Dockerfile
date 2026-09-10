FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

FROM node:20-alpine AS builder
WORKDIR /app
ARG VITE_API_BASE_URL
ARG VITE_DEFAULT_CURRENCY
ARG VITE_THEME
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_DEFAULT_CURRENCY=${VITE_DEFAULT_CURRENCY}
ENV VITE_THEME=${VITE_THEME}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/dist ./dist
RUN npm install -g serve
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
