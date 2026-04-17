import json
import logging
from decimal import Decimal

from chain_harvester.utils import normalize_to_decimal
from eth_utils.conversions import to_bytes

from agents.models import Agent, AgentUrnEventState
from core.constants import SECONDS_PER_YEAR, VAT_ADDRESS
from core.utils.dates import get_all_snapshot_dates_after_midnight, get_min_max_dt
from core.utils.processors import BaseSnapshotsManager
from msc.constants import PREMIUM_APR_PER_SECOND
from msc.models import MSCItemSnapshot
from msc.utils import decode_duty_ray, get_ssr_events_for_date

log = logging.getLogger(__name__)


class MSCDebtSnapshotManager(BaseSnapshotsManager):
    def __init__(self, chain_async):
        super().__init__()
        self.network = chain_async.chain
        self.chain_async = chain_async

    async def sync(self):
        agents = await Agent.all()
        for agent in agents:
            await self._process_snapshots(agent)

    async def _process_snapshots(self, agent):
        latest_snapshot = await MSCItemSnapshot.filter(
            network=self.network,
            agent=agent.slug,
            uid="debt",
        ).latest("date")
        if latest_snapshot:
            latest_date = latest_snapshot.date
        else:
            earliest_ilk_state = (
                await AgentUrnEventState.filter(ilk=agent.ilk).order_by("order_index").first()
            )
            if earliest_ilk_state:
                latest_date = earliest_ilk_state.datetime.date()
            else:
                return

        if not await self._is_current_balance_synced(agent, latest_date):
            return

        dates = get_all_snapshot_dates_after_midnight(self.current_datetime, latest_date)
        for date in dates:
            await self._save_snapshots_for_date(
                agent,
                date,
            )

    async def _save_snapshots_for_date(self, agent, for_date):
        log.debug(
            "Saving debt snapshot for %s on %s",
            agent.slug,
            for_date,
        )

        dt_min, dt_max = get_min_max_dt(for_date)

        if self.current_date == for_date:
            dt_max = self.current_datetime

        events = await AgentUrnEventState.filter(
            ilk=agent.ilk, datetime__gte=dt_min, datetime__lt=dt_max
        ).order_by("order_index")

        latest_state = (
            await MSCItemSnapshot.filter(
                network=self.network,
                agent=agent.slug,
                uid="debt",
            )
            .order_by("-date")
            .first()
        )
        if latest_state:
            balance = Decimal(latest_state.balance)
            cumulative_interest = Decimal(latest_state.cumulative_interest)
        else:
            balance = Decimal(0)
            cumulative_interest = Decimal(0)

        ssr_events = await get_ssr_events_for_date(for_date)
        if len(ssr_events):
            ssr_event = ssr_events.pop(0)
            ssr_args = json.loads(ssr_event["args"])
            ssr_current = decode_duty_ray(ssr_args["data"]).quantize(Decimal("1e-30"))
        else:
            # decode_duty_ray returns (duty/RAY) - 1 — i.e. the per-second rate
            # above 1. Zero rate means no SSR yet, not "100% per second".
            ssr_current = Decimal(0)

        day_events = []
        day_events.extend(ssr_events)
        day_events.extend(events)
        day_events.sort(
            key=lambda x: x.order_index if hasattr(x, "order_index") else x["order_index"]
        )

        daily_interest = Decimal(0)
        base_rate = ssr_current + PREMIUM_APR_PER_SECOND
        base_rate_start_of_day = base_rate
        weighted_balance_sum = Decimal(0)
        segment_start = dt_min

        for event in day_events:
            if hasattr(event, "datetime"):
                event_dt = event.datetime
            else:
                event_dt = event["datetime"]

            segment_seconds = int(event_dt.timestamp()) - int(segment_start.timestamp())

            profit_segment = balance * base_rate * segment_seconds
            daily_interest += profit_segment
            weighted_balance_sum += balance * segment_seconds
            if isinstance(event, dict):
                ssr_args = json.loads(event["args"])
                ssr_current = decode_duty_ray(ssr_args["data"]).quantize(Decimal("1e-30"))
                base_rate = ssr_current + PREMIUM_APR_PER_SECOND
            else:
                balance = Decimal(event.art * event.rate)
            segment_start = event_dt

        # apply end of day segment
        segment_seconds = int(dt_max.timestamp()) - int(segment_start.timestamp())
        if segment_seconds > 0:
            profit_segment = balance * base_rate * segment_seconds
            daily_interest += profit_segment
            weighted_balance_sum += balance * segment_seconds

        cumulative_interest += daily_interest

        total_seconds = int(dt_max.timestamp() - dt_min.timestamp())
        if total_seconds > 0 and weighted_balance_sum > 0:
            average_balance = weighted_balance_sum / Decimal(total_seconds)
            rate_per_second = daily_interest / weighted_balance_sum
            apr = rate_per_second * SECONDS_PER_YEAR
        else:
            average_balance = Decimal(0)
            apr = Decimal(0)

        await MSCItemSnapshot.update_or_create(
            network=self.network,
            agent=agent.slug,
            date=for_date,
            uid="debt",
            defaults={
                "balance": balance,
                "start_rate": base_rate_start_of_day,
                "end_rate": base_rate,
                "apr": apr,
                "daily_interest": daily_interest,
                "cumulative_interest": cumulative_interest,
                "average_balance": average_balance,
                "what": "debt",
            },
        )

    async def _is_current_balance_synced(self, agent, for_date):
        _, dt_max = get_min_max_dt(for_date)

        current_state = await AgentUrnEventState.filter(ilk=agent.ilk, datetime__lt=dt_max).latest(
            "order_index"
        )

        ilk_bytes = to_bytes(text=agent.ilk).ljust(32, b"\0")
        calls = [
            (
                VAT_ADDRESS,
                [
                    "ilks(bytes32)((uint256,uint256,uint256,uint256,uint256))",
                    ilk_bytes,
                ],
                ["ilk", []],
            )
        ]
        data = await self.chain_async.multicall(calls, block_identifier=current_state.block_number)
        value = data["ilk"]
        onchain_debt = normalize_to_decimal(value[0], 18) * normalize_to_decimal(value[1], 27)

        if int(onchain_debt) != int(current_state.debt):
            log.warning(
                "Balance missmatch for address=%s; ilk=%s! Onchain=%s vs DB=%s;",
                VAT_ADDRESS,
                agent.ilk,
                onchain_debt,
                current_state.debt,
            )
            return False
        return True
