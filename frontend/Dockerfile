# --- Build CSS avec Tailwind ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Image finale nginx ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/*.html /usr/share/nginx/html/
COPY --from=build /app/src /usr/share/nginx/html/src
COPY --from=build /app/dist /usr/share/nginx/html/dist
EXPOSE 80
