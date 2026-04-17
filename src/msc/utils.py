from decimal import Decimal

from bakit.utils.db import fetch_all_sql

from core.constants import RAY
from core.utils.dates import get_min_max_dt
from events.models import EventSSR


async def get_ssr_events_for_date(for_date):
    """Get savings events for a specific date including the previous event.

    Fetches EventSSR records on the specified date.
    Includes the most recent event before the date to provide context for the first
    event of the day.

    Args:
        for_date (datetime.date): Date to fetch events for (date object, not datetime)

    Returns:
        List[dict]: List of EventSSR records ordered by order_index.
                   Includes the previous event before the specified date and all
                   events that occurred on the specified date.
    """
    sql = f"""
        WITH prev_event AS (
            SELECT *
            FROM {EventSSR.db_table()}
            WHERE
                datetime < %(date_min)s::timestamptz
            ORDER BY order_index DESC
            LIMIT 1
        ),
        today_events AS (
            SELECT *
            FROM {EventSSR.db_table()}
            WHERE
                datetime >= %(date_min)s::timestamptz
                AND datetime < %(date_max)s::timestamptz
            ORDER BY order_index DESC
        )
        SELECT *
        FROM prev_event
        UNION ALL
        SELECT *
        FROM today_events
        ORDER BY order_index ASC;
    """
    dt_min, dt_max = get_min_max_dt(for_date)
    events = await fetch_all_sql(sql, {"date_min": dt_min, "date_max": dt_max})
    return events


def decode_duty_ray(duty_ray):
    """Convert duty RAY value (1e27 fixed point) to per-second duty."""
    duty_ray = Decimal(duty_ray)
    per_second_factor = duty_ray / RAY
    duty_per_second = per_second_factor - Decimal(1)
    return duty_per_second
