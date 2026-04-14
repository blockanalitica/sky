from tortoise import Tortoise, models


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


class NetworkModel(CoreModel):
    class Meta:
        abstract = True

    @classmethod
    def db_table(cls, network):
        return cls.network(network)._meta.db_table

    @classmethod
    def network(cls, network):
        suffix = _calculate_model_suffix(network)
        model_name = f"{cls.__name__}{suffix}"
        try:
            return Tortoise.apps.get("core")[model_name]
        except KeyError as err:
            raise ValueError(f"No {cls.__name__} model found for network: {network}") from err


def _calculate_model_suffix(network_name):
    return "".join([name.capitalize() for name in network_name.split("_")])


def create_model_variants(model_classes, module_name, network):
    instances = {}
    suffix = _calculate_model_suffix(network)
    for base_cls in model_classes:
        class_name = f"{base_cls.__name__}{suffix}"

        # Get base Meta attributes
        base_meta = getattr(base_cls, "Meta", object)
        meta_attrs = {
            "ordering": getattr(base_meta, "ordering", []),
            "indexes": getattr(base_meta, "indexes", []),
            "unique_together": getattr(base_meta, "unique_together", ()),
        }

        # Define a new Meta class
        meta = type("Meta", (), meta_attrs)

        # Create the new model subclass
        new_cls = type(
            class_name, (base_cls,), {"__module__": module_name, "network": network, "Meta": meta}
        )

        instances[class_name] = new_cls

    return instances
