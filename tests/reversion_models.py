from django.db import models
from django.contrib.admin import ModelAdmin, register

import reversion

from django_handleref.admin import VersionAdmin

from tests.models import Org, HandleRefModel


@reversion.register
class VersionedOrg(HandleRefModel):
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class HandleRef:
        tag = 'org'
        delete_cascade = ["sub_entities"]

    def __unicode__(self):
        return self.name


@register(VersionedOrg)
class OrgAdmin(VersionAdmin, ModelAdmin):
    pass


