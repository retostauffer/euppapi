
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext
from django.shortcuts import HttpResponse

import logging
logger = logging.getLogger("euppapi.api")
logger.info(" inside {:s}.py".format(__name__))

#def test(request):
#    """test()
#
#    Desc
#
#    Parameters
#    ==========
#    param : foo
#        desc
#
#    Return
#    ======
#    Description of return
#    """
#
#    import re
#    context = {"page_title": gettext("Station Overview")}
#
#    return HttpResponse(res, content_type = content_type) if request else res
