import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from handlers.user_handlers import (
    start, unlock_premium, i_have_paid, receive_screenshot, 
    cancel_payment, claim_offer, reject_offer, PAY_SCREENSHOT
)
from handlers.admin_handlers import (
    admin_panel, admin_callback, receive_setting, 
    approve_payment, reject_payment, EDIT_SETTING,
    RECEIVE_BROADCAST_MESSAGE, receive_broadcast,
    RECEIVE_NEW_ADMIN, receive_new_admin,
    RECEIVE_REMOVE_ADMIN, receive_remove_admin
)
from keep_alive import keep_alive

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    keep_alive()
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
        entry_points=[CallbackQueryHandler(admin_callback, pattern='^admin_.*$')],
        states={
            EDIT_SETTING: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE, receive_setting)],
            RECEIVE_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.IMAGE | filters.Document.VIDEO | filters.VIDEO, receive_broadcast)],
            RECEIVE_NEW_ADMIN: [MessageHandler(filters.TEXT, receive_new_admin)],
            RECEIVE_REMOVE_ADMIN: [MessageHandler(filters.TEXT, receive_remove_admin)],
        },
        fallbacks=[CommandHandler("admin", admin_panel)]
    )
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(admin_conv)
    
    # Base Admin Callbacks
    # Base Admin Callbacks (Handled inside admin_conv mostly, but we keep these for non-conversation flows)
    application.add_handler(CallbackQueryHandler(approve_payment, pattern='^approve_payment_.*$'))
    application.add_handler(CallbackQueryHandler(reject_payment, pattern='^reject_payment_.*$'))
    
    # Offer Reject & Cancel Callbacks (works globally)
    application.add_handler(CallbackQueryHandler(reject_offer, pattern='^reject_offer$'))
    application.add_handler(CallbackQueryHandler(cancel_payment, pattern='^cancel_payment$'))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
