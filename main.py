import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from handlers.user_handlers import (
    start, unlock_premium, i_have_paid, receive_screenshot, 
    cancel_payment, claim_offer, PAY_SCREENSHOT
)
from handlers.admin_handlers import (
    admin_panel, admin_callback, receive_setting, 
    approve_payment, reject_payment, EDIT_SETTING
)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_bot_token_here":
        logger.error("No valid Telegram Bot Token provided in .env!")
        return

    application = Application.builder().token(token).build()

    # User Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim_offer", claim_offer))
    
    # Payment Flow Conversation
    pay_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(i_have_paid, pattern='^i_have_paid$')],
        states={
            PAY_SCREENSHOT: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_screenshot)],
        },
        fallbacks=[CallbackQueryHandler(cancel_payment, pattern='^cancel_payment$')]
    )
    application.add_handler(pay_conv)
    
    # Additional User Callbacks
    application.add_handler(CallbackQueryHandler(unlock_premium, pattern='^unlock_premium$'))

    # Admin Conversation (Editing Settings)
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern='^admin_edit_.*$')],
        states={
            EDIT_SETTING: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE, receive_setting)],
        },
        fallbacks=[CommandHandler("admin", admin_panel)]
    )
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(admin_conv)
    
    # Base Admin Callbacks
    application.add_handler(CallbackQueryHandler(admin_callback, pattern='^admin_.*$'))
    application.add_handler(CallbackQueryHandler(approve_payment, pattern='^approve_payment_.*$'))
    application.add_handler(CallbackQueryHandler(reject_payment, pattern='^reject_payment_.*$'))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
