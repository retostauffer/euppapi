
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext
from django.shortcuts import HttpResponse

import logging
logger = logging.getLogger("euppapi.api")
logger.info(" inside {:s}.py".format(__name__))


from .models import *

def get_messages(request, type, product, daterange):
    """test()

    GET parameters allowed are '?step', '?number', and '?param'.  Single values
    or colon separated lists.  E.g., 'step=0:6:12' will return forecast steps
    '0', '6', and '12' only. 'param=2t:cp' will subset '2t' and 'cp' only.
    'number' works like 'step'. If not set, all steps/parameters will be
    returned.  In case the format is wrong a JSON array is returned containing
    logical True on 'error'.

    Parameters
    ==========
    request : django request
    type : str
        E.g., forecast, reforecast
    product : str
        E.g., ens, hr
    daterange : str
        Format must be '2017-01-01' or '2017-01-01:2017-01-31'.

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
        daterange = [mtch.group(1)] * 2
    else:
        daterange = [x.replace("/", "")  for x in mtch.groups()]

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
    res = dict(error = False,
               nmsg = 0, type = type, product = product,
               note = note,
               baseurl = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset",
               daterange = daterange)

    # Fetching request arguments. Will set request_problem to True
    # if we encounter any problems. This will change the note and
    # prevent django from trying to load data from the database.
    if request:

        # Steps
        req_steps = request.GET.get("step")
        if req_steps is None:
            res["step"] = None # None? -> all
        elif not re.match("^[0-9:]+$", req_steps):
            res["note"] += "argument ?step wrong format"
            res["error"] = True
        else:
            res["step"] = [int(x) for x in re.findall("[0-9]+", req_steps)]

        # Params
        req_param = request.GET.get("param")
        if req_param is None:
            res["param"] = None # None? -> all
        elif not re.match("^[\w:]+$", req_param):
            res["note"] += "argument ?param wrong format"
            res["error"] = True
        else:
            res["param"] = re.findall("[\w]+", req_param)

        # Number
        req_number = request.GET.get("number")
        if req_number is None:
            res["number"] = None # None? -> all
        elif not re.match("^[0-9:]+$", req_number):
            res["note"] += "argument ?number wrong format"
            res["error"] = True
        else:
            res["number"] = [int(x) for x in re.findall("[0-9]+", req_numbers)]


    # -------------------------------------------
    # No problem found? Fetching data
    # -------------------------------------------
    if not res["error"]:
        messages = []
        for ot in objType:
            msgs = ot.message_set.filter(date__range     = daterange)
            if res["step"]:   msgs = msgs.filter(step_end__in = res["step"])
            if res["param"]:  msgs = msgs.filter(param__in = res["param"])
            if res["number"]: msgs = msgs.filter(number__in = res["number"])
            # Adding count
            res["nmsg"] += msgs.all().count()
            # Adding data
            for rec in msgs.all():
                messages.append(dict(datadate     = rec.date.strftime(datefmt),
                                     datatime     = rec.time,
                                     hindcastdate = None if not rec.hdate else rec.hdate.strftime(datefmt),
                                     path         = rec.file.path,
                                     byterange    = f"{rec.bytes_begin}:{rec.bytes_end}",
                                     param        = rec.param,
                                     step         = rec.step_end,
                                     number       = rec.number,
                                     leveltype    = rec.leveltype.leveltype))
        # Appending messages 
        res["messages"] = messages

    # Prepare return
    return HttpResponse(json.dumps(res), content_type = "application/json") if request else res
