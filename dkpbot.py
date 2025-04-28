import discord
import os
import time
import pymysql
import random
import datetime

from dotenv import load_dotenv
from discord.ext import tasks
from collections import defaultdict
from asyncio import sleep
from contextlib import contextmanager

load_dotenv() # load all the variables from the env file
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
bot = discord.Bot(intents=intents)
log_channel = int(os.getenv('LOG_CHANNEL'))
results_channel = int(os.getenv('RESULTS_CHANNEL'))


try:
    mydb = pymysql.connect(
        host="127.0.0.1",
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        database="dkpbot"
    )
    print("post")
except Exception as err:
    print(f"Connection error: {err}")


@contextmanager
def get_cursor(commit=False, **kwargs):
    mydb.ping(reconnect=True)
    cursor = mydb.cursor(**kwargs)  # Create the cursor
    try:
        yield cursor  # Yield control to the caller
        if commit:  # If we need to commit, commit changes
            mydb.commit()
    except Exception as e:
        print(f"Error during database operation: {e}")
        mydb.rollback()  # Optionally, rollback on error
        raise  # Re-raise the error to propagate it
    finally:
        cursor.close()  # Always close the cursor after use

bid_dict = {}
close_dict = {}
roll_dict = {}
item_cache = {}
roll_tracker= defaultdict(set)

async def send_log_channel_message(message):
    chan = bot.get_channel(log_channel)
    await chan.send(message)

def create_character_record(discord_id, character_name, character_class):
    if(check_if_main_record_exists(discord_id) == False):
        create_main_record(discord_id,character_name,0,character_class)
        return "Created record for " + character_name
    else:
        name = get_main_name_by_discord_id(discord_id)
        ret = (f"A record already exists for your account for character name: {name}")
        return ret


def get_main_name_by_discord_id(id):
    with get_cursor() as mycursor:
        mycursor.execute("SELECT main_name FROM dkp WHERE discord_id = %s",(id,))
        row = mycursor.fetchone()
        if row:
            return row[0]
        else:
            return "`No character registered for this discord ID`"

def check_if_main_record_exists(discord_id):
    with get_cursor() as mycursor:
        mycursor.execute("SELECT dkp_value FROM dkp WHERE discord_id = %s",(discord_id,))
        row = mycursor.fetchone()
        return row is not None

def create_main_record(discord_id,main_name,dkp_value,character_class):
    with get_cursor(commit=True) as mycursor:
        mycursor.execute("INSERT INTO dkp (discord_id,main_name,dkp_value,character_class) VALUES (%s, %s, %s, %s)",(discord_id,main_name,dkp_value,character_class))

def create_bid(item_name,timeout,timeout_seconds,channel_id):
    with get_cursor(commit=True) as mycursor:
        mycursor.execute("INSERT INTO bids (item_name,timeout,timeout_reset,channel_id) VALUES (%s, %s, %s, %s)",(item_name,timeout,timeout_seconds,channel_id))

def create_roll(item_name,channel_id):
    with get_cursor(commit=True) as mycursor:
        mycursor.execute("INSERT INTO rolls (item_name,channel_id) VALUES (%s,%s)",(item_name,channel_id))

def add_attendance_tick(granted_by):
    with get_cursor(commit=True) as mycursor:
        mycursor.execute("INSERT INTO attendance (granted_by) VALUES (%s)", (granted_by,))

def add_user_attendance_records(discord_ids):
    with get_cursor(commit=True) as mycursor:
        query = "INSERT INTO attendance_ticks (discord_id) VALUES (%s)"
        values = [(discord_id,) for discord_id in discord_ids]
        mycursor.executemany(query, values)

