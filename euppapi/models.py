
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

import logging
logger = logging.getLogger("{:s}.models".format(settings.APP_NAME))
logger.setLevel(settings.LOGLEVEL)

class AutoDateTimeField(models.DateTimeField):
    def pre_save(self, model_instance, add):
        return timezone.now()

# -------------------------------------------------------------------
# -------------------------------------------------------------------

# Referencing main data types
class GriddedDataTypes(models.Model):

    type      = models.CharField(max_length = 20)  # forecast, reforecast, analysis
    product   = models.CharField(max_length = 10)   # ens, ana, hr
    kind      = models.CharField(max_length = 10)  # surface, pressure

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["type", "product", "kind"], name = "unique_datatype")
        ]

# Referencing files
class Files(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    datatype = models.ForeignKey(GriddedDataTypes, on_delete = models.CASCADE)
    path     = models.CharField(max_length = 200)
    version  = models.PositiveSmallIntegerField(null = True)

# Init date/date
class Dates(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    date = models.DateField(max_length = 3, unique = True)

# Referencing Domain
class Domains(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    domain     = models.CharField(max_length = 3, unique = True)

# Referencing level type
class Leveltypes(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    leveltype  = models.CharField(max_length = 3, unique = True)

# Name of parameter
class Parameters(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    name       = models.CharField(max_length = 8)
    ecmwfid    = models.PositiveIntegerField()
    domain     = models.ForeignKey(Domains,    on_delete = models.PROTECT)
    leveltype  = models.ForeignKey(Leveltypes, on_delete = models.PROTECT)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["name", "ecmwfid"], name = "unique_parameter")
        ]


# Gridded Analysis message
class GriddedAnalysisMessages(models.Model):
    file       = models.ForeignKey(Files, on_delete = models.CASCADE)

    # Time information
    date       = models.ForeignKey(Dates, on_delete = models.PROTECT)
    hour       = models.PositiveSmallIntegerField()

    # Parameter information
    param      = models.ForeignKey(Parameters, on_delete = models.PROTECT)

    # Bytes range within grib file
    bytes_begin = models.PositiveIntegerField() #models.PositiveBigIntegerField()
    bytes_end   = models.PositiveIntegerField() #models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["date", "hour", "param"], name = "unique_gridded_analysis_message")
        ]

# Grib message
class GriddedForecastMessages(models.Model):
    file       = models.ForeignKey(Files, on_delete = models.CASCADE)

    # Time information
    date       = models.ForeignKey(Dates, on_delete = models.PROTECT)
    step       = models.PositiveSmallIntegerField()
    number     = models.SmallIntegerField(validators = [MinValueValidator(-1), MaxValueValidator(50)])

    # Parameter information
    param      = models.ForeignKey(Parameters, on_delete = models.PROTECT)

    # Bytes range within grib file
    bytes_begin = models.PositiveIntegerField() #models.PositiveBigIntegerField()
    bytes_end   = models.PositiveIntegerField() #models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["date", "step", "number", "param"], name = "unique_gridded_forecast_message")
        ]

# Grib message
class GriddedReforecastMessages(models.Model):
    file       = models.ForeignKey(Files, on_delete = models.CASCADE)

    # Time information
    date       = models.ForeignKey(Dates, on_delete = models.PROTECT, related_name = "init_date")
    hdate      = models.ForeignKey(Dates, on_delete = models.PROTECT, related_name = "hindcast_date")
    step       = models.PositiveSmallIntegerField()
    number     = models.SmallIntegerField(validators = [MinValueValidator(-1), MaxValueValidator(50)])

    # Parameter information
    param      = models.ForeignKey(Parameters, on_delete = models.PROTECT)

    # Bytes range within grib file
    bytes_begin = models.PositiveIntegerField() #models.PositiveBigIntegerField()
    bytes_end   = models.PositiveIntegerField() #models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["date", "hdate", "step", "number", "param"], name = "unique_gridded_reforecast_message")
        ]

## Grib message
#class Message(models.Model):
#    datatype   = models.ForeignKey(DataType,  on_delete = models.CASCADE)
#    file       = models.ForeignKey(File,      on_delete = models.CASCADE)
#
#    # Time information
#    date       = models.ForeignKey(Date, on_delete = models.PROTECT, related_name = "init_date")
#    hdate      = models.ForeignKey(Date, on_delete = models.PROTECT, related_name = "hindcast_date")
#    step       = models.PositiveSmallIntegerField()
#    number     = models.SmallIntegerField(validators = [MinValueValidator(-1), MaxValueValidator(50)])
#
#    # Parameter information
#    param      = models.ForeignKey(Parameter, on_delete = models.PROTECT)
#
#    # Bytes range within grib file
#    bytes_begin = models.PositiveIntegerField() #models.PositiveBigIntegerField()
#    bytes_end   = models.PositiveIntegerField() #models.PositiveBigIntegerField()
#
#    class Meta:
#        constraints = [
#            models.UniqueConstraint(fields = ["date", "hdate", "step", "number", "param"], name = "unique_message")
#        ]
