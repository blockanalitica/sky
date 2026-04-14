from tortoise import fields
from tortoise.indexes import Index

from core.utils.models import CoreModel


class MSCItemSnapshot(CoreModel):
    network = fields.CharField(max_length=32)
    agent = fields.CharField(max_length=32)
    date = fields.DateField()

    uid = fields.CharField(max_length=128)

    balance = fields.DecimalField(max_digits=32, decimal_places=18, null=True)
    start_rate = fields.DecimalField(max_digits=64, decimal_places=18, null=True)
    end_rate = fields.DecimalField(max_digits=64, decimal_places=18, null=True)
    apr = fields.DecimalField(max_digits=64, decimal_places=18, null=True)
    daily_interest = fields.DecimalField(max_digits=32, decimal_places=18)
    cumulative_interest = fields.DecimalField(max_digits=32, decimal_places=18)

    average_balance = fields.DecimalField(max_digits=32, decimal_places=18)

    what = fields.CharField(max_length=32)
    source = fields.CharField(max_length=32, null=True)

    class Meta:
        unique_together = [("network", "agent", "date", "uid")]
        indexes = [
            Index(fields=["network", "agent", "uid", "date"]),
        ]
