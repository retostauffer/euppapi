

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

    ###files = parser.get_files("_data")
    #tmp = []
    #for file in files:
    #    if re.match(".*[0-9]{4}-[0-9]{2}-[0-9]{2}.*", file):
    #        tmp.append(file)
    #files = tmp
    #parser.process_file("_data/EU_reforecast_ens_pressure_params_2017-01-02_0.grb.index")
    #parser.process_file("_data/EU_forecast_efi_params_2017-01_0.grb.index")
    #parser.process_file("_data/EU_reforecast_ens_pressure_params_2017-01-02_0.grb.index")

    BASEURL = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset"
    DATADIR = "_data"

    # Processing 'analysis'
    files = []
    for year in range(1997, 2020):
        for month in range(1, 13):
            u1 = f"{BASEURL}/data/ana/pressure/EU_analysis_pressure_params_{year:04d}-{month:02d}.grb.index"
            d1 = os.path.join(DATADIR, os.path.basename(u1))
            files.append(d1 if os.path.isfile(d1) else u1)

            u2 = f"{BASEURL}/data/ana/surf/EU_analysis_surf_params_{year:04d}-{month:02d}.grb.index"
            d2 = os.path.join(DATADIR, os.path.basename(u2))
            files.append(d2 if os.path.isfile(d2) else u2)

    for file in files:
        #parser.process_file(file, file_constant = True, nrows = 1000, verbose = True)
        parser.process_file(file, file_constant = True, verbose = True)

    # Check how many stations we have in the database
    #stations = Station.objects.count()
    #logger.info("In total {:d} stations in database.".format(stations))

    #obj.load_opendata_files()
    #obj.load_opendata_files(n = 20)

