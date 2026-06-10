=====================
monotremata-interface
=====================

A Django application 

.. contents:: Table of Contents
   :depth: 2
   :local:


Requirements
============

- Python ≥ 3.12
- Django ≥ 6.0


Quick Start
===========

.. code-block:: bash

   uv run monotremata setup -s run --database sqlite3

    # will run :
      # manage.py makemigrations
      # manage.py migrate
      # manage.py loaddata ...
      # manage.py runserver 0.0.0.0:${DJANGO_PORT}



Available keys for database engine:

=============== ==========================================
Key             Engine
=============== ==========================================
``spatialite``  ``django.contrib.gis.db.backends.spatialite``
``postgis``     ``django.contrib.gis.db.backends.postgis``
``postgres``    ``django.db.backends.postgresql``
``sqlite3``    ``django.db.backends.sqlite3``
=============== ==========================================

