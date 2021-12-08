

import os
import re
import sys
os.environ["DJANGO_SETTINGS_MODULE"] = "euppapi.settings"

from django.conf import settings

import logging
logger = logging.getLogger("euppDB")
logger.setLevel(settings.LOGLEVEL)

from scripts.indexparser import IndexParser

from euppapi.models import DataType

if __name__ == "__main__":

    parser = IndexParser()

    files = parser.get_files("_data")
    print(files)
    #tmp = []
    #for file in files:
    #    if re.match(".*[0-9]{4}-[0-9]{2}-[0-9]{2}.*", file):
    #        tmp.append(file)
    #files = tmp
    #parser.process_file("_data/EU_reforecast_ens_pressure_params_2017-01-02_0.grb.index")
    #parser.process_file("_data/EU_forecast_efi_params_2017-01_0.grb.index")
    #parser.process_file("_data/EU_reforecast_ens_pressure_params_2017-01-02_0.grb.index")

    for file in files:
        parser.process_file(file, domain_levtype_constant = True, nrows = 1000, verbose = True)

    # Check how many stations we have in the database
    #stations = Station.objects.count()
    #logger.info("In total {:d} stations in database.".format(stations))

    #obj.load_opendata_files()
    #obj.load_opendata_files(n = 20)

