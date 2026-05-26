import asyncio
from app.event_processor import process_event

async def worker_loop():

    while True:
        try:
            await process_event()

        except Exception as e:
            print("EVENT WORKER ERROR:", e)
        await asyncio.sleep(5)
if __name__ == "__main__":
    asyncio.run(worker_loop())