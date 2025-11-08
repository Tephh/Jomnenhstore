import logging
import sqlite3
import os
import asyncio
from datetime import datetime

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    print("Error: Required packages not installed. Please run: python setup.py")
    TELEGRAM_AVAILABLE = False

from config import BOT_TOKEN, ADMIN_USERNAME, ADMIN_PASSWORD
from database import Database
from khqr import MockKHQRPayment

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class JomNenhBot:
    def __init__(self):
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram packages not installed.")
            return
            
        self.db = Database()
        self.khqr = MockKHQRPayment()
        
        try:
            self.app = Application.builder().token(BOT_TOKEN).build()
            self.setup_handlers()
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
    
    def setup_handlers(self):
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("account", self.account))
        self.app.add_handler(CommandHandler("products", self.show_products))
        self.app.add_handler(CommandHandler("orders", self.show_orders))
        self.app.add_handler(CommandHandler("admin", self.admin_login))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Callback query handlers
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = f"""
👋 Welcome {user.first_name} to *JomNenh Bot*!

🤖 *Available Commands:*
/account - View your account
/products - Browse products  
/orders - View your orders
/admin - Admin access
/help - Get help

🎮 *We sell:*
• Software Licenses
• Game Accounts  
• Premium Subscriptions
• Digital Products

💳 *Payment:* KHQR Bakong (Cambodia)
🇰🇭 *Service:* Cambodia Wide

_Start shopping by clicking the button below!_ 
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Browse Products", callback_data="view_products")],
            [InlineKeyboardButton("👤 My Account", callback_data="my_account")],
            [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
🤖 *JomNenh Bot Help*

*Commands:*
/start - Start the bot
/account - View your account info  
/products - Browse available products
/orders - View your order history
/admin - Admin login
/help - Show this help message

*How to Buy:*
1. Click "Browse Products"
2. Choose a category
3. Select a product
4. Confirm purchase
5. Scan KHQR to pay
6. Receive product instantly!

*Support:*
For issues, contact @tephh
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            account_text = f"""
👤 *Account Information*

🆔 *User ID:* `{user_data[0]}`
👤 *Name:* {user_data[2]} {user_data[3]}
📛 *Username:* @{user_data[1] or 'N/A'}
💰 *Balance:* ${user_data[4]:.2f}
📅 *Member since:* {user_data[5][:10]}
            """
            await update.message.reply_text(account_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Account not found!")
    
    async def show_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        products = self.db.get_products()
        
        if not products:
            await update.message.reply_text("📭 No products available at the moment.")
            return
        
        # Show categories first
        categories = set([product[4] for product in products])
        keyboard = []
        
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                f"📁 {category.title()}", 
                callback_data=f"category_{category}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔍 View All Products", callback_data="view_all_products")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📦 *Choose a category:*", reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_products_by_category(self, query, category):
        products = self.db.get_products(category)
        
        if not products:
            await query.edit_message_text(f"📭 No products in *{category}* category.", parse_mode='Markdown')
            return
        
        text = f"📦 *Products - {category.title()}*\n\n"
        keyboard = []
        
        for product in products:
            text += f"""
🆔 *#{product[0]}*
📛 *Name:* {product[1]}
📝 *Description:* {product[2]}
💰 *Price:* ${product[3]:.2f}
📊 *Stock:* {product[5]}
────────────────────
            """
            keyboard.append([InlineKeyboardButton(
                f"🛒 Buy {product[1]} - ${product[3]:.2f}", 
                callback_data=f"buy_{product[0]}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="view_products")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_all_products(self, query):
        products = self.db.get_products()
        
        text = "📦 *All Products*\n\n"
        keyboard = []
        
        for product in products:
            text += f"""
🆔 *#{product[0]}*
📛 *Name:* {product[1]}
📝 *Description:* {product[2]}
💰 *Price:* ${product[3]:.2f}
📁 *Category:* {product[4]}
📊 *Stock:* {product[5]}
────────────────────
            """
            keyboard.append([InlineKeyboardButton(
                f"🛒 Buy {product[1]}", 
                callback_data=f"buy_{product[0]}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="view_products")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def initiate_purchase(self, query, product_id):
        product = self.db.get_product(product_id)
        
        if not product:
            await query.edit_message_text("❌ Product not found!")
            return
        
        if product[5] <= 0:  # Check stock
            await query.edit_message_text("❌ This product is out of stock!")
            return
        
        text = f"""
🛒 *Confirm Purchase*

📛 *Product:* {product[1]}
📝 *Description:* {product[2]}
💰 *Price:* ${product[3]:.2f}
📦 *Stock:* {product[5]}

