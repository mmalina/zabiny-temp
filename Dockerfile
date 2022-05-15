ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY . /zabiny-temp
WORKDIR /zabiny-temp

# Install requirements for add-on
RUN apk add --no-cache nginx python3 py3-numpy py3-pillow py3-pip && \
    pip3 install requests imageio pytz

COPY data/default.conf /etc/nginx/conf.d/

CMD ["./run.sh"]
