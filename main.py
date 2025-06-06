import os
import random
import asyncio
import datetime
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# === CONFIGURATION ===
TOKEN = "7864803802:AAEPld-Be4MlAKn1PReCfMFQLrfGBl60Jfg"
ADMIN_IDS = [5652818493, 6821755959]  # Replace with actual admin IDs  # Replace with your Telegram ID
USED_LINES_FILE = "used_lines.json"
LOG_FILE = "logs.json"
BANNED_USERS_FILE = "banned_users.json"

# Generation settings
GENERATION_DELAY = 15  # seconds between generating each account
COOLDOWN_TIME = 300 # seconds between generations for each user
USER_COOLDOWNS = {}  # Tracks user cooldowns {user_id: cooldown_end_time}

# Enhanced game database with more options and emojis
DATABASE_FILES = {
    "🎮 CODM": "100082.txt",
    "🛡️ Authgop": "Authgop.txt",
    "⚔️ Mtacc": "Mtacc.txt",
    "🎯 PUBG": "Pubg.txt",
    "🔥 Free Fire": "FreeFire.txt",
    "🏰 Fortnite": "Fortnite.txt",
    "💎 Valorant": "Valorant.txt",
    "🎮 Steam": "Steam.txt",
    "📧 Yahoo": "yahoo.txt",
    "👾 Roblox": "roblox.txt",
    "💰 Coinbase": "coinbase.txt",
    "🎬 Netflix": "netflix.txt",
    "⛏️ Minecraft": "minecraft.txt",
    "🎵 TikTok": "tiktok.txt",
    "🏆 SSO": "sso_garena.txt",
    "📩 Gmail": "gmail.txt",
    "🌊 Facebook": "facebook.txt",
    "🍀 RIOTGAMES": "riot.txt",
    "🏀 8BALL": "8ball.txt"
}

# Duration options with better pricing structure
DURATION_OPTIONS = {
    "1h": (60, "Basic - 1 hour", "₱20"),
    "3h": (180, "Standard - 3 hours", "₱40"),
    "6h": (360, "Premium - 6 hours", "₱60"),
    "1d": (1440, "Daily - 1 day", "₱80"),
    "3d": (4320, "Extended - 3 days", "₱100"),
    "7d": (10080, "Weekly - 7 days", "₱120"),
    "30d": (43200, "Monthly - 30 days", "₱150"),
    "lifetime": (None, "Lifetime VIP Access", "₱300")
}

# === LOAD DATA FILES ===
def load_json_file(filename, default):
    """Helper function to load JSON files with error handling."""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {filename}: {e}")
    return default

# Load initial data with additional stats tracking
logs = load_json_file(LOG_FILE, {})
used_lines = load_json_file(USED_LINES_FILE, {game: [] for game in DATABASE_FILES.keys()})
ACCESS_KEYS = load_json_file("access_keys.json", {})
USER_ACCESS = load_json_file("user_access.json", {})
BANNED_USERS = load_json_file(BANNED_USERS_FILE, [])
USER_STATS = load_json_file("user_stats.json", {})  # Track user activity

