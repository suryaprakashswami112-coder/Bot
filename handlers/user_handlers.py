import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_setting, add_user, update_user_status, add_payment, get_user, get_admins

PAY_SCREENSHOT = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db_user = get_user(user.id)
    if not db_user:
        add_user(user.id, user.username or "", user.first_name or "", user.last_name or "")
    
    welcome_text = get_setting('welcome_text') or "Welcome to our premium bot!"
    welcome_photo = get_setting('welcome_photo')
    demo_url = get_setting('demo_url') or "https://example.com"
    
    keyboard = [
        [InlineKeyboardButton("📁 UNLOCK PREMIUM 💎", callback_data="unlock_premium")],
        [InlineKeyboardButton("👁 WATCH DEMO 💎", url=demo_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if welcome_photo and welcome_photo != 'none':
            await update.message.reply_photo(photo=welcome_photo, caption=welcome_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in start: {e}")
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup)

async def unlock_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    premium_text = get_setting('premium_text') or "Premium Access"
    upi_qr = get_setting('upi_qr')
    proofs_url = get_setting('proofs_url') or "https://t.me/proofs"
    
    keyboard = [
        [InlineKeyboardButton("✅ I HAVE PAID (Submit Screenshot)", callback_data="i_have_paid")],
        [InlineKeyboardButton("📜 VIEW PROOFS", url=proofs_url)],
        [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if upi_qr and upi_qr != 'none':
            await query.message.reply_photo(photo=upi_qr, caption=premium_text, reply_markup=reply_markup)
        else:
            await query.message.reply_text(text=premium_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in unlock_premium: {e}")
        await query.message.reply_text(text=premium_text, reply_markup=reply_markup)

async def i_have_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("📸 ᴋɪɴᴅʟʏ ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ᴛᴏ ᴠᴇʀɪꜰʏ")
    return PAY_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    photo_file = None
    
    if update.message.photo:
        photo_file = update.message.photo[-1].file_id
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        photo_file = update.message.document.file_id
        
    if not photo_file:
        await update.message.reply_text("Please send a valid image screenshot.")
        return PAY_SCREENSHOT
    
    payment_id = add_payment(user.id, 79.0, photo_file)
    if not payment_id:
        await update.message.reply_text("Error processing payment. Try again.")
        return ConversationHandler.END
        
    confirm_message = get_setting('confirm_message') or "✅ Screenshot Submitted!\nPlease wait for the admin to verify."
    await update.message.reply_text(confirm_message)
    
    admins = get_admins()
    admin_caption = (
        f"🚨 **New Payment Received!**\n"
        f"👤 Name: {user.first_name} {user.last_name or ''} {('(@' + user.username + ')') if user.username else ''}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"🕰 Time: {update.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"💳 Payment ID: `{payment_id}`\n\n"
        f"Please approve or reject below."
    )
    keyboard = [
        [
            InlineKeyboardButton("✅ Send Link & Approve", callback_data=f"approve_payment_{payment_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in admins:
        try:
            await context.bot.send_photo(
                chat_id=int(admin_id), 
                photo=photo_file, 
                caption=admin_caption, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")
            
    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        
    offer_text = get_setting('offer_text') or "Original Price: ₹79\nYour Offer Price: ₹59 ONLY!"
    offer_qr = get_setting('offer_qr') or get_setting('upi_qr')
    
    keyboard = [
        [InlineKeyboardButton("✅ I PAID ₹59", callback_data="i_have_paid")],
        [InlineKeyboardButton("❌ No thanks, I'm broke", callback_data="reject_offer")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if offer_qr and offer_qr != 'none':
            if query:
                await query.message.reply_photo(photo=offer_qr, caption=offer_text, reply_markup=reply_markup)
            else:
                await update.message.reply_photo(photo=offer_qr, caption=offer_text, reply_markup=reply_markup)
        else:
            if query:
                await query.message.reply_text(text=offer_text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text=offer_text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error in cancel_payment (offer flow): {e}")

    return ConversationHandler.END

async def reject_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    text = "😔 Offer rejected. See you next time! click here to start again👉🏻(/start)👈🏻"
    await query.message.reply_text(text)

async def claim_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Just route to the cancel_payment logic since it shows the offer
    await cancel_payment(update, context)
