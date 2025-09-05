import requests
import urllib.parse
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from flask import Flask, jsonify

# Initialize Flask app for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Biological Term Translator Bot is running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Telegram Bot Token from environment variable
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8008763177:AAGGPXWJI9LZ853mb5CPK0M8-93B_ppCTlo')
PORT = int(os.environ.get('PORT', 10000))  # Fixed to port 10000
HOST = '0.0.0.0'  # Bind to all interfaces

def get_biological_meaning(term):
    """
    Get the biological meaning of a term in Burmese from the Paxsenix API
    """
    # Base API URL
    base_url = "https://api.paxsenix.dpdns.org/v1/deepseek-chat/chat"
    
    # Construct the prompt with the user's term
    prompt = f'Provide the biological meaning of the following term in Burmese. Use this exact format: \'Meaning Of [Term] In Burmese :\' followed by the definition. The definition should be a direct translation of the scientific meaning, similar to this example for \'Glycogen\':Meaning Of Glycogen In Burmese : glucos(မော်လီကျူး)နှင့်တူသောဖွဲ့စည်းပုံရှိသည့် polysaccharide ဖြစ်ပြီး ကျွန်ုပ်တို့ခန္ဓာကိုယ်တွင်သိုလှောင်ထားသော ကာဗိုဟိုက်ဒရိတ်ပုံစံတစ်မျိုးဖြစ်သည်.Now provide the meaning for: \'{term}\''
    
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Construct the full URL
    url = f"{base_url}?text={encoded_prompt}"
    
    # Headers
    headers = {
        "Authorization": "Bearer sk-paxsenix-45-dpDQ7eXYt8esnLxDyjFLV0X1XOWWrV218mhTqMEcdJW1J"
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        if data.get("ok"):
            return data.get("message", "No message found in response")
        else:
            return f"Error: {data.get('message', 'Unknown error')}"
            
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"
    except ValueError as e:
        return f"Failed to parse JSON response: {e}"

# Telegram Bot Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = """
🤖 *Biological Term Translator Bot*

Welcome! I can translate biological terms into Burmese with their scientific meanings.

Simply send me any biological term like:
- Protein
- DNA
- Enzyme
- Cell
- Carbohydrates

I'll provide the Burmese translation with the scientific definition!

Type /help for more information.
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = """
📖 *How to use this bot:*

1. Send any biological term (English)
2. I'll fetch the Burmese translation with scientific meaning
3. Wait a few seconds for the response

Examples of terms you can try:
- `Protein`
- `Mitochondria`
- `Photosynthesis`
- `Enzyme`
- `Cell membrane`

The bot uses the Paxsenix API to provide accurate biological definitions.
    """
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_message = update.message.text.strip()
    
    # Ignore empty messages
    if not user_message:
        await update.message.reply_text("Please send a biological term to translate.")
        return
    
    # Show typing action
    await update.message.reply_chat_action(action="typing")
    
    # Send "Thinking The Translation" message first
    thinking_message = await update.message.reply_text("🤔 Thinking The Translation...")
    
    # Get the biological meaning
    result = get_biological_meaning(user_message)
    
    # Edit the thinking message to show the final result
    await thinking_message.edit_text(result)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")

async def main():
    """Main function to run the bot"""
    print("Starting Biological Term Translator Telegram Bot...")
    
    # Create Telegram application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("Bot is running...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep the application running
    await asyncio.Event().wait()

def run_flask():
    """Run Flask app for health checks on port 10000 and bind to 0.0.0.0"""
    print(f"Starting Flask server on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)

if __name__ == "__main__":
    # For Render deployment, we need to run both Flask and Telegram bot
    import threading
    
    # Start Flask in a separate thread for health checks
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run the Telegram bot in the main thread
    asyncio.run(main())