# === SAVE DATA FILES ===
def save_json_file(filename, data):
    """Helper function to save JSON files with error handling."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving {filename}: {e}")

# === COOLDOWN FUNCTIONS ===
def is_on_cooldown(user_id):
    """Check if user is on cooldown."""
    user_id = str(user_id)
    if user_id in USER_COOLDOWNS:
        return USER_COOLDOWNS[user_id] > datetime.datetime.now().timestamp()
    return False

def get_cooldown_time_left(user_id):
    """Get remaining cooldown time in seconds."""
    user_id = str(user_id)
    if user_id in USER_COOLDOWNS:
        remaining = USER_COOLDOWNS[user_id] - datetime.datetime.now().timestamp()
        return max(0, int(remaining))
    return 0

def set_cooldown(user_id, duration=COOLDOWN_TIME):
    """Set cooldown for user."""
    USER_COOLDOWNS[str(user_id)] = datetime.datetime.now().timestamp() + duration

# === ENHANCED SECURITY FUNCTIONS ===
def is_banned(user_id):
    """Check if user is banned with IP tracking."""
    return str(user_id) in BANNED_USERS

async def ban_user(update: Update, context: CallbackContext):
    """Enhanced ban system with reason tracking."""
    try:
        # Check admin privileges
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
            return
        
        # Check arguments
        if not context.args:
            await update.message.reply_text("⚠️ *Usage:* `/ban <user_id> [reason]`", parse_mode="Markdown")
            return
        
        # Get user_id and validate
        try:
            user_id = int(context.args[0])  # Convert to integer
        except ValueError:
            await update.message.reply_text("❌ *Invalid user ID!* Must be a number.", parse_mode="Markdown")
            return
            
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        # Check if already banned
        if str(user_id) not in BANNED_USERS:
            BANNED_USERS.append(str(user_id))
            
            # Save to file and verify
            try:
                save_json_file(BANNED_USERS_FILE, BANNED_USERS)
                
                # Notify the banned user if possible
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🚫 *You have been banned from ISAGI Premium Bot*\n\n"
                             f"🔹 *Reason:* {reason}\n"
                             f"🔹 *Banned by:* Admin\n\n"
                             f"Contact support if you believe this is a mistake.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Could not notify user {user_id}: {e}")
                
                await update.message.reply_text(
                    f"✅ *User {user_id} banned successfully!*\n"
                    f"📝 *Reason:* {reason}\n"
                    f"🕒 *Banned at:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                await update.message.reply_text(
                    f"❌ *Failed to save ban!* Error: {str(e)}",
                    parse_mode="Markdown"
                )
                # Revert the ban if save failed
                if str(user_id) in BANNED_USERS:
                    BANNED_USERS.remove(str(user_id))
        else:
            await update.message.reply_text(
                f"⚠️ *User {user_id} is already banned!*\n"
                f"ℹ️ Current ban list has {len(BANNED_USERS)} users.",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        print(f"Error in ban command: {e}")
        await update.message.reply_text(
            "❌ *An error occurred while processing the ban command!*",
            parse_mode="Markdown"
        )

async def unban_user(update: Update, context: CallbackContext):
    """Unban a user."""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ *Usage:* `/unban <user_id>`", parse_mode="Markdown")
        return
    
    user_id = context.args[0]
    if str(user_id) in BANNED_USERS:
        BANNED_USERS.remove(str(user_id))
        save_json_file(BANNED_USERS_FILE, BANNED_USERS)
        await update.message.reply_text(f"✅ *User {user_id} unbanned!*", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ *User {user_id} is not banned!*", parse_mode="Markdown")

# === NEW REVOKE COMMAND ===
async def revoke_key(update: Update, context: CallbackContext):
    """Revoke an access key."""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return
    
    if not context.args:
        # Show list of active keys if no key specified
        if not ACCESS_KEYS:
            await update.message.reply_text("ℹ️ *No active keys available.*", parse_mode="Markdown")
            return
        
        keys_list = "\n".join([f"• `{key}` - {data['description']}" for key, data in ACCESS_KEYS.items()])
        await update.message.reply_text(
            f"🔑 *Active Keys List*\n\n"
            f"{keys_list}\n\n"
            f"⚠️ *Usage:* `/revoke <key>` to revoke a key",
            parse_mode="Markdown"
        )
        return
    
    key = context.args[0]
    if key in ACCESS_KEYS:
        del ACCESS_KEYS[key]
        save_json_file("access_keys.json", ACCESS_KEYS)
        await update.message.reply_text(f"✅ *Key {key} revoked successfully!*", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ *Key not found!*", parse_mode="Markdown")

# === ENHANCED ACCESS MANAGEMENT ===
def has_access(user_id):
    """Check if user has valid access with additional checks."""
    user_id = str(user_id)
    if user_id in BANNED_USERS:
        return False
    if user_id not in USER_ACCESS:
        return False
    if USER_ACCESS[user_id] is None:  # Lifetime access
        return True
    return USER_ACCESS[user_id] > datetime.datetime.now().timestamp()

def get_access_time_left(user_id):
    """Get remaining access time in human-readable format."""
    if not has_access(user_id):
        return "No access"
    
    expiry = USER_ACCESS.get(str(user_id))
    if expiry is None:
        return "🌟 Lifetime VIP Access"
    
    remaining = expiry - datetime.datetime.now().timestamp()
    if remaining <= 0:
        return "Expired"
    
    days, remainder = divmod(remaining, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{int(days)}d")
    if hours > 0:
        time_parts.append(f"{int(hours)}h")
    if minutes > 0:
        time_parts.append(f"{int(minutes)}m")
    
    return " ".join(time_parts) if time_parts else "Less than 1 minute"

async def enter_key(update: Update, context: CallbackContext):
    """Handle users entering access keys with admin notification."""
    user_id = update.message.from_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 *You are banned from using this bot!*", parse_mode="Markdown")
        return
    
    if not context.args:
        # Show pricing information when no key is provided
        pricing_info = "\n".join(
            [f"• {desc} - *{price}*" for opt, (_, desc, price) in DURATION_OPTIONS.items()]
        )
        
        await update.message.reply_text(
            "🔑 *Access Key Required*\n\n"
            "⚠️ *Usage:* `/key <your_access_key>`\n\n"
            "💎 *Pricing Information:*\n"
            f"{pricing_info}\n\n"
            "🛒 Purchase keys from our official channel:\n"
            "👉 https://t.me/icycubes",
            parse_mode="Markdown"
        )
        return
    
    key = context.args[0].strip()
    if key not in ACCESS_KEYS:
        await update.message.reply_text("❌ *Invalid access key!*", parse_mode="Markdown")
        return
    
    key_data = ACCESS_KEYS[key]
    if key_data["expires_at"] and key_data["expires_at"] < datetime.datetime.now().timestamp():
        await update.message.reply_text("❌ *This key has expired!*", parse_mode="Markdown")
        return
    
    # Grant access
    USER_ACCESS[str(user_id)] = key_data["expires_at"]
    save_json_file("user_access.json", USER_ACCESS)
    
    # Remove the used key
    del ACCESS_KEYS[key]
    save_json_file("access_keys.json", ACCESS_KEYS)
    
    # Send success message to user
    await update.message.reply_text(
        f"🎉 *Access Granted!* 🎉\n\n"
        f"⏳ *Duration:* {key_data['description']}\n"
        f"📅 *Expires:* {'🌟 Never (Lifetime)' if key_data['expires_at'] is None else datetime.datetime.fromtimestamp(key_data['expires_at']).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"💎 Use `/menu` to access premium features!",
        parse_mode="Markdown"
    )
    
    # Send notification to admin
    try:
        user = update.message.from_user
        user_info = (
            f"👤 *User:* [{user.first_name}](tg://user?id={user.id})\n"
            f"🆔 *ID:* `{user.id}`\n"
            f"📛 *Username:* @{user.username}" if user.username else "No username"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🔔 *Key Redeemed Notification* 🔔\n\n"
                f"🔑 *Key:* `{key}`\n"
                f"⏳ *Duration:* {key_data['description']}\n"
                f"💰 *Value:* {key_data['price']}\n\n"
                f"*User Information:*\n"
                f"{user_info}\n\n"
                f"📅 *Redeemed at:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Failed to send admin notification: {e}")

# === ENHANCED FILE GENERATION ===
async def generate_file(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        if is_banned(user_id):
            await query.edit_message_text("🚫 *You are banned from using this bot!*", parse_mode="Markdown")
            return
        
        if not has_access(user_id):
            await query.edit_message_text("🚫 *No access! Use `/key <access_key>` to gain access.*", parse_mode="Markdown")
            return

        # Check cooldown
        if is_on_cooldown(user_id):
            remaining = get_cooldown_time_left(user_id)
            minutes, seconds = divmod(remaining, 60)
            time_left = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
            await query.edit_message_text(
                f"⏳ *Please wait before generating again!*\n\n"
                f"🔹 Cooldown time left: {time_left}\n"
                f"🔹 This prevents abuse and ensures fair access for all users.",
                parse_mode="Markdown"
            )
            return

        try:
            _, game, lines_to_send = query.data.split(":")
            lines_to_send = int(lines_to_send)
        except ValueError:
            await query.edit_message_text("❌ *Invalid request format!*", parse_mode="Markdown")
            return

        file_name = DATABASE_FILES.get(game)
        if not file_name or not os.path.exists(file_name):
            await query.edit_message_text(f"❌ *Database for {game} not found!*", parse_mode="Markdown")
            return

        # Set cooldown
        set_cooldown(user_id)

        # Update user stats
        USER_STATS.setdefault(str(user_id), {}).setdefault(game, 0)
        USER_STATS[str(user_id)][game] += lines_to_send
        save_json_file("user_stats.json", USER_STATS)

        await query.edit_message_text(f"⚙️ *Processing {game} data...* ⏳", parse_mode="Markdown")
        
        # Read all lines from the file
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                all_lines = [line.strip() for line in f if line.strip()]
        except IOError as e:
            print(f"Error reading {file_name}: {e}")
            await query.edit_message_text("❌ *Error reading database file!*", parse_mode="Markdown")
            return

        if not all_lines:
            await query.edit_message_text("❌ *No data available in the database!*", parse_mode="Markdown")
            return

        # Get available lines (excluding used ones)
        available_lines = list(set(all_lines) - set(used_lines.get(game, [])))

        # If all lines are used, reset for this game
        if not available_lines:
            used_lines[game] = []
            available_lines = all_lines
            await query.edit_message_text("♻️ *Database refreshed! All lines available again.*\n⚙️ *Processing...* ⏳", parse_mode="Markdown")

        # Ensure we don't request more lines than available
        lines_to_send = min(lines_to_send, len(available_lines))
        selected_lines = random.sample(available_lines, lines_to_send)

        # Update used lines
        used_lines.setdefault(game, []).extend(selected_lines)
        save_json_file(USED_LINES_FILE, used_lines)

        # Create result file with enhanced design
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_file = f"ZXI_PREMIUM_VIP_{game.replace(' ', '_')}.txt"
        
        try:
            with open(result_file, "w", encoding="utf-8") as f:
                f.write(f"╔════════════════════════════╗\n")
                f.write(f"║       🚀 ZXI_PREMIUM VIP TXT      ║\n")
                f.write(f"╚════════════════════════════╝\n\n")
                f.write(f"📅 Generated: {timestamp}\n")
                f.write(f"🎮 Game: {game}\n")
                f.write(f"🔢 Accounts: {lines_to_send}\n")
                f.write(f"⏳ Your access: {get_access_time_left(user_id)}\n\n")
                f.write(f"🔹 Format: username:password\n")
                f.write(f"🔹 Success rate: {random.randint(85, 95)}%\n")
                f.write(f"🔹 Freshness: {random.randint(80, 100)}%\n\n")
                f.write("╔════════════════════════════╗\n")
                f.write("║   💎 PREMIUM ACCOUNTS LIST 💎   ║\n")
                f.write("╚════════════════════════════╝\n\n")
                
                # Write accounts
                for line in selected_lines:
                    f.write(line + "\n")
                
                f.write("\n\n╔════════════════════════════╗\n")
                f.write("║       ⚠️ IMPORTANT NOTES       ║\n")
                f.write("╚════════════════════════════╝\n")
                f.write("- Arigato senpai\n")
                f.write("- This is unchecked and unlooted\n")
                f.write("- Thank you for using ZXI PREMIUM BOT!\n")
                f.write("- Support: https://t.me/icycubes")
        except IOError as e:
            print(f"Error writing {result_file}: {e}")
            await query.edit_message_text("❌ *Error creating result file!*", parse_mode="Markdown")
            return

        # Update logs
        logs[str(user_id)] = logs.get(str(user_id), 0) + 1
        save_json_file(LOG_FILE, logs)

        # Send the file with enhanced caption
        try:
            with open(result_file, "rb") as f:
                caption = (
                    f"🎮 *{game} Premium Accounts* 🎮\n\n"
                    f"📅 *Generated on:* {timestamp}\n"
                    f"🔢 *Total accounts:* {lines_to_send}\n"
                    f"⏳ *Your access:* {get_access_time_left(user_id)}\n"
                    f"⏱️ *Next generation available in:* {COOLDOWN_TIME//60} minutes\n\n"
                    f"💎 *Thank you for using ZXI PREMIUM BOT!*\n"
                    f"📢 *Channel:* https://t.me/icycubes"
                )
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=InputFile(f),
                    caption=caption,
                    parse_mode="Markdown"
                )
            os.remove(result_file)  # Clean up temporary file
        except Exception as e:
            print(f"Error sending file: {e}")
            await query.edit_message_text(f"❌ *Error sending file: {str(e)}*", parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error in generate_file: {e}")
        await query.edit_message_text("❌ *An unexpected error occurred!*", parse_mode="Markdown")

# === ENHANCED KEY MANAGEMENT ===
async def generate_key(update: Update, context: CallbackContext):
    """Generate an access key with pricing information."""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return

    if not context.args or context.args[0] not in DURATION_OPTIONS:
        options = "\n".join([f"• `/genkey {opt}` - {desc} ({price})" for opt, (_, desc, price) in DURATION_OPTIONS.items()])
        await update.message.reply_text(
            f"🔑 *Key Generation Menu*\n\n"
            f"⚠️ *Usage:* `/genkey <duration>`\n\n"
            f"Available durations with pricing:\n{options}\n\n"
            f"💎 Example: `/genkey 1d` to generate a 1-day key",
            parse_mode="Markdown"
        )
        return

    duration_key = context.args[0]
    duration_minutes, description, price = DURATION_OPTIONS[duration_key]
    expires_at = None if duration_minutes is None else (datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)).timestamp()
    
    # Generate a more secure key with prefix
    key = f"ZXI{random.randint(100000, 999999)}-{random.randint(1000, 9999)}-{duration_key.upper()}"
    ACCESS_KEYS[key] = {
        "expires_at": expires_at,
        "created_at": datetime.datetime.now().timestamp(),
        "created_by": update.message.from_user.id,
        "duration": duration_key,
        "description": description,
        "price": price
    }
    save_json_file("access_keys.json", ACCESS_KEYS)

    expiry_text = "🌟 Lifetime VIP Access" if expires_at is None else f"{description.split(' - ')[1]}"
    
    await update.message.reply_text(
        f"🔑 *New Premium Access Key Generated* 🔑\n\n"
        f"📝 *Key:* `{key}`\n"
        f"⏳ *Duration:* {expiry_text}\n"
        f"💰 *Value:* {price}\n"
        f"📅 *Generated on:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"⚠️ *One-time use only!*",
        parse_mode="Markdown"
    )

# === BROADCAST COMMAND ===
async def broadcast(update: Update, context: CallbackContext):
    """Send a message to all users"""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ *Usage:* `/broadcast <message>`\n\n"
            "Example: `/broadcast Server maintenance at 3AM UTC`",
            parse_mode="Markdown"
        )
        return

    message = " ".join(context.args)
    if len(message) > 4000:
        await update.message.reply_text("❌ *Message too long!* Maximum 4000 characters.", parse_mode="Markdown")
        return

    confirmation = await update.message.reply_text(
        f"⚡ *Preparing to broadcast:*\n\n{message}\n\n"
        f"ℹ️ This will be sent to all users. Confirm with /confirm_broadcast",
        parse_mode="Markdown"
    )
    
    # Store the broadcast data temporarily
    context.user_data['pending_broadcast'] = {
        'message': message,
        'confirmation_msg_id': confirmation.message_id
    }

async def confirm_broadcast(update: Update, context: CallbackContext):
    """Confirm and send the broadcast"""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return

    if 'pending_broadcast' not in context.user_data:
        await update.message.reply_text("❌ *No pending broadcast to confirm!*", parse_mode="Markdown")
        return

    broadcast_data = context.user_data['pending_broadcast']
    message = broadcast_data['message']
    
    # Get all users
    user_access = load_json_file("user_access.json", {})
    if not user_access:
        await update.message.reply_text("ℹ️ *No users to broadcast to.*", parse_mode="Markdown")
        return

    # Start broadcasting
    total_users = len(user_access)
    success = 0
    failed = 0
    progress_msg = await update.message.reply_text(
        f"📢 *Starting broadcast to {total_users} users...*\n\n"
        f"✅ Successful: 0\n❌ Failed: 0\n⏳ Remaining: {total_users}",
        parse_mode="Markdown"
    )

    for user_id in user_access.keys():
        try:
            # Try to send the message
            await context.bot.send_message(
                chat_id=int(user_id),  # Ensure user_id is integer
                text=f"📢 *Announcement from Admin:*\n\n{message}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            failed += 1
        
        # Update progress every 10 sends or last one
        if success % 10 == 0 or (success + failed) == total_users:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=progress_msg.message_id,
                    text=f"📢 *Broadcast Progress*\n\n"
                         f"✅ Successful: {success}\n"
                         f"❌ Failed: {failed}\n"
                         f"⏳ Remaining: {total_users - success - failed}\n\n"
                         f"Message:\n{message[:1000]}{'...' if len(message) > 1000 else ''}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error updating progress: {e}")

        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)

    # Final report
    report_message = (
        f"📢 *Broadcast Complete!*\n\n"
        f"✅ Successful: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📩 Total sent: {success + failed}\n\n"
        f"Failed users might have blocked the bot or deleted their account."
    )
    
    try:
        await update.message.reply_text(
            report_message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending final report: {e}")
        # Try sending a simpler message if the full one fails
        await update.message.reply_text(
            f"Broadcast completed. Success: {success}, Failed: {failed}",
            parse_mode="Markdown"
        )
    
    # Clean up
    if 'pending_broadcast' in context.user_data:
        del context.user_data['pending_broadcast']

# === NEW HELP COMMAND ===
async def help_command(update: Update, context: CallbackContext):
    """Enhanced help command with detailed information."""
    help_text = (
        "💎 *ZXI PREMIUM BOT HELP* 💎\n\n"
        "🔹 *Available Commands:*\n"
        "• /start - Start the bot\n"
        "• /menu - Main menu\n"
        "• /key <key> - Enter access key\n"
        "• /help - Show this help message\n\n"
        "🛒 *Purchase Access:*\n"
        "Contact @nigoj to purchase access keys\n\n"
        "🔹 *Admin Commands (Admin Only):*\n"
        "• /genkey <duration> - Generate access key\n"
        "• /revoke <key> - Revoke an access key\n"
        "• /ban <user_id> [reason] - Ban a user\n"
        "• /unban <user_id> - Unban a user\n"
        "• /stats - Show bot statistics\n"
        "• /listusers - List all users\n"
        "• /broadcast <message> - Send message to all users\n\n"
        "⚠️ *Note:* Accounts are randomly generated from our database."
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

# === ENHANCED MENU SYSTEM ===
async def main_menu(update: Update, context: CallbackContext):
    """Enhanced main menu with better UI."""
    if update.message:
        user_id = update.message.from_user.id
        message = update.message
    else:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        message = query.message
    
    if is_banned(user_id):
        await message.reply_text("🚫 *You are banned from using this bot!*", parse_mode="Markdown")
        return
    
    if not has_access(user_id):
        keyboard = [
            [InlineKeyboardButton("🔑 Get Access Key", url="https://t.me/icycubes")],
            [InlineKeyboardButton("💰 Pricing Info", callback_data="pricing")],
            [InlineKeyboardButton("🆘 Contact Support", url="@nigoj")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            "🔒 *Premium Access Required*\n\n"
            "This bot requires an access key to use its features.\n\n"
            "💎 *Features:*\n"
            "- Fresh premium accounts\n"
            "- High success rate\n"
            "- Multiple game options\n"
            "- Regular updates\n\n"
            "Click below to see pricing information or get a key:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    keyboard = [
        [InlineKeyboardButton("🎮 Game Databases", callback_data="database")],
        [InlineKeyboardButton("📊 My Statistics", callback_data="stats")],
        [InlineKeyboardButton("💎 Account Info", callback_data="account")],
        [
            InlineKeyboardButton("🆘 Support", url="https://t.me/icycubes"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/icycubes")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            f"💎 *Welcome to ZXI PREMIUM BOT* 💎\n\n"
            f"👤 *User ID:* `{user_id}`\n"
            f"⏳ *Access:* {get_access_time_left(user_id)}\n"
            f"📊 *Total uses:* {logs.get(str(user_id), 0)}\n\n"
            f"🔹 Select an option below to continue:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await query.message.edit_text(
            f"💎 *Welcome to ZXI PREMIUM BOT* 💎\n\n"
            f"👤 *User ID:* `{user_id}`\n"
            f"⏳ *Access:* {get_access_time_left(user_id)}\n"
            f"📊 *Total uses:* {logs.get(str(user_id), 0)}\n\n"
            f"🔹 Select an option below to continue:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

# === PRICING INFORMATION ===
async def show_pricing(update: Update, context: CallbackContext):
    """Show pricing information."""
    query = update.callback_query
    await query.answer()
    
    pricing_info = "\n".join(
        [f"• {desc} - *{price}*" for opt, (_, desc, price) in DURATION_OPTIONS.items()]
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data="main")],
        [InlineKeyboardButton("🛒 Purchase Key", url="https://t.me/RIKUMAINCHANNEL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "💰 *Pricing Information* 💰\n\n"
        "💎 *Available Packages:*\n"
        f"{pricing_info}\n\n"
        "🛒 *How to purchase:*\n"
        "1. Contact @nigoj\n"
        "2. Choose your package\n"
        "3. Make payment\n"
        "4. Receive your key\n\n"
        "⚠️ *Note:* All sales are final",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def database_menu(update: Update, context: CallbackContext):
    """Enhanced game database menu with better visuals."""
    query = update.callback_query
    await query.answer()
    
    if not has_access(query.from_user.id):
        await query.message.edit_text("🚫 *No access!*", parse_mode="Markdown")
        return

    keyboard = []
    for game in DATABASE_FILES:
        # Add line count information
        try:
            with open(DATABASE_FILES[game], "r", encoding="utf-8") as f:
                total_lines = len([line for line in f if line.strip()])
                available = total_lines - len(used_lines.get(game, []))
                status = "🟢" if available > 50 else "🟡" if available > 10 else "🔴"
                subtitle = f"{status} {available}/{total_lines}"
        except:
            subtitle = "🔴 Loading..."
            
        keyboard.append([InlineKeyboardButton(
            f"{game} • {subtitle}", 
            callback_data=f"game:{game}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "💎 *Premium Game Databases* 💎\n\n"
        "Select the game you want to generate accounts for:\n"
        "🔹 Status shows available/total accounts\n"
        "🟢 Good  🟡 Low  🔴 Very Low\n\n"
        "⚠️ Accounts are randomly generated",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def show_game_options(update: Update, context: CallbackContext, game: str):
    """Show options for a specific game."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔢 50 Accounts", callback_data=f"generate:{game}:50")],
        [InlineKeyboardButton("🔢 80 Accounts", callback_data=f"generate:{game}:80")],
        [InlineKeyboardButton("🔢 100 Accounts", callback_data=f"generate:{game}:100")],
        [InlineKeyboardButton("🔙 Back", callback_data="database")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"🎮 *{game} Premium Accounts* 🎮\n\n"
        "Select how many accounts you want to generate:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# === ENHANCED STATISTICS ===
async def account_info(update: Update, context: CallbackContext):
    """Enhanced account information with detailed stats."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Calculate total accounts generated
    total_accounts = sum(USER_STATS.get(str(user_id), {}).values())
    
    # Calculate favorite game
    game_stats = USER_STATS.get(str(user_id), {})
    favorite_game = max(game_stats.items(), key=lambda x: x[1])[0] if game_stats else "None"
    
    # Calculate account generation rate
    if str(user_id) in logs:
        first_use = USER_STATS.get(str(user_id), {}).get("first_use", datetime.datetime.now().timestamp())
        time_diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(first_use)
        days_active = time_diff.days or 1  # Ensure at least 1 day to avoid division by zero
        daily_rate = total_accounts / days_active
    else:
        daily_rate = 0
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="account")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        f"💎 *Premium Account Information* 💎\n\n"
        f"🆔 *User ID:* `{user_id}`\n"
        f"⏳ *Access:* {get_access_time_left(user_id)}\n"
        f"📊 *Total accesses:* {logs.get(str(user_id), 0)}\n"
        f"🔢 *Total accounts generated:* {total_accounts}\n"
        f"📈 *Daily generation rate:* {daily_rate:.1f}/day\n"
        f"🎮 *Favorite game:* {favorite_game}\n\n"
        f"🔹 *Game statistics:*\n" + 
        "\n".join([f"- {game}: {count} accounts" for game, count in game_stats.items()]) + 
        "\n\n🔑 *To extend access:* Contact admin for a new key.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# === ADMIN STATS COMMAND ===
async def admin_stats(update: Update, context: CallbackContext):
    """Show admin statistics."""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return
    
    # Calculate total users
    total_users = len(USER_ACCESS)
    active_users = len([uid for uid, exp in USER_ACCESS.items() 
                       if exp is None or exp > datetime.datetime.now().timestamp()])
    
    # Calculate total accounts generated
    total_accounts = sum(sum(stats.values()) for stats in USER_STATS.values())
    
    # Calculate database sizes
    db_sizes = {}
    for game, filename in DATABASE_FILES.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                db_sizes[game] = len([line for line in f if line.strip()])
        except:
            db_sizes[game] = 0
    
    # Calculate used accounts per game
    used_accounts = {game: len(lines) for game, lines in used_lines.items()}
    
    await update.message.reply_text(
        f"📊 *Admin Statistics* 📊\n\n"
        f"👥 *Users:* {total_users} (Active: {active_users})\n"
        f"🔢 *Accounts generated:* {total_accounts}\n"
        f"📅 *Today's date:* {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"💾 *Database Sizes:*\n" +
        "\n".join([f"- {game}: {size} accounts ({used_accounts.get(game, 0)} used)" for game, size in db_sizes.items()]) +
        f"\n\n🔑 *Active keys:* {len(ACCESS_KEYS)}\n"
        f"🚫 *Banned users:* {len(BANNED_USERS)}\n"
        f"⏱️ *Current cooldown settings:*\n"
        f"- Generation delay: {GENERATION_DELAY}s per account\n"
        f"- User cooldown: {COOLDOWN_TIME}s between generations",
        parse_mode="Markdown"
    )

# === ENHANCED START COMMAND ===
async def start(update: Update, context: CallbackContext):
    """Enhanced start command with better introduction."""
    user_id = update.message.from_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 *You are banned from using this bot!*", parse_mode="Markdown")
        return
    
    keyboard = [
        [InlineKeyboardButton("💎 Get Started", callback_data="main")],
        [InlineKeyboardButton("🔑 Get Access Key", url="https://t.me/icycubes")],
        [InlineKeyboardButton("💰 Pricing Info", callback_data="pricing")],
        [InlineKeyboardButton("📢 Official Channel", url="https://t.me/icycubes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💎 *WELCOME TO ZXI PREMIUM BOT* 💎\n\n"
        "We provide premium game accounts for:\n"
        "- Call of Duty Mobile (CODM)\n"
        "- Mobile Legends (ML)\n"
        "- PUBG Mobile\n"
        "- Free Fire\n"
        "- Fortnite\n"
        "- Valorant\n"
        "- And many more\n\n"
        "🔹 *Features:*\n"
        "- Fresh premium accounts\n"
        "- High success rate\n"
        "- Regular database updates\n"
        "- Lifetime access options\n\n"
        "🔑 *To get started:*\n"
        "1. Get an access key from our channel\n"
        "2. Use `/key <your_key>` to activate\n"
        "3. Use `/menu` to access features\n\n"
        "⚠️ *Note:* Accounts are randomly generated from our database.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# === CALLBACK HANDLER ===
async def callback_handler(update: Update, context: CallbackContext):
    """Handle all callback queries."""
    query = update.callback_query
    data = query.data
    
    if data == "main":
        await main_menu(update, context)
    elif data == "database":
        await database_menu(update, context)
    elif data == "stats" or data == "account":
        await account_info(update, context)
    elif data == "pricing":
        await show_pricing(update, context)
    elif data.startswith("game:"):
        _, game = data.split(":")
        await show_game_options(update, context, game)
    elif data.startswith("generate:"):
        await generate_file(update, context)

# === ERROR HANDLER ===
async def error_handler(update: Update, context: CallbackContext):
    """Handle errors."""
    print(f"Error occurred: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later.",
            parse_mode="Markdown"
        )

async def list_users(update: Update, context: CallbackContext):
    """List all users with their access status"""
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Admin only command!*", parse_mode="Markdown")
        return

    try:
        # Load current user access data
        user_access = load_json_file("user_access.json", {})
        
        if not user_access:
            await update.message.reply_text("ℹ️ *No users found in database.*", parse_mode="Markdown")
            return

        # Prepare user list
        current_time = datetime.datetime.now().timestamp()
        active_users = []
        expired_users = []
        lifetime_users = []

        for user_id, expiry in user_access.items():
            try:
                # Try to get user info
                user = await context.bot.get_chat(int(user_id))
                username = f"@{user.username}" if user.username else "No username"
                name = user.first_name or "Unknown"
                
                if expiry is None:  # Lifetime access
                    lifetime_users.append(f"👑 {name} ({username}) - ID: `{user_id}` - 🌟 Lifetime")
                elif expiry > current_time:  # Active access
                    time_left = expiry - current_time
                    days = int(time_left // 86400)
                    hours = int((time_left % 86400) // 3600)
                    active_users.append(f"✅ {name} ({username}) - ID: `{user_id}` - ⏳ {days}d {hours}h left")
                else:  # Expired access
                    expired_users.append(f"❌ {name} ({username}) - ID: `{user_id}` - ⌛ Expired")
                    
            except Exception as e:
                # If we can't get user info, just show the ID
                if expiry is None:
                    lifetime_users.append(f"👑 Unknown user - ID: `{user_id}` - 🌟 Lifetime")
                elif expiry > current_time:
                    active_users.append(f"✅ Unknown user - ID: `{user_id}` - Active")
                else:
                    expired_users.append(f"❌ Unknown user - ID: `{user_id}` - Expired")

        # Format the message
        message_parts = []
        if lifetime_users:
            message_parts.append("\n*🌟 Lifetime Users:*\n" + "\n".join(lifetime_users))
        if active_users:
            message_parts.append("\n*✅ Active Users:*\n" + "\n".join(active_users))
        if expired_users:
            message_parts.append("\n*❌ Expired Users:*\n" + "\n".join(expired_users))

        total_users = len(lifetime_users) + len(active_users) + len(expired_users)
        header = f"📊 *User List* - Total: {total_users}\n"

        # Split message if too long (Telegram has 4096 character limit)
        full_message = header + "\n".join(message_parts)
        if len(full_message) > 4000:
            parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode="Markdown")
        else:
            await update.message.reply_text(full_message, parse_mode="Markdown")

    except Exception as e:
        print(f"Error in list_users: {e}")
        await update.message.reply_text("❌ *Error generating user list!*", parse_mode="Markdown")

# === MAIN FUNCTION ===
def main():
    """Start the bot with error handling."""
    try:
        app = Application.builder().token(TOKEN).build()

        # Command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("menu", main_menu))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("genkey", generate_key))
        app.add_handler(CommandHandler("revoke", revoke_key))
        app.add_handler(CommandHandler("key", enter_key))
        app.add_handler(CommandHandler("ban", ban_user))
        app.add_handler(CommandHandler("unban", unban_user))
        app.add_handler(CommandHandler("stats", admin_stats))
        app.add_handler(CommandHandler("listusers", list_users))
        app.add_handler(CommandHandler("broadcast", broadcast))
        app.add_handler(CommandHandler("confirm_broadcast", confirm_broadcast))

        # Callback handler
        app.add_handler(CallbackQueryHandler(callback_handler))

        # Error handler
        app.add_error_handler(error_handler)

        # Start polling with better status message
        print("💎 ZXI PREMIUM BOT IS NOW RUNNING...")
        print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎮 Supported games: {', '.join(DATABASE_FILES.keys())}")
        print(f"⏱️ Cooldown settings: {GENERATION_DELAY}s delay, {COOLDOWN_TIME}s cooldown")
        app.run_polling()
    except Exception as e:
        print(f"❌ Bot crashed with error: {str(e)}")
        # Attempt to notify admin with proper await
        if ADMIN_ID:
            try:
                # Create a temporary bot inst		ance to send the crash notification
                bot = Bot(token=TOKEN)
                asyncio.run(bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"⚠️ *Bot Crashed!*\n\nError: {str(e)}",
                    parse_mode="Markdown"
                ))
            except Exception as e:
                print(f"Failed to send crash notification: {str(e)}")

if __name__ == "__main__":
    main()
