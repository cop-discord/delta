import discord, random, string, os, requests
from discord.ext import commands 
from tools.checks import Perms, Mod
from tools.utils import EmbedBuilder


def is_detention(): 
 async def predicate(ctx: commands.Context): 
  check = await ctx.bot.db.fetchrow("SELECT * FROM naughtycorner WHERE guild_id = $1", ctx.guild.id)
  if not check: await ctx.send_warning("Naughty corner is not configured")
  return check is not None 
 return commands.check(predicate)
 
class Misc(commands.Cog):
  def __init__(self, bot: commands.AutoShardedBot): 
    self.bot = bot     
    
  @commands.Cog.listener()
  async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState): 
   naughty = await self.bot.db.fetchrow("SELECT * FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2", member.guild.id, member.id)
   if naughty: 
     check = await self.bot.db.fetchrow("SELECT * FROM naughtycorner WHERE guild_id = $1", member.guild.id)
     if check:
      channel = member.guild.get_channel(int(check['channel_id']))      
      if after.channel.id != channel.id: await member.move_to(channel=channel, reason=f"Moved to the naughty corner")
  
  @commands.group(aliases=['detention', 'nc'], invoke_without_command=True)
  async def naughtycorner(self, ctx: commands.Context, *, member: discord.Member=None): 
   if member is None: return await ctx.create_pages()
   return await ctx.invoke(self.bot.get_command('naughtycorner add'), member=member)

  @naughtycorner.command(help="config", aliases=['configure', 'set'], brief="manage server", usage="[voice channel]", name="setup", description="configure naughty corner voice channel")
  @Perms.get_perms("manage_guild")
  async def nc_setup(self, ctx: commands.Context, *, channel: discord.VoiceChannel): 
   check = await self.bot.db.fetchrow("SELECT * FROM naughtycorner WHERE guild_id = $1", ctx.guild.id)
   if check: await self.bot.db.execute("UPDATE naughtycorner SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id) 
   else: await self.bot.db.execute("INSERT INTO naughtycorner VALUES ($1,$2)", ctx.guild.id, channel.id)
   return await ctx.send_success(f"Naughty corner voice channel configured -> {channel.mention}")

  @naughtycorner.command(help="config", name="unsetup", brief="manage server", description="disable naughty corner feature in the server") 
  @Perms.get_perms('manage_guild')
  @is_detention()
  async def nc_unsetup(self, ctx: commands.Context): 
   await self.bot.db.execute('DELETE FROM naughtycorner WHERE guild_id = $1', ctx.guild.id)
   return await ctx.send_success("Naughty corner is now disabled")
  
  @naughtycorner.command(help="config", name="add", brief="timeout members", description="add a member to the naughty corner", usage="[member]")
  @Perms.get_perms('moderate_members')
  @is_detention()
  async def nc_add(self, ctx: commands.Context, *, member: discord.Member): 
   if await Mod.check_hieracy(ctx, member): 
    check = await self.bot.db.fetchrow("SELECT * FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
    if check: return await ctx.send_warning("This member is **already** in the naughty corner")
    await self.bot.db.execute("INSERT INTO naughtycorner_members VALUES ($1,$2)", ctx.guild.id, member.id)
    res = await self.bot.db.fetchrow("SELECT channel_id FROM naughtycorner WHERE guild_id = $1", ctx.guild.id)
    channel = ctx.guild.get_channel(int(res['channel_id']))
    await member.move_to(channel=channel, reason=f"Moved to the naughty corner by {ctx.author}")
    return await ctx.send_success(f"Moved **{member}** to {channel.mention if channel else '**Naughty Corner**'}") 
  
  @naughtycorner.command(help="config", name="remove", brief="timeout emmbers", description="remove a member from the naughty corner", usage="[member]")
  @Perms.get_perms('moderate_members')
  @is_detention()
  async def nc_remove(self, ctx: commands.Context, *, member: discord.Member): 
   if await Mod.check_hieracy(ctx, member): 
    check = await self.bot.db.fetchrow("SELECT * FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
    if not check: return await ctx.send_warning("This member is **not** in the naughty corner")
    await self.bot.db.execute("DELETE FROM naughtycorner_members WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
    return await ctx.send_success(f"Removed **{member}** from **Naughty Corner**") 
  
  @naughtycorner.command(help="config", name="members", aliases=['list'], description="returns members from the naughty corner")
  @is_detention()
  async def nc_list(self, ctx: commands.Context): 
   results = await self.bot.db.fetch("SELECT user_id FROM naughtycorner_members WHERE guild_id = $1", ctx.guild.id)
   if len(results) == 0: return await ctx.send_warning("There are no **naughty** members in this server")
   i=0
   k=1
   l=0
   mes = ""
   number = []
   messages = []
   for result in results:     
     mes = f"{mes}`{k}` <@!{result['user_id']}>\n"
     k+=1
     l+=1
     if l == 10:
       messages.append(mes)
       number.append(discord.Embed(color=self.bot.color, title=f"naughty members in {ctx.guild.name} ({len(results)})", description=messages[i]))
       i+=1
       mes = ""
       l=0
    
   messages.append(mes)
   number.append(discord.Embed(color=self.bot.color, title=f"naughty members in {ctx.guild.name} ({len(results)})", description=messages[i]))
   await ctx.paginator(number)  

async def setup(bot: commands.AutoShardedBot) -> None:
  await bot.add_cog(Misc(bot))       