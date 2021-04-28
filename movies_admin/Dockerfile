FROM python:3
ENV PYTHONUNBUFFERED=1

COPY . /movies_admin
RUN pip install -r /movies_admin/requirements/dev.txt

WORKDIR /movies_admin
