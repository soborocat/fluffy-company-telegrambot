import os
import logging
import asyncio
import signal
import datetime
import html
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def forward_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        post = update.channel_post
        
        # 텍스트 추출 (일반 텍스트 우선, HTML 버전은 나중에 처리)
        text = post.text or post.caption or ""
        
        # HTML 버전이 있다면 HTML 엔티티 디코딩
        if post.text_html or post.caption_html:
            html_text = post.text_html or post.caption_html
            # HTML 엔티티 디코딩: &lt; → <, &gt; → >, &amp; → & 등
            text = html.unescape(html_text)
            
            # HTML 태그를 Discord 마크다운으로 변환
            text = text.replace('<b>', '**').replace('</b>', '**')
            text = text.replace('<strong>', '**').replace('</strong>', '**')
            text = text.replace('<i>', '*').replace('</i>', '*')
            text = text.replace('<em>', '*').replace('</em>', '*')
            text = text.replace('<code>', '`').replace('</code>', '`')
            text = text.replace('<pre>', '``````')
            text = text.replace('<u>', '__').replace('</u>', '__')
            text = text.replace('<s>', '~~').replace('</s>', '~~')
            text = text.replace('<strike>', '~~').replace('</strike>', '~~')
            
            # 링크 처리: <a href="url">text</a> → [text](url)
            import re
            text = re.sub(r'<a href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text)
            
            # 나머지 HTML 태그 제거
            text = re.sub(r'<[^>]+>', '', text)
        
        # Discord Embed 구성
        embed = {
            "title": "📢 알려요",
            "description": text[:4096] if text else "내용 없음",
            "color": 5814783,  # 파란색
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": f"{post.chat.title if post.chat.title else '알 수 없음'}"
            }
        }
        
        # 이미지 처리
        if post.photo:
            largest_photo = max(post.photo, key=lambda x: x.width * x.height)
            file_info = await context.bot.get_file(largest_photo.file_id)
            embed["image"] = {"url": file_info.file_path}
        
        # 문서/파일 처리
        if post.document:
            file_info = await context.bot.get_file(post.document.file_id)
            embed["fields"] = [{
                "name": "📎 첨부파일",
                "value": f"[{post.document.file_name or '파일'}]({file_info.file_path})",
                "inline": False
            }]
        
        # 비디오 처리
        if post.video:
            file_info = await context.bot.get_file(post.video.file_id)
            if post.video.thumbnail:
                thumb_info = await context.bot.get_file(post.video.thumbnail.file_id)
                embed["thumbnail"] = {"url": thumb_info.file_path}
            embed["fields"] = embed.get("fields", []) + [{
                "name": "🎥 동영상",
                "value": f"[동영상 보기]({file_info.file_path})",
                "inline": False
            }]
        
        # Discord로 전송
        payload = {"embeds": [embed]}
        
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(DISCORD_WEBHOOK, json=payload)
                logging.info(f"Embed 메시지 전송 완료: {text[:50]}...")
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
