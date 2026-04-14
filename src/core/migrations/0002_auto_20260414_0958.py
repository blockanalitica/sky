from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Block',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('chain_id', fields.IntField()),
                ('number', fields.BigIntField()),
                ('hash', fields.BinaryField()),
                ('timestamp', fields.BigIntField()),
            ],
            options={'table': 'block', 'app': 'core', 'unique_together': [['chain_id', 'number']], 'pk_attr': 'id'},
            bases=['CoreModel'],
        ),
    ]