@tasks.loop(seconds=1.0)
async def slow_count():
    #print("slow loop check " + str(slow_count.current_loop))
    if not bid_dict and not close_dict and not roll_dict:
        #print("stopping slow loop at: " + str(slow_count.current_loop))
        slow_count.stop()
    for key, value in list(bid_dict.items()):
        current_time = int(time.time())
        rounded_value = int(value)
        if rounded_value - current_time == 30:
            channel = bot.get_channel(key)
            if channel:
                await channel.send("⏰ 30 seconds left to bid.")
        elif rounded_value - current_time == 10:
            channel = bot.get_channel(key)
            if channel:
                await channel.send("⏰ 10 seconds left to bid.")
        #print(f"Key: {key}, Value: {value}")
        if value < time.time():
            channel = bot.get_channel(key)
            if channel:
                await channel.send("Bids are now closed. Channel will close in 20 seconds.")
            del bid_dict[key]
            await complete_bid(key)
    for key, value in list(roll_dict.items()):
        current_time = int(time.time())
        rounded_value = int(value)
        if rounded_value - current_time == 30:
            channel = bot.get_channel(key)
            if channel:
                await channel.send("⏰ 30 seconds left to roll.")
        elif rounded_value - current_time == 10:
            channel = bot.get_channel(key)
            if channel:
                await channel.send("⏰ 10 seconds left to roll.")
        if value < time.time():
            channel = bot.get_channel(key)
            if channel:
                await channel.send("Rolls are now closed. Channel will close in 20 seconds.")
            del roll_dict[key]
            await complete_roll(key)
    for key, value in list(close_dict.items()):
        current_time = int(time.time())
        rounded_value = int(value)
        if value < time.time():
            channel = bot.get_channel(key)
            del close_dict[key]
            await channel.delete()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

async def complete_bid(channel_id):
    with get_cursor(commit=True) as mycursor:
        mycursor.execute("SELECT item_name,top_bidder,top_bid_amt,second_bidder,second_bid_amt,main_has_bid FROM bids WHERE channel_id = %s", (channel_id,))
        result = mycursor.fetchone()
        if not result: #weird error
            await send_log_channel_message(f"Error in bid #<{channel_id}>. did not return bid results upon complete.")
            return
        
        item_won, winner_id, amount_paid, second_bidder_id, second_bid_amt, main_has_bid = result

        if winner_id is None: #nobody bid. Grats rot.
            channel = bot.get_channel(results_channel)
            await channel.send(
                f"**🏅 Bidding Complete!**\n"
                f"**Item:** {item_won}\n"
                f"**Winner:** Rot!"
            )
            return
        
        #get winner name
        mycursor.execute("SELECT main_name, dkp_value FROM dkp WHERE discord_id = %s",(winner_id,))
        result = mycursor.fetchone()
        if result:
            winner_name, winner_before_dkp = result
        else:
            winner_name = "Rot"

        #get 2nd place winner name
        mycursor.execute("SELECT main_name FROM dkp WHERE discord_id = %s",(second_bidder_id,))
        result = mycursor.fetchone()
        if result:
            second_winner_name = result[0]
        else:
            second_winner_name = "None"
        
        #put data in completed bids
        query="INSERT INTO completed_bids (item_name,winner,dkp_cost,second_place,second_place_bid) VALUES (%s, %s, %s, %s, %s)"
        val = (item_won,winner_name,amount_paid,second_winner_name,second_bid_amt)
        mycursor.execute(query,val)

        #delete old bid row
        mycursor.execute("DELETE FROM bids WHERE channel_id = %s", (channel_id,))

        #update winner dkp
        winner_after_dkp = winner_before_dkp - amount_paid
        mycursor.execute("UPDATE dkp SET dkp_value = %s WHERE discord_id = %s", (winner_after_dkp, winner_id))
        result_string =(
            f"```🏅 Bidding Complete!\n"
            f"Item: {item_won}\n"
            f"Winner: {winner_name} for {amount_paid} DKP\n"
        )

        #add second place info if exists
        if second_bid_amt != 0:
            result_string += f"Second Place: {second_winner_name} with a bid of {second_bid_amt} DKP\n```"
        else:
            result_string += "```"
        
        #build log msg
        log_message = f"💰 Bid complete for `{item_won}`. Winner: **{winner_name}** for {amount_paid} DKP."
        if main_has_bid:
            log_message += (f"`main`")
        else:
            log_message += (f"`alt`")

        #send log msg, also send to main channel for readability.
        chan = bot.get_channel(channel_id)
        await chan.send(log_message)
        await send_log_channel_message(log_message)
        
        #send pretty result msg
        channel = bot.get_channel(results_channel)
        await channel.send(result_string)

