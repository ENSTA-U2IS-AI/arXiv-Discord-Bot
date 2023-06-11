from discord.ext import commands
import random as rd


class Utils(commands.Cog):
    def __init__(self, bot) -> None: self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self): print("Utils cog ready")

    #
    #  Debug commands
    #
    @commands.group(name="debug", aliases=['d'])
    async def debug(self, ctx):
        if ctx.invoked_subcommand is None: await ctx.send('please use a subcommand', delete_after=10)

    @debug.command(name="ping", help="ping command")
    async def ping_command(self, ctx): await ctx.send(f'pong ! ({round(self.bot.latency *1000)} ms)')

    @debug.command(name='echo', help='repeat')
    async def echo_command(self, ctx, *, message: str): await ctx.send(message)

    #
    #  Utils commands
    #
    @commands.group(name="utils", aliases=['u'])
    async def utils(self, ctx):
        if ctx.invoked_subcommand is None: await ctx.send('please use a subcommand', delete_after=10)

    @utils.command(name='dice', help='roll a dice - optionnal : nbr side / nbr dice')
    async def dice_command(self, ctx, *args: int):
        side = 6 if len(args) == 0 else args[0]
        dices = 1 if len(args) <= 1 else args[1]
        dice = [str(rd.choice(range(1, side + 1))) for _ in range(dices)]
        await ctx.send('I choose ' + ', '.join(dice) + ' for you')


# entry point for bot's load_extension method
async def setup(bot): await bot.add_cog(Utils(bot))
