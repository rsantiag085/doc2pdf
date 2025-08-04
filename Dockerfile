FROM linuxserver/libreoffice:25.2.5
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask \
    && mkdir -p /tmp/uploads \
    && chmod 777 /tmp/uploads
EXPOSE 80
CMD ["python", "app.py"]