async def complete_roll(channel_id):
    #pull winner ids from db, congratulate in log channel.
    with get_cursor() as mycursor:
        query="SELECT item_name,winner_id,second_id,winner_roll,second_roll,main_has_rolled FROM rolls WHERE channel_id = %s"
        val = (channel_id,)
        mycursor.execute(query,val)
        result = mycursor.fetchone()
        if result:
            item_name, winner_id, second_id, winner_roll,second_roll,main_has_rolled = result
            winner_name = get_main_name_by_discord_id(winner_id)
            message = (f"🎲 Roll completed for `{item_name}`. Winner: {winner_name} with a roll of {winner_roll}.")
            if main_has_rolled:
                message += (f"`main`")
            else:
                message += (f"`alt`")
            await send_log_channel_message(message)
            chan = bot.get_channel(channel_id)
            await chan.send(f"🎲 Roll completed for `{item_name}`. Winner: **{winner_name}** with a roll of {winner_roll}.")
            if second_id is not None:
                second_name = get_main_name_by_discord_id(second_id)
                await send_log_channel_message(f"└    Runner-up: {second_name} with a roll of {second_roll}.")
                await chan.send(f"└    Runner-up: {second_name} with a roll of {second_roll}.")
            #delete row
            mycursor.execute("DELETE FROM rolls WHERE channel_id = %s", (channel_id,))
        else:
            await send_log_channel_message(f"Unable to retrieve roll results for channel: <#{channel_id}>.")

@bot.slash_command(name="register", description="Register a character with the bot.")
async def register(
    ctx: discord.ApplicationContext,
    character_name:str, 
    character_class: discord.Option(
        str,
        description="Your main character's class.",
        choices=['Bard', 'Beastlord', 'Cleric', 'Druid', 'Enchanter', 'Magician','Monk', 'Necromancer', 'Paladin', 'Ranger', 'Rogue','Shadowknight', 'Shaman', 'Warrior', 'Wizard'],
        )):
        returnstring = create_character_record(ctx.author.id,character_name,character_class)
        await ctx.respond(returnstring,ephemeral=True)
        await send_log_channel_message(f"{ctx.author.mention} created DKP log for character: {character_name} class: {character_class}")

@bot.slash_command(name="unregister", description="Remove a DKP record from the bot.")
async def unregister(
    ctx: discord.ApplicationContext,
    character_name: str,
    reason:str
):
    with get_cursor(commit=True) as mycursor:
        mycursor.execute("SELECT * FROM dkp WHERE main_name = %s", (character_name,))
        result = mycursor.fetchone()
        if result is None:
            await ctx.respond(f"Unable to find record for main name: {character_name}",ephemeral=True)
            return
        mycursor.execute("DELETE FROM dkp WHERE main_name = %s", (character_name,))
        await ctx.respond(f"Record for {character_name} deleted.",ephemeral=True)
        logmessage = (f"{ctx.author.mention} deleted DKP record for character: {character_name}")
        if reason:
            logmessage += (f" for reason: {reason}")
        await send_log_channel_message(logmessage)


@bot.slash_command(name="startbid", description="Start bid on item for duration")
async def startbid(ctx: discord.ApplicationContext, item_name:str, duration:int):
    #add sql to add to bids, start loop that checks if bid has ended
    endtime = time.time() + duration
    cat = discord.utils.get(ctx.guild.channels, name="Bot")
    chan = await ctx.guild.create_text_channel(name=f"💰-{item_name}",category=cat)
    await chan.send(
        f"**📢 Bidding now open for `{item_name}`!**\n"
        f"Start placing your bids using `/bid` now!\n"
        f"⏳ This auction will close automatically in {duration} seconds.")
    channel_id = chan.id
    create_bid(item_name,endtime,30,channel_id)
    bid_dict[channel_id] = endtime
    close_dict[channel_id] = endtime + 20
    if not slow_count.is_running():
        slow_count.start()
    await ctx.respond(f"Started bid for: {item_name} for {str(duration)} seconds",ephemeral=True)
    await send_log_channel_message(f"{ctx.author.mention} started bid for {item_name} in <#{channel_id}> duration: {duration} seconds.")

