-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    joined_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create payments table
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES public.users(user_id) ON DELETE CASCADE,
    amount NUMERIC,
    screenshot_file_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, confirmed, rejected
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create settings table
CREATE TABLE IF NOT EXISTS public.settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Insert default settings
INSERT INTO public.settings (key, value) VALUES
    ('welcome_text', 'Welcome to our premium bot!'),
    ('welcome_photo', 'none'),
    ('premium_text', '💎 VIP ACCESS PAYMENT\n\n⚡️ FLASH SALE: Only 4 Spots Left! 🔥\n🍑 ONE-TIME PAYMENT: ₹79 ONLY!\n🔓 LIFETIME VALIDITY\n\n1️⃣ Scan QR & Pay ₹79\n2️⃣ Click ''I HAVE PAID'' button below\n✅ UPI ID: YOUR_UPI_ID'),
    ('premium_photo', 'none'),
    ('upi_message', 'Pay to this UPI'),
    ('upi_qr', 'none'),
    ('crypto_message', 'Pay to this Crypto Address'),
    ('crypto_qr', 'none'),
    ('confirm_message', '✅ Screenshot Submitted!\nPlease wait for the admin to verify.'),
    ('demo_url', 'https://example.com/demo'),
    ('howto_url', 'https://example.com/howto'),
    ('proofs_url', 'https://t.me/your_proofs_channel'),
    ('offer_text', '🛑 WAIT! DON''T GO YET!\n\nIs the price too high? 😟\n💎 Original Price: ₹79\n🎁 Your Offer Price: ₹59 ONLY!\n\n⚠️ This offer disappears soon.'),
    ('offer_qr', 'none'),
    ('broadcast_message', '💎 𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐂𝐎𝐍𝐅𝐈𝐑𝐌𝐄𝐃 💎\n\n👤 𝑺𝒐𝒎𝒆𝒐𝒏𝒆 𝒋𝒖𝒔𝒕 𝒖𝒏𝒍𝒐𝒄𝒌𝒆𝒅 𝑳𝒊𝒇𝒆𝒕𝒊𝒎𝒆 𝑨𝒄𝒄𝒆𝒔𝒔!\n\n⚡️ 𝙄𝙣𝙨𝙩𝙖𝙣𝙩 𝘼𝙥𝙥𝙧𝙤𝙫𝙖𝙡\n🔓 𝙁𝙪𝙡𝙡 𝘼𝙘𝙘𝙚𝙨𝙨 𝙂𝙧𝙖𝙣𝙩𝙚𝙙\n✅ 100% 𝙑𝙚𝙧𝙞𝙛𝙞𝙚𝙙\n\n👉 /CLAIM_OFFER 👈🏻 (ᴄʟᴀɪᴍ ʏᴏᴜʀ ꜱᴘᴏᴛ ɴᴏᴡ 🥵)'),
    ('join_link', 'https://t.me/+your_private_channel_link')
ON CONFLICT (key) DO NOTHING;
