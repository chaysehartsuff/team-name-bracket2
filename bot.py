import os
import discord
from discord import app_commands
from discord.ext import commands

from mr_bracket import Bracket
from guild_state import setGuildVar, getGuildVar

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── add this inside your file ─────────────────────────────────────

@bot.tree.command(name="next_stage",
                  description="Begin intial or move to next stage")
async def next_stage(interaction: discord.Interaction):
    requires_confirmation = getGuildVar(guild_id, "requires_confirmation", False)
    if requires_confirmation:
        await interaction.response.send_message(
            "Complete confirmation before proceeding.",
            ephemeral=True
        )
    else:
        guild_id = interaction.guild.id
        current = getGuildVar(guild_id, "stage", 0)
        # if unset (0), this makes it 1
        new_stage = current + 1
        setGuildVar(guild_id, "stage", new_stage)
        await process_stage(interaction)

@bot.tree.command(name="clear_stage",
                  description="Reset stages")
async def clear_stage(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    setGuildVar(guild_id, "stage", None)
    await interaction.response.send_message(
        "✅ Stage cleared.",
        ephemeral=True
    )

@bot.tree.command(name="confirm",
                  description="Confirm prompt in the current stage")
async def confirm(interaction: discord.Interaction):
    setGuildVar(interaction.guild_id, "requires_confirmation", False)

@bot.event
async def on_ready():
    await bot.tree.sync()  # registers your slash commands with Discord
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

async def process_stage(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    current_stage = getGuildVar(guild_id, "stage", 0)
    
    match current_stage:
        case 1:
            bracket = Bracket()
            bracket.add_name("Player 1", 100)
            bracket.add_name("Player 2", 200)
            bracket.add_name("Player 3", 300)
            bracket.add_name("Player 4", 400)
            bracket.add_name("Player 5", 500)
            bracket.add_name("Player 6", 600)
            bracket.add_name("Player 7", 700)
            bracket.add_name("Player 8", 800)
            # bracket.add_name("Player 9", 900)
            # bracket.add_name("Player 10", 1000)
            # bracket.add_name("Player 11", 1100)
            # bracket.add_name("Player 12", 1200)
            # bracket.add_name("Player 13", 1300)
            # bracket.add_name("Player 14", 1400)
            # bracket.add_name("Player 15", 1500)
            # bracket.add_name("Player 16", 1600)

            bracket.finalize()
            #print(bracket._bracket.rounds, flush=True)
            #print(bracket._bracket.rounds[0][1].competitor_a.name, flush=True)
            # bracket.generate_standings(bracket._bracket.rounds)
            # print(bracket.rounds, flush=True)

            # print(f"Winner: {bracket.get_winner()}", flush=True)
            bracket.submit_winner("Player 1", 3, 2)
            bracket.submit_winner("Player 2", 5, 2)
            bracket.submit_winner("Player 6", 4, 2)
            bracket.submit_winner("Player 4", 3, 2)
            # print(f"Winner: {bracket.get_winner()}", flush=True)
            # print(bracket.rounds, flush=True)

            bracket.submit_winner("Player 1", 3, 1)
            bracket.submit_winner("Player 6", 5, 4)
            # print(f"Winner: {bracket.get_winner()}", flush=True)
            # print(bracket.rounds, flush=True)
            bracket.submit_winner("Player 6", 12, 9)
            print(f"Winner: {bracket.get_winner()}", flush=True)
            bracket.generate_standings(bracket._bracket.rounds, guild_id)

            await interaction.response.send_message(
                "Stage 1",
                ephemeral=True
            )
        case 2:
            await interaction.response.send_message(
                "Stage 2",
                ephemeral=True
            )

# to prevents next_stage until confirmation
def must_confirm(guild_id):
    setGuildVar(guild_id, "requires_confirmation", True)
    return None



# ──────────────────────────────────────────────—

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
    bot.run(TOKEN)