@bot.slash_command(name="startroll", description="Start a roll off for an item")
async def startroll(ctx: discord.ApplicationContext, item_name:str, duration:int):
    endtime = time.time() + duration
    cat = discord.utils.get(ctx.guild.channels, name="Bot")
    chan = await ctx.guild.create_text_channel(name=f"🎲-{item_name}",category=cat)
    await chan.send(
        f"**📢 Rolls are now open for `{item_name}`!**\n"
        f"Start placing your bids using `/roll` now!\n"
        f"⏳ This roll will close automatically in {duration} seconds.")
    channel_id = chan.id
    create_roll(item_name,channel_id)
    roll_dict[channel_id] = endtime
    close_dict[channel_id] = endtime + 20
    if not slow_count.is_running():
        slow_count.start()
    await ctx.respond(f"Started roll for: {item_name} for {str(duration)} seconds",ephemeral=True)
    await send_log_channel_message(f"{ctx.author.mention} started roll for {item_name} in <#{channel_id}> duration: {duration} seconds.")

@bot.slash_command(name="roll", description="Roll on an item in its roll channel.")
async def roll(ctx: discord.ApplicationContext, roll_type: discord.Option(str, choices=['main','alt'])):
    if ctx.channel.id not in roll_dict and ctx.channel_id in close_dict:
        await ctx.respond("Rolls on this item have closed.", ephemeral=True)
        return
    if ctx.channel.id not in roll_dict:
        await ctx.respond("You can't use this command here. Use `/roll` in the channel for the item you want to roll on.", ephemeral=True)
        return
    #check roll_tracker
    roller_id = ctx.author.id
    channel_id = ctx.channel.id
    if roller_id in roll_tracker[channel_id]:
        await ctx.respond("You've already rolled in this channel.", ephemeral=True)
        return
    #pull info from db
    with get_cursor(commit=True) as mycursor:
        roll_value = random.randint(0, 10000)
        await ctx.respond("Good luck!", ephemeral=True)
        await ctx.channel.send(f"{ctx.author.mention} rolled a {roll_value} for `{roll_type}`!")

        # Fetch current roll data
        query = "SELECT winner_id, winner_roll, second_roll, main_has_rolled FROM rolls WHERE channel_id = %s"
        mycursor.execute(query, (channel_id,))
        result = mycursor.fetchone()

        if not result:
            await ctx.respond("Roll does not exist.", ephemeral=True)
            return
        # get our vars
        winner_id, winner_roll, second_roll, main_has_rolled = result

        # prevent alt roll if a main has rolled
        if roll_type == 'alt' and main_has_rolled:
            await ctx.respond("A main has already rolled on this item.", ephemeral=True)
            return

        # determine if roller takes first or second place
        update_fields = {}

        if roll_value > winner_roll or (roll_type == 'main' and not main_has_rolled):
            if roll_type == 'main' and not main_has_rolled:
                main_has_rolled = 1  # Mark that a main has rolled
            update_fields.update({
                "winner_id": roller_id,
                "winner_roll": roll_value,
                "second_id": winner_id,
                "second_roll": winner_roll,
                "main_has_rolled": main_has_rolled
            })
            await ctx.channel.send(f"📢 {ctx.author.mention} is now winning with a roll of {roll_value}.")
        elif roll_value > second_roll:
            if roll_type == 'main' and not main_has_rolled:
                main_has_rolled = 1  # Mark that a main has rolled
            update_fields.update({
                "second_id": roller_id,
                "second_roll": roll_value,
                "main_has_rolled": main_has_rolled
            })
        if roll_type == 'main' and not main_has_rolled:
            main_has_rolled = 1  # Mark that a main has rolled

        

        # Update database if necessary
        if update_fields:
            set_clause = ", ".join(f"{field} = %s" for field in update_fields)
            values = list(update_fields.values()) + [channel_id]
            update_query = f"UPDATE rolls SET {set_clause} WHERE channel_id = %s"
            mycursor.execute(update_query, tuple(values))

        # Track roller to prevent duplicate rolls
        roll_tracker[channel_id].add(roller_id)

