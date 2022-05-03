from aiogram import Bot, exceptions
import asyncio
from connect import *
import config
from time import time

bot = Bot(config.token)

async def delete_message():
    while True:
        sql = "SELECT `chat_id`, `message_id` FROM `delete_messages` WHERE `delete_time` <= %s"
        cursor.execute(sql, [int(time())])
        
        if cursor.rowcount > 0:
            fetchmany = True
            while fetchmany:
                messages = cursor.fetchmany(100)
                if not messages:
                    fetchmany = False
                    await asyncio.sleep(1)
                    continue
    
                for message in messages:
                    try:
                        chat_id, message_id = message
                        await bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass
    
                    sql = "DELETE FROM `delete_messages` WHERE `chat_id` = %s AND `message_id` = %s"
                    cursor.execute(sql, [chat_id, message_id])
    
                    await asyncio.sleep(0.04)
        await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.run_until_complete(delete_message())