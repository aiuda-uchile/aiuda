FROM node:22.22-bookworm-slim

WORKDIR /workspace/src/frontend

COPY src/frontend/package*.json ./
RUN npm install

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]