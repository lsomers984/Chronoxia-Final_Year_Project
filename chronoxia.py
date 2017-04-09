# Imports Required for this Project

import asyncio
import os
import sys

sys.path.insert(0, "lib")
import logging
import logging.handlers
import traceback
import datetime
import subprocess

# Python and Discord PY check Routine
try:
    assert sys.version_info >= (3, 5)
    from discord.ext import commands
    import discord
except ImportError:
    print("Discord.py is not installed.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n"
          "https://lsomers984.github.io/Chrono-Docs/\n")
    sys.exit()
except AssertionError:
    print("Chronoxia needs Python 3.5 or superior.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n"
          "https://lsomers984.github.io/Chrono-Docs/\n")
    sys.exit()

from cogs.utils.settings import Settings
from cogs.utils.dataIO import dataIO
from cogs.utils.chat_formatting import inline
from collections import Counter
from io import TextIOWrapper

#
#       Chronoxia - A Multifunctional Discord Bot based on Discord.py and its extensions
#       https://github.com/lsomers984/Chronoxia---Final-Year-Project
#
#       cogs/utils/checks.py both contain some modified functions originally made by Rapptz
#             https://github.com/Rapptz/RoboDanny/
#

description = "Chronoxia - A Multifunctional Discord Bot by Wolfstorm"


# Bot Class
class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        def prefix_manager(bot, message):
            """
            Returns Prefixs of the server if set.
            If None are set or is none on server, returns global prefixs

            Requires an instance of Bot and Message Object to be passed as args.
            """
            return bot.settings.get_prefixes(message.server)

        self.counter = Counter()
        self.uptime = datetime.datetime.utcnow()  # Refreshed before bot Logins
        self._message_modifiers = []
        self.settings = Settings()
        self._intro_displayed = False
        self._shutdown_mode = None
        self.logger = set_logger(self)

        if 'self_bot' in kwargs:
            self.settings.self_bot = kwargs['self_bot']
        else:
            kwargs['self_bot'] = self.settings.self_bot
            if self.settings.self_bot:
                kwargs['pm_help'] = False
        super().__init__(*args, command_prefix=prefix_manager, **kwargs)

    async def send_message(self, *args, **kwargs):
        if self._message_modifiers:
            if "content" in kwargs:
                pass
            elif len(args) == 2:
                args = list(args)
                kwargs["content"] = args.pop()
            else:
                return await super().send_message(*args, **kwargs)

            content = kwargs['content']
            for m in self._message_modifiers:
                try:
                    content = str(m(content))
                except:  # Faulty modifiers should not
                    pass  # break send_message
            kwargs['content'] = content

        return await super().send_message(*args, **kwargs)

    # Graceful Quiting with Exit Code 0
    async def shutdown(self, *, restart=False):
        """
        Quits Chronoxia with Exit Code 0. If restart is True, exit code is 26.
        Launcher auto restarts when exit code is 26
        """
        self._shutdown_mode = not restart
        await self.logout()

    # Adds a Message Modifier to the bot
    def add_message_modifier(self, func):
        """
         A message modifier is a callable that accepts a message's
         content as the first positional argument.
         Before a message gets sent, func will get called with
         the message's content as the only argument. The message's
         content will then be modified to be the func's return
         value.

         Exceptions thrown by the callable will be catched and
         silenced.
         """
        if not callable(func):
            raise TypeError("The message modifier function "
                            "must be a callable.")

            self._message_modifiers.append(func)

        # Remove Message Modifier from the bot


def remove_message_modifier(self, func):
    if func not in self._message_modifiers:
        raise RuntimeError("Function not present in the message "
                           "modifiers.")

    self._message_modifiers.remove(func)


# Remove all Message Modifiers from the bot
def clear_message_modifiers(self):
    self._message_modifiers.clear()


async def send_cmd_help(self, ctx):
    if ctx.invoked_subcommand:
        pages = self.formatter.format_help_for(ctx, ctx.invoked_subcommand)
        for page in pages:
            await self.send_message(ctx.message.channel, page)
    else:
        pages = self.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            await self.send_message(ctx.message.channel, page)


def user_allowed(self, message):
    author = message.author

    if author.bot:
        return False

    if author == self.user:
        return self.settings.self_bot

    mod = self.get_cog('Mod')

    if mod is not None:
        if self.settings.owner == author.id:
            return True
        if not message.channel.is_private:
            server = message.server
            names = (self.settings.get_server_admin(
                server), self.settings.get_server_mod(server))
            results = map(
                lambda name: discord.utils.get(author.roles, name=name),
                names)
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

    # Pip Install - OSX


