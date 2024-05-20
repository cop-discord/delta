import typing, sys, os, time, discord, asyncpg, aiohttp, random, string, asyncio, datetime, typing
from discord.ext import commands
from discord.gateway import DiscordWebSocket
from tools.utils import StartUp, create_db_pool
from tools.ext import Client, HTTP
from humanfriendly import format_timespan
from typing import List 
from tools.utils import PaginatorView
from io import BytesIO
from discord import CustomActivity, MessageReference

def generate_key():
  return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"

async def getprefix(bot, message):
       if not message.guild: return "*"
       check = await bot.db.fetchrow("SELECT * FROM selfprefix WHERE user_id = $1", message.author.id) 
       if check: selfprefix = check["prefix"]
       res = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id = $1", message.guild.id) 
       if res: guildprefix = res["prefix"]
       else: guildprefix = "*"    
       if not check and res: selfprefix = res["prefix"]
       elif not check and not res: selfprefix = "*"
       return guildprefix, selfprefix 

intents=discord.Intents.all()
intents.presences = False

async def checkthekey(key: str):
  check = await bot.db.fetchrow("SELECT * FROM cmderror WHERE code = $1", key)
  if check: 
    newkey = await generate_key(key)
    return await checkthekey(newkey)
  return key  


class deltacontext(commands.Context): 
 def __init__(self, **kwargs): 
  super().__init__(**kwargs) 

 def find_role(self, name: str): 
   for role in self.guild.roles:
    if role.name == "@everyone": continue  
    if name.lower() in role.name.lower(): return role 
   return None

 async def send_success(self, message: str) -> discord.Message:  
  return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"> {self.bot.yes} {self.author.mention}: {message}") )
 
 async def send_error(self, message: str) -> discord.Message: 
  return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"> {self.bot.no} {self.author.mention}: {message}") ) 
 
 async def send_warning(self, message: str) -> discord.Message: 
  return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"> {self.bot.warning} {self.author.mention}: {message}") )

 async def paginator(self, embeds: List[discord.Embed]):
  if len(embeds) == 1: return await self.send(embed=embeds[0]) 
  view = PaginatorView(self, embeds)
  view.message = await self.reply(embed=embeds[0], view=view) 
 
 async def cmdhelp(self): 
    command = self.command
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    if command.cog_name == "owner": return
    embed = discord.Embed(color=bot.color, title=commandname, description=command.description)
    embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
    embed.add_field(name="category", value=command.help)
    embed.add_field(name="aliases", value=', '.join(map(str, command.aliases)) or "none")
    embed.add_field(name="permissions", value=command.brief or "any")
    embed.add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False)
    await self.reply(embed=embed)

 async def create_pages(self): 
  embeds = []
  i=0
  for command in self.command.commands: 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    i+=1 
    embeds.append(discord.Embed(color=bot.color, title=f"{commandname}", description=command.description).set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url).add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False).set_footer(text=f"delta ^-^・aliases: {', '.join(a for a in command.aliases) if len(command.aliases) > 0 else 'none'} ・ {i}/{len(self.command.commands)}・module: {command.help}", icon_url="https://cdn.discordapp.com/attachments/1234941491646828608/1239942120333250600/Blackstar.png?ex=6644c196&is=66437016&hm=4cedd2340ec853bbc8923a90905f461881b816024037643776d93af1eee5ad7b&"))
     
  return await self.paginator(embeds)  

