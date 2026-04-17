import logging

from chain_harvester.utils import create_index

from core.constants import VAT_ADDRESS
from core.models import EventVat
from core.utils.processors import (
    NetworkProcessor,
    determine_last_processed_block,
    save_latest_block,
)
from events.constants import SKY_FIRST_BLOCK

log = logging.getLogger(__name__)


class EventVatProcessor(NetworkProcessor):
    redis_key = "event_vat_processor_latest_block"

    async def sync(self):
        await self.process_events()

    async def process_events(self, from_block=None):
        if from_block is not None:
            self.from_block = from_block
        else:
            self.from_block = await determine_last_processed_block(
                self.redis_key,
                EventVat,
                SKY_FIRST_BLOCK,
            )

        if self.to_block is None:
            self.to_block = await self.chain_async.get_latest_block()

        # Vat logs are anonymous, so the first topic corresponds to the
        # executed function selector rather than the event signature.
        topics = [
            "0xb65337df00000000000000000000000000000000000000000000000000000000",  # fold
            "0x870c616d00000000000000000000000000000000000000000000000000000000",  # fork
            "0x7bab3f4000000000000000000000000000000000000000000000000000000000",  # grab
            "0x7608870300000000000000000000000000000000000000000000000000000000",  # frob
        ]

        events = self.chain_async.fetch_events(
            [VAT_ADDRESS],
            self.from_block,
            topics=[topics],
            to_block=self.to_block,
            anonymous=True,
        )
        await self.save_events(events)

    async def save_events(self, events):
        """Normalize fetched logs and bulk insert them into ``UrnVatEvent``.

        The batch checkpoint is updated after every successful bulk insert so a
        restart can continue close to the last persisted event instead of
        replaying the entire range.
        """
        events_to_create = []
        async for event in events:
            order_index = create_index(
                event["blockNumber"], event["transactionIndex"], event["logIndex"]
            )
            args = event["args"]["event_layout"]
            event_name = event["args"]["executed_function"]

            log.debug(f"Saving {event_name} from {event['address']}, {event['blockDateTime']}")

            # ``fold`` changes the ilk rate; the remaining tracked methods are
            # position-oriented urn updates.
            if event_name == "fold":
                source = "rate"
            else:
                source = "position"

            # Depending on the decoded ABI, the ilk may be exposed under either
            # key. Prefer ``i`` but fall back to ``ilk`` for compatibility.
            ilk = args.get("i")
            if not ilk:
                ilk = args.get("ilk")

            events_to_create.append(
                EventVat(
                    block_number=event["blockNumber"],
                    datetime=event["blockDateTime"],
                    tx_hash=event["transactionHash"].to_0x_hex(),
                    order_index=order_index,
                    event=event_name,
                    args=args,
                    address=event["address"].lower(),
                    source=source,
                    ilk=ilk,
                )
            )

            # Flush in chunks to keep memory bounded during large backfills.
            if len(events_to_create) >= 1000:
                await EventVat.bulk_create(events_to_create, ignore_conflicts=True)
                log.debug(f"Saved batch of {len(events_to_create)} events")

                await save_latest_block(
                    self.redis_key,
                    events_to_create[-1].block_number,
                )
                events_to_create = []

        if events_to_create:
            await EventVat.bulk_create(events_to_create, ignore_conflicts=True)
            log.debug(f"Saved final batch of {len(events_to_create)} events")
            await save_latest_block(
                self.redis_key,
                events_to_create[-1].block_number,
            )

        # Always advance the checkpoint to the requested upper bound so empty
        # ranges are also marked as processed.
        await save_latest_block(self.redis_key, self.to_block)
