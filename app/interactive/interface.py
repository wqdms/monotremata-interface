import requests
import jupyterlab
import ipywidgets
import rdflib
import matplotlib
import numpy
import geopandas
import pandera
import pandas 
from types import SimpleNamespace
# pandas Because pandas==3.0.2 depends on numpy{python_full_version >=
# '3.14'}>=2.3.3 and saqc==2.8.0 depends on numpy<=2.2.6, we can
# conclude that pandas==3.0.2 and saqc==2.8.0 are incompatible.
# import saqc 
from django import setup
from monotremata import models
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "interface.settings"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
setup()
class Packages:
    requests = requests
    jupyterlab = jupyterlab
    ipywidgets = ipywidgets
    rdflib = rdflib
    matplotlib = matplotlib
    numpy = numpy
    geopandas = geopandas
    pandera = pandera
    pandas = pandas
    # saqc = saqc


class ModelHandler:
    def __init__(self):
        pass
    def get_model(self,name):
        model = None
        if hasattr(models,name):
            model = getattr(models,name)
        return model
    
    def update_create(self,model_name,data:dict):
        model = self.get_model(model_name)
        if model:
            i,c = model.objects.update_or_create(**data)
            return i 

