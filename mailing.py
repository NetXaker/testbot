from connect import cursor
import asyncio
from aiogram import Bot, utils
import config
import json

bot = Bot(config.token)

async def mailing():
    run = True
    while run:

        sql = "SELECT `message_id`, `from_user_id`, `reply_markup`, `last_user_id`, `mail_type` FROM `mailing` WHERE `status` = %s"
        cursor.execute(sql, [1])

        if cursor.rowcount == 0:
            await asyncio.sleep(2)
            continue

        message_id, from_user_id, reply_markup, last_user_unique_id, mail_type = cursor.fetchone()
        if reply_markup:
            reply_markup = json.loads(reply_markup)
            
        if mail_type == 'users':
            table = 'users'
            column = 'user_id'
            sleep = 0.05
        else:
            table = 'groups'
            column = 'chat_id'
            sleep = 0.05

        sql = f"SELECT `id`, `{column}` FROM `{table}` WHERE `id` > %s"
        cursor.execute(sql, [last_user_unique_id])

        if cursor.rowcount > 0:
            users = cursor.fetchall()
            last_id = users[-1][0]
            for i in users:
                sql = "SELECT `mail_type` FROM `mailing` WHERE `status` = %s"
                cursor.execute(sql, [1])

                if cursor.rowcount == 0:
                    break

                user_last_id = i[0]
                user_id = i[1]
                try:
                    if reply_markup:
                        await bot.copy_message(user_id, from_user_id, message_id, reply_markup=reply_markup)
                    else:
                        await bot.copy_message(user_id, from_user_id, message_id)
                    sql = "UPDATE `mailing` SET `last_user_id` = %s"
                    cursor.execute(sql, [user_last_id])

                    if last_id == user_last_id:
                        sql = "DELETE FROM `mailing`"
                        cursor.execute(sql)
                except utils.exceptions.RetryAfter:
                    asynctio.sleep(1)
                    break
                    
                except Exception:
                    sql = f"DELETE FROM `{table}` WHERE `{column}` = %s"
                    cursor.execute(sql, [user_id])

                await asyncio.sleep(sleep)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mailing())
