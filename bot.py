import os, sys, re, asyncio
import discord
from discord import app_commands, Permissions
from discord.ext import commands
import math
from typing import Optional, List
from bracketool.domain import Competitor, Clash
from ai import get_name_submission

import random
from typing import List

from mr_bracket import Bracket, ClashInfo
from guild_state import setGuildVar, getGuildVar, clearGuild

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot_removing_reaction = {}

# ─── add this inside your file ─────────────────────────────────────

@bot.tree.command(name="start",
                  description="Begin team name bracket")
@app_commands.default_permissions(administrator=True)
async def start(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    current = getGuildVar(guild_id, "stage", 0)
    if current == 0:
        setGuildVar(guild_id, "stage", 1)
        if not await validate_start(interaction):
            return        
        await close_submissions(interaction.guild, os.getenv("BRACKET_CHANNEL_NAME"))
        await interaction.response.send_message("Starting bracket...", ephemeral=True)
        await process_stage(guild_id)
    else:
        await interaction.response.send_message(
            "Bracket has already started.",
            ephemeral=True
        )

@bot.tree.command(name="reset",
                  description="Reset stages")
@app_commands.default_permissions(administrator=True)
async def clear_stage(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    clearGuild(guild_id)
    await interaction.response.send_message(
        "✅ Reset Everything.",
        ephemeral=True
    )

@bot.tree.command(name="test",
                  description="Test something")
@app_commands.default_permissions(administrator=True)
async def clear_stage(interaction: discord.Interaction):
    guild = interaction.guild
    
    # Check if members intent is enabled
    members_intent_enabled = bot.intents.members
    
    # Try to get member count from guild object
    member_count = guild.member_count if hasattr(guild, 'member_count') else "Unknown"
    
    # Check how many members we can actually see
    visible_members = len(guild.members)
    visible_humans = len([m for m in guild.members if not m.bot])
    
    debug_info = (
        f"Debug Information:\n"
        f"- Members Intent Enabled: {members_intent_enabled}\n"
        f"- Guild Member Count: {member_count}\n"
        f"- Visible Members: {visible_members}\n"
        f"- Visible Humans: {visible_humans}\n"
    )
    
    await interaction.response.send_message(debug_info, ephemeral=True)

@bot.tree.command(name="confirm",
                 description="Confirms the pending operation")
@app_commands.default_permissions(administrator=True)
async def confirm(interaction: discord.Interaction):
    setGuildVar(interaction.guild_id, "requires_confirmation", False)
    await process_stage(interaction.guild_id)
    await interaction.response.send_message(
        getGuildVar(interaction.guild_id, "confirm_message",  "Confirmed"),
        ephemeral=True
    )
    setGuildVar(interaction.guild_id, "confirm_message", None)

@bot.tree.command(name="give_vote",
                  description="Give votes to users")
@app_commands.default_permissions(administrator=True)
async def give_vote(interaction: discord.Interaction, amount: int = 1, user_id: str = None):
    guild_id = interaction.guild.id
    
    if user_id is not None:
        try:
            user_id_int = int(user_id)
            current_votes = get_user_vote_count(guild_id, user_id_int)
            new_votes = current_votes + amount
            set_user_vote_count(guild_id, user_id_int, new_votes)
            
            user_name = user_id
            try:
                member = interaction.guild.get_member(user_id_int)
                if member:
                    user_name = member.display_name
            except:
                pass
            
            await interaction.response.send_message(
                f"Added {amount} vote(s) to {user_name}. New total: {new_votes}",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "Invalid user ID. Please provide a valid numeric ID.",
                ephemeral=True
            )
    else:
        non_bot_members = [member for member in interaction.guild.members if not member.bot]
        if not non_bot_members:
            await interaction.response.send_message(
                "No users found in the server.",
                ephemeral=True
            )
            return
        
        # Give votes to all non-bot users
        updated_users = 0
        for member in non_bot_members:
            current_votes = get_user_vote_count(guild_id, member.id)
            new_votes = current_votes + amount
            set_user_vote_count(guild_id, member.id, new_votes)
            updated_users += 1
        
        await interaction.response.send_message(
            f"Added {amount} vote(s) to {updated_users} users.",
            ephemeral=True
        )

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in {event}: {sys.exc_info()[1]}", flush=True)

@bot.event
async def on_ready():
    await bot.tree.sync()  # registers your slash commands with Discord
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)
    if message.guild is None:
        return
    bot_is_playing = getGuildVar(message.guild.id, "bot_is_playing", False)
    if message.author.bot and bot_is_playing == False:
        return
    
    guild_id = message.guild.id

    # Only handle if we are in the bracket channel
    bracket_channel_name = os.getenv("BRACKET_CHANNEL_NAME")
    if message.channel.name == bracket_channel_name:
        current_stage = getGuildVar(guild_id, "stage", 0)
        match current_stage:
            case 1:
                open_qual_mode = getGuildVar(guild_id, "open_qual_mode")
                match open_qual_mode:
                    case "submissions":
                        content = message.content.strip()
                        open_qual_round = getGuildVar(guild_id, "open_qual_round", 0)
                        round_subs: List = getGuildVar(guild_id, f"open_qual_round_{open_qual_round}_submissions", [])
                        qualified_submissions: List = getGuildVar(guild_id, "qualified_submissions", [])
                        min_sub_length = int(os.getenv("MIN_SUB_LENGTH", 3))
                        max_sub_length = int(os.getenv("MAX_SUB_LENGTH", 32))

                        # Check all submission rules
                        if len(content) < min_sub_length:
                            await message.delete()
                            await message.author.send(f"Your submission in {message.channel.mention} must be at least {min_sub_length} characters long.")
                            return
                        elif len(content) > max_sub_length:
                            await message.delete()
                            await message.author.send(f"Your submission in {message.channel.mention} must be at most {max_sub_length} characters long.")
                            return
                        for sub in round_subs:
                            if sub["name"].lower() == content.lower():
                                await message.delete()
                                await message.author.send(
                                    f"Your submission '{content}' in {message.channel.mention} is a duplicate for this round."
                                )
                                return
                        for sub in qualified_submissions:
                            if sub["name"].lower() == content.lower():
                                await message.delete()
                                await message.author.send(
                                    f"Your submission '{content}' in {message.channel.mention} has already qualified in a previous round."
                                )
                                return
                        # Passed, lets add to round submissions and process
                        round_subs.append({
                            "name": content,
                            "votes": []
                        })
                        setGuildVar(guild_id, f"open_qual_round_{open_qual_round}_submissions", round_subs)
                        await process_stage(guild_id)
                        return
                    case "voting":
                        await message.delete()
                        await message.interaction.response.send_message(
                            "Submissions are closed",
                            ephemeral=True
                        )
                        return
                return
            case 2:
                return

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:
        return
        
    bot_is_playing = getGuildVar(payload.guild_id, "bot_is_playing", False)
    if payload.user_id == bot.user.id and bot_is_playing == False:
        return
        
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return
        
    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return
        
    user = await bot.fetch_user(payload.user_id)
    for reaction in message.reactions:
        if str(reaction.emoji) == str(payload.emoji):
            await handle_reaction_add(reaction, user)
            break

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
    
    # prevent handling bot reactions
    key = f"{payload.message_id}:{payload.user_id}:{payload.emoji}"
    if key in bot_removing_reaction:
        if bot_removing_reaction[key] == True:
            print(f"Removing reaction {key} - NOT RUNNING HANDLE", flush=True)
            del bot_removing_reaction[key]
            return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return
    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return
    user = await bot.fetch_user(payload.user_id)
    for reaction in message.reactions:
        if str(reaction.emoji) == str(payload.emoji):
            await handle_reaction_remove(reaction, user)
            break
            W
async def handle_reaction_add(reaction: discord.Reaction, user: discord.User):
    if reaction.message.guild is None:
        return
    guild_id = reaction.message.guild.id
    bracket_channel_name = os.getenv("BRACKET_CHANNEL_NAME")
    if reaction.message.channel.name == bracket_channel_name:
        current_stage = getGuildVar(guild_id, "stage", 0)
        match current_stage:
            case 1:
                open_qual_mode = getGuildVar(guild_id, "open_qual_mode")
                match open_qual_mode:
                    case "submissions":
                        key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                        bot_removing_reaction[key] = True
                        await reaction.remove(user)
                        return
                    case "voting":
                        open_qual_round = getGuildVar(guild_id, "open_qual_round", 0)
                        round_submissions: List = getGuildVar(guild_id, f"open_qual_round_{open_qual_round}_submissions", [])

                        content = reaction.message.content
                        valid = False
                        for submission in round_submissions:
                            name = submission["name"]
                            # match "(number) name"
                            pattern = rf'^\(\s*\d+\s*\)\s*{re.escape(name)}$'
                            if re.match(pattern, content):
                                valid = True
                                break

                        exception_messages = [
                            "Use 👍 to add votes, Use ⭕ to clear your votes"
                        ]
                        if not valid and content not in exception_messages:
                            key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                            bot_removing_reaction[key] = True
                            await reaction.remove(user)
                            return
                        
                        match str(reaction.emoji):
                            case "👍":
                                user_votes_remaining = get_user_vote_count(guild_id, user.id)
                                if user_votes_remaining < 1:
                                    key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                                    bot_removing_reaction[key] = True
                                    await reaction.remove(user)
                                else:
                                    message_content = reaction.message.content
                                    total_message_votes = 0
                                    m = re.match(r'^\(\s*\d+\s*\)\s*(.+)$', message_content)
                                    if m:
                                        submission_name = m.group(1)
                                        # Find the submission in round_submissions
                                        for submission in round_submissions:
                                            if submission['name'] == submission_name:
                                                submission['votes'].append(user.id)
                                                total_message_votes = len(submission['votes'])
                                                break

                                        # Update the submissions in the guild state
                                        setGuildVar(
                                            guild_id,
                                            f"open_qual_round_{open_qual_round}_submissions",
                                            round_submissions
                                        )
                                    
                                    user_votes_remaining -= 1
                                    set_user_vote_count(guild_id, user.id, user_votes_remaining)

                                    # Update message content with new total
                                    old_content = reaction.message.content
                                    new_content = re.sub(r'\(\s*\d+\s*\)', f'({total_message_votes})', old_content, count=1)
                                    await reaction.message.edit(content=new_content)

                                    key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                                    bot_removing_reaction[key] = True
                                    await reaction.remove(user)

                                return
                            case "⭕":
                                live_submission_messages = getGuildVar(guild_id, "live_submission_messages", [])
                                user_votes_remaining = get_user_vote_count(guild_id, user.id)
                                for submission in round_submissions:
                                    # remove all of this users votes from the submission
                                    original_count = len(submission['votes'])
                                    submission['votes'] = [v for v in submission['votes'] if v != user.id]
                                    removed_count = original_count - len(submission['votes'])
                                    if removed_count == 0:
                                        continue

                                    user_votes_remaining += removed_count
                                    total_message_votes = len(submission['votes'])
                                    set_user_vote_count(guild_id, user.id, user_votes_remaining)
                                    # update live message
                                    for live_message in live_submission_messages:
                                        m = re.match(r'^\(\s*\d+\s*\)\s*(.+)$', live_message.content)
                                        if m:
                                            raw_name = m.group(1)
                                            if raw_name == submission['name']:
                                                new_content = re.sub(r'\(\s*\d+\s*\)', f'({total_message_votes})', live_message.content, count=1)
                                                await live_message.edit(content=new_content)
                                                break


                                key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                                bot_removing_reaction[key] = True
                                await reaction.remove(user)
                            case _:
                                key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                                bot_removing_reaction[key] = True
                                await reaction.remove(user)

                        await process_stage(guild_id)
                        return
                return
            case 2:
                playoff_mode = getGuildVar(guild_id, "playoff_mode", "view")
                if playoff_mode == "view":
                    return
                elif playoff_mode == "voting":
                    current_clash: ClashInfo = getGuildVar(guild_id, "current_clash")
                    # check if current_clash was properly setup
                    if not (hasattr(current_clash, "team1emoji") and hasattr(current_clash, "team2emoji")):
                        return

                    team1_votes = getGuildVar(guild_id, "team1_votes", [])
                    team2_votes = getGuildVar(guild_id, "team2_votes", [])

                    match reaction.emoji:
                        case current_clash.team1emoji:
                            team1_votes.append(user.id)
                            team2_votes = [uid for uid in team2_votes if uid != user.id]

                            key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                            bot_removing_reaction[key] = False
                            await reaction.message.remove_reaction(current_clash.team2emoji, user)
                        case current_clash.team2emoji:
                            team2_votes.append(user.id)
                            team1_votes = [uid for uid in team1_votes if uid!= user.id]

                            key = f"{reaction.message.id}:{user.id}:{reaction.emoji}"
                            bot_removing_reaction[key] = False
                            await reaction.message.remove_reaction(current_clash.team1emoji, user)

                    setGuildVar(guild_id, "team1_votes", team1_votes)
                    setGuildVar(guild_id, "team2_votes", team2_votes)
                    await process_stage(guild_id)

                return
            
async def handle_reaction_remove(reaction: discord.Reaction, user: discord.User):
    if user.bot or reaction.message.guild is None:
        return
    
    guild_id = reaction.message.guild.id
    bracket_channel_name = os.getenv("BRACKET_CHANNEL_NAME")
    if reaction.message.channel.name == bracket_channel_name:
        current_stage = getGuildVar(guild_id, "stage", 0)
        match current_stage:
            case 2:
                playoff_mode = getGuildVar(guild_id, "playoff_mode", "view")
                if playoff_mode == "voting":
                    current_clash: ClashInfo = getGuildVar(guild_id, "current_clash")
                    # check if current_clash was properly setup
                    if not (hasattr(current_clash, "team1emoji") and hasattr(current_clash, "team2emoji")):
                        print("Current clash not properly setup on add", flush=True)
                        return

                    team1_votes = getGuildVar(guild_id, "team1_votes", [])
                    team2_votes = getGuildVar(guild_id, "team2_votes", [])

                    match reaction.emoji:
                        case current_clash.team1emoji:
                            team1_votes = [uid for uid in team1_votes if uid != user.id]
                        case current_clash.team2emoji:
                            team2_votes = [uid for uid in team2_votes if uid != user.id]

                    setGuildVar(guild_id, "team1_votes", team1_votes)
                    setGuildVar(guild_id, "team2_votes", team2_votes)
                    await process_stage(guild_id)

async def process_stage(guild_id: int):
    current_stage = getGuildVar(guild_id, "stage", 0)
    bracket_channel_name = os.getenv("BRACKET_CHANNEL_NAME")
    
    match current_stage:
        case 1:
            # validate env settings
            max_submissions = int(os.getenv("OPEN_QUAL_MAX_ROUND_SUBMISSONS"))
            total_rounds = int(os.getenv("OPEN_QUAL_ROUNDS"))
            total_qual_spots = int(os.getenv("OPEN_QUAL_PASSTHRU_SUBMISSIONS"))
            user_votes_per_round = os.getenv("OPEN_QUAL_MAX_VOTES", 3)

            # Beging processing
            open_qual_round = getGuildVar(guild_id, "open_qual_round", 0)
            qualified_submissions = getGuildVar(guild_id, "qualified_submissions", [])
            open_qual_mode = getGuildVar(guild_id, "open_qual_mode", "submissions")

            # detect initial setup
            if open_qual_round == 0:
                # Setup first round
                open_qual_mode = "submissions"
                open_qual_round = 1

            total_remaining_qual_spots = total_qual_spots - len(qualified_submissions)
            round_qual_spots = math.floor(total_remaining_qual_spots / (total_rounds - (open_qual_round - 1)))
            
            round_submissions: List = getGuildVar(guild_id, f"open_qual_round_{open_qual_round}_submissions", [])
            if open_qual_mode == "submissions":

                # New round just started
                if len(round_submissions) == 0 and await is_submission_open(bot.get_guild(guild_id), bracket_channel_name) == False:
                    setGuildVar(guild_id, "requires_confirmation", True)
                    await open_submissions(bot.get_guild(guild_id), bracket_channel_name)
                    await send_channel_message(guild_id, bracket_channel_name ,f"Submissions Open! {open_qual_round}/{total_rounds}")
                    await send_channel_message(guild_id, bracket_channel_name, f"We'll accept a total of {max_submissions} names... Go!")
                elif len(round_submissions) >= max_submissions:
                    # ensure submissions don't exceed max
                    while len(round_submissions) > max_submissions:
                        round_submissions.pop()
                    await close_submissions(bot.get_guild(guild_id), bracket_channel_name)
                    open_qual_mode = "voting"
                    await send_channel_message(guild_id, bracket_channel_name ,f"Submissions closed...")
                    await send_channel_message(guild_id, bracket_channel_name, f"Each person gets {user_votes_per_round} votes")
                    await send_channel_message(guild_id, bracket_channel_name, f"The top {round_qual_spots} most voted names qualify for playoffs 😎")
                    instruction_message = await send_channel_message(guild_id, bracket_channel_name ,f"Use 👍 to add votes, Use ⭕ to clear your votes")
                    await instruction_message.add_reaction("⭕")
                    clear_user_votes(guild_id)

                    live_submission_messages = []
                    # Prepare all message sending tasks
                    message_tasks = []
                    for submission in round_submissions:
                        message_tasks.append(send_channel_message(guild_id, bracket_channel_name, f"(0) {submission['name']}"))
                    
                    # Execute all message sending tasks in parallel
                    messages = await asyncio.gather(*message_tasks)
                    live_submission_messages.extend(messages)
                    
                    # Now add reactions to all messages
                    reaction_tasks = []
                    for message in live_submission_messages:
                        reaction_tasks.append(message.add_reaction("👍"))
                    
                    # Wait for all reactions to be added
                    await asyncio.gather(*reaction_tasks)
                    
                    # Store the messages for later reference
                    setGuildVar(guild_id, f"live_submission_messages", live_submission_messages)

                    # Bot can vote too !    
                    bot_is_playing = os.getenv("BOT_IS_PLAYING", "false").lower() == "true"
                    if bot_is_playing and getGuildVar(guild_id, "bot_is_playing", False) == False:
                        setGuildVar(guild_id, "bot_is_playing", True)
                        bot_votes = int(os.getenv("BOT_VOTES", 1))
                        # Randomly select messages to vote on until bot_votes is reached
                        if live_submission_messages and bot_votes > 0:
                            random_messages = [random.choice(live_submission_messages) for _ in range(bot_votes)]
                            print(f"Bot is voting on {len(random_messages)} submissions", flush=True)
                            
                            # Add reactions to the randomly selected messages
                            for message in random_messages:
                                # Now manually process the vote logic (similar to handle_reaction_add)
                                message_content = message.content
                                total_message_votes = 0
                                m = re.match(r'^\(\s*\d+\s*\)\s*(.+)$', message_content)
                                
                                if m:
                                    submission_name = m.group(1)
                                    for submission in round_submissions:
                                        if submission['name'] == submission_name:
                                            # Add bot's vote
                                            submission['votes'].append(bot.user.id)
                                            total_message_votes = len(submission['votes'])
                                            break
                                    
                                    # Update the submissions in the guild state
                                    setGuildVar(
                                        guild_id,
                                        f"open_qual_round_{open_qual_round}_submissions",
                                        round_submissions
                                    )
                                
                                    # Update message content with new vote count
                                    new_content = re.sub(r'\(\s*\d+\s*\)', f'({total_message_votes})', message_content, count=1)
                                    await message.edit(content=new_content)
                                    print(f"Bot voted for: {submission_name}, new vote count: {total_message_votes}", flush=True)
                        
                        setGuildVar(guild_id, "bot_is_playing", False)

                    setGuildVar(guild_id, f"live_submission_messages", live_submission_messages)
                else:
                    # event processing lands here
                    bot_is_playing = os.getenv("BOT_IS_PLAYING", "false").lower() == "true"
                    setGuildVar(guild_id, "confirm_message", "Still collecting submissions..." + ("(spam to trigger bot submissions)" if bot_is_playing else ""))
                    setGuildVar(guild_id, "requires_confirmation", True)
                    if bot_is_playing and getGuildVar(guild_id, "bot_is_playing", False) == False:
                        msg_freq = int(os.getenv("BOT_SUBMISSION_FREQUENCY", 3))
                        amt_msgs_since_last_bot_sub = getGuildVar(guild_id, "amt_msgs_since_last_bot_sub", 0)
                        amt_msgs_since_last_bot_sub += 1
                        if amt_msgs_since_last_bot_sub >= msg_freq:
                            setGuildVar(guild_id, "bot_is_playing", True)
                            amt_msgs_since_last_bot_sub = 0
                            print("Sending bot message...", flush=True)
                            await send_channel_message(guild_id, bracket_channel_name, get_name_submission())
                            setGuildVar(guild_id, "bot_is_playing", False)
                        setGuildVar(guild_id, "amt_msgs_since_last_bot_sub", amt_msgs_since_last_bot_sub)
            elif open_qual_mode == "voting":
                check_count = min(round_qual_spots + 1, len(round_submissions))
                # Admin must confirm round submission
                if getGuildVar(guild_id, "requires_confirmation") == False:
                    setGuildVar(guild_id, "requires_confirmation", True)
                    # sort by most votes
                    round_submissions.sort(key=lambda x: x["votes"], reverse=True)
                    force_tie_breaker = os.getenv("OPEN_QUAL_FORCE_TIE_BREAKER", "false").lower() == "true"
                    if force_tie_breaker:
                        top_submissions = round_submissions[:check_count]
                        for submission in top_submissions:
                            for sub_submission in round_submissions:
                                if sub_submission["name"] != submission["name"]:
                                    if len(sub_submission["votes"]) == len(submission["votes"]):
                                        setGuildVar(guild_id, "confirm_message", "Break the Tie!")
                                        return

                    # round confirmed
                    round_qual_submissions = round_submissions[:round_qual_spots]
                    open_qual_round += 1
                    open_qual_mode = "submissions"
                    qualified_submissions = getGuildVar(guild_id, "qualified_submissions", [])
                    qualified_submissions.extend(round_qual_submissions)
                    setGuildVar(guild_id, "qualified_submissions", qualified_submissions)
                    setGuildVar(guild_id, "open_qual_round", open_qual_round)
                    setGuildVar(guild_id, "open_qual_mode", open_qual_mode)

                    message = ""
                    for idx, submission in enumerate(round_qual_submissions):
                        message += f"**{submission['name']}**"
                        if idx + 1 < len(round_qual_submissions) - 1:
                            message += ", "
                        elif idx + 1 == len(round_qual_submissions) - 1:
                            message += " and "

                    if len(round_qual_submissions) > 0:
                        await send_channel_message(guild_id, bracket_channel_name, message + " are moving on!")

                    # stage cofirmed
                    if len(qualified_submissions) == total_qual_spots:
                        setGuildVar(guild_id, "stage", 2)
                    
                    return await process_stage(guild_id)

                return
            # update vars
            setGuildVar(guild_id, "open_qual_mode", open_qual_mode)
            setGuildVar(guild_id, "open_qual_round", open_qual_round)
        case 2:
            playoff_mode = getGuildVar(guild_id, "playoff_mode", "view")

            if playoff_mode == "view":
                bracket: Bracket = getGuildVar(guild_id, "bracket", None)

                # initialize bracket for first time
                if bracket is None:
                    setGuildVar(guild_id, "requires_confirmation", True)
                    bracket = Bracket()
                    qualified_submissions = getGuildVar(guild_id, "qualified_submissions", [])
                    for submission in qualified_submissions:
                        bracket.add_name(submission["name"], len(submission["votes"]))
                        # reset for playoffs
                        submission["votes"] = []

                    bracket.finalize()
                    setGuildVar(guild_id, "bracket", bracket)

                view_message = getGuildVar(guild_id, "view_message", f"The Top {len(bracket._bracket.rounds[bracket.rounds - 1]) * 2} is here!")

                # generate standings
                image_path = bracket.generate_standings(guild_id)
                await send_channel_image(guild_id, 
                                         bracket_channel_name,
                                         image_path,
                                         view_message)
                
                playoff_mode = "voting"
                setGuildVar(guild_id, "playoff_mode", playoff_mode)

                return
            elif playoff_mode == "voting":
                # Admin must confirm match submission
                if getGuildVar(guild_id, "requires_confirmation") == False:
                    setGuildVar(guild_id, "requires_confirmation", True)
                    bracket: Bracket = getGuildVar(guild_id, "bracket")
                    current_clash: ClashInfo = getGuildVar(guild_id, "current_clash")

                    if current_clash is None:
                        current_clash = bracket.get_next_clash()
                        await send_channel_message(guild_id, bracket_channel_name, "Which name is more worthy?")
                        emoji1, emoji2 = get_emoji_clash_pair()
                        # stash them on the clash object
                        current_clash.team1emoji = emoji1
                        current_clash.team2emoji = emoji2

                        # send the VS line
                        vs_text = f"**{current_clash.team1}** {emoji1} VS **{current_clash.team2}** {emoji2}"
                        msg = await send_channel_message(guild_id, bracket_channel_name, vs_text)

                        # add the reactions for voting
                        await msg.add_reaction(emoji1)
                        await msg.add_reaction(emoji2)

                        setGuildVar(guild_id, "current_clash", current_clash)

                    elif bracket.get_winner() is None:
                        team1_votes = getGuildVar(guild_id, "team1_votes", [])
                        team2_votes = getGuildVar(guild_id, "team2_votes", [])

                        # ensure we do not have a atie
                        if len(team1_votes) != len(team2_votes):
                            message = ""
                            if len(team1_votes) > len(team2_votes):
                                bracket.submit_winner(current_clash.team1, len(team1_votes), len(team2_votes))
                                message = f"**{current_clash.team1}** is moving on!"
                            else:
                                bracket.submit_winner(current_clash.team2, len(team2_votes), len(team1_votes))
                                message = f"**{current_clash.team2}** is moving on!"

                            current_clash = None
                            if bracket.get_winner() is not None:
                                message = f"Well it's official! The winner is **{bracket.get_winner()}**!"
                                current_clash = ClashInfo(0, 0, "", "")

                            setGuildVar(guild_id, "view_message", message)

                            team1_votes = []
                            team2_votes = []
                            playoff_mode = "view"
                            setGuildVar(guild_id, "current_clash", current_clash)
                            setGuildVar(guild_id, "team1_votes", team1_votes)
                            setGuildVar(guild_id, "team2_votes", team2_votes)
                            setGuildVar(guild_id, "playoff_mode", playoff_mode)
                            await process_stage(guild_id)
                        else:
                            setGuildVar(guild_id, "confirm_message", "We need a tiebreaker vote...")
                    else:
                        print("POST WINNER CELEBRATION", flush=True)
                        bracket: Bracket = getGuildVar(guild_id, "bracket")
                        img_path = bracket.generate_win_meme(guild_id, "pass_sword")
                        await send_channel_image(guild_id, bracket_channel_name, img_path)
                        return

                    return
                return

def prompt_confirmation(interaction):
    setGuildVar(interaction.guild.id, "requires_confirmation", True)

async def open_submissions(guild: discord.Guild, channel_name: str):
    # find the channel by name
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel is None:
        return None

    # compute a new overwrite for @everyone
    overwrite = channel.overwrites_for(guild.default_role)
    overwrite.send_messages = True
    overwrite.add_reactions = False

    # apply the permission overwrite
    await channel.set_permissions(guild.default_role, overwrite=overwrite)
    return None

async def close_submissions(guild: discord.Guild, channel_name: str):
    # find the channel by name
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel is None:
        return None

    # compute a new overwrite for @everyone
    overwrite = channel.overwrites_for(guild.default_role)
    overwrite.send_messages = False
    overwrite.add_reactions = False

    # apply the permission overwrite
    await channel.set_permissions(guild.default_role, overwrite=overwrite)
    return None

async def is_submission_open(guild: discord.Guild, channel_name: str):
    # find the channel by name
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel is None:
        return None

    # compute the current permissions
    permissions = channel.permissions_for(guild.default_role)
    return permissions.send_messages
def validate_submission(interaction):
    # Max 16 characters
    return None

async def validate_start(interaction: discord.Interaction):
    max_submissions = int(os.getenv("OPEN_QUAL_MAX_ROUND_SUBMISSONS"))
    total_rounds = int(os.getenv("OPEN_QUAL_ROUNDS"))
    submission_passthru = int(os.getenv("OPEN_QUAL_PASSTHRU_SUBMISSIONS"))
    bracket_channel_name = os.getenv("BRACKET_CHANNEL_NAME")
    force_tie_breaker = os.getenv("OPEN_QUAL_FORCE_TIE_BREAKER", "false").lower()

    if bracket_channel_name is None:
        await interaction.response.send_message(
            "Error: Bracket channel name not set in environment variables.",
            ephemeral=True
        )
        return False
    if total_rounds < 1:
        await interaction.response.send_message(
            "Error: Number of rounds must be greater than 0.",
            ephemeral=True
        )
        return False
    min_max_submissions = math.ceil(submission_passthru /total_rounds)
    if max_submissions < min_max_submissions:
        await interaction.response.send_message(
            f"Error: Maximum submissions per round is {min_max_submissions}.",
            ephemeral=True
        )
        return False
    # Check if submission_passthru is NOT a power of 2
    if submission_passthru <= 0 or (submission_passthru & (submission_passthru - 1)) != 0:
        await interaction.response.send_message(
            "Error: Number of submissions must be a power of 2 (2, 4, 8, 16, 32, etc.).",
            ephemeral=True
        )
        return False
    if force_tie_breaker not in ["true", "false"]:
        await interaction.response.send_message(
            "Error: OPEN_QUAL_FORCE_TIE_BREAKER must be 'true' or 'false'.",
            ephemeral=True
        )
        return False
    return True

async def send_channel_message(guild_id: int, channel_name: str, content: str):
    # Get the guild
    guild = bot.get_guild(guild_id)
    if not guild:
        print(f"Error: Could not find guild with ID {guild_id}", flush=True)
        return None
    
    # Find the channel
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        print(f"Error: Could not find channel '{channel_name}' in guild {guild.name}", flush=True)
        return None
    
    # Send the message
    return await channel.send(content)


async def send_channel_image(guild_id: int, channel_name: str, image_path: str, content: str = None) -> Optional[discord.Message]:
    # Get the guild
    guild = bot.get_guild(guild_id)
    if not guild:
        print(f"Error: Could not find guild with ID {guild_id}", flush=True)
        return None
    
    # Find the channel
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        print(f"Error: Could not find channel '{channel_name}' in guild {guild.name}", flush=True)
        return None
    
    # Check if the file exists
    if not os.path.isfile(image_path):
        print(f"Error: Image file not found at path: {image_path}", flush=True)
        return None
    
    try:
        # Create a file object from the image path
        file = discord.File(image_path)
        
        # Send the message with the file
        return await channel.send(content=content, file=file)
    except Exception as e:
        print(f"Error sending image: {str(e)}", flush=True)
        return None


def get_user_vote_count(guild_id: int, user_id: int) -> int:
    """
    Get the number of votes a user has left.
    Creates and initializes the count if it doesn't exist.
    """
    # Get the user vote count dictionary, default to empty dict if not exists
    user_vote_count = getGuildVar(guild_id, "user_vote_count", {})
    
    # Convert user_id to string since JSON keys are strings
    user_id_str = str(user_id)
    
    # Check if the user exists in the dictionary
    if user_id_str not in user_vote_count:
        # User doesn't exist, create entry with default max votes
        max_votes = int(os.getenv("OPEN_QUAL_MAX_VOTES", 3))
        user_vote_count[user_id_str] = max_votes
        
        # Save the updated dictionary
        setGuildVar(guild_id, "user_vote_count", user_vote_count)
    
    # Return the user's vote count
    return user_vote_count[user_id_str]

def set_user_vote_count(guild_id: int, user_id: int, count: int) -> None:
    """
    Set the number of votes a user has left.
    """
    # Get the user vote count dictionary, default to empty dict if not exists
    user_vote_count = getGuildVar(guild_id, "user_vote_count", {})
    
    # Convert user_id to string since JSON keys are strings
    user_id_str = str(user_id)
    
    # Set the user's vote count
    user_vote_count[user_id_str] = count
    
    # Save the updated dictionary
    setGuildVar(guild_id, "user_vote_count", user_vote_count)


def clear_user_votes(guild_id: int) -> None:
    """
    Clear all user vote counts for a specific guild.
    This resets the voting state for everyone in the guild.
    """
    # Set an empty dictionary to reset all user votes
    setGuildVar(guild_id, "user_vote_count", {})

def get_emoji_clash_pair() -> list[str]:
    pairs = [
        ["🐨", "🐻"],
        ["🦁", "🐯"],
        ["🐱", "🐶"],
        ["🐼", "🐵"],
        ["🦊", "🐺"],
        ["🐮", "🐷"],
        ["🐸", "🐭"],
        ["🐲", "🦄"],
        ["🐧", "🦉"],
        ["🦝", "🐰"],
    ]
    return random.choice(pairs)

# ──────────────────────────────────────────────—

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")
    bot.run(TOKEN)
