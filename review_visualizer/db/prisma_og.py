from prisma import Prisma


class PrismaClient:
    def __init__(self):
        self.db = Prisma()

    async def __aenter__(self) -> Prisma:
        await self.db.connect()
        return self.db

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.db.disconnect()