@bot.slash_command(name="bid", description="Bid on an item in its auction channel.")
async def bid(
    ctx: discord.ApplicationContext, 
    amount: int, 
    character_type: discord.Option(str, choices=['main', 'alt'])
):
    if amount < 2:
        await ctx.respond("The bid amount must be a positive number with a minimum of 2.", ephemeral=True)
        return
    # Early returns for invalid bid conditions
    if ctx.channel.id not in bid_dict and ctx.channel.id in close_dict:
        await ctx.respond("Bids on this item have closed.", ephemeral=True)
        return

    if ctx.channel.id not in bid_dict:
        await ctx.respond("You can't use this command here. Use `/bid` in the channel for the item you want to bid for.", ephemeral=True)
        return

    with get_cursor(commit=True) as mycursor:
        # Fetch the current bid status
        mycursor.execute("SELECT main_has_bid, top_bidder FROM bids WHERE channel_id = %s", (ctx.channel.id,))
        bid_data = mycursor.fetchone()

        if not bid_data or bid_data[0] is None:
            await ctx.respond("Bid does not exist.", ephemeral=True)
            return

        main_has_bid, top_bidder_id = bid_data

        # Prevent bidding by the current top bidder
        if top_bidder_id and ctx.author.id == int(top_bidder_id):
            if main_has_bid == 0 and character_type == 'main':
                pass  # Allow the main bid
            else:
                await ctx.respond("You're already the top bidder on this item.", ephemeral=True)
                return

        # Validate user DKP balance
        mycursor.execute("SELECT dkp_value, main_name FROM dkp WHERE discord_id = %s", (ctx.author.id,))
        dkp_data = mycursor.fetchone()

        if not dkp_data:
            await ctx.respond("You don't have a DKP record. Create one with `/register`.", ephemeral=True)
            return

        dkp_value, character_name = dkp_data

        if amount > dkp_value:
            await ctx.respond(f"You don't have enough DKP. Your current DKP: {dkp_value}", ephemeral=True)
            return

        # Determine bid eligibility based on character type and current bid status
        allow_bid, overwrite, main_bid = 0, 0, 0

        if character_type == 'alt' and main_has_bid == 1:
            allow_bid = 0
        elif character_type == 'alt' and main_has_bid == 0:
            allow_bid = 1
        elif character_type == 'main' and main_has_bid == 1:
            allow_bid = 1
            main_bid = 1
        elif character_type == 'main' and main_has_bid == 0:
            allow_bid = 1
            overwrite = 1
            main_bid = 1

        if allow_bid == 0:
            await ctx.respond("A main has already bid on this item.", ephemeral=True)
            return

        if allow_bid == 1:
            # Extend bidding time if it's near the end
            if bid_dict and any(value - int(time.time()) <= 30 for value in bid_dict.values()):
                for key in bid_dict:
                    bid_dict[key] += 30
                    close_dict[key] = bid_dict[key] + 20
                    channel = bot.get_channel(key)
                    await channel.send("Bidding time extended.")

        if overwrite == 1:
            # Update the top bid and insert into the database
            mycursor.execute(
                "UPDATE bids SET top_bid_amt = %s, top_bidder = %s, main_has_bid = %s WHERE channel_id = %s", 
                (amount, ctx.author.id, main_bid, ctx.channel.id)
            )
            await ctx.respond(f"New top bid placed: {amount} DKP by <{character_name}>! Type: {character_type}", ephemeral=False)
        else:
            # Handle second place or invalid bid
            mycursor.execute("SELECT top_bid_amt, top_bidder, second_bidder, second_bid_amt FROM bids WHERE channel_id = %s", (ctx.channel.id,))
            result = mycursor.fetchone()

            if not result:
                await ctx.respond("Error: No SQL response.", ephemeral=True)
                return

            top_bid_amt, top_bidder, second_bidder, second_bid_amt = result

            if top_bid_amt < amount:
                # Move top bidder to second and update the first bid
                mycursor.execute(
                    "UPDATE bids SET top_bid_amt = %s, top_bidder = %s, second_bid_amt = %s, second_bidder = %s, main_has_bid = %s WHERE channel_id = %s",
                    (amount, ctx.author.id, top_bid_amt, top_bidder, main_bid, ctx.channel.id)
                )
                await ctx.respond(f"New top bid placed: {amount} DKP by <{character_name}>! Type: {character_type}", ephemeral=False)
            else:
                await ctx.respond(f"Invalid bid. Current top bid is: {top_bid_amt} by: <@{top_bidder}>", ephemeral=True)
                return

