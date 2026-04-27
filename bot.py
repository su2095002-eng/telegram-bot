import requests
import time
import hashlib
import hmac
import base64
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ====== THAY THÔNG TIN ======
TOKEN = "8749356697:AAFfiYD2SZPzXCaJpzVVh-fcJ8WhDC--_lo"
host = "identify-ap-southeast-1.acrcloud.com"
access_key = "296c929b5dc7ba13d230b5ef1124f920"
access_secret = "mabjWhiYNpQWMbzzq43LckcuiOMLVYCIeZLVa9NH"
# ===========================

def recognize(file_path):
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = "\n".join([
        http_method,
        http_uri,
        access_key,
        data_type,
        signature_version,
        timestamp
    ])

    sign = base64.b64encode(
        hmac.new(access_secret.encode('ascii'),
                 string_to_sign.encode('ascii'),
                 digestmod=hashlib.sha1).digest()
    ).decode('ascii')

    with open(file_path, 'rb') as f:
        files = {'sample': f}
        data = {
            'access_key': access_key,
            'sample_bytes': os.path.getsize(file_path),
            'timestamp': timestamp,
            'signature': sign,
            'data_type': data_type,
            'signature_version': signature_version
        }

        url = f"http://{host}{http_uri}"
        res = requests.post(url, files=files, data=data)

    return res.json()

# ====== HANDLE AUDIO ======
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Đang nhận diện...")

    file = await update.message.audio.get_file()
    file_path = "song.mp3"
    await file.download_to_drive(file_path)

    result = recognize(file_path)

    try:
        music = result['metadata']['music'][0]
        title = music['title']
        artist = music['artists'][0]['name']

        await update.message.reply_text(f"🎵 {title} - {artist}")
    except Exception as e:
        print(result)  # debug
        await update.message.reply_text("❌ Không nhận diện được")

# ====== CHẠY BOT ======
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.AUDIO, handle_audio))

print("Bot đang chạy...")
app.run_polling()