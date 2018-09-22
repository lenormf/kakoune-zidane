# -*- coding: utf-8 -*-
#
# github_plugin.py for zidane
# by lenormf
#

from irc3.plugins.command import command
import irc3

import github


@irc3.plugin
class Github:
    requires = ["irc3.plugins.log"]

    def __init__(self, bot):
        self.bot = bot
        self.log = bot.log

        if "github_plugin" not in bot.config:
            raise RuntimeError("No [github_plugin] section set in the configuration")
        else:
            if "token" not in bot.config["github_plugin"]:
                raise RuntimeError("No Github API token declared")
            elif "repository" not in bot.config["github_plugin"]:
                raise RuntimeError("No target repository declared")

        token = bot.config["github_plugin"]["token"]
        repository = bot.config["github_plugin"]["repository"]

        if "debug" in bot.config["github_plugin"] and bot.config["github_plugin"]["debug"]:
            github.enable_console_debug_logging()

        try:
            self.g = github.Github(token)
        except github.GithubException as e:
            raise RuntimeError("Unable to initialize the Github API wrapper: %s (%s)" % (e.data["message"], e.status))

        try:
            self.g = self.g.get_repo(repository)
        except github.GithubException as e:
            raise RuntimeError("Unable to fetch the target repository: %s (%s)" % (e.data["message"], e.status))

    @command(permission="view")
    async def issue(self, mask, target, args):
        """Display information about given issues

        %%issue <id>...
        """

        self.log.debug("User %s is searching issues: %s", mask.nick, (mask, target, args))

        messages = []
        for id_issue in args["<id>"]:
            if id_issue.startswith("#"):
                id_issue = id_issue[1:]

            try:
                id_issue = int(id_issue)

                try:
                    issue = self.g.get_issue(id_issue)
                except github.GithubException as e:
                    if e.status == 404:
                        messages.append(f"{mask.nick}: no such issue ({id_issue})")
                    else:
                        self.log.error("Github API error: %s (%s)", e.data["message"], e.status)
                else:
                    messages.append(f"Issue #{id_issue}: {issue.title} - {issue.html_url}")
            except ValueError:
                messages.append(f"{mask.nick}: invalid identifier ({id_issue})")
                continue

        return messages

    @command(permission="view")
    async def pr(self, mask, target, args):
        """Display information about given pull requests

        %%pr <id>...
        """

        self.log.debug("User %s is searching pull requests: %s", mask.nick, (mask, target, args))

        messages = []
        for id_pr in args["<id>"]:
            if id_pr.startswith("#"):
                id_pr = id_pr[1:]

            try:
                id_pr = int(id_pr)

                try:
                    pr = self.g.get_pull(id_pr)
                except github.GithubException as e:
                    if e.status == 404:
                        messages.append(f"{mask.nick}: no such pull request ({id_pr})")
                    else:
                        self.log.error("Github API error: %s (%s)", e.data["message"], e.status)
                else:
                    messages.append(f"PR #{id_pr}: {pr.title} - {pr.html_url}")
            except ValueError:
                messages.append(f"{mask.nick}: invalid identifier ({id_pr})")
                continue

        return messages