async def pip_install(self, name, *, timeout=None):
    """
       Installs a pip package in the local 'lib' folder in a thread safe
       way. On Mac systems the 'lib' folder is not used.
       Can specify the max seconds to wait for the task to complete

       Returns a bool indicating if the installation was successful
       """

    IS_MAC = sys.platform == "darwin"
    interpreter = sys.executable

    if interpreter is None:
        raise RuntimeError("Couldn't find Python's interpreter")

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade",
        "--target", "lib",
        name
    ]

    if IS_MAC:  # --target is a problem on Homebrew.
        args.remove("--target")
        args.remove("lib")

    def install():
        code = subprocess.call(args)
        sys.path_importer_cache = {}
        return not bool(code)

    response = self.loop.run_in_executor(None, install)
    return await asyncio.wait_for(response, timeout=timeout)  

    # Format Class
class Formatter(commands.HelpFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _add_subcommands_to_page(self, max_width, commands):
        for name, command in sorted(commands, key=lambda t: t[0]):
            if name in command.aliases:
                # skip aliases
                continue

            entry = '  {0:<{width}} {1}'.format(name, command.short_doc,
                                                width=max_width)
            shortened = self.shorten(entry)
            self._paginator.add_line(shortened)


def initialize(bot_class=Bot, formatter_class=Formatter):
    # Backwards Compatible Discord PY Stuff
    formatter = formatter_class(show_check_failure=False)

    bot = bot_class(formatter=formatter, description=description, pm_help=None)

    import __main__
    __main__.send_cmd_help = bot.send_cmd_help
    __main__.user_allowed = bot.user_allowed
    __main__.settings = bot.settings

    # Def - get_oauth_url
    async def get_oauth_url():
        try:
            data = await bot.application_info()
        except Exception as e:
            return "Couldn't retrieve invite link.Error: {}".format(e)
        return discord.utils.oauth_url(data.id)

    # Def - Set Owner of Bot
    async def set_bot_owner():
        if bot.settings.self_bot:
            bot.settings.owner = bot.user.id
            return "[Selfbot mode]"

        if bot.settings.owner:
            owner = discord.utils.get(bot.get_all_members(),
                                      id=bot.settings.owner)
            if not owner:
                try:
                    owner = await bot.get_user_info(bot.settings.owner)
                except:
                    owner = None
                if not owner:
                    owner = bot.settings.owner  # Just the ID then
            return owner

        how_to = "Do `[p]set owner` in chat to set it"

        if bot.user.bot:  # Can fetch owner
            try:
                data = await bot.application_info()
                bot.settings.owner = data.owner.id
                bot.settings.save_settings()
                return data.owner
            except:
                return "Failed to fetch owner. " + how_to
        else:
            return "Yet to be set. " + how_to

            # Bot Event Def - on_ready

    @bot.event
    async def on_ready():

        if bot._intro_displayed:
            return
        bot._intro_displayed = True

        owner_cog = bot.get_cog('Owner')
        total_cogs = len(owner_cog._list_cogs())
        users = len(set(bot.get_all_members()))
        servers = len(bot.servers)
        channels = len([c for c in bot.get_all_channels()])

        login_time = datetime.datetime.utcnow() - bot.uptime
        login_time = login_time.seconds + login_time.microseconds / 1E6

        print("Login successful. ({}ms)\n".format(login_time))

        owner = await set_bot_owner()

        print("-----------------")
        print("Chronoxia - Discord Bot")
        print("-----------------")
        print(str(bot.user))
        print("\nBot Connection Information:")
        print("No. of Servers: {}".format(servers))
        print("No. of Channels: {}".format(channels))
        print("No. of Users: {}\n".format(users))
        prefix_label = 'Prefix'
        if len(bot.settings.prefixes) > 1:
            prefix_label += 'es'
        print("{}: {}".format(prefix_label, " ".join(bot.settings.prefixes)))
        print("Owner: " + str(owner))
        print("{}/{} active modules with {} commands".format(
            len(bot.cogs), total_cogs, len(bot.commands)))
        print("-----------------")

        if bot.settings.token and not bot.settings.self_bot:
            print("\nUse this following API URL to bring your bot to a server:")
            url = await get_oauth_url()
            bot.oauth_url = url
            print(url)

        print("\nOfficial Server: ---")
        print("Keep me updated by selecting 'Update' in the Launcher")
        await bot.get_cog('Owner').disable_commands()

    # Bot Envent Def - on_resumed
    @bot.event
    async def on_resumed():
        bot.counter["session_resumed"] += 1

    # Bot Event Def - on_command
    @bot.event
    async def on_command(command, ctx):
        bot.counter["processed_commands"] += 1

    # Bot Event Def - on_message
    @bot.event
    async def on_message(message):
        bot.counter["messages_read"] += 1
        if bot.user_allowed(message):
            await bot.process_commands(message)

    # Bot Event Def - on_command_error
    @bot.event
    async def on_command_error(error, ctx):
        channel = ctx.message.channel
        if isinstance(error, commands.MissingRequiredArgument):
            await bot.send_cmd_help(ctx)
        elif isinstance(error, commands.BadArgument):
            await bot.send_cmd_help(ctx)
        elif isinstance(error, commands.DisabledCommand):
            await bot.send_message(channel, "That command has been disabled by the owner :crying_cat_face:")
        elif isinstance(error, commands.CommandInvokeError):
            bot.logger.exception("Exception in command '{}'".format(
                ctx.command.qualified_name), exc_info=error.original)
            oneliner = "Error in command '{}' - {}: {}".format(
                ctx.command.qualified_name, type(error.original).__name__,
                str(error.original))
            await ctx.bot.send_message(channel, inline(oneliner))
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CheckFailure):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            await bot.send_message(channel, "That command is not available in Direct/Private Messages :cring_cat_face:")
        else:
            bot.logger.exception(type(error).__name__, exc_info=error)

    return bot


