


import django
django.setup()
from django.conf import settings

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level = logging.DEBUG)
logger = logging.getLogger("euppDB")

import re
import sys
import json
import datetime as dt

class IndexParser:

    def get_files(self, dir):
        """get_files(dir)

        Parameters
        ==========
        dir : str
            Name of the directory where you have your grib index files stored.

        Returns
        =======
        List of file names.
        """
        from os import path
        if not isinstance(dir, str):
            raise TypeError("Input 'dir' must be string.")
        if not path.exists(dir):
            raise Exception(f"Directory {dir} does not exist.")

        from glob import glob
        return glob(path.join(dir, "EU_*.index"))


    def _parse_filename_(self, file):
        """_parse_filename_(file)

        For internal use, parses the file naems to extract
        some information. Files must follow as pecific file
        name convention; else will fail.

        Parameters
        ==========
        file : str
            Path to the GRIB index file to be processed.

        Returns
        =======
        Dictionary with datatype, product, and kind.
        """
        from os import path

        # Getting datatype/kind
        mtch = re.match(r"^(EU_)(.*?)(?=(_params)).*\.grb\.index\.zip$", path.basename(file))
        if not mtch:
            raise Exception("Filename '{path.basename(file)}' not in expected format")
        mtch = mtch.groups()[1].split("_")

        # Version
        vers = re.match(".*_([0-9]+)\.grb\.index$", path.basename(file))
        vers = int(vers.group(1)) if vers else None

        if len(mtch) == 4:
            res = dict(type = mtch[0], product = mtch[1], kind = mtch[2], version = vers)
        else:
            res = dict(type = mtch[0], product = mtch[1], kind = mtch[1], version = vers)

        # Force re-write 'ctr' to 'ens'
        for n in ["product", "kind"]:
            if res[n] == "ctr": res[n] = "ens"

        return res

    # Helper function to get begin/end step
    def _get_steps_(self, x):
        if re.match("^[0-9]+$", x):
            return int(x),int(x)
        else:
            mtch = re.match("^([0-9]+)-([0-9]+)$", x)
            return int(mtch.group(1)), int(mtch.group(2))
        raise Exception("You should never end up down here!")



    def process_file(self, file, file_constant = False, nrows = None, verbose = False):
        """process_file(file)

        Parameters
        ==========
        file : str
            Path to the GRIB index file to be processed.
        file_constant : bool
            Defaults to False, if True '_path', 'domain' and 'levtype' are only picked
            from the first message we find. Else from each one (takes about twice as long).
        nrows : None or positive int
             Number of rows (messages) to process from current file. This
             mode is only for development purposes!
        verbose : bool
             Switch verbose mode on/off.
        """

        import os
        import requests
        from tempfile import NamedTemporaryFile
        from euppapi.models import GriddedDataTypes, Files, Domains, Leveltypes, Dates, Parameters
        from euppapi.models import GriddedAnalysisMessages
        from euppapi.models import GriddedForecastMessages
        from euppapi.models import GriddedReforecastMessages

        if not isinstance(file, str):
            raise TypeError("Input 'file' must be string.")

        if not re.match(".*\.zip$", file):
            raise Exception(f"File '{file}' is not a zip file.")
        if not os.path.isfile(file):
            raise Exception(f"File '{file}' does not exist.")
        if not isinstance(file_constant, bool):
            raise TypeError("Input 'file' must be boolean True or False.")
        if not isinstance(nrows, int) and not nrows is None:
            raise TypeError("Input 'nrows' must be None or integer.")
        if isinstance(nrows, int):
            if nrows <= 0:
                raise ValueError("If 'nrows' is integer, it must be positive.")
        if not isinstance(verbose, bool):
            raise TypeError("Input 'verbose' must be boolean.")


        if (verbose): print(f"Processing file: {file}")

        # Open zip file; get file names, and process them one by one (typically
        # there is only one in there!!)
        import zipfile
        zip = zipfile.ZipFile(file)

        # Processing files ...
        for filename in zip.namelist():
            if not os.path.isdir(filename):

                dummy_date = dt.date(1900, 1, 1)
                counter = 0
                res = []

                # Create datatype if not yet existing
                file_info = self._parse_filename_(file)
                tmp_dt = GriddedDataTypes.objects.get_or_create(type    = file_info["type"],
                                                        product = file_info["product"],
                                                        kind    = file_info["kind"])[0]

                # Looping over the content of the file inside the zip:
                for rec in zip.open(filename):

                    # Development output ...
                    counter += 1
                    if (verbose): sys.stdout.write(f"    Preparing record {counter}\r")

                    rec = json.loads(rec)
                    #print(rec)


                    # Updating Domain and Leveltype
                    if counter == 1 or not file_constant:
                        # Updating files
                        tmp_f = Files.objects.get_or_create(datatype = tmp_dt, path = rec["_path"],
                                                           version = file_info["version"])
                        tmp_d = Domains.objects.get_or_create(domain = rec["domain"])
                        tmp_l = Leveltypes.objects.get_or_create(leveltype = rec["levtype"])

                    # Parameter object (django model)
                    param   = rec["param"] if not "levelist" in rec else "".join([rec["param"], rec["levelist"]])
                    tmp_param   = Parameters.objects.get_or_create(name = param,
                                                                  ecmwfid = rec["_param_id"],
                                                                  domain      = tmp_d[0],
                                                                  leveltype   = tmp_l[0])

                    # Date objects (django model)
                    date      = dt.datetime.strptime(rec["date"], "%Y%m%d").date()
                    tmp_date  = Dates.objects.get_or_create(date = date)


                    # Setting control run member to member 0
                    if re.match("^(ens|efi)$", tmp_dt.product) and not "number" in rec: rec["number"] = 0

                    if tmp_dt.type == "forecast":
                        step_begin, step_end = self._get_steps_(rec["step"])
                        msg = GriddedForecastMessages(
                                        datatype    = tmp_dt,
                                        file        = tmp_f[0],
                                        date        = tmp_date[0],
                                        step        = step_end,
                                        number      = rec["number"],
                                        param       = tmp_param[0],
                                        bytes_begin = rec["_offset"],
                                        bytes_end   = rec["_offset"] + rec["_length"])
                    elif tmp_dt.type == "reforecast":
                        # Hindcast date; specifically for reforecasts
                        hdate     = dummy_date if not "hdate" in rec else dt.datetime.strptime(rec["hdate"], "%Y%m%d").date()
                        tmp_hdate = Dates.objects.get_or_create(date = hdate)
                        step_begin, step_end = self._get_steps_(rec["step"])
                        msg = GriddedReforecastMessages(
                                        datatype    = tmp_dt,
                                        file        = tmp_f[0],
                                        date        = tmp_date[0],
                                        hdate       = tmp_hdate[0],
                                        step        = step_end,
                                        number      = rec["number"],
                                        param       = tmp_param[0],
                                        bytes_begin = rec["_offset"],
                                        bytes_end   = rec["_offset"] + rec["_length"])
                    elif tmp_dt.type == "analysis":
                        msg = GriddedAnalysisMessages(
                                        datatype    = tmp_dt,
                                        file        = tmp_f[0],
                                        date        = tmp_date[0],
                                        hour        = int(rec["time"]) / 100,
                                        param       = tmp_param[0],
                                        bytes_begin = rec["_offset"],
                                        bytes_end   = rec["_offset"] + rec["_length"])
                    else:
                        raise Exception(f"Unexpted type {tmp_dt.type}")

                    # Adding message
                    res += [msg]

                    # Break if nrows is set
                    if nrows and counter > (nrows - 1): break


                if verbose: sys.stdout.flush()

            # That is, indeed, not nice ... whatever.
            #####if verbose: print(f"  Adding {len(res)} to database.")
            if tmp_dt.type == "forecast":
                bulkobj = GriddedForecastMessages.objects
            elif tmp_dt.type == "reforecast":
                bulkobj = GriddedReforecastMessages.objects
            else:
                bulkobj = GriddedAnalysisMessages.objects
            # Ignore conflicts: if insert is impossible (wrong) or the key
            # exists we skip this (INSERT OR IGNORE).
            bulkobj.bulk_create(res, batch_size = int(5e4), ignore_conflicts = True)
            #bulkobj.bulk_create(res, batch_size = int(5e4), ignore_conflicts = False)
            # -----------------------------------------


        zip.close()                # Close the file after opening it
        del zip



