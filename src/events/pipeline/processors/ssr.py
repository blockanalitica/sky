import logging

from chain_harvester.utils import create_index

from core.utils.processors import (
    NetworkProcessor,
    determine_last_processed_block,
    save_latest_block,
)
from events.models import EventSSR

log = logging.getLogger(__name__)

SUSDS = "0xa3931d71877c0e7a3148cb7eb4463524fec27fbd"


class EventSSRProcessor(NetworkProcessor):
    redis_key = "event_ssr_processor_latest_block"

    async def sync(self):
        await self.process_events()

    async def process_events(self, from_block=None):
        if from_block:
            self.from_block = from_block
        else:
            self.from_block = await determine_last_processed_block(
                self.redis_key,
                EventSSR,
                20677434,
            )

        topics = [
            "0xe986e40cc8c151830d4f61050f4fb2e4add8567caad2d5f5496f9158e91fe4c7",  # file
        ]
        events = self.chain_async.fetch_events(
            [SUSDS],
            self.from_block,
            topics=[topics],
            to_block=self.to_block,
        )
        await self.save_events(events)

    async def save_events(self, events):
        events_to_create = []
        async for event in events:
            order_index = create_index(
                event["blockNumber"], event["transactionIndex"], event["logIndex"]
            )
            args = event["args"]
            if args["what"] not in ["ssr"]:
                continue

            events_to_create.append(
                EventSSR(
                    block_number=event["blockNumber"],
                    datetime=event["blockDateTime"],
                    tx_hash=event["transactionHash"].to_0x_hex(),
                    order_index=order_index,
                    event=args["what"],
                    args=args,
                    address=event["address"].lower(),
                )
            )

            if len(events_to_create) >= 1000:
                await EventSSR.bulk_create(events_to_create, ignore_conflicts=True)
                log.debug(f"Saved batch of {len(events_to_create)} dsr events")

                await save_latest_block(
                    self.redis_key,
                    events_to_create[-1].block_number,
                )
                events_to_create = []

        if events_to_create:
            await EventSSR.bulk_create(events_to_create, ignore_conflicts=True)
            log.debug(f"Saved batch of {len(events_to_create)} dsr events")

            await save_latest_block(
                self.redis_key,
                events_to_create[-1].block_number,
            )

        await save_latest_block(self.redis_key, self.to_block)