# Checks Folders are created
def check_folders():
    folders = ("data", "data/chronoxia", "cogs", "cogs/utils")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)


# Interactive Setup

def interactive_setup(settings):
    first_run = settings.bot_settings == settings.default_settings

    if first_run:
        print("Chronoxia - First run configuration\n")
        print("If you haven't already, create a new account:\n"
              "https://lsomers984.github.io/Chrono-Docs/chrono_guide_bot_accounts/"
              "#creating-a-new-bot-account")
        print("and obtain your bot's token like described.")

    # Login Selection
    if not settings.login_credentials:
        print("\nInsert your bot's token:")
        while settings.token is None and settings.email is None:
            choice = input("> ")
            if "@" not in choice and len(choice) >= 50:  # Assuming token
                settings.token = choice
            elif "@" in choice:  # Email Login
                settings.email = choice
                settings.password = input("\nPassword> ")
            else:
                print("That doesn't look like a valid token.")
        settings.save_settings()

    # Prefix Selection
    if not settings.prefixes:
        print("\nChoose a prefix. A prefix is what you type before a command."
              "\nA typical prefix would be the exclamation mark.\n"
              "Can be multiple characters. You will be able to change it "
              "later and add more of them.\nChoose your prefix:")
        confirmation = False
        while confirmation is False:
            new_prefix = ensure_reply("\nPrefix> ").strip()
            print("\nAre you sure you want {0} as your prefix?\nYou "
                  "will be able to issue commands like this: {0}help"
                  "\nType yes to confirm or no to change it".format(
                new_prefix))
            confirmation = get_answer()
        settings.prefixes = [new_prefix]
        settings.save_settings()

    # Admin Role Assignment
    if first_run:
        print("\nInput the admin role's name. Anyone with this role in Discord"
              " will be able to use the bot's admin commands")
        print("Leave blank for default name (ChronoAdmin)")
        settings.default_admin = input("\nAdmin role> ")
        if settings.default_admin == "":
            settings.default_admin = "ChronoAdmin"
        settings.save_settings()

        # Moderator Role Assignment
        print("\nInput the moderator role's name. Anyone with this role in"
              " Discord will be able to use the bot's mod commands")
        print("Leave blank for default name (ChronoMod)")
        settings.default_mod = input("\nModerator role> ")
        if settings.default_mod == "":
            settings.default_mod = "ChronoMod"
        settings.save_settings()

        # Config Complete
        print("\n Configuration Complete. Leave this window open to keep "
              "Chronoxia Online.\n All Commands will have to be issues through "
              "Discord's chat, *NOTE: This window will now be read-only*. \n"
              "Please Hit Enter to Continue:)")
        input("\n")


