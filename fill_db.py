

import os
import re
import sys
os.environ["DJANGO_SETTINGS_MODULE"] = "euppapi.settings"

from django.conf import settings

import logging
logger = logging.getLogger("euppDB")
logger.setLevel(settings.LOGLEVEL)

from scripts.indexparser import IndexParser

# --------------------------------------------------------------
# Helper function processing files
# --------------------------------------------------------------
def process_files(urls, DATADIR, verbose = True, nrows = None):
    parser = IndexParser()
    for url in urls:
        zipfile = prepare_zipfile(url, DATADIR, verbose = verbose)
        parser.process_file(zipfile, file_constant = True, verbose = verbose, nrows = nrows)


def prepare_zipfile(url, DATADIR, verbose = True):

    import os
    import requests
    import zipfile
    import tempfile

    local_index = os.path.join(DATADIR, os.path.basename(url))
    local_zip   = os.path.join(DATADIR, os.path.basename(url) + ".zip")
    if not os.path.isfile(local_zip):
        if verbose: print(f"Downloading {url}\nCreating {local_zip}")
        req = requests.get(url)
        if not req.status_code == 200:
            raise Exception("Got 404 for {url}")
        with open(local_index, "w") as fid: fid.write(req.text)

        # Create zip file
        zip = zipfile.ZipFile(local_zip, "w", zipfile.ZIP_DEFLATED)
        print(os.path.basename(local_index))
        print(local_index)
        #zip.write(local_index)
        zip.write(local_index, os.path.basename(local_index))
        zip.close()
        os.remove(local_index)

    return local_zip


## --------------------------------------------------------------
## --------------------------------------------------------------
#def read_zipfile(file):
#    import re
#    import zipfile
#
#    if not isinstance(file, str):      raise TypeError("Input must be string (zipfile).")
#    if not re.match(".*\.zip$", file): raise Exception("Must be zip file!")
#    if not os.path.isfile(file):       raise Exception(f"Problems reading {file}.")
#
#    zip = zipfile.ZipFile(file)  # Flexibility with regard to zipfile
#    content = []
#    for filename in zip.namelist():
#        if not os.path.isdir(filename):
#            # read the file
#            for line in zip.open(filename):
#                content.append(line)
#                print(line)
#            zip.close()                # Close the file after opening it
#    del zip
#    return content


# --------------------------------------------------------------
# Setting up analysis files/urls and process them
# --------------------------------------------------------------
def process_analysis(BASEURL, DATADIR, years, months, nrows = None):

    # Processing 'analysis'
    urls = []
    #for year in range(1997, 1998):
    for year in years:
        for month in months:
            urls.append(f"{BASEURL}/data/ana/pressure/EU_analysis_pressure_params_{year:04d}-{month:02d}.grb.index")
            urls.append(f"{BASEURL}/data/ana/surf/EU_analysis_surf_params_{year:04d}-{month:02d}.grb.index")

    print(urls)
    process_files(urls, DATADIR, nrows = nrows)


# --------------------------------------------------------------
# Forecasts
# --------------------------------------------------------------
def process_forecasts(BASEURL, DATADIR, years, months, version = 0, nrows = None):

    import datetime as dt

    urls = []
    for year in years:
        for month in months:
            ## Control run
            urls.append(f"{BASEURL}/data/fcs/pressure/EU_forecast_ctr_pressure_params_{year:04d}-{month:02d}_{version}.grb.index")
            urls.append(f"{BASEURL}/data/fcs/surf/EU_forecast_ctr_surf_params_{year:04d}-{month:02d}_{version}.grb.index")

            # EFI
            urls.append(f"{BASEURL}/data/fcs/efi/EU_forecast_efi_params_{year:04d}-{month:02d}_{version}.grb.index")

            # Ensemble members
            curr = dt.date(year, month, 1)
            end  = (dt.date(year, month + 1, 1) if month < 12 else dt.date(year + 1, 1, 1)) - dt.timedelta(1)
            while curr <= end:
                date = curr.strftime("%Y-%m-%d")
                # Enemble
                urls.append(f"{BASEURL}/data/fcs/pressure/EU_forecast_ens_pressure_params_{date}_{version}.grb.index")
                urls.append(f"{BASEURL}/data/fcs/surf/EU_forecast_ens_surf_params_{date}_{version}.grb.index")
                curr += dt.timedelta(1)

        process_files(urls, DATADIR, nrows = nrows)


