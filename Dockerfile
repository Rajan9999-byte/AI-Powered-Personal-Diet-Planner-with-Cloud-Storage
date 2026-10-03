FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend ./frontend
COPY public ./public
COPY vite.config.js ./vite.config.js
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY public ./public
COPY data ./data
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
COPY .env.example ./
EXPOSE 8080
CMD ["python", "-m", "backend"]