class HelpCommand(commands.HelpCommand):
  def __init__(self, **kwargs):
   self.categories = {
      "home": "return to the main page", 
      "info": "view information about the bot", 
      "moderation": "keep your server safe", 
      "antiraid": "protect your server against raids",
      "automod": "doing the mod's job",
      "antinuke": "protect your server againt unfaithful admins",
      "emoji": "manage the emojis in your server",
      "utility": "most commands are here...",
      "config": "configure your server",
      "lastfm": "lastfm integration with the bot",
      "fun": "commands to use when you are bored",
      "roleplay": "this is self explanatory",
      "donor": "only rich people use these",
      "economy": "play with my money"
      } 
   super().__init__(**kwargs)
  
  async def send_bot_help(self, mapping):
    embed = discord.Embed(color=self.context.bot.color, title="Help menu") 
    embed.add_field(name="help", value="Please use the **dropdown** menu below to view all the bot's commands", inline=False) 
    embed.add_field(name="contact", value="If you need support you can contact us in the [**support server**](https://discord.gg/g4GSSuVu)", inline=False)
    embed.set_author(name=self.context.author.name, icon_url=self.context.author.display_avatar.url)
    embed.set_footer(text=f"command count: {len(set(bot.walk_commands()))}")
    options = []
    for c in self.categories: options.append(discord.SelectOption(label=c, description=self.categories.get(c)))
    select = discord.ui.Select(options=options, placeholder="Select a category")

    async def select_callback(interaction: discord.Interaction): 
     if interaction.user.id != self.context.author.id: return await self.context.bot.ext.send_warning(interaction, "You are not the author of this embed", ephemeral=True)
     if select.values[0] == "home": return await interaction.response.edit_message(embed=embed)
     com = []
     for c in [cm for cm in set(bot.walk_commands()) if cm.help == select.values[0]]:
      if c.parent: 
        if str(c.parent) in com: continue 
        com.append(str(c.parent))
      else: com.append(c.name)  
     e = discord.Embed(color=bot.color, title=f"", description=f">>> command arguments\n```[] - required\n<> - optional```").add_field(name=f"commands {select.values[0]}", value=f"```{', '.join(com)}```", inline=False) .set_author(name=self.context.author.name, icon_url=self.context.author.display_avatar.url)  
     return await interaction.response.edit_message(embed=e)
    select.callback = select_callback

    view = discord.ui.View(timeout=None)
    view.add_item(select) 
    return await self.context.reply(embed=embed, view=view)
  
  async def send_command_help(self, command: commands.Command): 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    if command.cog_name == "owner": return
    embed = discord.Embed(color=bot.color, title=commandname, description=command.description)
    embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
    embed.add_field(name="category", value=command.help)
    embed.add_field(name="aliases", value=', '.join(map(str, command.aliases)) or "none")
    embed.add_field(name="permissions", value=command.brief or "any")
    embed.add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False)
    channel = self.get_destination()
    await channel.send(embed=embed)

  async def send_group_help(self, group: commands.Group): 
   ctx = self.context
   embeds = []
   i=0
   for command in group.commands: 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    i+=1 
    embeds.append(discord.Embed(color=bot.color, title=f"{commandname}", description=command.description).set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url).add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False).set_footer(text=f"aliases: {', '.join(a for a in command.aliases) if len(command.aliases) > 0 else 'none'} ・ {i}/{len(group.commands)}・module: {command.help}", icon_url="https://cdn.discordapp.com/attachments/1201461002848448522/1204450128321319002/luma_yellow.png?ex=65d4c698&is=65c25198&hm=f7606fd5d04d1878e0f28cfeb4821d0c861c939d1fd6372bcf42b5d0eb6e7ac5&"))
     
   return await ctx.paginator(embeds) 