# --------------------------------------------------------------
# Reforecasts
# --------------------------------------------------------------
def process_reforecasts(BASEURL, DATADIR, years, months, version = 0, nrows = None):

    import datetime as dt

    #https://storage.ecmwf.europeanweather.cloud/benchmark-dataset/data/rfcs/surf/EU_reforecast_ctr_surf_params_2018-01_0.grb.index
    #https://storage.ecmwf.europeanweather.cloud/benchmark-dataset/data/rfcs/pressure/EU_reforecast_ctr_pressure_params_2017-02_0.grb.index
    #https://storage.ecmwf.europeanweather.cloud/benchmark-dataset/data/rfcs/surf/EU_reforecast_ens_surf_params_2018-01-01_0.grb.index
    #https://storage.ecmwf.europeanweather.cloud/benchmark-dataset/data/rfcs/pressure/EU_reforecast_ens_pressure_params_2017-06-26_0.grb.index

    urls = []
    for year in years:
        for month in months:
            ## Control run
            urls.append(f"{BASEURL}/data/rfcs/surf/EU_reforecast_ctr_surf_params_{year:04d}-{month:02d}_{version}.grb.index")
            urls.append(f"{BASEURL}/data/rfcs/pressure/EU_reforecast_ctr_pressure_params_{year:04d}-{month:02d}_{version}.grb.index")

            # Ensemble members
            curr = dt.date(year, month, 1)
            end  = (dt.date(year, month + 1, 1) if month == 12 else dt.date(year + 1, 1, 1)) - dt.timedelta(1)
            while curr <= end:
                # Skip if not Monday (1) or Thursday (4)
                if not  curr.timetuple().tm_wday in [1, 4]: continue
                date = curr.strftime("%Y-%m-%d")
                # Enemble
                urls.append(f"{BASEURL}/data/rfcs/surf/EU_reforecast_ens_surf_params_{date}_{version}.grb.index")
                urls.append(f"{BASEURL}/data/rfcs/pressure/EU_reforecast_ens_pressure_params_{date}_{version}.grb.index")
                curr += dt.timedelta(1)

        process_files(urls, DATADIR, nrows = nrows)


# --------------------------------------------------------------
# Main part ...
# --------------------------------------------------------------
if __name__ == "__main__":


    BASEURL = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset"
    DATADIR = "_data"
    url = "https://storage.ecmwf.europeanweather.cloud/benchmark-dataset/data/ana/surf/EU_analysis_surf_params_1997-03.grb.index"


    #process_analysis(BASEURL,    DATADIR, range(1997, 2020), range(1, 3), nrows = 10)
    #process_forecasts(BASEURL,   DATADIR, range(2017, 2019), range(1, 3), nrows = 10)
    #process_reforecasts(BASEURL, DATADIR, range(2017, 2019), range(1, 3), nrows = 10)
    process_analysis(BASEURL,    DATADIR, [1997], [1], nrows = 10)
    process_forecasts(BASEURL,   DATADIR, [2017], [1], nrows = 10)
    process_reforecasts(BASEURL, DATADIR, [2017], [1], nrows = 10)
    #process_analysis(BASEURL,    DATADIR, [1997], [1]) #, nrows = 10)
    #process_forecasts(BASEURL,   DATADIR, [2017], [1]) #, nrows = 10)
    #process_reforecasts(BASEURL, DATADIR, [2017], [1]) #, nrows = 10)

