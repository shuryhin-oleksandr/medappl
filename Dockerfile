FROM python:3.8

ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./start.sh /start-django
# RUN sed -i 's/\r$//g' /start-django
RUN chmod +x /start-django

COPY ./ /app
WORKDIR app

EXPOSE 8000
