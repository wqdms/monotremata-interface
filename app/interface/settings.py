from monotremata.defaults import *

DATABASES = {"default": DATABASES[getenv("DATABASE_ENGINE", "sqlite3")]}
DEBUG = True
if DATABASE_ENGINE not in ["sqlite3"]:
    INSTALLED_APPS.append("rest_framework_gis")
    INSTALLED_APPS.append("ontology")
GIT_URL = getenv("GIT_URL", "http://forgejo.forgejo.svc.cluster.local")