"""euppapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.urls import re_path, path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
#from django.conf.urls import url
from django.conf.urls import handler404, handler500

from . import views
from . import api

import logging
logger = logging.getLogger("euppapi.urls")

urlpatterns = [
    path("",                      views.home, name = "home"),
    re_path(r"^api/analysis/(?P<daterange>[0-9]{4}-[0-9]{2}-[0-9]{2}(/[0-9]{4}-[0-9]{2}-[0-9]{2})?)/?$", api.get_messages_analysis, name = "API Analysis"),
    re_path(r"^api/forecast/(?P<product>\w+)/(?P<daterange>[0-9]{4}-[0-9]{2}-[0-9]{2}(/[0-9]{4}-[0-9]{2}-[0-9]{2})?)/?$", api.get_messages_forecast, name = "API Forecast"),
    re_path(r"^api/reforecast/(?P<product>\w+)/(?P<daterange>[0-9]{4}-[0-9]{2}-[0-9]{2}(/[0-9]{4}-[0-9]{2}-[0-9]{2})?)/?$", api.get_messages_forecast, name = "API Reforecast"),
    #####re_path(r"^api/(?P<type>\w+)/(?P<product>\w+)/(?P<daterange>[0-9]{4}-[0-9]{2}-[0-9]{2}(/[0-9]{4}-[0-9]{2}-[0-9]{2})?)/(?P<steprange>[0-9]+(/[0-9]+)?)/?$", api.get_messages, name = "API"),
    #path("map",                   views.map),
    #path("overview",              views.overview),
    #path("documentation",         views.documentation),
    #path("station/<int:request_ID>", views.station_details),
    #path("admin/", admin.site.urls),
    #path("test",   api.test),
] + static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)


