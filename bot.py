import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# =======================================================
# HARDCODED FIX: Put your actual text keys inside the quotes
# =======================================================
TELEGRAM_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
UPSCALE_API_KEY = "PASTE_YOUR_UPSCALER_API_KEY_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting message when /start is issued."""
    await update.message.reply_text("👋 Hi! Send me any image, and I will upscale it for you using AI!")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads the image, sends it to the upscaling API, and replies with the result."""
    status_message = await update.message.reply_text("⚡ Processing your image... Please wait.")
    
    try:
        # Get highest resolution image
        photo = update.message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)
        
        image_url = tg_file.file_path
        img_response = requests.get(image_url)
        
        if img_response.status_code != 200:
            raise Exception("Failed to download image from Telegram.")

        await status_message.edit_text("🤖 AI is enhancing your image pixels...")
        
        # Example using Clipdrop API endpoint
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
    """Start the bot."""
    # Ensure placeholders were modified
    if "PASTE_YOUR_" in TELEGRAM_TOKEN or "PASTE_YOUR_" in UPSCALE_API_KEY:
        logger.critical("CRITICAL: You forgot to replace the placeholder text with your real tokens!")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))

    # Run the bot using Polling
    logger.info("Bot is starting up successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
