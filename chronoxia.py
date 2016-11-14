#Imports Required for this Project

import asyncio
import os
import time
import sys
import logging
import logging.handlers
import shutil
import traceback

# Error check to attempt to import Discord and Discord.ext. If Discord.PY is not installed then,
# return error
try:
    from discord.ext import commands
    import discord
except ImportError:
    print("Discord.py is not installed.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n"
          "https://lsomers984.github.io/ChrSono-Docs/\n")
    sys.exit()

from cogs.utils.settings import Settings
from cogs.utils.dataIO import dataIO
from cogs.utils.chat_formatting import inline

#
#       Chronoxia - A Multifunctional Discord Bot based on Discord.py and its extensions
#       https://github.com/lsomers984/Chronoxia---Final-Year-Project
#
#       cogs/utils/checks.py both contain some modified functions originally made by Rapptz
#             https://github.com/Rapptz/RoboDanny/tree/async

description = " Chronoxia - A Multifunctional Discord Bot by L. Somers"

# Format Class: TBC
class Format(commands.HelpFormatter):
    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)

    def _add_subcommands_to_page(self, max_width, commands):
        for name, command in sorted(commands, key=lambda t: t[0]):
            if name in command.aliases:
                # skip aliases
                continue

            entry = ' {0:<{width}} {1}'.format(name, command.short_doc, width=max_width)
            shortened = self.shorten(entry)
            self._paginator.add_line(shortened)

format = Format(show_check_failure=False)

bot = commands.Bot(command_prefix=["_"], format=format, description=description, pm_help=None)

settings = Settings()

#   Bot Event - On Ready do the following:
#   1) Load Owner Module
#   2) Show Total Number of Modules Loaded, Number of Users and Servers and Channels the Bot can access
#   3) Start the Uptime Command counter

@bot.event
async def on_ready():
    owner_cog = bot.get_cog('Owner')
    total_cogs = len(owner_cog._list_cogs())
    users = len(set(bot.get_all_members()))
    servers = len(bot.servers)
    channels = len( [c for c in bot.get_all_channels()] )
    if not hasattr(bot, "uptime"):
        bot.uptime = int(time.perf_counter())
    if settings.login_type == "token" and settings.owner == "ID_Here":
        await set_bot_owner()
    print('------')
    print("{} is now online.".format(bot.user_name))
    print('------')
    print("Bot Connection Information: ")
    print("Number of Servers: {}".format(servers))
    print("Number of Channels: {}".format(channels))
    print("Number of Users: {}".format(users))
    print("\n{}/{} active modules with {} commands".format(len(bot.cogs), total_modules, len(bot.commands)))
    prefix_label = "Prefixes:" \
        if len(bot.command_prefix) > 1 else "Prefix:"
        print("{} {}\n".format(prefix_label, " ".join(bot.command_prefix)))
    if settings.login_type == "token":
        print('------')
        print("Use the following API URL to bring this bot to your server: ")
        url = await get_oauth_url()
        bot.ouath_url = url
        print(url)
        print('------')
    await bot.get_cog('Owner').disable_commands()

#   Bot Event: on_command
@bot.event
async def on_command(command, ctx):
    pass

#   Bot Event: on_message
async def on_message(message):
    if user_allowed(message):
        await bot.process_commands(message)

#   Bot Event: On_Command_Error
@bot.event
async def on_command_error(error, ctx):
    channel = ctx.message.channel
    if isinstance(error, commands.MissingRequiredArguement):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.BadArguement):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(channel, "That command has been disabled by the owner :crying_cat_face: ")
    elif isinstance(error, commands.CommandInvokeError):
        logger.exception("Exception in command '{}'".format(ctx.command.qualified_name), exc_info=error.original)
        oneliner = "Error in command '{}' - {}:{}".format(ctx.command.qualified_name, type(error.original).__name__, str(error.original))
        await ctx.bot.send_message(channel, inline(oneliner))
    elif isinstance(error. commands.CommandNotFound):
        pass
    elif isinstance(error, commands.CheckFailure):
        pass
    elif isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(channel, "That command is not available in Direct/Private Messages :cring_cat_face:")
    else:
        logger.exception(type(error).__name__, exc_info=error)

#   Async Definition: send_command_help
async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        pages = bot.format.format_help_for(ctx, ctx.invoked_subcommand)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)

#   Definition: user_allowed
def user_allowed(message):
    author = message.author
    if author.bot or author == bot.user:
        return False
    mod = bot.get_cog('Mod')

    if mod is not None:
        if settings.owner == author.id:
            return True
        if not message.channel.is_private:
            server = message.server
            names = (settings.get_server_admin(server), settings.get_server_mod(server))
            results = map(lambda name: discord.utils.get(author.roles, name=name), names)
            for r in results:
                if r is not None:
                    return True

        if author.id in mod.blacklist_list:
            return False
        if mod.whitelist_list:
            if author.id not in mod.whitelist_list:
                return False

        if not message.channel.is_private:
            if message.server.id in mod.ignore_list["SERVERS"]:
                return False

            if message.channel.id in mod.ignore_list["CHANNELS"]:
                return False
        return True
    else:
        return True

