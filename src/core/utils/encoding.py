import json
from datetime import date, datetime
from decimal import Decimal


def encode_value(val):
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return val


# Recursively encode all values in the snapshots
def encode_row(row):
    if isinstance(row, dict):
        return {k: encode_value(v) for k, v in row.items()}
    return row


def encode_response(response):
    if isinstance(response, list):
        return [encode_row(row) for row in response]
    return encode_row(response)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)
