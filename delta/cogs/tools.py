import asyncpg, shazamio, datetime
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType, CommandOnCooldown
import discord
from shazamio import Shazam, Serialize
from difflib import SequenceMatcher
import ffprobe
import datetime
import humanize
import humanfriendly
import dateutil.parser

class tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hit_cooldown = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)

    async def get_flavors(self):
        return [
            "watermelon",
            "blueberry sour raspberry",
            "strawberry raspberry cherry ice",
            "blueberry sour raspberry",
            "cherry",
            "blue razz lemonade",
            "cherry cola",
            "pink lemonade",
            "tropical",
            "fruit punch",
            "peach mango",
            "mango",
            "apple",
            "banana",
            "delta",
            "legal cocaine"
        ]

    async def get_user_flavor(self, user_id):
        async with self.bot.db.acquire() as conn:
            flavor = await conn.fetchval("SELECT flavor FROM vape_users WHERE user_id = $1", user_id)
            return flavor

    async def set_user_flavor(self, user_id, flavor):
        async with self.bot.db.acquire() as conn:
            await conn.execute(
                "INSERT INTO vape_users (user_id, flavor) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET flavor = $2",
                user_id, flavor
            )

    async def get_user_count(self, user_id, flavor):
        async with self.bot.db.acquire() as conn:
            count = await conn.fetchval("SELECT count FROM vape_counts WHERE user_id = $1 AND flavor = $2", user_id, flavor)
            return count if count is not None else 0

    async def increment_user_count(self, user_id, flavor):
        async with self.bot.db.acquire() as conn:
            await conn.execute(
                "INSERT INTO vape_counts (user_id, flavor, count) VALUES ($1, $2, 1) ON CONFLICT (user_id, flavor) DO UPDATE SET count = vape_counts.count + 1",
                user_id, flavor
            )

    async def get_user_stats(self, user_id):
        async with self.bot.db.acquire() as conn:
            stats = await conn.fetch("SELECT flavor, count FROM vape_counts WHERE user_id = $1", user_id)
            return {row['flavor']: row['count'] for row in stats}


    @commands.hybrid_command(help="utility",aliases=["fnshop"])
    async def fortniteshop(self, ctx):
        """
        Get the fortnite item shop for today
        """

        now = datetime.datetime.now()
        url = f"https://bot.fnbr.co/shop-image/fnbr-shop-{now.day}-{now.month}-{now.year}.png"
        embed = discord.Embed(color=self.bot.color, title="", description="")
        embed.set_image(url=url)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(help="utility", descriprion="get a track name from sound")
    async def shazam(self, ctx):
        if not ctx.message.attachments: return await ctx.send_warning("Please provide a video")
        song = await Shazam().recognize_song(await ctx.message.attachments[0].read())
        embed = discord.Embed(color=self.bot.color, title="Found", description=f"> **[{song['track']['share']['text']}]({song['track']['share']['href']})**")
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await ctx.reply(embed=embed)
    
    @commands.group(help="roleplay", invoke_without_command=True)
    async def vape(self, ctx):
     return await ctx.create_pages() 

    @vape.command(name="flavour", aliases=["flavor"])
    async def set_flavour(self, ctx, *, chosen_flavor: str = None):
        flavors = await self.get_flavors()

        if not chosen_flavor:
            flavor_list = "\n".join(f"> {flavor}" for flavor in flavors)
            embed = discord.Embed(
            description=f"To select a flavour, please use `{ctx.clean_prefix}vape flavour <option>` (e.g {ctx.clean_prefix}vape flavour watermelon)\n\n" + flavor_list,
            color=self.bot.color
        )
            await ctx.send(embed=embed)
            return

        chosen_flavor = chosen_flavor.lower()

        if chosen_flavor not in flavors:
            await ctx.send_warning(f"Invalid flavor, please choose from the available options.")
            return

        await self.set_user_flavor(ctx.author.id, chosen_flavor)
        await ctx.send_success(f"Flavor set to `{chosen_flavor}`")

    @vape.command(name="hit")
    async def vape_hit(self, ctx):
        user_id = ctx.author.id
        flavor = await self.get_user_flavor(user_id)

        if not flavor:
            await ctx.send_warning(f"You need to set a flavor first using the `{ctx.clean_prefix}flavour` command.")
            return

        bucket = self.hit_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        
        if retry_after:
            await ctx.send_warning(f"relax you fucking addict, you can take another hit in **{retry_after:.2f}** seconds")
            return

        count = await self.get_user_count(user_id, flavor)
        await self.increment_user_count(user_id, flavor)

        await ctx.send_success(f"You took a hit of your **{flavor}** flavoured vape, you've hit this vape a total of **{count + 1}** times")

    @vape_hit.error
    async def vape_hit_error(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            await ctx.send_warning("relax you fucking addict, you can take another hit in **{:.2f}** seconds.".format(error.retry_after))
        else:
            raise error
        
    @vape.command(name="stats")
    async def vape_stats(self, ctx):
        user_id = ctx.author.id
        flavor = await self.get_user_flavor(user_id)

        if not flavor:
            await ctx.send_warning(f"You need to set a flavor first using the `{ctx.clean_prefix}flavour` command.")
            return

        stats = await self.get_user_stats(user_id)
    
        if not stats:
            await ctx.send_warning("You haven't hit your vape yet.")
            return

        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Vape Stats", color=self.bot.color)
        for flavor, count in sorted_stats:
            embed.add_field(name=flavor.capitalize(), value=f"Hit Count: {count}", inline=False)

        await ctx.send(embed=embed)

    @vape.command(name="top", aliases=["addicts"])
    async def vape_leaderboard(self, ctx):
        async with self.bot.db.acquire() as conn:
            query = """
            SELECT user_id, SUM(count) AS total_hits
            FROM vape_counts
            GROUP BY user_id
            ORDER BY total_hits DESC
            LIMIT 10
            """
            leaderboard_data = await conn.fetch(query)

            if not leaderboard_data:
                await ctx.send_warning("No vape data found for the leaderboard.")
                return

            description = "\n".join(
            f"`{index}.` **{self.bot.get_user(entry['user_id']).name if self.bot.get_user(entry['user_id']) else 'id: ' + str(entry['user_id'])}** - `{entry['total_hits']}` hits"
            for index, entry in enumerate(leaderboard_data, start=1)
            )

            embed = discord.Embed(title="global vape addicts", description=description, color=self.bot.color)

            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(tools(bot))   