#   Async Definitions for Discord API Communication. Getting the Authorization URL and Bot Owner Info
async def get_oauth_url():
    try:
        data = await bot.application_info()
    except Exception as e:
        return "Could Not Retrieve Invite Link :crying_cat_face:. Error: {}".format(e)
    return discord.utils.oauth_url(data.id)

async def set_bot_owner():
    try:
        data = await bot.application_info()
        settings.owner = data.owner.id
    except Exception as e:
        print("Could Not Retrive Owner ID :crying_cat_face:. Error: {}".format(e))
        return
    print("{} has been recognised as the owner of this bot by the Discord API :smile_cat:".format(data.owner_name))

#   Definition: check_folders - Are the folders set up correctly?
def check_folders():
    folders = ("data", "data/chronoxia", "cogs", "cogs/utils")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + "folder. Please Wait...")
            os.makedirs(folder)

#   Definition: check_configs - Are the Configs for the Bot Set Up?
def check_configs():
    if settings.bot_settings == settings.default_settings:
        print("Chronoxia - First Run Only Configuration")
        print('------')
        print("If you haven't already, I strongly advise\n"
              "you create a new account: https://lsomers984.github.io/Chrono-Docs/")
        print("Also, Obtain the token for your bot like described on that page :) ")
        print("\nPlease insert your bot's token now and press Enter: ")

        choice = input("> ")

        if "@" not in choice and len(choice) >= 50: #Assuming that they use a token
            settings.login_type = "token"
            settings.email = choice
        elif "@" in choice: #Assuming Email Login
            settings.login_type = "email"
            settings.email = choice
            settings.password = input("\nPassword> ")
        else:
            os.remove('data/chronoxia/settings.json')
            input("Invalid Input. Please Restart Chronoxoia and repeat the First Time Run Process")
            exit(1)

        print("\nPlease Choose a prefix. A prefix is what you type before a command.\n"
              "Typical Prefixes include: Exclamation Mark (!), Hashtag (#), Tilde(~)\n"
              "It can be multiple characters. You will be able to change it later and\n"
              "add more of them. \n Please enter your prefix and press enter: ")
        confirmation = False
        while confirmation is False:
            new_prefix = ensure_reply("\nPrefix> ").strip()
            print("\nAre you sure you want {0} as your prefix?\nYou "
                  "will be able to issue commands like this: {0}help"
                  "\nType yes to confirm or no to change it".format(new_prefix))
            confirmation = get_answer()

            settings.prefixes = [new_prefix]
            if settings.login_type == "email":
                print("\nOnce you're done with the configuration, you will have to type "
                      "'{}set owner' *in Discord's chat*\nto set yourself as owner.\n"
                      "Press enter to continue".format(new_prefix))
                settings.owner = input("") # Shh, this was never here ;)
                if settings.owner == "":
                    settings.owner = "id_here"
                if not settings.owner.isdigit() or len(settings.owner) < 17:
                    if settings.owner != "id_here":
                        print("\nERROR: What you entered is not a valid ID. Set "
                              "yourself as owner later with {}set owner".format(new_prefix))
                    settings.owner = "id_here"
            else:
                settings.owner = "id_here"

            print("\n Set the name of the Administrator Role. Anyone with this role will be "
                  "able to use the bots Administator Commands")
            print("Leave it Blank for it to use the Default Role: Discord General Manager")
            settings.default_admin = input("\nAdmin Role> ")
            if settings.default_admin == "":
                settings.default_admin = "Discord General Manager"

        print("\n Set the name of the Moderators Role. Anyone with this role will be"
              "able to use the bots Moderator Commands")
        print("Leave it Blank for it to use the Default Role: Moderator")
        settings.default_mod = input("\nMod Role> ")
        if settings.default_mod == "":
            settings.default_mod = "Moderator"

        print("\n Configuration Complete. Leave this window open to keep "
              "Chronoxia Online.\n All Commands will have to be issues through "
              "Discord's chat, *NOTE: This window will now be read-only*. \n"
              "Please Hit Enter to Continue:)")
        input("\n")

    if not os.path.isfile("data/chronoxia/cogs.json"):
        print("Creating new modules.json. PLease Wait...")
        dataIO.save_json("data/chronoxia/cogs.json", {})

