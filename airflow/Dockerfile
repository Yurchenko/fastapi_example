FROM python:3.9

ENV PYTHONUNBUFFERED 1

COPY Pipfile /tmp
COPY Pipfile.lock /tmp
WORKDIR tmp
RUN pip install pipenv
RUN pipenv requirements > requirements.txt
RUN pip install -r requirements.txt
COPY app /tmp
EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

# If running behind a proxy like Nginx or Traefik add --proxy-headers
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]