import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================================
# 🛠️ EVERYTHING YOU NEED TO FIX IS RIGHT HERE:
# ====================================================================
TELEGRAM_TOKEN = "PUT_YOUR_ACTUAL_TELEGRAM_BOT_TOKEN_HERE"
UPSCALE_API_KEY = "PUT_YOUR_ACTUAL_CLIPDROP_API_KEY_HERE"
RENDER_WEB_URL = "https://imageupscallingbot.onrender.com" 
# ====================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting message when /start is issued."""
    await update.message.reply_text("👋 Hi! Send me any image, and I will upscale it for you using AI!")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads the image, sends it to the upscaling API, and replies with the result."""
    status_message = await update.message.reply_text("⚡ Processing your image... Please wait.")
    
    try:
        # Get highest resolution image version
        photo = update.message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)
        
        # Download file to memory
        image_url = tg_file.file_path
        img_response = requests.get(image_url)
        
        if img_response.status_code != 200:
            raise Exception("Failed to download image from Telegram.")

        await status_message.edit_text("🤖 AI is enhancing your image pixels...")
        
        # Call the Upscaling API (Clipdrop Endpoint Structure)
        api_url = "https://api.clipdrop.co/image-upscaling/v1" 
        headers = {"x-api-key": UPSCALE_API_KEY}
        files = {"image_file": ("image.jpg", img_response.content, "image/jpeg")}
        data = {"target_width": photo.width * 2, "target_height": photo.height * 2} 

        upscale_response = requests.post(api_url, headers=headers, files=files, data=data)

        if upscale_response.status_code == 200:
            await status_message.edit_text("📤 Uploading your high-res image...")
            await update.message.reply_document(
                document=upscale_response.content,
                filename="upscaled_image.png",
                caption="✨ Here is your upscaled image!"
            )
            await status_message.delete()
        else:
            logger.error(f"API Error: {upscale_response.text}")
            await status_message.edit_text("❌ Sorry, the upscaling service encountered an error.")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await status_message.edit_text("❌ Something went wrong while processing your image.")

def main():
    """Start the bot using Webhooks."""
    # Safety Check: Ensures you modified the configuration values before executing
    if "PUT_YOUR_" in TELEGRAM_TOKEN or "PUT_YOUR_" in UPSCALE_API_KEY or "your-subdomain" in RENDER_WEB_URL:
        logger.critical("CRITICAL: You forgot to replace the placeholder tokens or the Render URL!")
        return

    # Create the Application connection
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register text and photo handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))

    # Render supplies a PORT environment variable automatically. Defaults to 8000 locally.
    port = int(os.environ.get("PORT", 8000))

    logger.info(f"Starting Web Service on port {port} using webhook...")
    
    # Run using webhook instead of run_polling()
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{RENDER_WEB_URL}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
