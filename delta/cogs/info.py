import discord, random
from discord.ext import commands
from discord.ui import View, Button

class info(commands.Cog):
   def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot        

   
   @commands.hybrid_command(aliases=(["bi"]), description="check bot info", help="info")
   async def botinfo(self, ctx):
    embed = discord.Embed(color=self.bot.color, title="delta 2.1.1", description="A bot created by **marian** running on `discord.py`\nYou can press here **[invite link](https://discordapp.com/oauth2/authorize?client_id=1079453080191512576&scope=bot+applications.commands&permissions=8)**").add_field(name="System & Info", value=f">>> Lines: **{self.bot.lines:,}**\nPing: **{self.bot.ping}**\nMembers: **{sum(g.member_count for g in self.bot.guilds):,}**\nServers: **{len(self.bot.guilds):,}**")
    await ctx.reply(embed=embed)
    
   @commands.hybrid_command(description="check bot connection", help="info")
   async def ping(self, ctx):
    await ctx.reply(f"....pong 🏓 `{self.bot.ping}ms`")

   @commands.hybrid_command(description="invite the bot", help="info", aliases=["support", "inv"])
   async def invite(self, ctx):
    avatar_url = self.bot.user.avatar.url
    embed = discord.Embed(color=self.bot.color, description="Add the bot in your server!")
    embed.set_author(name=self.bot.user.name, icon_url=f"{avatar_url}")
    button1 = Button(label="invite", url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands")
    button2 = Button(label="support", url="https://discord.gg/vvdTdmaebh")
    view = View()
    view.add_item(button1)
    view.add_item(button2)
    await ctx.reply(embed=embed, view=view)

async def setup(bot) -> None:
    await bot.add_cog(info(bot))      
