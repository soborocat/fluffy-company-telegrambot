import os
import logging
import asyncio
import signal
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def forward_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        text = update.channel_post.text_html or update.channel_post.caption_html
        
        if text:
            async with aiohttp.ClientSession() as session:
                try:
                    await session.post(DISCORD_WEBHOOK, json={"content": text})
                    logging.info(f"메시지 전송 완료: {text[:50]}...")
                except Exception as e:
                    logging.error(f"전송 실패: {e}")

async def main():
    if not DISCORD_WEBHOOK or not BOT_TOKEN:
        logging.error("환경변수가 설정되지 않았습니다")
        return
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POSTS, forward_notice))
    
    # 종료 신호 처리
    stop_signals = (signal.SIGTERM, signal.SIGINT)
    for sig in stop_signals:
        signal.signal(sig, lambda s, f: asyncio.create_task(app.stop()))
    
    # 수동으로 시작/실행
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    logging.info("봇이 실행 중입니다. Ctrl+C로 종료하세요.")
    
    # 무한 대기 (봇이 실행되는 동안)
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("봇 종료 중...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