async def voice_channel_autocomplete(ctx: discord.AutocompleteContext):
    return [vc.name for vc in ctx.interaction.guild.voice_channels]

@bot.slash_command(name="grantdkp", description="Grants DKP to a user or all users in a voice channel.")
async def grantdkp(
    ctx: discord.ApplicationContext,
    amount: int,
    is_attendance_tick: bool = False,
    main_name: str = None,
    reason:str = None,
    voice_channel: discord.Option(
        str,
        description="Select a voice channel",
        autocomplete=voice_channel_autocomplete
    ) = None
):
    if not main_name and not voice_channel:
        await ctx.respond("You must provide a main name to grant DKP to a single user, or a voice channel to grant DKP to all users in that channel.",ephemeral=True)
        return
    if main_name and voice_channel:
        await ctx.respond("Only provide a voice channel or main name to this command.", ephemeral=True)
        return
    with get_cursor(commit=True) as mycursor:
        if main_name:
            mycursor.execute("SELECT discord_id,dkp_value FROM dkp WHERE main_name = %s", (main_name,))
            result = mycursor.fetchone()
            if result:
                disc_id = result[0]
                cur_dkp = result[1]
                new_dkp = cur_dkp + amount
                mycursor.execute("UPDATE dkp SET dkp_value = %s WHERE discord_id = %s", (new_dkp,disc_id))
                await ctx.respond(f"Updated DKP for main <{main_name}> from {cur_dkp} to {new_dkp}",ephemeral=True)
                response = (f"{ctx.author.mention} updated DKP for main <{main_name}> from {cur_dkp} to {new_dkp}")
                if reason:
                    response += (f" for reason: {reason}")
                if is_attendance_tick:
                    query = "INSERT INTO attendance_ticks (discord_id) VALUES (%s)"
                    value = disc_id
                    mycursor.execute(query, (value,))
                    response += (f" added attendance tick for user.")
                await send_log_channel_message(response)
                return
            else:
                await ctx.respond(f"Unable to find record for: {main_name}",ephemeral=True)
                return
        if voice_channel:
            selected_channel = discord.utils.get(ctx.guild.voice_channels, name=voice_channel)
            if not selected_channel:
                await ctx.respond("Voice channel not found. No DKP granted or attendance tick added.", ephemeral=True)
                return
            members = selected_channel.members
            if not members:
                await ctx.respond(f"No users found in **{voice_channel}**. No DKP granted or attendance tick added.", ephemeral=True)
                return
            not_found_users = []
            valid_members = []
            discord_ids = []
            updates = []
            for member in members:
                discord_id = member.id
                # Check if user exists in the DKP table
                mycursor.execute("SELECT dkp_value FROM dkp WHERE discord_id = %s", (discord_id,))
                result = mycursor.fetchone()
                if result:
                    new_dkp = result[0] + amount
                    #mycursor.execute("UPDATE dkp SET dkp_value = %s WHERE discord_id = %s", (new_dkp, discord_id))
                    valid_members.append(member.mention)
                    updates.append((new_dkp, discord_id))
                else:
                    not_found_users.append(member.mention)
                if is_attendance_tick:
                    discord_ids.append(discord_id)
            if updates:
                mycursor.executemany("UPDATE dkp SET dkp_value = %s WHERE discord_id = %s", updates)
            if is_attendance_tick:
                #make tick record, add tick records for all attendees.
                granter = get_main_name_by_discord_id(ctx.author.id)
                query = "INSERT INTO attendance (granted_by,reason) VALUES (%s,%s)"
                mycursor.execute(query, (granter,reason))
                if discord_ids:
                    query = "INSERT INTO attendance_ticks (discord_id) VALUES (%s)"
                    values = [(discord_id,) for discord_id in discord_ids]
                    mycursor.executemany(query, values)
            await ctx.respond(f"Granted {amount} DKP to everyone in channel {voice_channel}.",ephemeral=True)
            response = (f"{ctx.author} Granted {amount} DKP to: {', '.join(valid_members)}")
            if reason:
                response += " for reason: " + reason
            if not_found_users:
                response = (
                    f"\n⚠️ The following users were **not found** in the DKP table and were skipped:\n"
                    f"{', '.join(not_found_users)}"
                )
            await send_log_channel_message(response)

