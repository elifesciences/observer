FROM python:3.8
RUN mkdir /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip wheel && \
    pip install -r requirements.txt --no-cache-dir --no-color
COPY . .
RUN chmod +x manage.sh
CMD ["./manage.sh", "runserver", "0.0.0.0:8000"]
