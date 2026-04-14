from tortoise import fields
from tortoise.indexes import Index

from core.utils.models import CoreModel


class Agent(CoreModel):
    slug = fields.CharField(max_length=32, primary_key=True)
    name = fields.CharField(max_length=32, null=True)
    ilk = fields.CharField(max_length=32, null=True)


class AgentIlkRateEvent(CoreModel):
    block_number = fields.IntField()
    datetime = fields.DatetimeField(null=True)
    tx_hash = fields.CharField(max_length=66)
    ilk = fields.CharField(max_length=64)
    u = fields.CharField(max_length=42)
    rate = fields.DecimalField(max_digits=48, decimal_places=0)
    cumulative_rate = fields.DecimalField(max_digits=48, decimal_places=0, null=True)
    order_index = fields.CharField(max_length=26, primary_key=True)

    class Meta:
        ordering = ["order_index"]
        indexes = [Index(fields=["ilk", "order_index"])]


class AgentUrnEventState(CoreModel):
    block_number = fields.IntField()
    owner_address = fields.CharField(max_length=42, null=True)
    datetime = fields.DatetimeField(null=True)
    tx_hash = fields.CharField(max_length=66)
    order_index = fields.CharField(max_length=26)
    ilk = fields.CharField(max_length=64)
    urn = fields.CharField(max_length=42)
    event = fields.CharField(max_length=64, null=True)
    ink = fields.DecimalField(max_digits=64, decimal_places=18)
    art = fields.DecimalField(max_digits=64, decimal_places=18)
    dart = fields.DecimalField(max_digits=64, decimal_places=18)
    dink = fields.DecimalField(max_digits=64, decimal_places=18)
    rate = fields.DecimalField(max_digits=64, decimal_places=32)
    debt = fields.DecimalField(max_digits=64, decimal_places=18)

    class Meta:
        ordering = ["order_index"]
        unique_together = ["urn", "ilk", "order_index"]
        indexes = [
            Index(fields=["urn"]),
            Index(fields=["urn", "datetime"]),
            Index(fields=["ilk"]),
            Index(fields=["ilk", "datetime", "order_index"]),
            Index(fields=["ilk", "order_index"]),
        ]
