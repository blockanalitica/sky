import json
import logging
from decimal import Decimal

from bakit.utils.db import fetch_all_sql, streaming_fetch_all_sql
from chain_harvester.utils import RAY, normalize_to_decimal

from agents.models import Agent, AgentIlkRateEvent, AgentUrnEventState
from core.constants import MAX_UINT256
from core.utils.tools import chunk_generator_by_key
from events.models import EventVat

log = logging.getLogger(__name__)


class AgentUrnStatesProcessor:
    def __init__(self):
        self.latest_rates_mapping = {}

    async def sync(self):
        agents = await Agent.all()
        for agent in agents:
            await self.process_rate_events(agent)
            await self.process_urn_positions(agent)

    async def process_rate_events(self, agent):
        ilk = agent.ilk
        obj = await AgentIlkRateEvent.filter(ilk=ilk).order_by("-order_index").first()
        if obj:
            from_order_index = obj.order_index
            self.latest_rates_mapping[ilk] = obj.cumulative_rate
        else:
            from_order_index = "0"
            self.latest_rates_mapping[ilk] = RAY

        sql = f"""
            SELECT
                  event
                , block_number
                , address
                , args
                , order_index
                , datetime
                , tx_hash
                , ilk
            FROM {EventVat.db_table()}
            WHERE source = 'rate' AND ilk = %(ilk)s
                AND order_index > %(from_order_index)s
            ORDER BY order_index
        """

        events_to_create = []

        async with streaming_fetch_all_sql(
            sql, {"ilk": ilk, "from_order_index": from_order_index}, prefetch=5000
        ) as cursor:
            async for event in cursor:
                log.info(f"Processing {event['datetime']} for {event['address']}")
                block_number = event["block_number"]
                dt = event["datetime"]
                tx_hash = event["tx_hash"]
                order_index = event["order_index"]
                ilk = event["ilk"]
                args = json.loads(event["args"])
                u = args["u"]
                rate = args["rate"]

                cumulative_rate = self.latest_rates_mapping.get(ilk, RAY)
                cumulative_rate += Decimal(rate)

                events_to_create.append(
                    AgentIlkRateEvent(
                        block_number=block_number,
                        datetime=dt,
                        tx_hash=tx_hash,
                        ilk=ilk,
                        u=u,
                        rate=rate,
                        cumulative_rate=cumulative_rate,
                        order_index=order_index,
                    )
                )
                self.latest_rates_mapping[ilk] = cumulative_rate

                if len(events_to_create) >= 1000:
                    await AgentIlkRateEvent.bulk_create(events_to_create, ignore_conflicts=True)
                    events_to_create = []

        if events_to_create:
            await AgentIlkRateEvent.bulk_create(events_to_create, ignore_conflicts=True)

    async def process_urn_positions(self, agent):
        ilk = agent.ilk
        obj = await AgentUrnEventState.filter(ilk=ilk).order_by("-order_index").first()
        if obj:
            from_order_index = obj.order_index
        else:
            from_order_index = "0"

        current_rate, rate_checkpoints = await self._load_rate_checkpoints(
            ilk,
            from_order_index,
        )
        next_rate_index = 0

        sql = f"""
            SELECT
                  event
                , block_number
                , address
                , args
                , order_index
                , datetime
                , tx_hash
                , ilk
            FROM {EventVat.db_table()}
            WHERE source = 'position' AND ilk = %(ilk)s
                AND order_index > %(from_order_index)s
            ORDER BY order_index
        """

        async with streaming_fetch_all_sql(
            sql, {"ilk": ilk, "from_order_index": from_order_index}, prefetch=5000
        ) as cursor:
            chunks = chunk_generator_by_key(cursor, 5000, lambda item: item["block_number"])

            async for events in chunks:
                current_rate, next_rate_index = await self.process_events_chunk(
                    events,
                    current_rate=current_rate,
                    ilk=ilk,
                    rate_checkpoints=rate_checkpoints,
                    next_rate_index=next_rate_index,
                )

    async def _load_rate_checkpoints(self, ilk, from_order_index):
        """Fetch the minimum rate state needed to replay position events."""
        rate_obj = (
            await AgentIlkRateEvent.filter(ilk=ilk, order_index__lte=from_order_index)
            .order_by("-order_index")
            .first()
        )
        current_rate = rate_obj.cumulative_rate if rate_obj else RAY
        rate_checkpoints = (
            await AgentIlkRateEvent.filter(ilk=ilk, order_index__gt=from_order_index)
            .order_by("order_index")
            .values("order_index", "cumulative_rate")
        )
        return current_rate, list(rate_checkpoints)

    async def _load_previous_chunk_states(self, ilk, events):
        """Load the latest persisted state for each urn touched in a chunk."""
        if not events:
            return {}

        urns = set()
        for event in events:
            args = json.loads(event["args"])
            if event["event"] == "fork":
                urns.add(args["src"])
                urns.add(args["dst"])
            else:
                urns.add(args["u"])

        if not urns:
            return {}

        sql = f"""
            SELECT DISTINCT ON (urn)
                  urn
                , ink
                , art
            FROM {AgentUrnEventState.db_table()}
            WHERE ilk = %(ilk)s
                AND urn = ANY(%(urns)s)
                AND order_index <= %(order_index)s
            ORDER BY urn, order_index DESC
        """
        rows = await fetch_all_sql(
            sql,
            {
                "ilk": ilk,
                "urns": sorted(urns),
                "order_index": events[0]["order_index"],
            },
        )
        return {
            row["urn"]: {
                "ink": row["ink"],
                "art": row["art"],
            }
            for row in rows
        }

    def _expand_position_event(self, event):
        """Split a Vat event into one or more normalized urn updates."""
        event = dict(event)
        args = json.loads(event["args"])

        if event["event"] != "fork":
            event["parsed_args"] = args
            return [event]

        log.info(f"Processing fork event {event['datetime']} for {event['address']}")
        if args["src"] == args["dst"]:
            return []

        src_event = dict(event)
        src_event["parsed_args"] = {
            "i": event["ilk"],
            "u": args["src"],
            "v": args["src"],
            "w": args["src"],
            "sig": args["sig"],
            "dart": args["dart"] * -1,
            "dink": args["dink"] * -1,
        }
        dst_event = dict(event)
        dst_event["parsed_args"] = {
            "i": event["ilk"],
            "u": args["dst"],
            "v": args["dst"],
            "w": args["dst"],
            "sig": args["sig"],
            "dart": args["dart"],
            "dink": args["dink"],
        }
        return [src_event, dst_event]

    def _advance_rate(self, rate_checkpoints, next_rate_index, current_rate, order_index):
        """Advance the in-memory rate pointer to the latest checkpoint in range."""
        while next_rate_index < len(rate_checkpoints):
            checkpoint = rate_checkpoints[next_rate_index]
            if checkpoint["order_index"] > order_index:
                break
            current_rate = checkpoint["cumulative_rate"]
            next_rate_index += 1
        return current_rate, next_rate_index

    async def process_events_chunk(
        self,
        events,
        *,
        current_rate,
        ilk,
        rate_checkpoints,
        next_rate_index,
    ):
        """Convert a block-sized chunk of Vat events into urn state rows.

        Fork events are split into synthetic source/destination updates so each
        affected urn gets its own snapshot. Within the chunk, already-computed
        urn balances are cached in memory to avoid repeated database lookups for
        later events in the same block.
        """
        states = await self._load_previous_chunk_states(ilk, events)
        events_to_create = []
        for event in events:
            for position_event in self._expand_position_event(event):
                log.info(
                    "Processing %s %s for %s",
                    position_event["ilk"],
                    position_event["datetime"],
                    position_event["address"],
                )
                block_number = position_event["block_number"]
                dt = position_event["datetime"]
                tx_hash = position_event["tx_hash"]
                order_index = position_event["order_index"]
                ilk = position_event["ilk"]
                current_rate, next_rate_index = self._advance_rate(
                    rate_checkpoints,
                    next_rate_index,
                    current_rate,
                    order_index,
                )
                args = position_event["parsed_args"]
                urn = args["u"]

                if urn in states:
                    ink = states[urn]["ink"]
                    art = states[urn]["art"]
                else:
                    ink = Decimal(0)
                    art = Decimal(0)

                dink = normalize_to_decimal(args["dink"], 18)
                dart = normalize_to_decimal(args["dart"], 18)
                ink += dink
                art += dart

                rate = normalize_to_decimal(current_rate, 27)

                if ink >= MAX_UINT256:
                    ink = Decimal(0)

                if dink >= MAX_UINT256:
                    dink = Decimal(0)

                events_to_create.append(
                    AgentUrnEventState(
                        block_number=block_number,
                        datetime=dt,
                        tx_hash=tx_hash,
                        ilk=ilk,
                        urn=urn,
                        event=position_event["event"],
                        ink=ink,
                        art=art,
                        dink=dink,
                        dart=dart,
                        rate=rate,
                        order_index=order_index,
                        debt=art * rate,
                    )
                )

                states[urn] = {
                    "ink": ink,
                    "art": art,
                }

                if len(events_to_create) >= 1000:
                    await AgentUrnEventState.bulk_create(events_to_create, ignore_conflicts=True)
                    events_to_create = []

        if events_to_create:
            await AgentUrnEventState.bulk_create(events_to_create, ignore_conflicts=True)
        return current_rate, next_rate_index
