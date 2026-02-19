FROM node:17

WORKDIR /opt/app

COPY package*.json .

RUN npm ci

COPY . .

CMD ["sh", "-c", "cp -R /opt/app/assets/. /opt/app/staticfiles/ && ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir /opt/app/staticfiles --public-url=./"]
