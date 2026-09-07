"""
@Author         : yanyongyu
@Date           : 2021-04-26 18:19:15
@LastEditors    : yanyongyu
@LastEditTime   : 2024-08-18 16:36:20
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from nonebot import on_regex
from nonebot.plugin import PluginMetadata

from src.plugins.github import config
from src.plugins.github.libs.opengraph import get_opengraph_image
from src.plugins.github.helpers import NO_GITHUB_EVENT, send_image
from src.providers.platform import TARGET_INFO, MESSAGE_INFO, extract_sent_message
from src.plugins.github.dependencies import (
    COMMIT,
    RELEASE,
    REPOSITORY,
    STORE_REGEX_VARS,
)
from src.plugins.github.cache.message_tag import (
    RepoTag,
    CommitTag,
    ReleaseTag,
    create_message_tag,
)
from src.plugins.github.libs.github import (
    FULLREPO_REGEX,
    GITHUB_REPO_LINK_REGEX,
    GITHUB_COMMIT_LINK_REGEX,
    GITHUB_RELEASE_LINK_REGEX,
    GITHUB_PR_COMMIT_LINK_REGEX,
)

__plugin_meta__ = PluginMetadata(
    "GitHub OpenGraph 查看",
    "查看 GitHub 仓库，提交或发布的 OpenGraph",
    "^owner/repo$: 通过仓库缩写查看 OpenGraph\ngithub.com/owner/repo: 通过 GitHub"
    " 仓库链接查看 OpenGraph\ngithub.com/owner/repo/commit/<hash>: 通过 GitHub"
    " 提交链接查看 OpenGraph\ngithub.com/owner/repo/pull/<number>/commits/<hash>: 通过"
    " GitHub PR 提交链接查看 OpenGraph\ngithub.com/owner/repo/releases/tag/<tag>: 通过"
    " GitHub 发布链接查看 OpenGraph\n",
)

repo_graph = on_regex(
    f"^{FULLREPO_REGEX}$", rule=NO_GITHUB_EVENT, priority=config.github_command_priority
)
# lower priority than issue link
repo_link_graph = on_regex(
    GITHUB_REPO_LINK_REGEX,
    rule=NO_GITHUB_EVENT,
    priority=config.github_command_priority + 10,
)


@repo_graph.handle(parameterless=(STORE_REGEX_VARS,))
@repo_link_graph.handle(parameterless=(STORE_REGEX_VARS,))
async def handle(
    target_info: TARGET_INFO, message_info: MESSAGE_INFO, repo: REPOSITORY
):
    tag = RepoTag(owner=repo.owner.login, repo=repo.name, is_receive=True)

    await create_message_tag(message_info, tag)

    if repo.private:
        return

    if not (image := await get_opengraph_image(tag)):
        return

    result = await send_image(image)

    tag = RepoTag(owner=repo.owner.login, repo=repo.name, is_receive=False)
    if sent_message_info := extract_sent_message(target_info, result):
        await create_message_tag(sent_message_info, tag)


commit_graph = on_regex(
    GITHUB_COMMIT_LINK_REGEX,
    rule=NO_GITHUB_EVENT,
    priority=config.github_command_priority,
)
pr_commit_graph = on_regex(
    GITHUB_PR_COMMIT_LINK_REGEX,
    rule=NO_GITHUB_EVENT,
    priority=config.github_command_priority,
)


@commit_graph.handle(parameterless=(STORE_REGEX_VARS,))
@pr_commit_graph.handle(parameterless=(STORE_REGEX_VARS,))
async def handle_commit(
    target_info: TARGET_INFO,
    message_info: MESSAGE_INFO,
    repo: REPOSITORY,
    commit: COMMIT,
):
    tag = CommitTag(
        owner=repo.owner.login, repo=repo.name, commit=commit.sha, is_receive=True
    )

    await create_message_tag(message_info, tag)

    if repo.private:
        return

    if not (image := await get_opengraph_image(tag)):
        return

    result = await send_image(image)

    tag = CommitTag(
        owner=repo.owner.login, repo=repo.name, commit=commit.sha, is_receive=False
    )
    if sent_message_info := extract_sent_message(target_info, result):
        await create_message_tag(sent_message_info, tag)


release_graph = on_regex(
    GITHUB_RELEASE_LINK_REGEX,
    rule=NO_GITHUB_EVENT,
    priority=config.github_command_priority,
)


@release_graph.handle(parameterless=(STORE_REGEX_VARS,))
async def handle_release(
    target_info: TARGET_INFO,
    message_info: MESSAGE_INFO,
    repo: REPOSITORY,
    release: RELEASE,
):
    tag = ReleaseTag(
        owner=repo.owner.login, repo=repo.name, tag=release.tag_name, is_receive=True
    )

    await create_message_tag(message_info, tag)

    if repo.private:
        return

    if not (image := await get_opengraph_image(tag)):
        return

    result = await send_image(image)

    tag = ReleaseTag(
        owner=repo.owner.login, repo=repo.name, tag=release.tag_name, is_receive=False
    )
    if sent_message_info := extract_sent_message(target_info, result):
        await create_message_tag(sent_message_info, tag)