@bot.slash_command(name="setdkp", description="Set the dkp of a player based on their main name.")
async def setdkp(
    ctx: discord.ApplicationContext, 
    main_name:str,
    amount:int
):
    with get_cursor(commit=True) as mycursor:
        query = "SELECT dkp_value FROM dkp WHERE main_name = %s" 
        mycursor.execute(query, (main_name,))
        result = mycursor.fetchone()
        if result:
            pre_val = result[0]
            mycursor.execute("UPDATE dkp SET dkp_value = %s WHERE main_name = %s", (amount, main_name))
            await ctx.respond(f"Updated DKP for character {main_name} to {amount}.", ephemeral=True)
            await send_log_channel_message(f"{ctx.author.mention} set dkp for {main_name} to {amount} (previously: {pre_val})")
        else:
            await ctx.respond(f"Error: No main found by that name.", ephemeral=True)

@bot.slash_command(name="attendancelist",description="Get Attendance info for a class or all users")
async def attendancelist(
    ctx: discord.ApplicationContext,
    character_class: discord.Option(
        str,
        description="Optional: filter by class",
        choices=['All','Bard', 'Beastlord', 'Cleric', 'Druid', 'Enchanter', 'Magician','Monk', 'Necromancer', 'Paladin', 'Ranger', 'Rogue','Shadowknight', 'Shaman', 'Warrior', 'Wizard']),
    limit: discord.Option(
        int,description="Limit the number of results",required=False,
        default=30  # default to 30
        )
    ):
    with get_cursor() as mycursor:
        if character_class:
            if character_class == "All":
                mycursor.execute("SELECT discord_id,main_name,dkp_value,time_registered FROM dkp ORDER BY dkp_value DESC LIMIT %s", (limit,))
                results = mycursor.fetchall()
                if not results:
                    await ctx.respond(f"No records found in DKP table.",ephemeral=True)
                response =( f"```\n"
                            f"{'Main Name':<10}|{'DKP':<8}|{'Total Attendance':<18}|{'90-Day':<18}|{'30-Day':<18}|\n")
                for row in results:
                    discord_id = row[0]
                    main_name = row[1]
                    dkp_value = row[2]
                    time_registered = row[3]
                    total_user_ticks, total_tick_count, total_percent = get_att(mycursor,discord_id,time_registered)
                    ninety_days_ago = datetime.datetime.now() - datetime.timedelta(days=90)
                    ninety_day_user_ticks, total_ninety_ticks, ninety_percent = get_att(mycursor,discord_id,ninety_days_ago)
                    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    thirty_day_user_ticks, total_thirty_ticks, thirty_percent = get_att(mycursor,discord_id,thirty_days_ago)
                    response +=(
                        f"{'-' * 77}\n"
                        f"{main_name:<10}|{dkp_value:<8}|{total_user_ticks:>4}/{total_tick_count:<4} = {total_percent:^5}%|{ninety_day_user_ticks:>4}/{total_ninety_ticks:<4} = {ninety_percent:^5}%|{thirty_day_user_ticks:>4}/{total_thirty_ticks:<4} = {thirty_percent:^5}%|\n"
                    )
                response += (f"```")
                await ctx.respond(response,ephemeral=True)
                        
