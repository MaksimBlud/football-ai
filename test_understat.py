
import asyncio
import aiohttp
from understat import Understat


async def main():

    async with aiohttp.ClientSession() as session:

        understat = Understat(session)

        players = await understat.get_league_players(
            "EPL",
            2025
        )

        print("Количество игроков:", len(players))

        print(players[:3])


if __name__ == "__main__":
    asyncio.run(main())