class CommandClient(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.presences = False    
        super().__init__(
            command_prefix=getprefix,
            shard_count=3,
            allowed_mentions=discord.AllowedMentions(roles=False, 
            everyone=False, users=True, replied_user=False), intents=intents, 
            help_command=HelpCommand(), strip_after_prefix=True, 
            #shard_count=1,
            activity=CustomActivity(name="🔗 discord.gg/esext", state="🔗 discord.gg/esext"), 
            owner_ids=[852784127447269396, 1035497951591673917, 797458672225091594]
        )
        self.color = 0xFFFFFF
        self.ext = Client(self) 
        self.yes = "<:approve:1211965458840952862>"
        self.no = "<:wrong:1211967022758494298>"
        self.proxy_url = "http://14a4a94eff770:c3ac0449fd@104.234.255.18:12323"
        self.warning = "<:warn:1208752506407223356>"
        self.left = "<:left:1018156480991612999>"
        self.right = "<:right:1018156484170883154>"
        self.goto = "<:filter:1039235211789078628>"
        self.m_cd=commands.CooldownMapping.from_cooldown(1,5,commands.BucketType.member)
        self.c_cd=commands.CooldownMapping.from_cooldown(1,5,commands.BucketType.channel)
        self.m_cd2=commands.CooldownMapping.from_cooldown(1,10,commands.BucketType.member)
        self.global_cd = commands.CooldownMapping.from_cooldown(2, 3, commands.BucketType.member)
        self.main_guilds = [1198291290178211921]
        self.session_id = "59071245027%3AD0cDcLaxyzVyVQ%3A16%3AAYdIOvL5SM85A62N-zDxn04CaabIDHneyhA6I0r6VQ"
        
        
    async def create_db_pool(self):
      self.db = await asyncpg.create_pool(port="5432", database="postgres", user="postgres.pexxcoqyhdudkxrzxidm", host="aws-0-us-east-1.pooler.supabase.com", password="NoYeCKsg0ivZpgKW")
        
    async def get_context(self, message, *, cls=deltacontext):
     return await super().get_context(message, cls=cls) 

    async def setup_hook(self) -> None:
       print("Attempting to start")
       self.session = HTTP()
       await self.create_db_pool()
       await self.load_extension("jishaku")
       await StartUp.loadcogs(self)
       
       self.loop.create_task(StartUp.startup(self))     
    
    @property
    def lines(self) -> int:
        """
        Return the code's amount of lines
        """

        lines = 0
        for d in [x[0] for x in os.walk("./") if not ".git" in x[0]]:
            for file in os.listdir(d):
                if file.endswith(".py"):
                    lines += len(open(f"{d}/{file}", "r").read().splitlines())

        return lines

    @property
    def ping(self) -> int: 
      return round(bot.latency * 1000)
    
    def convert_datetime(self, date: datetime.datetime=None):
     if date is None: return None  
     month = f'0{date.month}' if date.month < 10 else date.month 
     day = f'0{date.day}' if date.day < 10 else date.day 
     year = date.year 
     minute = f'0{date.minute}' if date.minute < 10 else date.minute 
     if date.hour < 10: 
      hour = f'0{date.hour}'
      meridian = "AM"
     elif date.hour > 12: 
      hour = f'0{date.hour - 12}' if date.hour - 12 < 10 else f"{date.hour - 12}"
      meridian = "PM"
     else: 
      hour = date.hour
      meridian = "PM"  
     return f"{month}/{day}/{year} at {hour}:{minute} {meridian} ({discord.utils.format_dt(date, style='R')})" 

    def ordinal(self, num: int) -> str:
     """Convert from number to ordinal (10 - 10th)""" 
     numb = str(num) 
     if numb.startswith("0"): numb = numb.strip('0')
     if numb in ["11", "12", "13"]: return numb + "th"
     if numb.endswith("1"): return numb + "st"
     elif numb.endswith("2"):  return numb + "nd"
     elif numb.endswith("3"): return numb + "rd"
     else: return numb + "th" 

    async def getbyte(self, video: str):  
      return BytesIO(await self.session.read(video, proxy=self.proxy_url, ssl=False)) 

    def is_dangerous(self, role: discord.Role) -> bool:
     permissions = role.permissions
     return any([
      permissions.kick_members, permissions.ban_members,
      permissions.administrator, permissions.manage_channels,
      permissions.manage_guild, permissions.manage_messages,
      permissions.manage_roles, permissions.manage_webhooks,
      permissions.manage_emojis_and_stickers, permissions.manage_threads,
      permissions.mention_everyone, permissions.moderate_members
     ])
    
    async def prefixes(self, message: discord.Message) -> List[str]: 
     prefixes = []
     for l in set(p for p in await self.command_prefix(self, message)): prefixes.append(l)
     return prefixes

    async def on_message(self, message: discord.Message): 
      channel_rl=await self.channel_ratelimit(message)
      member_rl=await self.member_ratelimit(message)
      if channel_rl == True:
          return
      if member_rl == True:
          return
      if message.content == "<@{}>".format(self.user.id): return await message.reply(content="prefixes: " + " ".join(f"`{g}`" for g in await self.prefixes(message)))
      await bot.process_commands(message) 
    
    async def channel_ratelimit(self,message:discord.Message) -> typing.Optional[int]:
        cd=self.c_cd
        bucket=cd.get_bucket(message)
        return bucket.update_rate_limit()

    async def member_ratelimit(self,message:discord.Message) -> typing.Optional[int]:
        cd=self.m_cd
        bucket=cd.get_bucket(message)
        return bucket.update_rate_limit()
    
    async def on_ready(self):
       await create_db_pool(self) 
       print(f"I bug {self.user} {self.user.id}")
    
    async def on_message_edit(self, before, after):
        if before.content != after.content: await self.process_commands(after)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
      if isinstance(error, commands.CommandNotFound): return 
      elif isinstance(error, commands.NotOwner): pass
      elif isinstance(error, commands.CheckFailure): 
        if isinstance(error, commands.MissingPermissions): return await ctx.send_warning(f"This command requires **{error.missing_permissions[0]}** permission")
      elif isinstance(error, commands.CommandOnCooldown):
        if ctx.command.name != "hit": return await ctx.reply(embed=discord.Embed(color=0xE1C16E, description=f"⌛ {ctx.author.mention}: You are on cooldown. Try again in {format_timespan(error.retry_after)}"), mention_author=False)    
      elif isinstance(error, commands.MissingRequiredArgument): return await ctx.cmdhelp()
      elif isinstance(error, commands.EmojiNotFound): return await ctx.send_warning(f"Unable to convert {error.argument} into an **emoji**")
      elif isinstance(error, commands.MemberNotFound): return await ctx.send_warning(f"Unable to find member **{error.argument}**")
      elif isinstance(error, commands.UserNotFound): return await ctx.send_warning(f"Unable to find user **{error.argument}**")
      elif isinstance(error, commands.RoleNotFound): return await ctx.send_warning(f"Couldn't find role **{error.argument}**")
      elif isinstance(error, commands.ChannelNotFound): return await ctx.send_warning(f"Couldn't find channel **{error.argument}**")
      elif isinstance(error, commands.UserConverter): return await ctx.send_warning(f"Couldn't convert that into an **user** ")
      elif isinstance(error, commands.MemberConverter): return await ctx.send_warning("Couldn't convert that into a **member**")
      elif isinstance(error, commands.BadArgument): return await ctx.send_warning(error.args[0])
      elif isinstance(error, commands.BotMissingPermissions): return await ctx.send_warning(f"I do not have enough **permissions** to execute this command")
      elif isinstance(error, discord.HTTPException): return await ctx.send_warning("Unable to execute this command")      
      else: 
       key = await checkthekey(generate_key())
       trace = str(error)
       rl=await self.member_ratelimit(ctx.message)
       if rl == True:
           return
       await self.db.execute("INSERT INTO cmderror VALUES ($1,$2)", key, trace)
       await self.ext.send_error(ctx, f"**An unexpected error was found with the command. Please report the code `{key}` in our [support server](https://discord.gg/ruDzGSdt2M)**")   


bot = CommandClient()

@bot.check
async def cooldown_check(ctx: commands.Context):
    bucket = bot.global_cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after: raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.member)
    return True

