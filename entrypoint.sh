#!/bin/sh

exec gunicorn \
  ${GUNICORN_OPTS} \
  -w ${GUNICORN_WORKERS:-4} \
  -b ${GUNICORN_BIND:-0.0.0.0:5000} \
  ${GUNICORN_APP:-wsgi:app}