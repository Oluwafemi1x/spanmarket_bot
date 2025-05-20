# spanmarket_bot.py
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states
CHOOSING, ADDING_TO_CART, AWAITING_PAYMENT_PROOF, ASKING_QUESTIONS = range(4)

# Product catalog
catalog = {
    "?? RDP Basic": {"price": 25, "description": "4GB RAM, 100GB NVMe Storage"},
    "??? RDP Plus": {"price": 35, "description": "4GB RAM, 200GB SSD"},
    "?? RDP Pro": {"price": 45, "description": "6GB RAM, 150GB NVMe Storage"},
    "?? RDP Ultra": {"price": 55, "description": "8GB RAM, 1.8TB SSD"},
    "?? RDP Max": {"price": 75, "description": "12GB RAM, 150GB SSD"},
    "?? RDP Elite": {"price": 85, "description": "20GB RAM, 200GB NVMe Storage"},
    "?? Cracking Class": {"price": 30, "description": "SMTP, Bank log, cookies"},
    "?? Combo Making": {"price": 50, "description": "How to make valid combos"},
    "?? Hotmail Combo": {"price": 100, "description": "Freshly generated Hotmail combos"},
}

# Admin user ID (replace with your actual Telegram user ID)
ADMIN_USER_ID = 940989051  # <-- Change this to your Telegram user ID (integer)