async def mobile(self):
    payload = {'op': self.IDENTIFY,'d': {'token': self.token,'properties': {'$os': sys.platform,'$browser': 'Discord iOS','$device': 'discord.py','$referrer': '','$referring_domain': ''},'compress': True,'large_threshold': 250,'v': 3}}
    if self.shard_id is not None and self.shard_count is not None:
        payload['d']['shard'] = [self.shard_id, self.shard_count]
    state = self._connection
    if state._activity is not None or state._status is not None: 
        payload["d"]["presence"] = {"status": state._status, "game": state._activity, "since": 0, "afk": True}
    if state._intents is not None:
        payload["d"]["intents"] = state._intents.value
    await self.call_hooks("before_identify", self.shard_id, initial=self._initial_identify)
    await self.send_as_json(payload)
discord.gateway.DiscordWebSocket.identify = mobile

async def check_ratelimit(ctx):
    cd=bot.m_cd2.get_bucket(ctx.message)
    return cd.update_rate_limit()

@bot.check 
async def blacklist(ctx: commands.Context): 
 if await ctx.bot.is_owner(ctx.author): return True
 rl=await check_ratelimit(ctx)
 if rl == True: return
 if ctx.guild is None: return False
 check = await bot.db.fetchrow("SELECT * FROM nodata WHERE user_id = $1", ctx.author.id)
 if check is not None: 
  if check["state"] == "false": return False 
  else: return True 
 embed = discord.Embed(color=bot.color, description=f"> **Do you agree to our [privacy policy](https://discord.gg/tYYxapzWvM)?**")
 yes = discord.ui.Button(emoji=bot.yes, style=discord.ButtonStyle.gray)
 no = discord.ui.Button(emoji=bot.no, style=discord.ButtonStyle.gray)
 async def yes_callback(interaction: discord.Interaction): 
    if interaction.user != ctx.author: return await interaction.response.send_message(embed=discord.Embed(color=bot.color, description=f"{bot.warning} {interaction.user.mention}: This is not your message"), ephemeral=True)
    await bot.db.execute("INSERT INTO nodata VALUES ($1,$2)", ctx.author.id, "true")                     
    await interaction.message.delete()
    await bot.process_commands(ctx.message)

 yes.callback = yes_callback

 async def no_callback(interaction: discord.Interaction): 
    if interaction.user != ctx.author: return await interaction.response.send_message(embed=discord.Embed(color=bot.color, description=f"{bot.warning} {interaction.user.mention}: This is not your message"), ephemeral=True)
    await bot.db.execute("INSERT INTO nodata VALUES ($1,$2)", ctx.author.id, "false")                        
    await interaction.response.edit_message(embed=discord.Embed(color=bot.color, description=f"You got blacklisted from using bot's commands. If this is a mistake, please contact our [**support server**](https://discord.gg/tYYxapzWvM) to find more"), view=None)
    return 

 no.callback = no_callback

 view = discord.ui.View()
 view.add_item(yes)
 view.add_item(no)
 await ctx.reply(embed=embed, view=view, mention_author=False)   

@bot.check
async def is_chunked(ctx: commands.Context):
  if ctx.guild: 
    if not ctx.guild.chunked: await ctx.guild.chunk(cache=True)
    return True

@bot.check
async def disabled_command(ctx: commands.Context):
  cmd = bot.get_command(ctx.invoked_with)
  if not cmd: return True
  check = await ctx.bot.db.fetchrow('SELECT * FROM disablecommand WHERE command = $1 AND guild_id = $2', cmd.name, ctx.guild.id)
  if check: await bot.ext.send_warning(ctx, f"The command **{cmd.name}** is **disabled**")     
  return check is None    

@bot.event
async def on_guild_join(guild: discord.Guild):
    if guild.owner_id in [965864806265524284, 1074668481867419758, 949395664167653447, 371224177186963460, 1012890560777961535, 853810604842287136, 1132259198256812072, 1122200192981155951, 1022258893117722664]:
        await guild.leave()
    
bot.run("xD")
