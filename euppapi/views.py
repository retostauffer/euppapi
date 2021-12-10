
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext
from django.shortcuts import HttpResponse

from django.views.defaults import page_not_found

import logging
logger = logging.getLogger("meteoapi.views")
logger.info(" inside {:s}.py".format(__name__))
logger.info("    STATIC_URL:       " + settings.STATIC_URL)
logger.info("    STATIC_ROOT:      " + settings.STATIC_ROOT)
logger.info("    STATICFILES_DIR:  " + settings.STATICFILES_DIRS[0])
logger.info("    BASE_DIR:         " + str(settings.BASE_DIR))


# Main page (index)
def home(request):

    ###context = {"page_title": "Meteo API"}
    context = {"page_title": None}
    return render(request, "home.html", context)

