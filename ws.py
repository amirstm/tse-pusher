import asyncio
import time


async def discord_async_method(a):
    while True:
        await asyncio.sleep(3)
        print(a)


async def main():
    # run discord_async_method() in the "background"
    asyncio.get_event_loop().create_task(
        asyncio.wait_for(
            asyncio.gather(*[discord_async_method(2), discord_async_method(4)]),
            timeout=None,
        )
    )

    print("1")
    await asyncio.sleep(4)
    asyncio.get_event_loop().create_task(discord_async_method(5))
    print("3")
    await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
