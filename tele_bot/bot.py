# import custom functions
from blindspot import detect_object_start, detect_object_stop

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# telegram bot token
TOKEN: str = '6379793471:AAHyW7T4ASdgNvYKI_qMlipWR670YYR3uZM'

'''
async def start_blindspot(update: Update, context: ContextTypes):
    await update.message.reply_text('Starting blindspot detection...')
    detect_object_start()


async def stop_blindspot(update: Update, context: ContextTypes):
    await update.message.reply_text('Blindspot detection stopped')
    detect_object_stop()
'''

async def handle_response(text: str) -> str:
    return text


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id: int = update.message.chat.id
    message_type: str = update.message.chat.type
    text: str = update.message.text
    response = await handle_response(text)

    print(f'User ({user_id}) in {message_type}: {text}')
    print(f'Bot: {response}')
    await update.message.reply_text(response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    await update.message.reply_text('Sorry, I can\'t do it')


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()
    #app.add_handler(CommandHandler('start_blindspot', start_blindspot))
    #app.add_handler(CommandHandler('stop_blindspot', stop_blindspot))
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    app.add_error_handler(error_handler)
    app.run_polling(poll_interval=1)
