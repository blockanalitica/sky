from tortoise import models


class CoreModel(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def db_table(cls):
        return cls._meta.db_table

    def __str__(self):
        return f"{self.__class__.__name__} object ({getattr(self, 'pk', 'no-pk')})"

    def __repr__(self):
        model_fields = [
            f"{key}={getattr(self, key)!r}" for key in self._meta.fields_map if hasattr(self, key)
        ]
        return f"{self.__class__.__name__}({', '.join(model_fields)})"