# In-memory user carts and payment proofs
user_cart = {}
payment_proofs = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = []
    keyboard = [
        [KeyboardButton("??? View Items")],
        [KeyboardButton("? Ask About an Item")],
        [KeyboardButton("?? Checkout")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "?? Welcome to *Span Market!* Choose an option below:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return CHOOSING


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "View Items" in text:
        return await show_items(update, context)
    elif "Ask About" in text:
        await update.message.reply_text(
            "?? Type the *exact name* of the item you want to ask about:",
            parse_mode="Markdown",
        )
        return ASKING_QUESTIONS
    elif "Checkout" in text:
        return await checkout(update, context)
    else:
        await update.message.reply_text("? Unrecognized option.")
        return CHOOSING
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "View Items" in text:
        return await show_items(update, context)
    elif "Ask About" in text:
        await update.message.reply_text("?? Type the *exact name* of the item you want to ask about:", parse_mode="Markdown")
        return ASKING_QUESTIONS
    elif "Checkout" in text:
        return await checkout(update, context)
    elif "Add More Items" in text:              # <-- Add this block
        return await show_items(update, context)
    else:
        await update.message.reply_text("? Unrecognized option.")
        return CHOOSING


async def show_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(item)] for item in catalog.keys()]
    keyboard.append([KeyboardButton("?? Back to Menu")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    message = "?? *Available Products:*\n\n"
    for item, info in catalog.items():
        message += f"{item}\n?? *${info['price']}*\n?? {info['description']}\n\n"

    await update.message.reply_text(message, parse_mode="Markdown")
    await update.message.reply_text(
        "?? Select an item to *add to cart*:", reply_markup=reply_markup, parse_mode="Markdown"
    )
    return ADDING_TO_CART


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "?? Back to Menu":
        return await start(update, context)

    if text in catalog:
        context.user_data.setdefault("cart", []).append(text)
        await update.message.reply_text(f"? *{text}* added to your cart.", parse_mode="Markdown")
        # Ask if user wants to add more or checkout
        keyboard = [
            [KeyboardButton("?? Add More Items")],
            [KeyboardButton("?? Proceed to Checkout")],
            [KeyboardButton("?? Back to Menu")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Would you like to add more products or proceed to checkout?",
            reply_markup=reply_markup,
        )
        return CHOOSING

    await update.message.reply_text("? Item not recognized. Please select from the list.")
    return ADDING_TO_CART


async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart_items = context.user_data.get("cart", [])
    if not cart_items:
        await update.message.reply_text("?? Your cart is empty.")
        return CHOOSING

    total = sum(catalog[item]["price"] for item in cart_items)
    summary = "\n".join(f"• {item} — *${catalog[item]['price']}*" for item in cart_items)
    deadline = datetime.now() + timedelta(hours=24)  # 24-hour payment window
    context.user_data["payment_deadline"] = deadline
    context.user_data["awaiting_payment"] = True

    message = (
        f"?? *Your Order Summary:*\n{summary}\n\n"
        f"?? *Total:* ${total}\n\n"
        "?? *Payment Methods:*\n"
        "?? *Bank Transfer:* `0246594941 (Wema Bank)`\n"
        "? *Bitcoin:* `17eaarJ59tEk139c6U81XmkyfmYX6cYJfB`\n"
        "?? *USDT (BEP20):* `0x7E8035a227D68DF8DB30EAEaD1C129423EcC3dcE`\n"
        "?? *USDT (TRC20):* `TGyFcqnJrbuqZ91AKrByY3PXevBe3Qytjv`\n"
        "?? *Ethereum (ETH):* `0x7E8035a227D68DF8DB30EAEaD1C129423EcC3dcE`\n\n"
        f"? *Deadline:* {deadline.strftime('%Y-%m-%d %H:%M:%S')} (24 hours)\n"
        "?? Please *upload your payment proof* below."
    )
    await update.message.reply_text(message, parse_mode="Markdown")
    return AWAITING_PAYMENT_PROOF


async def payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    deadline = context.user_data.get("payment_deadline")

    if not deadline or datetime.now() > deadline:
        await update.message.reply_text(
            "? Payment window expired. Please restart the process."
        )
        context.user_data["cart"] = []
        context.user_data["awaiting_payment"] = False
        return CHOOSING

    # Save payment proof info (for admin to review)
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        file_id = photo_file.file_id
        payment_proofs[user_id] = file_id
    elif update.message.document:
        doc_file = await update.message.document.get_file()
        file_id = doc_file.file_id
        payment_proofs[user_id] = file_id
    else:
        await update.message.reply_text("? Please send a photo or document as payment proof.")
        return AWAITING_PAYMENT_PROOF

    await update.message.reply_text(
        "?? Payment proof received! Waiting for admin confirmation."
    )

    # Notify admin with user info and payment proof
    admin_message = (
        f"?? Payment proof received from user {user_id} (@{update.effective_user.username or 'N/A'}).\n"
        f"Cart Items: {', '.join(context.user_data.get('cart', []))}\n"
        f"To confirm payment, send:\n"
        f"/confirm_payment {user_id}\n"
        f"To clear cart, send:\n"
        f"/clear_cart {user_id}"
    )

    app = context.application
    await app.bot.send_message(chat_id=ADMIN_USER_ID, text=admin_message)
    # Forward the proof file to admin
    if update.message.photo or update.message.document:
        await update.message.forward(chat_id=ADMIN_USER_ID)

    return CHOOSING


async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /confirm_payment <user_id>")
        return

    user_id_str = args[0]
    try:
        user_id = int(user_id_str)
    except ValueError:
        await update.message.reply_text("Invalid user_id. It should be a number.")
        return

    # Clear user cart and payment proof
    user_cart_data = context.application.user_data.get(user_id, {})
    user_cart_data["cart"] = []
    user_cart_data["awaiting_payment"] = False
    payment_proofs.pop(user_id, None)

    # Notify user
    try:
        await context.application.bot.send_message(
            chat_id=user_id,
            text="✅ Your payment has been confirmed! Your order will be processed shortly.",
        )
    except Exception as e:
        logger.warning(f"Failed to notify user {user_id}: {e}")

    await update.message.reply_text(f"✅ Payment confirmed for user {user_id}.")


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /clear_cart <user_id>")
        return

    user_id_str = args[0]
    try:
        user_id = int(user_id_str)
    except ValueError:
        await update.message.reply_text("Invalid user_id. It should be a number.")
        return

    user_cart_data = context.application.user_data.get(user_id, {})
    user_cart_data["cart"] = []
    user_cart_data["awaiting_payment"] = False
    payment_proofs.pop(user_id, None)

    # Notify user
    try:
        await context.application.bot.send_message(
            chat_id=user_id,
            text="⚠️ Your cart has been cleared by the admin.",
        )
    except Exception as e:
        logger.warning(f"Failed to notify user {user_id}: {e}")

    await update.message.reply_text(f"⚠️ Cart cleared for user {user_id}.")


async def ask_about_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    info = catalog.get(query)
    if info:
        await update.message.reply_text(f"{query}\n?? {info['description']}")
    else:
        await update.message.reply_text(
            "? Item not found. Make sure you typed the exact name."
        )
    return CHOOSING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("?? Session cancelled.")
    return ConversationHandler.END


BOT_TOKEN = "7584386438:AAElTyWeR-YYSauGwl8H4lAyau5kowLkP34"  # Replace with your actual token

app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
        ADDING_TO_CART: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_to_cart)],
        AWAITING_PAYMENT_PROOF: [MessageHandler(filters.PHOTO | filters.Document.ALL, payment_proof)],
        ASKING_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_about_item)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
# Admin commands for confirming payment and clearing carts
app.add_handler(CommandHandler("confirm_payment", confirm_payment))
app.add_handler(CommandHandler("clear_cart", clear_cart))

print("? Bot is running...")
app.run_polling()
