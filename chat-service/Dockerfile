FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production && npm cache clean --force
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm install --save-dev typescript @types/node && npx tsc && npm uninstall --save-dev typescript @types/node
RUN cp -r node_modules node_modules_prod && npm install

FROM node:20-alpine AS production
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules_prod ./node_modules
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 3004
CMD ["node", "dist/app.js"]
