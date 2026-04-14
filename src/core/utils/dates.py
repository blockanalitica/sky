from datetime import UTC, datetime, time, timedelta


def snapshot_dates_after_midnight(dt):
    current_time = dt.time()
    date = dt.date()
    after = time(0, 15)
    dates = [date]
    if current_time <= after:
        dates.append(date - timedelta(days=1))

    return dates


def snapshot_dates_before_midnight(dt):
    current_time = dt.time()
    date = dt.date()
    before = time(23, 45)
    dates = [date]
    if current_time >= before:
        dates.append(date + timedelta(days=1))

    return dates


def get_additional_snapshot_dates_after_midnight(dt):
    """Get relevant dates for snapshots after midnight.

    This function determines which dates should be used for generating snapshots
    when the current time is after midnight but before 00:15 UTC. It returns:
    - The current date
    - The previous date if current time is before 00:15 UTC

    Args:
        dt (datetime): The current datetime to check

    Returns:
        list: A list of dates to process for snapshots
    """
    current_time = dt.time()
    date = dt.date()
    after = time(0, 15)
    dates = [date]
    if current_time <= after:
        dates.append(date - timedelta(days=1))

    return dates


def get_additional_snapshot_dates_before_midnight(dt):
    """Get relevant dates for snapshots before midnight.

    This function determines which dates should be used for generating snapshots
    when the current time is before midnight but after 23:45 UTC. It returns:
    - The current date
    - The next date if current time is after 23:45 UTC

    Args:
        dt (datetime): The current datetime to check

    Returns:
        list: A list of dates to process for snapshots
    """
    current_time = dt.time()
    date = dt.date()
    before = time(23, 45)
    dates = [date]
    if current_time >= before:
        dates.append(date + timedelta(days=1))

    return dates


def get_all_snapshot_dates_after_midnight(current_datetime, latest_date):
    """Get all dates that need snapshots after midnight.

    This function calculates all dates that need snapshotting based on:
    1. The number of days between the latest snapshot date and current date
    2. Additional dates around midnight for the current date

    Args:
        current_datetime (datetime): The current datetime to consider
        latest_date (date): Date of the last snapshot

    Returns:
        list: A sorted list of dates to process for snapshots
    """
    dates = set()
    current_date = current_datetime.date()
    days = (current_date - latest_date).days
    for i in range(days + 1):
        date = latest_date + timedelta(days=i)
        dates.add(date)
        if date == current_date:
            dates.update(get_additional_snapshot_dates_after_midnight(current_datetime))
    return sorted(dates)


def ensure_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def get_min_max_dt(for_date):
    min_dt = datetime.combine(for_date, datetime.min.time(), tzinfo=UTC)
    max_dt = datetime.combine(for_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
    return min_dt, max_dt
