import asyncio
from typing import List

import discord
from discord.ext import commands

from . import style


class RoleAllView(discord.ui.View):
    """
    A view to start giving roles to everyone
    """

    def __init__(
        self, ctx: commands.Context, members: List[discord.Member], role: discord.Role
    ) -> None:
        """
        Initialize the view
        """
        super().__init__()
        self.ctx = ctx
        self.members = members
        self.role = role

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label="Start",
        emoji=style.Emoji.REGULAR.check,
    )
    async def start_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Start giving roles to everyone
        """
        await self.start_giving_roles(interaction, self.role)

    @discord.ui.button(
        style=discord.ButtonStyle.danger,
        label="Cancel",
        emoji=style.Emoji.REGULAR.cancel,
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Cancel the view
        """
        await interaction.message.delete()
        await self.ctx.command.reset_cooldown(self.ctx)

    async def start_giving_roles(
        self, interaction: discord.Interaction, role: discord.Role
    ) -> None:
        """
        Start giving roles to everyone
        """
        embed = discord.Embed(
            title="Bulk Role Add - In Progress",
            description="""This message will edit itself when it is finished.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "Starting to give roles to everyone...", ephemeral=True
        )

        for member in self.members:
            if role not in member.roles:
                await member.add_roles(role)
                await asyncio.sleep(1)

        embed = discord.Embed(
            title="Bulk Role Add - Finished",
            description="""Finished giving roles to everyone!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await interaction.message.edit(embed=embed)


class RoleRallView(discord.ui.View):
    """
    A view to start removing roles to everyone
    """

    def __init__(
        self, ctx: commands.Context, members: List[discord.Member], role: discord.Role
    ) -> None:
        """
        Initialize the view
        """
        super().__init__()
        self.ctx = ctx
        self.members = members
        self.role = role

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label="Start",
        emoji=style.Emoji.REGULAR.check,
    )
    async def start_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Start removing roles from everyone
        """
        await self.start_removing_roles(interaction, self.role)

    @discord.ui.button(
        style=discord.ButtonStyle.danger,
        label="Cancel",
        emoji=style.Emoji.REGULAR.cancel,
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Cancel the view
        """
        await interaction.message.delete()
        await self.ctx.command.reset_cooldown(self.ctx)

    async def start_removing_roles(
        self, interaction: discord.Interaction, role: discord.Role
    ) -> None:
        """
        Start giving roles to everyone
        """
        embed = discord.Embed(
            title="Bulk Role Remove - In Progress",
            description="""This message will edit itself when it is finished.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "Starting to remove roles from everyone...", ephemeral=True
        )

        for member in self.members:
            if role in member.roles:
                await member.remove_roles(role)
                await asyncio.sleep(1)

        embed = discord.Embed(
            title="Bulk Role Remove - Finished",
            description="""Finished removing roles from everyone!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await interaction.message.edit(embed=embed)
