import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
UPSCALE_API_KEY = os.getenv("UPSCALE_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting message when /start is issued."""
    await update.message.reply_text("👋 Hi! Send me any image, and I will upscale it for you using AI!")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads the image, sends it to the upscaling API, and replies with the result."""
    # Send an initial placeholder message
    status_message = await update.message.reply_text("⚡ Processing your image... Please wait.")
    
    try:
        # 1. Get the highest resolution image sent by the user
        photo = update.message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)
        
        # Download the file into memory
        image_url = tg_file.file_path
        img_response = requests.get(image_url)
        
        if img_response.status_count != 200:
            raise Exception("Failed to download image from Telegram.")

        # 2. Forward the image to the Upscaling API (Example using Clipdrop API structure)
        # Note: If your API provider requires JSON/Base64, adjust this part according to their docs.
        await status_message.edit_text("🤖 AI is enhancing your image pixels...")
        
        api_url = "https://api.clipdrop.co/image-upscaling/v1" # Replace with your chosen provider's URL
        headers = {"x-api-key": UPSCALE_API_KEY}
        files = {"image_file": ("image.jpg", img_response.content, "image/jpeg")}
        
        # Clipdrop supports 2x, 4x, etc. passed as form data
        data = {"target_width": photo.width * 2, "target_height": photo.height * 2} 

        upscale_response = requests.post(api_url, headers=headers, files=files, data=data)

        if upscale_response.status_code == 200:
            # 3. Send the upscaled image back as a document (so Telegram doesn't compress it again!)
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
    if not TELEGRAM_TOKEN or not UPSCALE_API_KEY:
        logger.critical("Missing Environment Variables! Ensure TELEGRAM_TOKEN and UPSCALE_API_KEY are set.")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))

    # Run the bot using Polling
    logger.info("Bot is starting up...")
    application.run_polling()

if __name__ == "__main__":
    main()
