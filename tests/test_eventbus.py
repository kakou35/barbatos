"""
Tests unitaires pour le bus d'événements asynchrone (core.bus).
"""

import asyncio
from core.bus import EventBus, Event


def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    async def sample_handler(event: Event):
        received.append(event.data)

    bus.subscribe("test.topic", sample_handler)

    async def run_test():
        await bus.publish("test.topic", data={"key": "val1"}, sender="tester")
        await bus.publish("other.topic", data={"key": "val2"}, sender="tester")

    asyncio.run(run_test())

    assert len(received) == 1
    assert received[0]["key"] == "val1"


def test_event_bus_wildcard():
    bus = EventBus()
    all_events = []

    async def wildcard_handler(event: Event):
        all_events.append(event.topic)

    bus.subscribe("*", wildcard_handler)

    async def run_test():
        await bus.publish("alpha", sender="tester")
        await bus.publish("beta", sender="tester")

    asyncio.run(run_test())

    assert len(all_events) == 2
    assert "alpha" in all_events
    assert "beta" in all_events


if __name__ == "__main__":
    test_event_bus_publish_subscribe()
    test_event_bus_wildcard()
    print("Tests EventBus validés avec succès !")
