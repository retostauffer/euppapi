



from django.conf import settings
from django.db import models
from django.utils import timezone

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
    product   = models.CharField(max_length = 5)   # ens, ana, hr
    kind      = models.CharField(max_length = 10)  # surface, pressure

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ["type", "product", "kind"], name = "unique_datatype")
        ]

# Referencing files
class File(models.Model):
    datatype = models.ForeignKey(DataType, on_delete = models.CASCADE)
    path     = models.CharField(max_length = 200)
    version  = models.PositiveSmallIntegerField(null = True)

# Referencing Domain
class Domain(models.Model):
    domain = models.CharField(max_length = 3, unique = True)

# Referencing level type
class Leveltype(models.Model):
    leveltype  = models.CharField(max_length = 3, unique = True)

# Grib message
class Message(models.Model):
    datatype   = models.ForeignKey(DataType, on_delete = models.CASCADE)
    file       = models.ForeignKey(File,     on_delete = models.CASCADE)
    domain     = models.ForeignKey(Domain, on_delete = models.CASCADE)
    leveltype  = models.ForeignKey(Leveltype, on_delete = models.CASCADE)

    # Time information
    date       = models.DateField()
    hdate      = models.DateField(null = True)
    time       = models.PositiveSmallIntegerField()
    step_begin = models.PositiveSmallIntegerField()
    step_end   = models.PositiveSmallIntegerField()
    number     = models.PositiveSmallIntegerField(null = True)

    # Parameter information
    param      = models.CharField(max_length = 8)
    param_id   = models.PositiveIntegerField()

    # Bytes range within grib file
    bytes_begin = models.PositiveBigIntegerField()
    bytes_end   = models.PositiveBigIntegerField()
