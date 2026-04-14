from tortoise import migrations
from tortoise.migrations import operations as ops
import functools
from json import dumps, loads
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Agent',
            fields=[
                ('slug', fields.CharField(primary_key=True, unique=True, db_index=True, max_length=32)),
                ('name', fields.CharField(null=True, max_length=32)),
                ('ilk', fields.CharField(null=True, max_length=32)),
            ],
            options={'table': 'agent', 'app': 'core', 'pk_attr': 'slug'},
            bases=['CoreModel'],
        ),
        ops.CreateModel(
            name='AgentIlkRateEvent',
            fields=[
                ('block_number', fields.IntField()),
                ('datetime', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('tx_hash', fields.CharField(max_length=66)),
                ('ilk', fields.CharField(max_length=64)),
                ('u', fields.CharField(max_length=42)),
                ('rate', fields.DecimalField(max_digits=48, decimal_places=0)),
                ('cumulative_rate', fields.DecimalField(null=True, max_digits=48, decimal_places=0)),
                ('order_index', fields.CharField(primary_key=True, unique=True, db_index=True, max_length=26)),
            ],
            options={'table': 'agentilkrateevent', 'app': 'core', 'indexes': [Index(fields=['ilk', 'order_index'])], 'pk_attr': 'order_index'},
            bases=['CoreModel'],
        ),
        ops.CreateModel(
            name='AgentUrnEventState',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('block_number', fields.IntField()),
                ('owner_address', fields.CharField(null=True, max_length=42)),
                ('datetime', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('tx_hash', fields.CharField(max_length=66)),
                ('order_index', fields.CharField(max_length=26)),
                ('ilk', fields.CharField(max_length=64)),
                ('urn', fields.CharField(max_length=42)),
                ('event', fields.CharField(null=True, max_length=64)),
                ('ink', fields.DecimalField(max_digits=64, decimal_places=18)),
                ('art', fields.DecimalField(max_digits=64, decimal_places=18)),
                ('dart', fields.DecimalField(max_digits=64, decimal_places=18)),
                ('dink', fields.DecimalField(max_digits=64, decimal_places=18)),
                ('rate', fields.DecimalField(max_digits=64, decimal_places=32)),
                ('debt', fields.DecimalField(max_digits=64, decimal_places=18)),
            ],
            options={'table': 'agenturneventstate', 'app': 'core', 'unique_together': (['urn', 'ilk', 'order_index'],), 'indexes': [Index(fields=['urn']), Index(fields=['urn', 'datetime']), Index(fields=['ilk']), Index(fields=['ilk', 'datetime', 'order_index']), Index(fields=['ilk', 'order_index'])], 'pk_attr': 'id'},
            bases=['CoreModel'],
        ),
        ops.CreateModel(
            name='EventSSR',
            fields=[
                ('block_number', fields.IntField()),
                ('datetime', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('order_index', fields.CharField(primary_key=True, unique=True, db_index=True, max_length=26)),
                ('tx_hash', fields.CharField(max_length=66)),
                ('address', fields.CharField(max_length=42)),
                ('args', fields.JSONField(encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
                ('event', fields.CharField(null=True, max_length=64)),
            ],
            options={'table': 'eventssr', 'app': 'core', 'indexes': [Index(fields=['datetime', 'order_index'])], 'pk_attr': 'order_index'},
            bases=['EventModel'],
        ),
        ops.CreateModel(
            name='EventVat',
            fields=[
                ('block_number', fields.IntField()),
                ('datetime', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('order_index', fields.CharField(primary_key=True, unique=True, db_index=True, max_length=26)),
                ('tx_hash', fields.CharField(max_length=66)),
                ('address', fields.CharField(max_length=42)),
                ('args', fields.JSONField(encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
                ('event', fields.CharField(null=True, max_length=64)),
                ('ilk', fields.CharField(null=True, max_length=32)),
                ('source', fields.CharField(null=True, max_length=32)),
            ],
            options={'table': 'eventvat', 'app': 'core', 'indexes': [Index(fields=['ilk', 'order_index']), Index(fields=['ilk', 'source', 'order_index']), Index(fields=['block_number'])], 'pk_attr': 'order_index'},
            bases=['EventModel'],
        ),
        ops.CreateModel(
            name='MSCItemSnapshot',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('network', fields.CharField(max_length=32)),
                ('agent', fields.CharField(max_length=32)),
                ('date', fields.DateField()),
                ('uid', fields.CharField(max_length=128)),
                ('balance', fields.DecimalField(null=True, max_digits=32, decimal_places=18)),
                ('start_rate', fields.DecimalField(null=True, max_digits=64, decimal_places=18)),
                ('end_rate', fields.DecimalField(null=True, max_digits=64, decimal_places=18)),
                ('apr', fields.DecimalField(null=True, max_digits=64, decimal_places=18)),
                ('daily_interest', fields.DecimalField(max_digits=32, decimal_places=18)),
                ('cumulative_interest', fields.DecimalField(max_digits=32, decimal_places=18)),
                ('average_balance', fields.DecimalField(max_digits=32, decimal_places=18)),
                ('what', fields.CharField(max_length=32)),
                ('source', fields.CharField(null=True, max_length=32)),
            ],
            options={'table': 'mscitemsnapshot', 'app': 'core', 'unique_together': [('network', 'agent', 'date', 'uid')], 'indexes': [Index(fields=['network', 'agent', 'uid', 'date'])], 'pk_attr': 'id'},
            bases=['CoreModel'],
        ),
    ]
