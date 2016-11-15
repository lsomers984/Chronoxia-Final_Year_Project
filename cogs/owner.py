import discord
from discord.ext import commands
from cogs.utils import checks
from __main__ import set_cog, send_cmd_help, settings
from .utils.dataIO import dataIO
from .utils.chat_formatting import pagify, box

import importlib
import traceback
import logging
import asyncio
import threading
import datetime
import glob
import os
import time
import aiohttp

log = logging.getLogger("chronoxia.owner")


# Classes for Exception Handling
class CogNotFoundError(Exception):
    pass


class CogLoadError(Exception):
    pass


class NoSetupError(CogLoadError):
    pass


class CogUnloadError(Exception):
    pass


class OwnerUnloadWithoutReloadError(CogUnloadError):
    pass


# Owner Class
class Owner:
    """All Owner Commands that relates to Bot Operations and Maintenance
    """

    # Definition for __init__
    def __init__(self, bot):
        self.bot = bot
        self.setowner_lock = False
        self.file_path = "data/chronoxia/disabled_commands.json"
        self.disabled_commands = dataIO.load_json(self.file_path)
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

        if __name__ == '__main__':
            def __unload(self):
                self.session.close()

                # Explanation taken from Discord.Py
                # @checks.is_owner - Checks in accordance to the ID set within the Discord API/Bot Settings,
                #                    If the user trying to run the command is Owner

    @commands.command()
    @checks.is_owner()
    async def load(self, *, module: str):
        """Loads a Module
        Example: [p]load Mod (where [p] = Prefix)
        """
        module = module.strip()
        if "cogs." not in module:
            module = "cogs." + module
        try:
            self._load_cog(module)
        except CogNotFoundError:
            await self.bot.say("That Module could not be found :crying_cat_face:")
        except CogLoadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("There was an issue loading this module :crying_cat_face:. "
                               "Check your console or logs for more information\n"
                               "\nError: '{}'".format(e.args[0]))
        except Exception as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say('Module was found and possibly loaded but '
                               'something went wrong. Check your console '
                               'or logs for more information.\n\n'
                               'Error: `{}`'.format(e.args[0]))
        else:
            set_cog(module, True)
            await self.disabled_commands()
            await self.bot.say("Module Enabled. Have fun! :smiley_cat:")

    @commands.group(invoke_without_command=True)
    @checks.is_owner()
    async def unload(self, *, module: str):
        """Unloads a Module

        E.g: [p]unload mod
        """
        module = module.split()
        if "cogs." not in module:
            module = "cogs." + module
        if not self.__does_cogfile_exist(module):
            await self.bot.say("Module does not Exist on my Filesystem."
                               " Autoloading will not be turned off in case"
                               " this was not supposed to happen :crying_cat_face:")
        else:
            set_cog(module, False)
        try:  # Attempt to Unload it - No Matter what happens
            self._unload_cog(module)
        except OwnerUnloadWithoutReloadError:
            await self.bot.say("Hey, Dont touch that! Unless you are reloading then "
                               "Carry on!")
        except CogUnloadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say('Sorry, I am unable to safely disable that Module.')
        else:
            await self.bot.say("Module is now Disabled. To Renable just do !load <module_name>.")

    @unload.command(name=all)
    @checks.is_owner
    async def unload_all(self):
        """Unloads all Modules"""
        cogs = self._list_cogs()
        still_loaded = []
        for cog in cogs:
            set_cog(cog, False)
            try:
                self._unload_cog(cog)
            except OwnerUnloadWithoutReloadError:
                pass
            except CogUnloadError as e:
                log.exception(e)
                traceback.print_exc()
                still_loaded.append(cog)
        if still_loaded:
            still_loaded = ", ".join(still_loaded)
            await self.boy.say("I was unable to unload some modules - ""{}".format(still_loaded) + ", I wonder why?")
        else:
            await self.bot.say("All of my modules are now unloaded :( I feel lighter!")

    @checks.is_mod()
    @commands.command(name="reload")
    async def _reload(self, module):
        """Reloads a module
        Example: reload audio"""
        if "cogs." not in module:
            module = "cogs." + module

        try:
            self._unload_cog(module, reloading=True)
        except:
            pass

        try:
            self._load_cog(module)
        except CogNotFoundError:
            await self.bot.say("That module cannot be found.")
        except NoSetupError:
            await self.bot.say("That module does not have a setup function.")
        except CogLoadError as e:
            log.exception(e)
            traceback.print_exc()
            await self.bot.say("That module could not be loaded. Check your"
                               " console or logs for more information.\n\n"
                               "Error: `{}`".format(e.args[0]))
        else:
            set_cog(module, True)
            await self.disable_commands()
            await self.bot.say("Module reloaded.")