💳 *Payment Method:* KHQR Bakong
🇰🇭 *Supported Banks:* All Cambodian Banks

Click *Confirm Purchase* to generate KHQR code.
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"confirm_buy_{product_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"category_{product[4]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def process_payment(self, query, product_id):
        product = self.db.get_product(product_id)
        user = query.from_user
        
        if not product:
            await query.edit_message_text("❌ Product not found!")
            return
        
        if product[5] <= 0:
            await query.edit_message_text("❌ This product is out of stock!")
            return
        
        # Create order
        order_id = self.db.create_order(user.id, product_id, 1, product[3])
        
        if not order_id:
            await query.edit_message_text("❌ Error creating order. Please try again.")
            return
        
        # Generate KHQR
        qr_filename, qr_data = self.khqr.generate_payment_qr(product[3], order_id)
        
        if qr_filename and os.path.exists(qr_filename):
            text = f"""
💳 *Payment Required*

📦 *Product:* {product[1]}
💰 *Amount:* ${product[3]:.2f}
🆔 *Order:* #{order_id}

📱 *Please scan the KHQR code below to pay using Bakong:*

💡 *After payment, the product will be delivered automatically within 30 seconds.*
⏰ *Please keep this chat open during payment...*
            """
            
            try:
                with open(qr_filename, 'rb') as qr_file:
                    await query.message.reply_photo(
                        photo=qr_file,
                        caption=text,
                        parse_mode='Markdown'
                    )
                
                # Clean up QR file
                os.remove(qr_filename)
                
                # Notify admin
                admin_text = f"""
🆕 *New Order Created*

👤 *Customer:* {user.first_name} (@{user.username})
📦 *Product:* {product[1]}
💰 *Amount:* ${product[3]:.2f}
🆔 *Order:* #{order_id}
📊 *Status:* Pending Payment
                """
                try:
                    await self.app.bot.send_message(ADMIN_USERNAME, admin_text, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Could not notify admin: {e}")
                
                # Start payment verification
                asyncio.create_task(self.check_payment_status(order_id, product, user))
                
            except Exception as e:
                logger.error(f"Error sending QR code: {e}")
                await query.edit_message_text("❌ Error processing payment. Please try again.")
        else:
            await query.edit_message_text("❌ Error generating payment QR code!")
    
    async def check_payment_status(self, order_id, product, user):
        # Simulate payment processing delay
        await asyncio.sleep(10)
        
        # Verify payment (mock - replace with real verification)
        payment_result = self.khqr.verify_payment(f"txn_{order_id}")
        
        if payment_result and payment_result.get('status') == 'success':
            self.db.update_order_status(order_id, 'completed', f"txn_{order_id}")
            
            # Send product to user
            if product[6]:  # is_digital
                digital_key = self.db.get_digital_key(product[0])
                delivery_text = f"""
🎉 *Payment Successful!*

📦 *Product:* {product[1]}
🆔 *Order:* #{order_id}
💰 *Amount:* ${product[3]:.2f}

🔑 *Your Key:* 
`{digital_key}`

💾 *Instructions:* Use this key to activate your product.

📧 *Support:* Contact @tephh for issues.

Thank you for your purchase! 🙏
                """
                await self.app.bot.send_message(user.id, delivery_text, parse_mode='Markdown')
            
            # Notify admin
            admin_text = f"""
✅ *Order Completed*

👤 *Customer:* {user.first_name} (@{user.username})
📦 *Product:* {product[1]}
💰 *Amount:* ${product[3]:.2f}
🆔 *Order:* #{order_id}
🔑 *Key Delivered:* Yes
            """
            try:
                await self.app.bot.send_message(ADMIN_USERNAME, admin_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Could not notify admin: {e}")
                
        else:
            self.db.update_order_status(order_id, 'failed')
            fail_text = f"""
❌ *Payment Failed*

🆔 *Order:* #{order_id}
📦 *Product:* {product[1]}

Please try again or contact support @tephh if you have paid.
            """
            await self.app.bot.send_message(user.id, fail_text, parse_mode='Markdown')
    
    async def show_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        orders = self.db.get_user_orders(user.id)
        
        if not orders:
            await update.message.reply_text("📭 You have no orders yet.")
            return
        
        orders_text = "📦 *Your Orders:*\n\n"
        for order in orders:
            status_emoji = "✅" if order[4] == "completed" else "⏳" if order[4] == "pending" else "❌"
            orders_text += f"""
🆔 *Order #*{order[0]}
📦 *Product:* {order[1]}
🔢 *Quantity:* {order[2]}
💰 *Amount:* ${order[3]:.2f}
📊 *Status:* {status_emoji} {order[4]}
📅 *Date:* {order[5][:16]}
────────────────────
            """
        
        await update.message.reply_text(orders_text, parse_mode='Markdown')
    
    async def admin_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.username == ADMIN_USERNAME.replace('@', ''):
            context.user_data['awaiting_password'] = True
            await update.message.reply_text("🔐 *Admin Login*\n\nPlease enter admin password:", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ You are not authorized to access admin panel.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get('awaiting_password'):
            if update.message.text == ADMIN_PASSWORD:
                context.user_data['admin_logged_in'] = True
                context.user_data['awaiting_password'] = False
                await self.show_admin_panel(update, context)
            else:
                await update.message.reply_text("❌ Incorrect password!")
                context.user_data['awaiting_password'] = False
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📊 View Products", callback_data="admin_view_products")],
            [InlineKeyboardButton("📦 View All Orders", callback_data="admin_view_orders")],
            [InlineKeyboardButton("📈 Statistics", callback_data="admin_stats")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👨‍💼 *Admin Panel*", reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_view_products(self, query):
        products = self.db.get_products()
        
        text = "📊 *All Products (Admin View)*\n\n"
        for product in products:
            stock_emoji = "🟢" if product[5] > 10 else "🟡" if product[5] > 0 else "🔴"
            text += f"""
🆔 *#{product[0]}*
📛 {product[1]}
💰 ${product[3]:.2f}
📦 Stock: {stock_emoji} {product[5]}
📁 Category: {product[4]}
────────────────────
            """
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    async def admin_view_orders(self, query):
        orders = self.db.get_all_orders()
        
        if not orders:
            await query.edit_message_text("📭 No orders found.")
            return
        
        text = "📦 *All Orders*\n\n"
        for order in orders:
            status_emoji = "✅" if order[4] == "completed" else "⏳" if order[4] == "pending" else "❌"
            text += f"""
🆔 *Order:* #{order[0]}
👤 *User:* {order[1]}
📦 *Product:* {order[2]}
💰 *Amount:* ${order[3]:.2f}
📊 *Status:* {status_emoji} {order[4]}
📅 *Date:* {order[5][:16]}
────────────────────
            """
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    async def admin_stats(self, query):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get total orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
        
        # Get completed orders
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
        completed_orders = cursor.fetchone()[0]
        
        # Get total revenue
        cursor.execute("SELECT SUM(total_amount) FROM orders WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Get total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        stats_text = f"""
📈 *Business Statistics*

👥 *Total Users:* {total_users}
📦 *Total Orders:* {total_orders}
✅ *Completed Orders:* {completed_orders}
💰 *Total Revenue:* ${total_revenue:.2f}
📊 *Success Rate:* {(completed_orders/total_orders*100) if total_orders > 0 else 0:.1f}%

🔄 *Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        await query.edit_message_text(stats_text, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "view_products":
            await self.show_products(update, context)
        elif data == "view_all_products":
            await self.show_all_products(query)
        elif data == "my_account":
            await self.account(update, context)
        elif data == "my_orders":
            await self.show_orders(update, context)
        elif data == "help":
            await self.help_command(update, context)
        elif data.startswith("category_"):
            category = data.replace("category_", "")
            await self.show_products_by_category(query, category)
        elif data.startswith("buy_"):
            product_id = int(data.replace("buy_", ""))
            await self.initiate_purchase(query, product_id)
        elif data.startswith("confirm_buy_"):
            product_id = int(data.replace("confirm_buy_", ""))
            await self.process_payment(query, product_id)
        elif data == "admin_view_products":
            await self.admin_view_products(query)
        elif data == "admin_view_orders":
            await self.admin_view_orders(query)
        elif data == "admin_stats":
            await self.admin_stats(query)
    
    def run(self):
        if not TELEGRAM_AVAILABLE:
            logger.error("Cannot run bot: Required packages not installed.")
            print("Please install required packages: python setup.py")
            return
            
        logger.info("🤖 JomNenh Bot is starting...")
        print("=" * 50)
        print("🎉 JomNenh Bot Started Successfully!")
        print(f"👤 Admin: {ADMIN_USERNAME}")
        print("💳 Payment: KHQR Bakong (Mock Mode)")
        print("📊 Database: Initialized with sample products")
        print("=" * 50)
        print("Press Ctrl+C to stop the bot.")
        
        try:
            self.app.run_polling()
        except Exception as e:
            logger.error(f"Bot stopped with error: {e}")

if __name__ == "__main__":
    bot = JomNenhBot()
    bot.run()