import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_stats, get_setting, update_setting, update_payment_status, get_payment, get_users_by_status, update_user_status

EDIT_SETTING = 1

def is_admin(user_id: int) -> bool:
    admin_id = os.getenv("ADMIN_USER_ID")
    return str(user_id) == admin_id

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Unauthorized.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"), InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("💳 Payments", callback_data="admin_payments"), InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👤 Admin Control", callback_data="admin_control"), InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🔗 Join Link", callback_data="admin_join_link")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 Admin Panel\n\nChoose an option:", reply_markup=reply_markup)
    return ConversationHandler.END

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.message.reply_text("Unauthorized.")
        return ConversationHandler.END

    data = query.data
    if data == "admin_stats":
        stats = get_stats()
        text = (f"📊 Stats\n\n"
                f"👥 Unique Users (Start): {stats['total_users']}\n"
                f"📋 Total Payments: {stats['total_payments']}\n"
                f"⏳ Pending: {stats['pending']}\n"
                f"✅ Confirmed: {stats['confirmed']}\n"
                f"❌ Rejected: {stats['rejected']}")
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data == "admin_settings":
        keyboard = [
            [InlineKeyboardButton("📝 Welcome Text", callback_data="admin_edit_welcome_text"), InlineKeyboardButton("🖼 Welcome Photo", callback_data="admin_edit_welcome_photo")],
            [InlineKeyboardButton("💎 Premium Text", callback_data="admin_edit_premium_text"), InlineKeyboardButton("🖼 Premium Photo", callback_data="admin_edit_premium_photo")],
            [InlineKeyboardButton("💳 UPI Message", callback_data="admin_edit_upi_message"), InlineKeyboardButton("🖼 UPI QR", callback_data="admin_edit_upi_qr")],
            [InlineKeyboardButton("✅ Confirm Msg", callback_data="admin_edit_confirm_message")],
            [InlineKeyboardButton("🛑 Offer Text", callback_data="admin_edit_offer_text"), InlineKeyboardButton("📢 Broadcast Msg", callback_data="admin_edit_broadcast_message")],
            [InlineKeyboardButton("🔗 Join Link", callback_data="admin_edit_join_link")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        await query.message.edit_text("⚙️ Settings\n\nChoose what to edit:\n(Send text or an image)", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data.startswith("admin_edit_"):
        setting_key = data.replace("admin_edit_", "")
        context.user_data['editing_setting'] = setting_key
        await query.message.reply_text(f"Please send the new value for `{setting_key}` (Text or Photo):", parse_mode='Markdown')
        return EDIT_SETTING
        
    elif data == "admin_back":
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"), InlineKeyboardButton("👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton("💳 Payments", callback_data="admin_payments"), InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("👤 Admin Control", callback_data="admin_control"), InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("🔗 Join Link", callback_data="admin_join_link")]
        ]
        await query.message.edit_text("🤖 Admin Panel\n\nChoose an option:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data in ["admin_users", "admin_payments", "admin_broadcast", "admin_control", "admin_join_link"]:
        await query.message.reply_text("This section is configured or under construction. Click Back to return.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]))
        
    return ConversationHandler.END

async def receive_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    setting_key = context.user_data.get('editing_setting')
    if not setting_key:
        return ConversationHandler.END
        
    if update.message.photo:
        value = update.message.photo[-1].file_id
    elif update.message.text:
        value = update.message.text
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        value = update.message.document.file_id
    else:
        await update.message.reply_text("Unsupported format. Please send Text or a Photo.")
        return EDIT_SETTING
        
    update_setting(setting_key, value)
    await update.message.reply_text(f"✅ Setting `{setting_key}` updated securely.", parse_mode='Markdown')
    return ConversationHandler.END

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
        
    payment_id = query.data.replace("approve_payment_", "")
    update_payment_status(payment_id, 'confirmed')
    payment = get_payment(payment_id)
    
    if payment:
        user_id = payment['user_id']
        update_user_status(user_id, 'approved')
        try:
            # Send confirmation to user
            confirm_message = get_setting('confirm_message') or "✅ Your payment was approved!"
            join_link = get_setting('join_link') or "https://t.me/example"
            await context.bot.send_message(chat_id=user_id, text=f"{confirm_message}\n\nJoin here: {join_link}")
            
            # Broadcast to unapproved users
            broadcast_msg = get_setting('broadcast_message') or "💎 𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐂𝐎𝐍𝐅𝐈𝐑𝐌𝐄𝐃 💎..."
            pending_users = get_users_by_status('pending')
            # Only broadcast if message isn't 'none' or something
            if broadcast_msg and broadcast_msg.lower() != 'none':
                for pu in pending_users:
                    if str(pu['user_id']) != str(user_id):
                        try:
                            await context.bot.send_message(chat_id=pu['user_id'], text=broadcast_msg)
                        except Exception as e:
                            print(f"Failed to broadcast to {pu['user_id']}: {e}")
        except Exception as e:
            print(f"Error sending confirm/broadcast: {e}")
            
    await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ APPROVED")

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
        
    payment_id = query.data.replace("reject_payment_", "")
    update_payment_status(payment_id, 'rejected')
    payment = get_payment(payment_id)
    
    if payment:
        user_id = payment['user_id']
        update_user_status(user_id, 'rejected')
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ Your payment was rejected by the admin. Please verify and try again.")
        except:
            pass
            
    await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ REJECTED")
