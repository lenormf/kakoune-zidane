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

        self.token = bot.config["github_plugin"]["token"]
        self.repository = bot.config["github_plugin"]["repository"]

        self.max_search_results = 3
        if "max_search_results" in bot.config["github_plugin"]:
            self.max_search_results = bot.config["github_plugin"]["max_search_results"]

        if "debug" in bot.config["github_plugin"] and bot.config["github_plugin"]["debug"]:
            github.enable_console_debug_logging()

        try:
            self.github = github.Github(self.token)
        except github.GithubException as e:
            raise RuntimeError("Unable to initialize the Github API wrapper: %s (%s)" % (e.data["message"], e.status))

        try:
            self.repo = self.github.get_repo(self.repository)
        except github.GithubException as e:
            raise RuntimeError("Unable to fetch the target repository: %s (%s)" % (e.data["message"], e.status))

    @command(permission="view", aliases=["i"])
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
                    issue = self.repo.get_issue(id_issue)
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
                    pr = self.repo.get_pull(id_pr)
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

    def _search(self, args, issue=True, pr=True):
        qualifiers = {
            "repo": self.repository,
            "in": "title,body,comments",
        }
        query = []

        if issue ^ pr:
            qualifiers["type"] = "issue" if issue else "pr"

        for i in args:
            si = i.split(":", 1)
            if len(si) < 2:
                query.append(i)
                continue

            si[1] = si[1].strip()
            if not len(si[1]):
                query.append(i)
                continue

            if si[0] in ["author", "commenter", "involves", "state"]:
                qualifiers[si[0]] = si[1]
            else:
                query.append(i)
                continue

        messages = []
        try:
            issues = self.github.search_issues(query=" ".join(query), sort="created", order="desc", **qualifiers)
            for issue in issues[:self.max_search_results]:
                messages.append("%s #%d: %s - %s" % ("Pull Request" if issue.pull_request else "Issue", issue.number, issue.title, issue.html_url))
        except github.GithubException as e:
            self.log.error("Github API error: %s (%s)", e.data["message"], e.status)
            return None

        return messages

    @command(permission="view", aliases=["s"])
    async def search(self, mask, target, args):
        """Search issues and pull requests

        %%search <query>...
        """

        results = self._search(args["<query>"], issue=True, pr=True)
        if results is None:
            return ["An error occured while fetching results"]
        elif not results:
            return [f"{mask.nick}: no results found"]

        return results

    @command(permission="view", aliases=["si"])
    async def search_issue(self, mask, target, args):
        """Search issues

        %%search_issue <query>...
        """

        results = self._search(args["<query>"], issue=True, pr=False)
        if results is None:
            return ["An error occured while fetching results"]
        elif not results:
            return [f"{mask.nick}: no results found"]

        return results

    @command(permission="view", aliases=["spr"])
    async def search_pr(self, mask, target, args):
        """Search pull requests

        %%search_pr <query>...
        """

        results = self._search(args["<query>"], issue=False, pr=True)
        if results is None:
            return ["An error occured while fetching results"]
        elif not results:
            return [f"{mask.nick}: no results found"]

        return results
