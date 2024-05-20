import discord
from discord.ext import commands
from tools.decorator import is_reskin


owners = [994896336040239114, 1107903478451408936]

class Auth(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    """
    @commands.group(invoke_without_command=True)
    async def reskin(self, ctx: commands.Context):
        await ctx.create_pages()
    
    @reskin.command(name="enable", description="enable reskin module in the server", help="donor", aliases=["e"], brief="manage server")
    @Perms.get_perms("administrator")
    async def reskin_enable(self, ctx: commands.Context):
       check = await self.bot.db.fetchrow("SELECT * FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
       if check: return await ctx.send_warning("Reskin is **already** enabled")
       await self.bot.db.execute("INSERT INTO reskin_toggle VALUES ($1)", ctx.guild.id)
       return await ctx.message.add_reaction("👍🏻")
    
    @reskin.command(name="disable", description="disable reskin module in the server", help="donor", aliases=["d"], brief="manage server")
    @Perms.get_perms("administrator")
    async def reskin_disable(self, ctx: commands.Context):
       check = await self.bot.db.fetchrow("SELECT * FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
       if not check: return await ctx.send_warning("Reskin is **not** enabled")
       await self.bot.db.execute("DELETE FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
       return await ctx.send_success("Reskin has been **disabled**")
    
    @reskin.command(description="edit your reskin name", name="name", usage="[name]", help="donor", brief="donor")
    @is_reskin()
    async def reskin_name(self, ctx: commands.Context, *, name: str):
       check = await self.bot.db.fetchrow("SELECT * FROM reskin WHERE user_id = $1", ctx.author.id)
       if not check: await self.bot.db.execute("INSERT INTO reskin VALUES ($1,$2,$3)", ctx.author.id, name, self.bot.user.avatar.url)
       await self.bot.db.execute("UPDATE reskin SET name = $1 WHERE user_id = $2", name, ctx.author.id)
       return await ctx.send_success(f"Reskin name set to **{name}**")
    
    @reskin.command(description="edit your reskin avatar", name="avatar", usage="[url]", aliases=["av"], help="donor", brief="donor")
    @is_reskin()
    async def reskin_avatar(self, ctx: commands.Context, *, url: str):
       if not url: return await ctx.send_warning("This is not an image")
       await self.bot.db.execute("UPDATE reskin SET avatar = $1 WHERE user_id = $2", url, ctx.author.id)
       return await ctx.send_success("Set your reskin avatar")
    
    @reskin.command(description="delete your reskin", name="delete", help="donor", brief="donor")
    async def reskin_delete(self, ctx: commands.Context):
       check = await self.bot.db.fetchrow("SELECT * FROM reskin WHERE user_id = $1", ctx.author.id)
       if not check: return await ctx.send_warning("You don't have a reskin set")
       await self.bot.db.execute("DELETE FROM reskin WHERE user_id = $1", ctx.author.id)
       return await ctx.send_success("Your reskin has been deleted")
    """
async def setup(bot):
    await bot.add_cog(Auth(bot))