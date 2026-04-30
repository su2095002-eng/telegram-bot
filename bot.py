import requests
import time
import hashlib
import hmac
import base64
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ====== THÔNG TIN ======
TOKEN = "8662314538:AAGKp2cZs-1GaS9bU6sayKzd4X89QY_mvwQ"
host = "identify-ap-southeast-1.acrcloud.com"
access_key = "296c929b5dc7ba13d230b5ef1124f920"
access_secret = "mabjWhiYNpQWMbzzq43LckcuiOMLVYCIeZLVa9NH"
# ======================


# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """👋 bot đẹp trai xin chào

👉 Hãy gửi file nhạc của bạn để hệ thống xử lý nhé

⚠️ Lưu ý: chỉ sử dụng file MP3, nếu file khác sẽ lỗi
"""
    await update.message.reply_text(text)


# ====== NHẬN DIỆN ======
def recognize(file_path):
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = "\n".join([
        http_method, http_uri, access_key,
        data_type, signature_version, timestamp
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


# ====== HANDLE ======
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Đang xử lý...")

    file_path = None

    try:
        # 👉 lấy file + tên gốc
        if update.message.audio:
            file = await update.message.audio.get_file()
            original_name = update.message.audio.file_name or "audio.mp3"
        elif update.message.document:
            file = await update.message.document.get_file()
            original_name = update.message.document.file_name or "audio.mp3"
        else:
            await update.message.reply_text("❌ Không phải file mp3")
            return

        # 👉 tránh trùng tên
        file_path = f"{update.message.message_id}_{original_name}"
        await file.download_to_drive(file_path)

        # 👉 gọi API
        result = recognize(file_path)
        print("API RESULT:", result)

        # ====== LOGIC BẢN QUYỀN ======
        title = "Không xác định"
        artist = ""

        # 🟢 mặc định = không bản quyền
        copyright_status = "🟢 Không có bản quyền"

        # 🔴 nếu nhận diện được = có bản quyền
        if result.get("status", {}).get("code") == 0:
            music = result['metadata']['music'][0]
            title = music.get('title', 'Unknown')
            artist = music.get('artists', [{}])[0].get('name', 'Unknown')
            copyright_status = "🔴 Có bản quyền"

        # 👉 caption đẹp
        caption = f"""✅ ĐÃ XỬ LÝ THÀNH CÔNG!
━━━━━━━━━━━━━━━
🎵 Bài hát: {title} {('- ' + artist) if artist else ''}
━━━━━━━━━━━━━━━

📌 Bản quyền: {copyright_status}

👉 File bên dưới để nghe & tải trực tiếp
"""

        print(">>> ĐANG GỬI FILE:", original_name)

        # 👉 gửi lại file (GIỮ NGUYÊN TÊN)
        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=original_name,
                caption=caption
            )

    except Exception as e:
        print("LỖI:", e)
        await update.message.reply_text("❌ Có lỗi xảy ra")

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


# ====== RUN ======
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_audio))

print("Bot đang chạy...")
app.run_polling()