@bot.slash_command(name="dkp", description="Get DKP for your character or all characters for a class.")
async def dkp(
    ctx: discord.ApplicationContext,
        character_class: discord.Option(
        str,
        description="Optional: filter by class",
        choices=['All','Bard', 'Beastlord', 'Cleric', 'Druid', 'Enchanter', 'Magician','Monk', 'Necromancer', 'Paladin', 'Ranger', 'Rogue','Shadowknight', 'Shaman', 'Warrior', 'Wizard'], 
        required=False
    )
):
    with get_cursor() as mycursor:
    # If a class is provided, return a list sorted by DKP
        if character_class:
            if character_class == "All":
                query = "SELECT main_name, dkp_value, character_class FROM dkp ORDER BY dkp_value DESC"
                mycursor.execute(query)
                results = mycursor.fetchall()
                if results:
                    lines = [f"{name:<15} {dkp:>3}  [{char_class}]" for name, dkp, char_class in results]
                    table = "\n".join(lines)
                    await ctx.respond(f"```All DKP:\n{table}```", ephemeral=True)
                else:
                    await ctx.respond("No DKP records found.", ephemeral=True)
            else:
                query = "SELECT main_name, dkp_value FROM dkp WHERE character_class = %s ORDER BY dkp_value DESC"
                val = (character_class,)
                mycursor.execute(query, val)
                results = mycursor.fetchall()
                if results:
                    lines = [f"{name:<15} {dkp:>3}" for name, dkp in results]
                    table = "\n".join(lines)
                    await ctx.respond(f"```{character_class} DKP:\n{table}```",ephemeral=True)
                else:
                    await ctx.respond(f"No characters found for class `{character_class}`.", ephemeral=True)
        #return for user of command
        else:
            await get_dkp_and_attendance(ctx)

def get_att(cursor, discord_id, timestamp):
    #returns 1{ticks user has been present since timestamp}, 2{ticks that have occurred since timestamp}, {1/2}
    query_total = "SELECT COUNT(*) FROM attendance_ticks WHERE discord_id = %s"
    cursor.execute(query_total, (discord_id,))
    user_ticks = cursor.fetchone()[0]
    query_totalticks = "SELECT COUNT(*) FROM attendance WHERE timestamp >= %s"
    cursor.execute(query_totalticks,(timestamp,))
    total_ticks = cursor.fetchone()[0]
    if total_ticks and total_ticks > 0:
        att_perc = round(user_ticks / total_ticks * 100, 1)
    else:
        att_perc = 0
    return user_ticks,total_ticks,att_perc

async def get_dkp_and_attendance(ctx):
    with get_cursor() as mycursor:
        id = ctx.author.id
        query = "SELECT dkp_value, main_name, time_registered FROM dkp WHERE discord_id = %s"
        val = (id,)
        mycursor.execute(query, val)
        result = mycursor.fetchone()
        if result:
            dkp_value = result[0]
            main_name = result[1]
            time_registered = result[2]
            total_user_ticks, total_tick_count, total_percent = get_att(mycursor,id,time_registered)
            ninety_days_ago = datetime.datetime.now() - datetime.timedelta(days=90)
            ninety_day_user_ticks, total_ninety_ticks, ninety_percent = get_att(mycursor,id,ninety_days_ago)
            thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
            thirty_day_user_ticks, total_thirty_ticks, thirty_percent = get_att(mycursor,id,thirty_days_ago)
            await ctx.respond(
                f"```\n"
                f"{'Main Name':<10}|{'DKP':<8}|{'Total Att':<18}|{'90-Day':<18}|{'30-Day':<18}|\n"
                f"{'-' * 10}|{'-' * 8}|{'-' * 18}|{'-' * 18}|{'-' * 18}|\n"
                f"{main_name:<10}|{dkp_value:<8}|{total_user_ticks:>4}/{total_tick_count:<4} = {total_percent:^5}%|{ninety_day_user_ticks:>4}/{total_ninety_ticks:<4} = {ninety_percent:^5}%|{thirty_day_user_ticks:>4}/{total_thirty_ticks:<4} = {thirty_percent:^5}%|\n"
                f"```",
                ephemeral=True
            )
        else:
            await ctx.respond(
                f"Unable to find DKP record. Use `/register` to register a character.",ephemeral=True
            )

bot.run(os.getenv('TOKEN')) # run the bot with the token
