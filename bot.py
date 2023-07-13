from discord import Intents
from discord.ext import commands

OWNER_IDS = []


class Bot(commands.Bot):
    def __init__(self, prefix="!", cogs=[], intents=Intents.default(), avatar=None) -> None:
        self.ready = False
        self._cogs = cogs
        self.avatar = avatar

        super().__init__(command_prefix=prefix, owner_ids=OWNER_IDS, intents=intents)

    async def setup(self) -> None:
        for cog in self._cogs: await self.load_extension(f"cogs.{cog}")

    async def run(self, token) -> None:
        print("Init cogs...")
        await self.setup()
        print("Running bot...")
        await super().start(token, reconnect=True)

    async def on_connect(self) -> None: print("bot connected")
    async def on_disconnect(self) -> None: print("bot disconnected")

    async def on_error(self, err, *args, **kwargs) -> None:
        if err == "on_command_error":
            await args[0].send("Something went wrong", delete_after=10)
        await super().on_error(err, *args, **kwargs)

    async def on_command_error(self, ctx, exc) -> None:
        if isinstance(exc, commands.errors.CommandNotFound):
            await ctx.send("Command does not exist", delete_after=10)
        elif hasattr(exc, "original"): raise exc.original
        else: raise exc

    async def on_ready(self) -> None:
        if not self.ready:
            if self.avatar is not None: await self.user.edit(avatar=self.avatar)
            self.ready = True
            # self.guilds = [guild async for guild in self.fetch_guilds()]
            msg = "______________________________________________________________\n"
            msg += f"bot ready - {self.user} is connected to the following guild:\n"
            msg += '\n'.join([f"{guild.name} (id: {guild.id})" for guild in self.guilds])
            msg += "\n______________________________________________________________"
            print(msg)
            print(f"{self.user} is connected")
        else: print("bot reconnected")
