# disc-dkp-bot

Requires:
pycord
pymysql
dotenv

Bot scopes:
- bot
- applications.commands

Bot permissions:
General
- Manage Channels
- View Channels
Text
- Send Messages
- Read Message History
Voice
- Connect

Your .env should look like:
```
 TOKEN={Token here}
 DB_USERNAME={db username here}
 DB_PASSWORD={db password here}
```

## Setup:
- Create a category to use for the bot as well as a log channel and a bidding results channel under that category.
- Within the log channel, use /setchannel log_channel
- Within the bidding results channel, use /setchannel results_channel
- In either of the above two channels use /setchannel bot_category

## Commands:
**/register {main_name} {character_class}**
- Registers the person interacting's discord ID and entered main name and character_class to the main DKP table with 0 DKP

**/unregister {main_name}**
- Deletes the row with main_name in the main DKP table
 
**/setchannel {channel_type}**
- Sets the channel that the command is used in to the selected channel_type
 
**/startbid {item_name} {duration}**
- Starts a bid for item name in a new channel for duration seconds
 
**/startroll {item_name} {duration}**
- Starts a roll for an item in a new channel for duration seconds
 
**/roll {chartype}**
- Rolls in a channel for a /startroll'd item, main automatically overwrites alt.
 
**/bid {amount} {chartype}**
- Bids in a channel for an item that was /startbid'd, main automatically overwrites alt.
 
**/grantdkp {amount} {reason} {is_attendance_tick} {main_name/voice_channel}**
- Grants amount dkp to main_name or all users in voice_channel for reason. is_attendance_tick will log a new attendance tick and grant all users in voice channel credit. If attendance tick is true and main_name is used, that user will be granted credit for a tick but a new tick will not be created. This means if you were to grant many ticks directly to a main_name, they could have over 100% attendance.
 
**/setdkp {main_name} {amount}**
- Sets the DKP for main_name to amount directly.
 
**/attendancelist {class} {limit}**
- Returns a list of attendance %s for selected class, limited to limit. Default is 30.
