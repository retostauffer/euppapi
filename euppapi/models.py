
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
class DataType(models.Model):

    baseurl   = models.CharField(max_length = 50)
    type      = models.CharField(max_length = 20)  # forecast, reforecast, analysis
    product   = models.CharField(max_length = 10)   # ens, ana, hr
    kind      = models.CharField(max_length = 10)  # surface, pressure

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["type", "product", "kind"], name = "unique_datatype")
        ]

# Referencing files
class File(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    datatype = models.ForeignKey(DataType, on_delete = models.CASCADE)
    path     = models.CharField(max_length = 200)
    version  = models.PositiveSmallIntegerField(null = True)

# Init date/date
class Date(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    date = models.DateField(max_length = 3, unique = True)

# Referencing Domain
class Domain(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    domain     = models.CharField(max_length = 3, unique = True)

# Referencing level type
class Leveltype(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    leveltype  = models.CharField(max_length = 3, unique = True)

# Name of parameter
class Parameter(models.Model):
    id         = models.SmallAutoField(primary_key = True)
    name       = models.CharField(max_length = 8)
    ecmwfid    = models.PositiveIntegerField()
    domain     = models.ForeignKey(Domain,    on_delete = models.PROTECT)
    leveltype  = models.ForeignKey(Leveltype, on_delete = models.PROTECT)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["name", "ecmwfid"], name = "unique_parameter")
        ]


# Grib message
class Message(models.Model):
    datatype   = models.ForeignKey(DataType,  on_delete = models.CASCADE)
    file       = models.ForeignKey(File,      on_delete = models.CASCADE)

    # Time information
    date       = models.ForeignKey(Date, on_delete = models.PROTECT, related_name = "init_date")
    hdate      = models.ForeignKey(Date, on_delete = models.PROTECT, related_name = "hindcast_date")
    step       = models.PositiveSmallIntegerField()
    number     = models.SmallIntegerField(validators = [MinValueValidator(-1), MaxValueValidator(50)])

    # Parameter information
    param      = models.ForeignKey(Parameter, on_delete = models.PROTECT)

    # Bytes range within grib file
    bytes_begin = models.PositiveIntegerField() #models.PositiveBigIntegerField()
    bytes_end   = models.PositiveIntegerField() #models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["date", "hdate", "step", "number", "param"], name = "unique_message")
        ]
