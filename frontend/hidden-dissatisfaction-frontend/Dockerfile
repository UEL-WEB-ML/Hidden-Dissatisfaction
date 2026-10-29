FROM node:24-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM dependencies AS test
RUN apk add --no-cache chromium
ENV CHROME_BIN=/usr/bin/chromium-browser
COPY . .
CMD ["npm", "test"]

FROM dependencies AS build
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist/hidden-dissatisfaction-frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
