import math
from datetime import timedelta


async def compute_time_weighted_vol(daily_data, window_days, for_date):
    window_start = for_date - timedelta(days=window_days)
    squared_returns = []
    total_time = 0.0
    return_count = 0

    for date, entries in daily_data.items():
        if date < window_start or len(entries) < 2:
            continue

        entries = sorted(entries)
        for i in range(len(entries) - 1):
            t0, p0 = entries[i]
            t1, p1 = entries[i + 1]
            delta_t = (t1 - t0).total_seconds() / (60 * 60 * 24)  # in days
            if delta_t <= 0:
                continue

            r = math.log(p1 / p0)
            squared_returns.append((r**2) * delta_t)
            total_time += delta_t
            return_count += 1

    if total_time == 0 or return_count == 0:
        return 0.0

    # Time-weighted standard deviation
    time_weighted_vol = math.sqrt(sum(squared_returns) / total_time)

    # Adjusted annualization: based on actual interval frequency
    avg_dt = total_time / return_count
    intervals_per_year = 365 / avg_dt
    annualized = time_weighted_vol * math.sqrt(intervals_per_year)

    return annualized
