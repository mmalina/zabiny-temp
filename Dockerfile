ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY . /zabiny-temp
WORKDIR /zabiny-temp

# Install requirements for add-on
RUN apk add --no-cache nginx

COPY data/default.conf /etc/nginx/http.d/

CMD ["./run.sh"]
