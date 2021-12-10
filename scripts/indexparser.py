


import django
django.setup()
from django.conf import settings

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level = logging.DEBUG)
logger = logging.getLogger("euppDB")

import sys
import json
from datetime import datetime as dt

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
        import re
        from os import path

        # Getting datatype/kind
        mtch = re.match(r"^(EU_)(.*?)(?=(_params)).*\.grb\.index$", path.basename(file))
        if not mtch:
            raise Exception("Filename not in expected format")
        mtch = mtch.groups()[1].split("_")

        # Version
        vers = re.match(".*_([0-9]+)\.grb\.index$", path.basename(file))
        vers = int(vers.group(1)) if vers else None

        if len(mtch) == 4:
            res = dict(type = mtch[0], product = mtch[1], kind = mtch[2], version = vers)
        else:
            res = dict(type = mtch[0], product = mtch[1], kind = mtch[1], version = vers)
        return res


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
        import re
        from euppapi.models import DataType, File, Domain, Leveltype, Message

        if not isinstance(file, str):
            raise TypeError("Input 'file' must be string.")
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


        # Create datatype if not yet existing
        file_info = self._parse_filename_(file)
        if file_info["kind"] == "ctr": file_info["kind"] = "ens"
        tmp_dt = DataType.objects.update_or_create(baseurl = "foo",
                                                   type    = file_info["type"],
                                                   product = file_info["product"],
                                                   kind    = file_info["kind"])[0]

        # Helper function to get begin/end step
        def get_steps(x):
            if re.match("^[0-9]+$", x):
                return int(x),int(x)
            else:
                mtch = re.match("^([0-9]+)-([0-9]+)$", x)
                return int(mtch.group(1)), int(mtch.group(2))
            raise Exception("You should never end up down here!")


        # Reading the file (JSON)
        counter = 0
        res = []
        with open(file, "r") as fid:
            for rec in fid:
                # Development output ...
                counter += 1
                if (verbose): sys.stdout.write(f"    Preparing record {counter}\r")

                rec = json.loads(rec)
                #print(rec)


                # Updating Domain and Leveltype
                if counter == 1 or not file_constant:
                    # Updating files
                    tmp_f = File.objects.update_or_create(datatype = tmp_dt, path = rec["_path"],
                            version = file_info["version"])[0]
                    tmp_d = Domain.objects.update_or_create(domain = rec["domain"])[0]
                    tmp_l = Leveltype.objects.update_or_create(leveltype = rec["levtype"])[0]

                param   = rec["param"] if not "levelist" in rec else "".join([rec["param"], rec["levelist"]])
                date    = dt.strptime(rec["date"], "%Y%m%d").date()
                hdate   = None if not "hdate" in rec else dt.strptime(rec["hdate"], "%Y%m%d").date()
                number  = None if not "number" in rec else int(rec["number"])
                step_begin, step_end = get_steps(rec["step"])

                # Adding message
                res += [Message(datatype    = tmp_dt,
                                file        = tmp_f,
                                domain      = tmp_d,
                                leveltype   = tmp_l,
                                date        = date,
                                hdate       = hdate,
                                time        = int(rec["time"]),
                                step_begin  = step_begin,
                                step_end    = step_end,
                                number      = number,
                                param       = param,
                                param_id    = int(rec["_param_id"]),
                                bytes_begin = rec["_offset"],
                                bytes_end   = rec["_offset"] + rec["_length"])]

                # Break if nrows is set
                if nrows and counter > (nrows - 1): break


        if (verbose): sys.stdout.flush()
        print(f"    Inserting {counter} messages into database")
        Message.objects.bulk_create(res, batch_size = int(5e4), ignore_conflicts = True)

