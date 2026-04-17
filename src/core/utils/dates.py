from datetime import UTC, datetime, time, timedelta


def _snapshot_dates_after_midnight(dt):
    """If we're within 15 minutes after midnight UTC, also produce yesterday's date.

    Gives downstream snapshot jobs a short grace window to finalize the prior day.
    """
    current_time = dt.time()
    date = dt.date()
    after = time(0, 15)
    dates = [date]
    if current_time <= after:
        dates.append(date - timedelta(days=1))
    return dates


def get_all_snapshot_dates_after_midnight(current_datetime, latest_date):
    """All dates that need a snapshot rebuild, from ``latest_date`` through today.

    On today's date, unions with the post-midnight grace dates so a run that
    starts right after midnight still refreshes yesterday.
    """
    dates = set()
    current_date = current_datetime.date()
    days = (current_date - latest_date).days
    for i in range(days + 1):
        date = latest_date + timedelta(days=i)
        dates.add(date)
        if date == current_date:
            dates.update(_snapshot_dates_after_midnight(current_datetime))
    return sorted(dates)


def get_min_max_dt(for_date):
    min_dt = datetime.combine(for_date, datetime.min.time(), tzinfo=UTC)
    max_dt = datetime.combine(for_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
    return min_dt, max_dt
