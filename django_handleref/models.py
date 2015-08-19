from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_handleref.manager import HandleRefManager

try:
    import reversion

    def handle_version(**kwargs):
        for instance in kwargs.get("instances"):
            instance.version = instance.version + 1
            instance.save()

    reversion.post_revision_commit.connect(handle_version)
except ImportError:
    pass

class HandleRefOptions(object):
    delete_cascade = []

    def __init__(self, cls, opts):
        if opts:
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)

        if not getattr(self, 'tag', None):
            self.tag = cls.__name__.lower()


class HandleRefMeta(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(HandleRefMeta, cls).__new__

        # only init subclass
        parents = [b for b in bases if isinstance(b, HandleRefMeta)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        new = super_new(cls, name, bases, attrs)
        opts = attrs.pop('HandleRef', None)
        if not opts:
            opts = getattr(new, 'HandleRef', None)

        setattr(new, '_handleref', HandleRefOptions(new, opts))
        return new


class HandleRefModel(models.Model):
    """
    Provides timestamps for creation and change times,
    versioning (using django-reversion) as well as
    the ability to soft-delete
    """

    id = models.AutoField(primary_key=True)
    status = models.CharField(_('Status'), max_length=255, blank=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)
    version = models.IntegerField(default=0)

    __metaclass__ = HandleRefMeta
    handleref = HandleRefManager()
    objects = models.Manager()

    class Meta:
        abstract = True
        get_latest_by = 'updated'
        ordering = ('-updated', '-created',)

    @property
    def handle(self):
        if not self.id:
            raise ValueError("id not set")
        return self._handleref.tag + str(self.id)

    def __unicode__(self):
        if not hasattr(self, "name"):
          name = self.__class__.__name__
        else:
          name = self.name
        return name + '-' + self.handle

    def delete(self, hard=False):

        """
        Override the vanilla delete functionality to soft-delete
        instead. Soft-delete is accomplished by setting the
        status field to "deleted"

        Arguments:

        hard <bool=False> if true, do a hard delete instead, effectively
        removing the object from the database
        """

        if hard:
            return models.Model.delete(self)
        self.status = "deleted"
        self.save()
        for key in self._handleref.delete_cascade:
            for child in getattr(self, key).all():
                child.delete(hard=hard)


