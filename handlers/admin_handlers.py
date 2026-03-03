import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_stats, get_setting, update_setting, update_payment_status, get_payment, get_users_by_status, update_user_status, get_admins, add_admin, remove_admin

EDIT_SETTING = 1
RECEIVE_BROADCAST_MESSAGE = 2
RECEIVE_NEW_ADMIN = 3
RECEIVE_REMOVE_ADMIN = 4

def is_admin(user_id: int) -> bool:
    admins = get_admins()
    return str(user_id) in admins

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
            [InlineKeyboardButton("💎 Premium Text", callback_data="admin_edit_premium_text")],
            [InlineKeyboardButton("💳 UPI / QR", callback_data="admin_edit_upi_message"), InlineKeyboardButton("🖼 UPI QR", callback_data="admin_edit_upi_qr")],
            [InlineKeyboardButton("✅ Confirm Msg", callback_data="admin_edit_confirm_message")],
            [InlineKeyboardButton("🛑 Offer Text", callback_data="admin_edit_offer_text"), InlineKeyboardButton("🖼 Offer QR", callback_data="admin_edit_offer_qr")],
            [InlineKeyboardButton("📢 Broadcast Msg", callback_data="admin_edit_broadcast_message"), InlineKeyboardButton("🔗 Join Options", callback_data="admin_join_options")],
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
        
    elif data == "admin_users":
        keyboard = [
            [InlineKeyboardButton("👥 All Users", callback_data="admin_users_all")],
            [InlineKeyboardButton("✅ Approved Users", callback_data="admin_users_approved")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        await query.message.edit_text("👥 Users\n\nChoose a list to view:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data.startswith("admin_users_"):
        status = data.replace("admin_users_", "")
        users = get_users_by_status(None if status == "all" else "approved")
        text = f"👥 {status.capitalize()} Users ({len(users)}):\n"
        for i, u in enumerate(users[:50]): # limit to 50
            text += f"- {u.get('first_name', '')} (@{u.get('username', '')}) `ID: {u.get('user_id')}`\n"
        if len(users) > 50: text += "...and more."
        if not users: text += "No users found."
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_users")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_payments":
        keyboard = [
            [InlineKeyboardButton("⏳ Pending", callback_data="admin_payments_pending"), InlineKeyboardButton("✅ Done", callback_data="admin_payments_confirmed")],
            [InlineKeyboardButton("❌ Rejected", callback_data="admin_payments_rejected")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        await query.message.edit_text("💳 Payments\n\nChoose payment status:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data.startswith("admin_payments_"):
        status = data.replace("admin_payments_", "")
        from database import supabase
        if supabase:
            resp = supabase.table('payments').select('*').eq('status', status).execute()
            payments = resp.data if resp.data else []
        else:
            payments = []
            
        text = f"💳 {status.capitalize()} Payments ({len(payments)}):\n"
        for p in payments[:50]:
            text += f"- ID: `{p['id'][:8]}...` | User: `{p['user_id']}`\n"
        if not payments: text += "No payments found."
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_payments")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_control":
        keyboard = [
            [InlineKeyboardButton("➕ Add Admin", callback_data="admin_add"), InlineKeyboardButton("➖ Remove Admin", callback_data="admin_remove")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
        ]
        admins = get_admins()
        text = "👤 Admin Control\n\nCurrent Admins:\n" + "\n".join([f"- `{a}`" for a in admins])
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data == "admin_add":
        await query.message.reply_text("Please reply with the Telegram User ID you want to ADD as Admin:")
        return RECEIVE_NEW_ADMIN
        
    elif data == "admin_remove":
        await query.message.reply_text("Please reply with the Telegram User ID you want to REMOVE from Admins:")
        return RECEIVE_REMOVE_ADMIN

    elif data == "admin_broadcast":
        await query.message.reply_text("Please send the message (Text/Photo/Video) you want to broadcast to ALL users:")
        return RECEIVE_BROADCAST_MESSAGE
        
    elif data == "admin_join_options":
        keyboard = [
            [InlineKeyboardButton("🔗 Join Channel Link", callback_data="admin_edit_join_link")],
            [InlineKeyboardButton("📝 Join Link Message", callback_data="admin_edit_join_msg")],
            [InlineKeyboardButton("👁 Preview Result", callback_data="admin_join_preview")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_settings")]
        ]
        await query.message.edit_text("🔗 Join Options\n\nEdit your post-payment join message:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_join_preview":
        join_link = get_setting('join_link') or "https://example.com"
        join_msg = get_setting('join_msg') or "Click below to join!"
        keyboard = [[InlineKeyboardButton("🔗 JOIN CHANNEL", url=join_link)]]
        try:
            await query.message.reply_text(f"*(Preview of Join Message)*\n\n{join_msg}", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            await query.message.reply_text(f"*(Preview of Join Message)*\n\n{join_msg}", reply_markup=InlineKeyboardMarkup(keyboard))
        
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
    await update.message.reply_text(f"✅ Setting {setting_key} updated securely.")
    return ConversationHandler.END

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
        
    users = get_users_by_status(None)
    total = len(users)
    if total == 0:
        await update.message.reply_text("No users to broadcast to.")
        return ConversationHandler.END
        
    progress_msg = await update.message.reply_text(f"⏳ Broadcasting to {total} users...\nProgress: [                    ] 0%")
    
    success = 0
    for i, u in enumerate(users):
        try:
            if update.message.photo:
                await context.bot.send_photo(chat_id=u['user_id'], photo=update.message.photo[-1].file_id, caption=update.message.caption)
            elif update.message.video:
                await context.bot.send_video(chat_id=u['user_id'], video=update.message.video.file_id, caption=update.message.caption)
            elif update.message.animation:
                await context.bot.send_animation(chat_id=u['user_id'], animation=update.message.animation.file_id, caption=update.message.caption)
            elif update.message.document:
                await context.bot.send_document(chat_id=u['user_id'], document=update.message.document.file_id, caption=update.message.caption)
            else:
                await context.bot.send_message(chat_id=u['user_id'], text=update.message.text)
            success += 1
        except:
            pass
            
        # Update progress bar every 10 users or at the end
        if (i + 1) % 10 == 0 or (i + 1) == total:
            percent = int(((i + 1) / total) * 100)
            bars = int(percent / 5)
            progress_bar = "[" + "█" * bars + " " * (20 - bars) + f"] {percent}%"
            try:
                await progress_msg.edit_text(f"⏳ Broadcasting to {total} users...\nProgress: {progress_bar}")
            except:
                pass
                
        await asyncio.sleep(0.05) # Prevent rate limits
        
    await progress_msg.edit_text(f"✅ Broadcast Complete!\nSuccessfully sent to {success}/{total} users.")
    return ConversationHandler.END

async def receive_new_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    new_admin = update.message.text.strip()
    if new_admin.isdigit():
        add_admin(new_admin)
        await update.message.reply_text(f"✅ User `{new_admin}` added as Admin.", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Invalid ID. Must be numbers.")
    return ConversationHandler.END

async def receive_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    old_admin = update.message.text.strip()
    if old_admin == str(update.effective_user.id):
        await update.message.reply_text("❌ You cannot remove yourself.")
    elif old_admin.isdigit():
        remove_admin(old_admin)
        await update.message.reply_text(f"✅ User `{old_admin}` removed from Admins.", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Invalid ID.")
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
            join_msg = get_setting('join_msg') or "Click below to join!"
            
            keyboard = [[InlineKeyboardButton("🔗 JOIN CHANNEL", url=join_link)]]
            try:
                await context.bot.send_message(chat_id=user_id, text=f"{confirm_message}\n\n{join_msg}", reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                await context.bot.send_message(chat_id=user_id, text=f"{confirm_message}\n\n{join_msg}\n{join_link}")
            
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