# Logger Set
def set_logger(bot):
    logger = logging.getLogger("chronoxia")
    logger.setLevel(logging.INFO)

    chrono_format = logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(chrono_format)
    if bot.settings.debug:
        stdout_handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        stdout_handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)

    fhandler = logging.handlers.RotatingFileHandler(
        filename='data/chronoxia/chronoxia.log', encoding='utf-8', mode='a',
        maxBytes=10 ** 7, backupCount=5)
    fhandler.setFormatter(chrono_format)

    logger.addHandler(fhandler)
    logger.addHandler(stdout_handler)

    dpy_logger = logging.getLogger("discord")
    if bot.settings.debug:
        dpy_logger.setLevel(logging.DEBUG)
    else:
        dpy_logger.setLevel(logging.WARNING)
    handler = logging.FileHandler(
        filename='data/chronoxia/discord.log', encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]"))
    dpy_logger.addHandler(handler)

    return logger


# Ensure Reply Def
def ensure_reply(msg):
    choice = ""
    while choice == "":
        choice = input(msg)
    return choice


# Get Answer Def
def get_answer():
    choices = ("yes", "y", "no", "n")
    c = ""
    while c not in choices:
        c = input(">").lower()
    if c.startswith("y"):
        return True
    else:
        return False


# Set Cog - To Be Moved
def set_cog(cog, value):
    data = dataIO.load_json("data/chronoxia/cogs.json")
    data[cog] = value
    dataIO.save_json("data/chronoxia/cogs.json", data)


# Load Cog
def load_cogs(bot):
    defaults = ("alias", "audio", "customcom", "downloader", "economy",
                "general", "image", "mod", "streams", "trivia")

    try:
        registry = dataIO.load_json("data/chronoxia/cogs.json")
    except:
        registry = {}

    bot.load_extension('cogs.owner')
    owner_cog = bot.get_cog('Owner')

    # Assuming the user deleted the Owner Cog
    if owner_cog is None:
        print("You got rid of owner.py!!! It had functions that I need"
              "to run special events :( I can not operate without it!!")
        print()
        print("Please go download it from:\n"
              "https://github.com/lsomers984/Chronoxia---Final-Year-Project")
        exit(1)

    # --No-Cogs Load
    if bot.settings._no_cogs:
        bot.logger.debug("Skipping initial cogs loading (--no-cogs)")
        if not os.path.isfile("data/chronoxia/cogs.json"):
            dataIO.save_json("data/chronoxia/cogs.json", {})
        return

    failed = []
    extensions = owner_cog._list_cogs()

    if not registry:  # All default cogs enabled by default
        for ext in defaults:
            registry["cogs." + ext] = True

    for extension in extensions:
        if extension.lower() == "cogs.owner":
            continue
        to_load = registry.get(extension, False)
        if to_load:
            try:
                owner_cog._load_cog(extension)
            except Exception as e:
                print("{}: {}".format(e.__class__.__name__, str(e)))
                bot.logger.exception(e)
                failed.append(extension)
                registry[extension] = False

    dataIO.save_json("data/chronxoia/cogs.json", registry)

    if failed:
        print("\nFailed to load: {}\n".format(" ".join(failed)))


# Def Main
def main(bot):
    check_folders()
    if not bot.settings.no_prompt:
        interactive_setup(bot.settings)
    load_cogs(bot)

    if bot.settings._dry_run:
        print("Quitting: dry run")
        bot._shutdown_mode = True
        exit(0)

    print("Logging into Discord...")
    bot.uptime = datetime.datetime.utcnow()

    if bot.settings.login_credentials:
        yield from bot.login(*bot.settings.login_credentials,
                             bot=not bot.settings.self_bot)
    else:
        print("No credentials available to login.")
        raise RuntimeError()
    yield from bot.connect()


if __name__ == '__main__':
    sys.stdout = TextIOWrapper(sys.stdout.detach(),
                               encoding=sys.stdout.encoding,
                               errors="replace",
                               line_buffering=True)
    bot = initialize()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(bot))
    except discord.LoginFailure:
        bot.logger.error(traceback.format_exc())
        if not bot.settings.no_prompt:
            choice = input("Invalid login credentials. If they worked before "
                           "Discord might be having temporary technical "
                           "issues.\nIn this case, press enter and try again "
                           "later.\nOtherwise you can type 'reset' to reset "
                           "the current credentials and set them again the "
                           "next start.\n> ")
            if choice.lower().strip() == "reset":
                bot.settings.token = None
                bot.settings.email = None
                bot.settings.password = None
                bot.settings.save_settings()
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
    except Exception as e:
        bot.logger.exception("Fatal exception, attempting graceful logout",
                             exc_info=e)
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()
        if bot._shutdown_mode is True:
            exit(0)
        elif bot._shutdown_mode is False:
            exit(26)  # Restart
        else:
            exit(1)
