
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext
from django.shortcuts import HttpResponse

import logging
logger = logging.getLogger("euppapi.api")
logger.info(" inside {:s}.py".format(__name__))


from .models import *

def get_messages(request, type, product, daterange, steprange):
    """test()

    Desc

    Parameters
    ==========
    request : django request
    type : str
        E.g., forecast, reforecast
    product : str
        E.g., ens, hr
    daterange : str
        Format must be '2017-01-01' or '2017-01-01:2017-01-31'.
    steprange : str
        Forecast step (forecast horizon) step range.
        Format must be '12' or '12-48'.

    Return
    ======
    Description of return
    """

    import re
    import json
    from django.db.models import Q

    context = {"page_title": "EUPP API"}
    note = ""

    # When requesting ens: fetch ens + ctr
    if product == "ens":
        objType = DataType.objects.filter(product__range = ["ctr", "ens"])
        #objType = DataType.objects.filter(Q(product__exact = "ctr") | Q(product__exact = "ens"))
    else:
        objType = DataType.objects.filter(product__exact = product)
    objType = objType.filter(type__exact = type)

    # Processing daterange and steprange
    mtch = re.match(r"([0-9]{4}-[0-9]{2}-[0-9]{2})(/[0-9]{4}-[0-9]{2}-[0-9]{2})?", daterange)
    if mtch.group(2) is None:
        daterange = mtch.group(1)
    else:
        daterange = [x.replace("/", "")  for x in mtch.groups()]
    mtch = re.match(r"([0-9]+)(/[0-9]+)?", steprange)
    if mtch.group(2) is None:
        steprange = mtch.group(1)
    else:
        steprange = [x.replace("/", "")  for x in mtch.groups()]


    ## Get format, if not set: default to 'json'
    #if request:
    #    output_format = request.GET.get("format")
    #    if not output_format or not output_format in ["xml", "json"]:
    #        output_format = "xml"

    #    phrase = request.GET.get("searchPhrase")

    content_type = "application/json"
    encoding = "utf-8" #latin1"
    datefmt  = "%Y-%m-%d %H:%M"

    # Initializing resulting dictionary
    res = dict(nmsg = 0, type = type, product = product,
               note = note,
               baseurl = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset",
               daterange = daterange, steprange = steprange)

    messages = []
    for ot in objType:
        msgs = ot.message_set.filter(date__range     = daterange,
                                     step_end__range = steprange)
        # Adding count
        res["nmsg"] += msgs.all().count()
        # Adding data
        for rec in msgs.all():
            messages.append(dict(datadate = rec.date.strftime(datefmt),
                                 datatime = rec.time,
                                 hindcastdate = None if not rec.hdate else rec.hdate.strftime(datefmt),
                                 _path     = rec.file.path,
                                 byterange = f"{rec.bytes_begin}:{rec.bytes_end}",
                                 param = rec.param,
                                 leveltype = rec.leveltype.leveltype))
    res["messages"] = messages
    return HttpResponse(json.dumps(res), content_type = "application/json") if request else res
