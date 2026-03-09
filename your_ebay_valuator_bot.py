import asyncio
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from services.valuation_service import ValuationService

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize valuation service
valuation_service = ValuationService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Send me a photo of any item and I'll valuate it for eBay reselling!\n\n"
        "📸 Just take a photo → Send it here → Get instant valuation"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Get the photo
        photo = await update.message.photo[-1].get_file()
        photo_data = await photo.download_as_bytearray()

        # Convert to base64 for valuation service
        photo_base64 = base64.b64encode(photo_data).decode('utf-8')

        # Get valuation using existing service
        valuation = valuation_service.evaluate_item(photo_base64, "image/jpeg")

        # Format response
        response = (
            f"💰 **{valuation.item_name}**\n"
            f"Value: **${valuation.estimated_value:.2f}**\n"
            f"Range: ${valuation.value_range['low']:.2f} - ${valuation.value_range['high']:.2f}\n"
            f"Condition: {valuation.condition_score}/10\n"
            f"Profit: **{valuation.profitability.value.upper()}**\n"
            f"Worth listing: {'✅ YES' if valuation.worth_listing else '❌ NO'}\n\n"
            f"📊 Resale Score: {valuation.resale_score}/10\n"
            f"🏪 Best platforms: {', '.join(valuation.recommended_platforms)}"
        )

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error analyzing image: {str(e)}\n"
            "Please try again with a clear photo."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 **eBay Valuator Bot Help**\n\n"
        "📸 Send any photo to get instant valuation\n"
        "💰 Get estimated value and profit potential\n"
        "📊 See condition and resale scores\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message",
        parse_mode='Markdown'
    )

async def main():
    if not TELEGRAM_TOKEN:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found in .env file")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("[BOT] eBay Valuator Bot started!")
    print("Send photos to get instant valuations")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
