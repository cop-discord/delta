import discord
from discord.ext import commands
import aiohttp

class IconCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setpfp(self, ctx, image_url):
            if not ctx.author.id in self.bot.owner_ids: return await ctx.send("nono")
            async with aiohttp.ClientSession() as session:
             async with session.get(image_url) as response:
                try:
                    image_data = await response.read()
                    await self.bot.user.edit(avatar=image_data)
                    await ctx.send("Bot profile picture updated successfully!")
                except Exception as e:
                    await ctx.send(f"An error occurred: {e}")

async def setup(bot) -> None:
    await bot.add_cog(IconCog(bot))   
