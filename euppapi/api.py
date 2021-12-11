
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext
from django.shortcuts import HttpResponse

import logging
logger = logging.getLogger("euppapi.api")
logger.info(" inside {:s}.py".format(__name__))


from .models import *

def _get_message_parse_args_(request, daterange, analysis = False):

    import re
    from datetime import datetime as dt

    # Dictionary to be returned
    note = "EUPP API request issued {:s}".format(dt.now().strftime("%Y-%m-%d %H:%M:%S"))
    res = dict(note = note, error = False)

    # Steps or hour (for analysis)
    what = "hour" if analysis else "step"
    req_steps = request.GET.get(what)
    if req_steps is None:
        res[what] = None # None? -> all
    elif not re.match("^[0-9:]+$", req_steps):
        res["note"] += "argument ?step wrong format"
        res["error"] = True
    else:
        res[what] = [int(x) for x in re.findall("[0-9]+", req_steps)]

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

    # Processing daterange and steprange
    mtch = re.match(r"([0-9]{4}-[0-9]{2}-[0-9]{2})(/[0-9]{4}-[0-9]{2}-[0-9]{2})?", daterange)
    if mtch.group(2) is None:
        res["daterange"] = [mtch.group(1)] * 2
    else:
        res["daterange"] = [x.replace("/", "")  for x in mtch.groups()]

    return res


# -----------------------------------------------------------
# -----------------------------------------------------------
# -----------------------------------------------------------
# -----------------------------------------------------------
def get_messages_analysis(request, daterange):
    """get_messages_analysis()

    GET parameters allowed are '?hour', '?number', and '?param'.  Single values
    or colon separated lists.  E.g., 'hour=0:6:12' will return analysis for hour
    '0', '6', and '12' only. 'param=2t:cp' will subset '2t' and 'cp' only.
    'number' works like 'step'. If not set, all steps/parameters will be
    returned.  In case the format is wrong a JSON array is returned containing
    logical True on 'error'.

    Parameters
    ==========
    request : django request
    daterange : str
        Format must be '2017-01-01' or '2017-01-01:2017-01-31'.

    Return
    ======
    JSON string.
    """

    import re
    import json
    from django.db.models import Q

    datefmt  = "%Y-%m-%d %H:%M"

    # When requesting ens: fetch ens + ctr
    ot = GriddedDataTypes.objects.filter(type__exact = "analysis")[0]

    # Initializing resulting dictionary
    res = _get_message_parse_args_(request, daterange, analysis = True)
    res.update(dict(type = "analysis",
                    baseurl = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset"),
                    nmsg = 0, messages = [])

    # -------------------------------------------
    # No problem found? Fetching data
    # -------------------------------------------
    if not res["error"]:
        msgs = ot.griddedanalysismessages_set.filter(date__date__range = res["daterange"]).order_by("date__date", "hour")
        if res["hour"]:   msgs = msgs.filter(hour__in         = res["hour"])
        if res["param"]:  msgs = msgs.filter(param__param__in = res["param"])
        if res["number"]: msgs = msgs.filter(number__in       = res["number"])
        # Adding count
        res["nmsg"] += msgs.all().count()
        # Adding data
        for rec in msgs.all():
            res["messages"].append(dict(datadate     = rec.date.date.strftime(datefmt),
                                        datatime     = rec.hour,
                                        path         = rec.file.path,
                                        byterange    = f"{rec.bytes_begin}-{rec.bytes_end}",
                                        param        = rec.param.name))
                                        ##leveltype    = rec.leveltype.leveltype))

    # Prepare return
    return HttpResponse(json.dumps(res), content_type = "application/json") if request else res


# -----------------------------------------------------------
# -----------------------------------------------------------
# -----------------------------------------------------------
# -----------------------------------------------------------
def get_messages_forecast(request, product, daterange):
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
    product : None (analysis) or str
        E.g., ens, hr
    daterange : str
        Format must be '2017-01-01' or '2017-01-01:2017-01-31'.

    Return
    ======
    JSON string.
    """

    import re
    import json
    from django.db.models import Q

    datefmt  = "%Y-%m-%d %H:%M"

    # When requesting ens: fetch ens + ctr
    objType = GriddedDataTypes.objects.filter(type__exact = "forecast", product__exact = product)

    # Initializing resulting dictionary
    res = _get_message_parse_args_(request, daterange, analysis = False)
    res.update(dict(type = "forecast", product = product,
                    baseurl = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset"),
                    nmsg = 0, messages = [])

    # -------------------------------------------
    # No problem found?
    # -------------------------------------------
    # Counting data first ....
    if not res["error"]:
        for ot in objType:
            msgs = ot.griddedforecastmessages_set.filter(date__date__range = res["daterange"]).order_by("date__date", "step")
            if res["step"]:   msgs = msgs.filter(step__in        = res["step"])
            if res["param"]:  msgs = msgs.filter(param__name__in = res["param"])
            if res["number"]: msgs = msgs.filter(number__in      = res["number"])
            # Adding count
            res["nmsg"] += msgs.all().count()

        msglimit = 5000
        if res["nmsg"] > msglimit:
            res["error"] = True
            res["note"] += "; ERORR: request would result in {:d} messages ({:d} is the limit)".format(res["nmsg"], msglimit)


    # Fetching data
    if not res["error"]:
        for ot in objType:
            msgs = ot.griddedforecastmessages_set.filter(date__date__range = res["daterange"]).order_by("date__date", "step")
            if res["step"]:   msgs = msgs.filter(step__in        = res["step"])
            if res["param"]:  msgs = msgs.filter(param__name__in = res["param"])
            if res["number"]: msgs = msgs.filter(number__in      = res["number"])
            # Adding data
            for rec in msgs.all():
                res["messages"].append(dict(datadate     = rec.date.date.strftime(datefmt),
                                            #hindcastdate = None if not rec.hdate else rec.hdate.strftime(datefmt),
                                            path         = rec.file.path,
                                            byterange    = f"{rec.bytes_begin}-{rec.bytes_end}",
                                            param        = rec.param.name,
                                            step         = rec.step,
                                            number       = rec.number))
                                            ##leveltype    = rec.leveltype.leveltype))

    # Prepare return
    return HttpResponse(json.dumps(res), content_type = "application/json") if request else res
