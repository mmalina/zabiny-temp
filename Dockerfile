ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY . /zabiny-temp
WORKDIR /zabiny-temp

# Install requirements for add-on
RUN apk add --no-cache python3 py3-numpy py3-pillow py3-gunicorn py3-wheel \
    py3-pip gcc libc-dev make python3-dev && \
    pip3 install "uvicorn[standard]" starlette requests imageio pytz

CMD ["uvicorn", "main:app", "-b 0.0.0.0:8000"]