#   Definition - Set Logger
def set_logger():
    global logger
    logger = logging.getLogger("discord")
    logger.setLevel(logger.WARNING)
    handler = logging.FileHandler(filename='data/chronoxia/discord.log', encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]"))
    logger.addHandler(handler)

    logger = logging.getLogger("chronoxia")
    logger.setLevel(logging.INFO)

    chrono_format =  logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(chrono_format)
    stdout_handler.setLevel(logging.INFO)

    fhandler = logging.handlers.RotatingFileHandler(
        filename='data/chronoxia/chrono.log', encoding='utf-8', mode='a',
        maxBytes=10**7, backupCount=5)
    fhandler.setFormatter(chrono_format)

    logger.addHandler(fhandler)
    logger.addHandler(stdout_handler)

#   Definition - Ensure Reply and Get Answer
def ensure_reply(msg):
    choice = ""
    while choice == "":
        choice = input(msg)
    return choice

def get_answer():
    choices = ("yes", "y", "no", "n")
    c = ""
    while c not in choices:
        c = input(">").lower()
    if c.startswith("y"):
        return True
    else:
        return False

#   Definition - Set and Load Cogs - IMPORTANT
def set_cog(cog,value):
    data = dataIO.load_json("data/chronoxia/cogs.json")
    data[cog] = value
    dataIO.save_json("data/chronoxia/cogs.json", data)

def load_cogs():
    try:
        if sys.argv[1] == "--no-prompt":
            no_prompt = True
        else:
            no_prompt = False
    except:
        no_prompt = False

    try:
        registry = dataIO.load_json("data/chronoxia/cogs.json")
    except:
        registry = {}

    bot.load_extension('cogs.owner')
    owner_cog = bot.get_cog('Owner')
    if owner_cog is None: #Assuming the user deleted the Owner Cog
        print("You got rid of owner.py!!! It had functions that I need"
              "to run special events :( I can not operate without it!!")
        print()
        print("Please go download it from:\n"
              "https://github.com/lsomers984/Chronoxia---Final-Year-Project")
        exit(1)

        failed = []
        extensions = owner_cog._list_cogs()
        for extension in extensions:
            if extension.lower() == "cogs,owner":
                continue
            in_reg = extension in registry
            if in_reg is False:
                if no_prompt is True:
                    registry[extension] = False
                    continue
                print("\n New Extension: {}".format(extension))
                print("Do you wish to load it?(y/n)")
                if not get_answer():
                    registry[extension] = False
                    continue
                registry[extension] = True
            if not registry[extension]:
                continue
            try:
                owner_cog._load_cog(extension)
            except Exception as e:
                print("{}: {}".format(e.__class__.__name__, str(e)))
                logger.exception(e)
                failed.append(extension)
                registry[extension] = False

        if extensions:
            dataIO.save_json("data/chronoxia/cogs.json", registry)

        if failed:
            print("\nFailed to Load: ", end="")
            for m in failed:
                print(m + "", end="")
            print("\n")

        return owner_cog

#   Definition - main()
def main():
    global settings

    check_folders()
    check_configs()
    set_logger()
    owner_cog = load_cogs()
    if settings.prefixes != []:
        bot.command_prefix = settings.prefixes
    else:
        print("No Prefix was set. Falling to Default: Exclaimation Point [!]")
        bot.command_prefix = ["!"]
        if settings.owner != "id_here":
            print("Please use !set owner to set yourself as owner")
        else:
            print("Once you are owner, Please use !set prefix to set command prefixes")

    if settings.owner == "id_here" and settings.login_type == "email":
        print("My Owner has not been set :(. Do '{}set owner' in chat to set"
              "yourself as owner.".format(bot.command_prefix[0]))
    else:
        owner_cog.owner.hidden = True # Hides the command {}set owner from view in {}help
    print("--- Logging In... ---")
    if os.name == "nt" and os.path.isfile("update.bat"): # Check for Windows and File called Update.bat
        print("Please use update.bat to keep me updated :D")
    else:
        print("Please ensure that you keep me updated by doing: git pull")
        print("Also please keep Discord.PY Up to Date - pip3 install -U git+https://github.com/Rapptz/"
              "discord.py@master#egg=discord.py[voice]")
    print("Support Server: Coming soon!")
    if settings.login_type == "token":
        yield from bot.login(settings.email)
    else:
        yield from bot.login(settings.email, settings.password)
    yield from bot.connect()

# If Statement
if __name__ == '__main__':
    error = False
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except discord.LoginFailure:
        error = True
        logger.error(traceback.format_exc())
        choice - input("Login Credentials are Invalid!"
                       "If the worked in the past, Discord might be having"
                       "issues. Please check http://status.discordapp.com\n"
                       "Otherwise you can type 'reset' to delete the current configuration"
                       "to restart the first run setup on the next startup. \n> ")
        if choice.strip() == "reset":
            shutil.copy('data/chronoxia/settings.json',
                        'data/chronoxia/settings-{}.bak'.format(int(time.time())))
            os.remove('data/chronoxia/settings.json')
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
    except:
        error = True
        logger.error(traceback.format_exc())
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()
        if error:
            exit(1)
