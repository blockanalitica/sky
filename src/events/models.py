from tortoise import fields
from tortoise.indexes import Index

from core.utils.models import CoreModel


class EventModel(CoreModel):
    block_number = fields.IntField()
    datetime = fields.DatetimeField(null=True)
    order_index = fields.CharField(max_length=26, primary_key=True)
    tx_hash = fields.CharField(max_length=66)
    address = fields.CharField(max_length=42)
    args = fields.JSONField()
    event = fields.CharField(max_length=64, null=True)

    class Meta:
        abstract = True


class EventVat(EventModel):
    ilk = fields.CharField(max_length=32, null=True)
    source = fields.CharField(max_length=32, null=True)

    class Meta:
        ordering = ["order_index"]
        indexes = [
            Index(fields=["ilk", "order_index"]),
            Index(fields=["ilk", "source", "order_index"]),
            Index(fields=["block_number"]),
        ]


class EventSSR(EventModel):
    class Meta:
        ordering = ["order_index"]
        indexes = [
            Index(fields=["datetime", "order_index"]),
        ]


class Block(CoreModel):
    id = fields.BigIntField(pk=True, generated=True)
    chain_id = fields.IntField()
    number = fields.BigIntField()
    hash = fields.BinaryField(max_length=32)
    timestamp = fields.BigIntField()

    class Meta:
        unique_together = [["chain_id", "number"]]
