import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
import tweepy

# Configuration
TWITTER_ACCOUNT = "bigbangdist10"
TELEGRAM_CHANNEL = "https://t.me/Yakstaschannel"
TELEGRAM_GROUP = "https://t.me/yakstascapital"
(
    START,
    VERIFY_TWITTER,
    GET_WALLET
) = range(3)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "To qualify for mr kayblezzy2's airdrop:\n\n"
        "1. Join our Telegram channel:\n"
        f"   → {TELEGRAM_CHANNEL}\n\n"
        "2. Join our Telegram group:\n"
        f"   → {TELEGRAM_GROUP}\n\n"
        "3. Follow our Twitter:\n"
        f"   → https://twitter.com/{TWITTER_ACCOUNT}\n\n"
        "After completing all steps, click the button below to verify!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ VERIFY TWITTER", callback_data="verify_twitter")]
        ])
    )
    return START

async def verify_twitter(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Please send your Twitter username (without @):\n\n"
        "Example: `elonmusk`",
        parse_mode="Markdown"
    )
    return VERIFY_TWITTER

async def check_twitter(update: Update, context):
    twitter_username = update.message.text.strip()
    context.user_data['twitter'] = twitter_username
    
    # Initialize Twitter API
    try:
        auth = tweepy.OAuth2BearerHandler(os.getenv("TWITTER_BEARER_TOKEN"))
        api = tweepy.API(auth)
        
        # Verify Twitter follow
        user = api.get_user(screen_name=twitter_username)
        relationship = api.get_friendship(
            source_screen_name=twitter_username,
            target_screen_name=TWITTER_ACCOUNT
        )
        
        if relationship[0].following:
            await update.message.reply_text(
                "✅ Twitter follow verified!\n\n"
                "Please send your Solana wallet address:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("← Back", callback_data="verify_twitter")]
                ])
            )
            return GET_WALLET
        else:
            await update.message.reply_text(
                "❌ You're not following our Twitter!\n\n"
                f"Please follow https://twitter.com/{TWITTER_ACCOUNT} and try again:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("← Back", callback_data="verify_twitter")]
                ])
            )
            return VERIFY_TWITTER
            
    except tweepy.errors.NotFound:
        await update.message.reply_text(
            "❌ Twitter account not found. Please send a valid username:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Back", callback_data="verify_twitter")]
            ])
        )
        return VERIFY_TWITTER
    except Exception as e:
        logging.error(f"Twitter verification error: {e}")
        await update.message.reply_text(
            "⚠️ Error verifying Twitter. Please try again:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Back", callback_data="verify_twitter")]
            ])
        )
        return VERIFY_TWITTER

async def get_wallet(update: Update, context):
    wallet = update.message.text.strip()
    
    # Simple Solana address validation
    if len(wallet) >= 32 and len(wallet) <= 44:
        # Get user info
        user = update.effective_user
        username = f"@{user.username}" if user.username else user.first_name
        
        # Notify admin
        admin_msg = (
            "🚀 New Airdrop Submission:\n\n"
            f"User: {username}\n"
            f"Twitter: @{context.user_data['twitter']}\n"
            f"Wallet: `{wallet}`"
        )
        
        try:
            await context.bot.send_message(
                chat_id=os.getenv("ADMIN_ID"),
                text=admin_msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Admin notification failed: {e}")
        
        # Final message to user
        await update.message.reply_text(
            "🎉 CONGRATULATIONS!\n\n"
            "You've passed mr kayblezzy2's airdrop call!\n\n"
            "100 SOL will be sent to your wallet:\n"
            f"`{wallet}`\n\n"
            "Well done, hope you didn't cheat the system!",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "❌ Invalid Solana address. Please send a valid wallet:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("← Back", callback_data="verify_twitter")]
        ])
    )
    return GET_WALLET

async def cancel(update: Update, context):
    await update.message.reply_text("Process cancelled.")
    return ConversationHandler.END

def main():
    # Create Application
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(verify_twitter, pattern="^verify_twitter$")],
            VERIFY_TWITTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_twitter)],
            GET_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wallet)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
