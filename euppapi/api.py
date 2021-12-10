
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

    # Dictionary to be returned
    res = dict(note = "", error = False)

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


def get_messages_analysis(request, daterange):
    """test()

    GET parameters allowed are '?step', '?number', and '?param'.  Single values
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
    ot = DataType.objects.filter(type__exact = "analysis")[0]

    # Initializing resulting dictionary
    res = _get_message_parse_args_(request, daterange, analysis = True)
    if res["hour"]: res["hour"] = [100 * x for x in res["hour"]]
    res.update(dict(type = "analysis",
                    baseurl = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset"),
                    nmsg = 0, messages = [])

    # -------------------------------------------
    # No problem found? Fetching data
    # -------------------------------------------
    if not res["error"]:
        msgs = ot.message_set.filter(date__date__range        = res["daterange"])
        if res["hour"]:   msgs = msgs.filter(time__in         = res["hour"])
        if res["param"]:  msgs = msgs.filter(param__param__in = res["param"])
        if res["number"]: msgs = msgs.filter(number__in       = res["number"])
        # Adding count
        res["nmsg"] += msgs.all().count()
        # Adding data
        for rec in msgs.all():
            res["messages"].append(dict(datadate     = rec.date.date.strftime(datefmt),
                                        datatime     = rec.time,
                                        path         = rec.file.path,
                                        byterange    = f"{rec.bytes_begin}-{rec.bytes_end}",
                                        param        = rec.param.param))
                                        ##leveltype    = rec.leveltype.leveltype))

    # Prepare return
    return HttpResponse(json.dumps(res), content_type = "application/json") if request else res

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
    objType = DataType.objects.filter(type__exact = type, product__exact = product)


    # Initializing resulting dictionary
    res = _get_message_parse_args_(request, daterange, analysis = False)
    res.update(dict(type = type, product = product,
                    baseurl = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset"),
                    nmsg = 0, messages = [])

    # -------------------------------------------
    # No problem found? Fetching data
    # -------------------------------------------
    if not res["error"]:
        for ot in objType:
            msgs = ot.message_set.filter(date__range          = res["daterange"])
            if res["step"]:   msgs = msgs.filter(step_end__in = res["step"])
            if res["param"]:  msgs = msgs.filter(param__in    = res["param"])
            if res["number"]: msgs = msgs.filter(number__in   = res["number"])
            # Adding count
            res["nmsg"] += msgs.all().count()
            # Adding data
            for rec in msgs.all():
                res["messages"].append(dict(datadate     = rec.date.strftime(datefmt),
                                            datatime     = rec.time,
                                            hindcastdate = None if not rec.hdate else rec.hdate.strftime(datefmt),
                                            path         = rec.file.path,
                                            byterange    = f"{rec.bytes_begin}-{rec.bytes_end}",
                                            param        = rec.param,
                                            step         = rec.step_end,
                                            number       = rec.number))
                                            ##leveltype    = rec.leveltype.leveltype))

    # Prepare return
    return HttpResponse(json.dumps(res), content_type = "application/json") if request else res
