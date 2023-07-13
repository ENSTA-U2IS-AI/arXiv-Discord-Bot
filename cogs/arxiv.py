from discord.ext import commands
from discord import Embed, DMChannel
from arxiv import arxiv
from arxiv import SortOrder, SortCriterion
import asyncio
import json
import pickle
import os
from copy import deepcopy


class Arxiv(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
        self._load_config()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.watch_new_papers())
        print("Arxiv cog ready")

    def _format_message(self, message: str, n=5500):
        message = " ".join(message.split()).replace("$", "")
        return (message[:n] + ".....") if len(message) > n else message

    def _format_authors(self, paper):
        authors = ', '.join(map(str, paper.authors))
        return (authors[:253] + '...') if len(authors) > 256 else authors

    #
    #  ArXiV commands
    #

    @commands.group(name='arxiv', aliases=["a", "paper", "papers"])
    async def arxiv(self, ctx):
        if ctx.invoked_subcommand is None: await ctx.send('please use a subcommand', delete_after=10)

    @arxiv.command(name='search', help='search paper on arxiv from a text query', aliases=["find"])
    async def search_command(self, ctx, *, message):

        try:
            search = arxiv.Search(query=message, **self._config["query"])
        except BaseException as e:
            await ctx.send("Error occured when trying to fetch arxiv database.")
            print(e)

        size_footer = len(search.query) + len(str(search.max_results)) + len(search.sort_by.value) + 41
        try:
            embed = Embed(color=0xFF5733)
            embed.set_author(name="ArXiV", url="https://arxiv.org", icon_url=self.bot.user.avatar.url)
            result_count = 0
            for result in search.results():
                result_count += 1
                embed_resume = self._format_message(result.summary, n=350)
                if len(embed) + len(embed_resume) + len(result.title) > 6000: continue
                embed.add_field(
                    name=f"{result.title}",
                    value=f"[[ArXiV]({result.entry_id})][[PAPER]({result.pdf_url})]\n{embed_resume}.",
                    inline=False)
            if not result_count:
                embed.add_field(
                    name="No result found for given search query",
                    value=""
                )
            embed.set_footer(
                text=f"query: \"{search.query}\", limit: {search.max_results}, sort_by: {search.sort_by.value}, len: {len(embed) + size_footer}/6000")
            await ctx.send(embed=embed)
        except BaseException as e:
            await ctx.send("Error occured.")
            print(e)

    #
    #  Config commands
    #

    @arxiv.group(name="config", help="arxiv parameters management, show config with no subcommand")
    async def config(self, ctx):
        if ctx.invoked_subcommand is None: await self.show_command(ctx)

    @config.command(name="show", help="display config", aliases=["ls"])
    async def show_command(self, ctx):
        message = "Query parameters (search command):\n\t"
        formatted_args = [f"{k}: {v.value if k in ['sort_by', 'sort_order'] else v}" for k, v in self._config["query"].items()]
        message += "\n\t".join(formatted_args)

        message += "\nWatcher parameters:\n\t"
        parameters = ["sleep_time", "cooldown", "max_results"]
        formatted_args = [f"{k}: {v}" for k, v in self._config["watch"].items() if k in parameters]
        message += "\n\t".join(formatted_args)

        await ctx.send("```\n" + message + "\n```")

    @config.command(name="edit", help="Edit command value from group and key.", aliases=["update"])
    async def edit_command(self, ctx, group, key, new_value):
        if (group not in self._config): return await ctx.send(f"Enter a valid group: `query` or `watch`, not {group}.")
        if (key not in self._config[group]): return await ctx.send(f"Enter a valid key, not {key}.")
        if key == "sort_by":
            sort_criterions = [c.value for c in SortCriterion]
            if new_value in sort_criterions: new_value = SortCriterion(new_value)
            else: return ctx.send(f"Wrong value for `sort_by` key, allowed values : {sort_criterions}")
        elif key == "sort_order":
            sort_orders = [c.value for c in SortOrder]
            if new_value in sort_orders: new_value = SortOrder(new_value)
            else: return ctx.send(f"Wrong value for `sort_order` key, allowed values : {sort_orders}")

        self._config[group][key] = int(new_value)
        self._save_config()

        await ctx.send("Value update !")

    def _load_config(self):
        with open("config.json") as configFile: self._config = json.load(configFile)
        self._config["query"]["sort_by"] = SortCriterion(self._config["query"]["sort_by"])
        self._config["query"]["sort_order"] = SortOrder(self._config["query"]["sort_order"])

    def _save_config(self):
        config = deepcopy(self._config)
        config["query"]["sort_by"] = config["query"]["sort_by"].value
        config["query"]["sort_order"] = config["query"]["sort_order"].value
        with open("config.json", "w") as configFile: json.dump(config, configFile, indent=2)

    #
    #  Watcher commands
    #

    @arxiv.group(name="watcher", help="manage the tracking of an arxiv category")
    async def watcher(self, ctx):
        if ctx.invoked_subcommand is None: await ctx.send('please use a subcommand', delete_after=10)

    @watcher.command(name="list", help="Add channel as a publishing entry for a given category", aliases=["l", "ls"])
    async def list_command(self, ctx):
        categories = list(map(lambda x: x["category"],
                              filter(lambda x: x["channel"] == ctx.channel.id, self._config["watch"]["publish_list"])))

        if len(categories) <= 0: message = "This channel has no categories set for the watcher."
        else: message = f"The categories watched in this channel are: {categories}."
        message += " You can find the available categories on the ArXiV website: https://arxiv.org/category_taxonomy."

        await ctx.send(message)

    @watcher.command(name="add", help="Add channel as a publishing entry for a given category", aliases=["init", "watch"])
    async def add_command(self, ctx, category):
        # TODO: check if category available

        channel = ctx.channel.id
        # check if is not already registered
        for p in self._config["watch"]["publish_list"]:
            if p["category"] == category and p["channel"] == channel:
                return await ctx.send(f"category {category} already added.")
        # create config
        save_file = os.path.join(self._config["watch"]["save_dir"], f"{category}.{channel}.pkl")
        self._config["watch"]["publish_list"].append({
            "category": category,
            "channel": channel,
            "active": True,
            "save_file": save_file
        })

        # create empty list for seen papers
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        with open(save_file, "wb") as saveFile: pickle.dump([], saveFile)

        # save config
        self._save_config()

        await ctx.send(f"Category {category} successfully added !")

    @watcher.command(name="remove", help="Remove category from the publishing list",
                     aliases=["delete", "del", "suppr"])
    async def remove_command(self, ctx, category):
        # remove config config
        channel = ctx.channel.id
        config = []
        for p in self._config["watch"]["publish_list"]:
            if p["category"] == category and p["channel"] == channel:
                # remove cache
                try: os.remove(p["save_file"])
                except BaseException: pass
            else: config.append(p)

        # save config
        self._config["watch"]["publish_list"] = config
        self._save_config()

        await ctx.send(f"Category {category} successfully removed !")

    async def watch_new_papers(self):
        while not self.bot.is_closed():
            config = self._config["watch"]

            for x in config["publish_list"]:
                if not x["active"]: continue

                # load previous publish_list data
                with open(x["save_file"], "rb") as savedPapers:
                    old_papers = pickle.load(savedPapers)

                # look for new papers in a given category
                search = arxiv.Search(query=x["category"], max_results=config["max_results"], sort_by=SortCriterion.SubmittedDate)
                new_papers = [r for r in search.results() if r.get_short_id() not in old_papers]
                new_papers = new_papers[-config["cooldown"]:]

                # post new papers into the right channel (keep chronology)
                channel = self.bot.get_channel(x["channel"])
                if channel is None:
                    # may be a dm channel
                    channel = DMChannel._from_message(channel_id=x["channel"], state=self.bot._connection)

                for paper in new_papers[::-1]:
                    # create embed
                    embed = Embed(
                        title=paper.title,
                        description=self._format_message(paper.summary),
                        url=paper.entry_id,
                        color=0xFF5733
                    )
                    embed.set_author(name=self._format_authors(paper))
                    embed.set_footer(text=f"{x['category']} published on {paper.published}")

                    await channel.send(embed=embed)

                # save new paper list (up to "max_results" items)
                new_papers = list(map(lambda p: p.get_short_id(), new_papers))
                with open(x["save_file"], "wb") as savedPapers:
                    pickle.dump((new_papers + old_papers)[:config["max_results"]], savedPapers)

            await asyncio.sleep(config["sleep_time"])


# entry point for bot's load_extension method
async def setup(bot): await bot.add_cog(Arxiv(bot))
