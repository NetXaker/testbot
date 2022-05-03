from loader import *

bot = Bot(config.token)
dp = Dispatcher(bot, storage=MemoryStorage())


def is_banned_user(m):
    sql = "SELECT `id` FROM `users_blacklist` WHERE `user_id` = %s"
    cursor.execute(sql, [m.from_user.id])
    if cursor.rowcount > 0:
        return True
    return False

@dp.message_handler(lambda m: is_banned_user(m), chat_type='private')
@dp.throttled(rate=1)
async def banned_update(message: types.Message):
    pass


def is_banned_group(m):
    sql = "SELECT `id` FROM `groups_blacklist` WHERE `group_id` = %s"
    cursor.execute(sql, [m.chat.id])
    if cursor.rowcount > 0:
        return True
    return False

@dp.my_chat_member_handler(lambda m: is_banned_group(m), chat_type=['supergroup'])
async def banned_update(member: types.ChatMemberUpdated):
    if member.new_chat_member.status != 'left':
        await bot.leave_chat(member.chat.id)


@dp.my_chat_member_handler()
async def my_chat_member_update(my_chat_member: types.ChatMemberUpdated):
    new_member = my_chat_member.new_chat_member
    old_member = my_chat_member.old_chat_member

    if my_chat_member.chat.type == 'private':
        user_id = my_chat_member.chat.id

        # if new_member.status == 'member':
        #     full_name = new_member.user.full_name
        #     admin = 1 if user_id in config.admin else 0
        #     sql = "INSERT INTO `users` VALUES (%s, %s, %s, %s)"
        #     cursor.execute(sql, [None, user_id, full_name, admin])

        if new_member.status == 'kicked':
            sql = "DELETE FROM `users` WHERE `user_id` = %s"
            cursor.execute(sql, [user_id])

        return
    
    if my_chat_member.chat.type != 'supergroup':
        text = '<b>bot faqat supergrouppalarda ishlaydi!</b>'
        await bot.send_message(my_chat_member.chat.id, text, 'html')
        return await bot.leave_chat(my_chat_member.chat.id)

    # if my_chat_member.from_user.id not in config.admin and new_member.status == 'member':
    #     return await bot.leave_chat(my_chat_member.chat.id)

    if new_member.status == 'member' and old_member.status != 'administrator':
        text = '''📊Men Guruhga kim qancha odam qo'shganligini aytib beruvchi botman. 

Bot orqali Guruhingizga istagancha odam yigʻib olasiz vedio qoʻllanmada koʻrsatilgan Botni ishlatish. 

/help  -  buyrugi orqali bot buyruqlari haqida ma'lumot olishingiz mumkin☑️

⚠️ Bot to'g'ri ishlashi uchun ADMIN huquqini berishingiz kerak'''
        await bot.send_message(my_chat_member.chat.id, text, 'html')
        
    elif new_member.status == 'administrator':
        chat_id = my_chat_member.chat.id
        chat_title = my_chat_member.chat.title
        chat_username = my_chat_member.chat.username

        users = await bot.get_chat_administrators(chat_id)
        
        admins = ''
        for user in users:
            admins += '{}-'.format(user['user']['id'])

        sql = "SELECT `id` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [chat_id])

        if cursor.rowcount > 0:
            sql = "UPDATE `groups` SET `title` = %s, `username` = %s, `admins` = %s WHERE `chat_id` = %s"
            cursor.execute(sql, [chat_title, chat_username, admins, chat_id])
        else:
            sql = "INSERT INTO `groups` VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, [None, chat_id, chat_title, chat_username, admins, 0])

        text = '<b>BOT - gruhga admin qilindi</b> ✅\n\n👮🏻‍♂️ <i>Men bu gruhda ishlashga tayyorman!</i>'
        res = await bot.send_message(my_chat_member.chat.id, text, parse_mode='html')
        
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, [None, my_chat_member.chat.id, res.message_id, int(time()) + 15])

    elif new_member.status == 'member' or new_member.status == 'restricted':
        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [my_chat_member.chat.id])

        if cursor.rowcount > 0:
            admins = cursor.fetchone()[0]
            user_id = new_member.user.id
            admins = admins.replace(f'{user_id}-', '')

        sql = "UPDATE `groups` SET `admins` = %s WHERE `chat_id` = %s"
        cursor.execute(sql, [admins, my_chat_member.chat.id])

        text = "😕 <b>Adminlik huquqi olib tashlandi.</b>\n\n<i>Bot to'g'ri ishlashi uchun ADMIN huquqini berishingiz kerak</i>"
        res = await bot.send_message(my_chat_member.chat.id, text, parse_mode='html')

        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, [None, my_chat_member.chat.id, res.message_id, int(time()) + 300])

    elif new_member.status == 'left':
        sql = "DELETE FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [my_chat_member.chat.id])

        sql = "DELETE FROM `allowed_members` WHERE `chat_id` = %s"
        cursor.execute(sql, [my_chat_member.chat.id])
        
        sql = "DELETE FROM `added_members` WHERE `chat_id` = %s"
        cursor.execute(sql, [my_chat_member.chat.id])

@dp.chat_member_handler()
async def chat_member_update(chat_member: types.ChatMemberUpdated):
    if chat_member.new_chat_member.status == 'member' and chat_member.old_chat_member.status not in ['restricted', 'kicked']:
        chat = chat_member.chat

        if chat_member.new_chat_member.user.id == chat_member.from_user.id:
            return

        sql = "SELECT `add_quantity`, `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [chat.id])

        if cursor.rowcount == 0:
            return
        
        add_quantity, admins = cursor.fetchone()
        if add_quantity == 0:
            return

        if config.bot_id not in admins:
            return

        from_user = chat_member.from_user
        new_member = chat_member.new_chat_member

        if cursor.rowcount == 0:
            return
        
        if str(from_user.id) not in admins and new_member.user.is_bot:
            return await bot.kick_chat_member(new_member.user.id)
        
        sql = "SELECT `quantity`, `required_members` FROM `added_members` WHERE `chat_id` = %s AND `user_id` = %s"
        cursor.execute(sql, [chat.id, from_user.id])

        quantity = 0
        required_members = 0
        
        if cursor.rowcount == 0:
            if add_quantity == 0:
                required_members = 1
                
            sql = "INSERT INTO `added_members` VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, [None, chat.id, from_user.id, from_user.full_name, 1, required_members])
        else:
            quantity, required_members = cursor.fetchone()
            if add_quantity == 0:
                required_members = 0
            else:
                required_members += 1
            
            sql = "UPDATE `added_members` SET `quantity` = %s, `required_members` = %s WHERE `chat_id` = %s AND `user_id` = %s"
            cursor.execute(sql, [quantity+1, required_members, chat.id, from_user.id])

        if required_members+1 == add_quantity:
            sql = "SELECT `id` FROM `allowed_members` WHERE `chat_id` = %s AND `user_id` = %s"
            cursor.execute(sql, [chat.id, from_user.id])
            
            if cursor.rowcount == 0:
                sql = "INSERT INTO `allowed_members` VALUES (%s, %s, %s)"
                cursor.execute(sql, [None, chat.id, from_user.id])
            
            permissions = types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_invite_users=True
            )

            await bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=from_user.id,
                permissions=permissions   
            )

            ahref = f"<a href='tg://user?id={from_user.id}'>{from_user.full_name}</a>"
            text = f"{ahref} <b>Rahmat!\nEnddi bemalol yozavering!.</b>"
            
            res = await bot.send_message(chat.id, text, 'html')
            sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, [None, chat.id, res.message_id, int(time()) + 30])

    if chat_member.old_chat_member.status != 'administrator':
        if chat_member.new_chat_member.status == 'administrator':
            sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
            cursor.execute(sql, [chat_member.chat.id])

            if cursor.rowcount == 0:
                return

            admins = cursor.fetchone()[0]
            admins += f'{chat_member.new_chat_member.user.id}-'

            sql = "UPDATE `groups` SET `admins` = %s WHERE `chat_id` = %s"
            cursor.execute(sql, [admins, chat_member.chat.id])
            
    elif chat_member.old_chat_member.status == 'administrator':
        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [chat_member.chat.id])

        if cursor.rowcount == 0:
            return

        admins = cursor.fetchone()[0]
        admins = admins.replace(f'{chat_member.new_chat_member.user.id}-', '')

        sql = "UPDATE `groups` SET `admins` = %s WHERE `chat_id` = %s"
        cursor.execute(sql, [admins, chat_member.chat.id])


@dp.message_handler(commands='stat', chat_type='private', chat_id=config.admin)
async def stat(message):
    sql = "SELECT COUNT(`id`) FROM `users`"
    cursor.execute(sql)
    users_count = cursor.fetchone()[0]
    
    sql = "SELECT COUNT(`id`) FROM `groups`"
    cursor.execute(sql)
    groups_count = cursor.fetchone()[0]
    
    text = f'Barcha odamlar soni: {users_count}\nBarcha guruhlar soni: {groups_count}'
    await message.answer(text)


@dp.message_handler(text='/start', chat_type='private')
async def get_text(message: types.Message):
    full_name = message.from_user.full_name
    user_id = message.from_user.id
    
    sql = "SELECT `id` FROM `users` WHERE `user_id` = %s"
    cursor.execute(sql, [message.from_user.id])
    
    if cursor.rowcount == 0:
        admin = 1 if user_id in config.admin else 0
        
        sql = 'INSERT INTO `users` VALUES (%s, %s, %s, %s)'
        cursor.execute(sql, [None, user_id, full_name, admin])
    
    text = f'''🤖 <b> Botga xush kelibsiz,</b> <a href="tg://user?id={user_id}">{full_name}</a>
    
📊Men Guruhga kim qancha odam qo'shganligini aytib beruvchi botman. 

Bot orqali Guruhingizga istagancha odam yigʻib olasiz vedio qoʻllanmada koʻrsatilgan Botni ishlatish. 

/help  -  buyrugi orqali bot buyruqlari haqida ma'lumot olishingiz mumkin☑️

⚠️ Bot to'g'ri ishlashi uchun ADMIN huquqini berishingiz kerak'''

    markup = types.InlineKeyboardMarkup()
    url = 'https://t.me/SifatliBotlar/120'
    markup.add(types.InlineKeyboardButton("📹VIDEO qo'llanma", config.help_link))
    url = f'https://t.me/{config.bot_username}?startgroup=new'
    markup.add(types.InlineKeyboardButton("➕GRUHGA QO'SHISH➕", url))
    await message.answer(text, 'html', reply_markup=markup)


@dp.message_handler(commands='help')
async def help(message: types.Message):
    await message.delete()
    
    if message.chat.type == 'supergroup':
        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [message.chat.id])
        
        if cursor.rowcount == 0:
            return
        
        admins = cursor.fetchone()[0]
        if str(message.from_user.id) not in admins:
            return
    
    text = '''🤖 Botimizning buyruqlari! 

/mymembers - 📊Siz qo'shgan odamlar soni!
__________________________
/yourmembers - 📈Reply qilingan odamning , guruhga qo'shgan odamlar soni!
__________________________
/top  -  🏆Eng ko'p odam qo'shgan 10 talik!
__________________________
/delson -  🗑Guruhga odam qo'shganlarni barchasini tozalash!
__________________________
/clean -  🧹Reply qilingan habar egasini malumotlarini 0 ga tenglash!

👥 Guruhga odam yigʻish buyruqlari

/add -  buyrug'i Guruhingizga majburiy odam qo'shishni yoqadi!. Bu orqali Guruhingizga istagancha odam yigʻib olasiz.
_________________________
/add 10 - majburiy odam qo'shishni yoqish!

❗️eslatma: 10 soni o'rniga istagan raqamizni yozib jonatishiz mumkin!
_________________________
/add off  - majburiy odam qo'shishni o'chirib qoyish uchun!'''
    
    markup = types.InlineKeyboardMarkup()
    url = 'https://t.me/SifatliBotlar/120'
    markup.add(types.InlineKeyboardButton("📹VIDEO qo'llanma", config.help_link))
    url = f'https://t.me/{config.bot_username}?startgroup=new'
    markup.add(types.InlineKeyboardButton("➕GRUHGA QO'SHISH➕", url))
    res = await message.answer(text, 'html', reply_markup=markup)

    if message.chat.type == 'supergroup':
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 300])


@dp.message_handler(commands='add')
async def add(message: types.Message):
    if message.chat.type == 'private':
        text = '''❗️Bu funksiya guruhda ishlaydi . Guruhga junating !

Qoʻllanma bilan toʻliq tanishib chiqing'''
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
        return await message.answer(text, 'html', reply_markup=markup)

    await message.delete()
    sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
    cursor.execute(sql, [message.chat.id])

    if cursor.rowcount == 0:
        return
        # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        # return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])
    
    admins = cursor.fetchone()[0]
    if str(message.from_user.id) not in admins:
        return
    
    try:
        add_quantity = message.text.split(' ')[1]
        if add_quantity == 'off':
            add_quantity = 0
            
            sql = "DELETE FROM `allowed_members` WHERE `chat_id` = %s"
            cursor.execute(sql, [message.chat.id])
            
            sql = "UPDATE `added_members` SET `required_members` = %s WHERE `chat_id` = %s"
            cursor.execute(sql, [0, message.chat.id])
        else:
            add_quantity = int(add_quantity)
    except (IndexError, ValueError):
        text = '''<b>Xato!</b>
\n<i>Misol:</i> <code>/add 10</code>'''
        res = await message.answer(text, 'html')
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 15])

    if add_quantity > 200000 or add_quantity < 0:
        text = "<b>Maksimal tarif: 200000!</b>"
        res = await message.answer(text, 'html')
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 15])

    sql = "UPDATE `groups` SET `add_quantity` = %s WHERE `chat_id` = %s"
    cursor.execute(sql, [add_quantity, message.chat.id])

    chat_title = message.chat.title
    if add_quantity == 0:
        text = f"<b>Majburiy odam qo'shish rejimi to'xtatildi!</b>"
    else:
        text = f'''<code>{chat_title}</code> <b>guruhida majburiy odam qo'shish tizimi ishga tushdi!

ТАРИФ: {add_quantity}!</b>'''

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
    res = await message.answer(text, 'html', reply_markup=markup)
    sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])


@dp.message_handler(commands='mymembers')
async def mymembers(message: types.Message):
    markup = types.InlineKeyboardMarkup()

    if message.chat.type == 'private':
        text = '''❗️Bu funksiya guruhda ishlaydi . Guruhga junating !

Qoʻllanma bilan toʻliq tanishib chiqing'''
        markup.add(types.InlineKeyboardButton('📹 Qo\'llanma', config.help_link))
        await message.answer(text, 'html', reply_markup=markup)
    else:
        try:
            await message.delete()
        except Exception:
            pass

        user_id = message.from_user.id
        full_name = message.from_user.full_name
        user_mention = f'<a href="tg://user?id={user_id}">{full_name}</a>'

        sql = "SELECT `quantity` FROM `added_members` WHERE `chat_id` = %s AND `user_id` = %s"
        cursor.execute(sql, [message.chat.id, user_id])
    
        delete_time = 10
        
        if cursor.rowcount > 0:
            quantity = cursor.fetchone()[0]
            if quantity > 0:
                delete_time = 300
                text = f"{user_mention}\n🔹<b> {quantity} Odam qoshdingiz!</b>"
            else:
                text = f'{user_mention}\n❌<b> Siz hali odam qoshmagansiz!</b>'
        else:
            text = f'{user_mention}\n❌<b> Siz hali odam qoshmagansiz!</b>'
    
        res = await message.answer(text, 'html', reply_markup=markup)
    
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + delete_time])


@dp.message_handler(commands='yourmembers')
async def mymembers(message: types.Message):
    markup = types.InlineKeyboardMarkup()

    if message.chat.type == 'private':
        text = '''❗️Bu funksiya guruhda ishlaydi . Guruhga junating !

Qoʻllanma bilan toʻliq tanishib chiqing'''
        markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
        await message.answer(text, 'html', reply_markup=markup)
    else:
        try:
            await message.delete()
        except Exception:
            pass

        delete_time = 10
        
        if message.reply_to_message:
            reply = message.reply_to_message

            user_id = reply.from_user.id
            full_name = reply.from_user.full_name
            user_mention = f'<a href="tg://user?id={user_id}">{full_name}</a>'

            sql = "SELECT `quantity` FROM `added_members` WHERE `chat_id` = %s AND `user_id` = %s"
            cursor.execute(sql, [message.chat.id, user_id])
            
            if cursor.rowcount > 0:
                quantity = cursor.fetchone()[0]
                if quantity > 0:
                    delete_time = 300
                    text = f"{user_mention}\n🔹<b> {quantity} Odam qoshgan!</b>"
                else:
                    text = f'{user_mention}\n❌<b> Hali odam qoshmagan!</b>'
            else:
                text = f'{user_mention}\n❌<b> Hali odam qoshmagan!</b>'
        else:
            text = "siz guruhga kim qancha odam qo'shganligini bilish uchun usha odamga (reply) qilib , /yourmembers so'zini junatishingiz kerak!</b>"
            markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
            
        res = await message.answer(text, 'html', reply_markup=markup)
    
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + delete_time])


@dp.message_handler(commands='clean')
async def mymembers(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    
    if message.chat.type == 'private':
        text = '''❗️Bu funksiya guruhda ishlaydi . Guruhga junating !

Qoʻllanma bilan toʻliq tanishib chiqing'''
        markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
        await message.answer(text, 'html', reply_markup=markup)
    else:
        try:
            await message.delete()
        except Exception:
            pass
        
        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [message.chat.id])

        if cursor.rowcount == 0:
            return
            # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
            # return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])

        admins = cursor.fetchone()[0]
        if str(message.from_user.id) not in admins:
            return
        
        delete_time = 60
        
        if message.reply_to_message:
            delete_time = 10
            reply = message.reply_to_message

            user_id = reply.from_user.id
            full_name = reply.from_user.full_name
            user_mention = f'<a href="tg://user?id={user_id}">{full_name}</a>'

            sql = "DELETE FROM `added_members` WHERE `chat_id` = %s AND `user_id` = %s"
            cursor.execute(sql, [message.chat.id, user_id])
        
            text = f"{user_mention}<b>ni Guruhdagi ma'lumoti tozalandi!/b> 🗑"
        else:
            text = "Guruhga odam qo'shgan odamni alohida malumotini tozalash uchun (reply) qilib shu odamga /clean so'zini jo'nating"
            markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
    
        res = await message.answer(text, 'html', reply_markup=markup)
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + delete_time])


@dp.message_handler(commands='delson')
async def delson(message):
    if message.chat.type == 'private':
        text = '''❗️Bu funksiya guruhda ishlaydi . Guruhga junating !

Qoʻllanma bilan toʻliq tanishib chiqing'''
        await message.answer(text, 'html', reply_markup=markup)
    else:
        try:
            await message.delete()
        except Exception:
            pass

        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [message.chat.id])

        if cursor.rowcount == 0:
            return
            # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
            # return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])

        admins = cursor.fetchone()[0]
        if str(message.from_user.id) not in admins:
            return

        sql = "DELETE FROM `added_members` WHERE `chat_id` = %s"
        cursor.execute(sql, [message.chat.id])

        chat_title = message.chat.title
        text = f"<code>{chat_title}</code> <b>✅ guruhida barcha odam qo'shganlar soni tozalandi!</b> 🗑"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📹 Qo'llanma", config.help_link))
        
        res = await message.answer(text, 'html', reply_markup=markup)
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 60])


@dp.message_handler(commands='top')
async def top(message):
    if message.chat.type == 'private':
        text = '''❗️Bu funksiya guruhda ishlaydi . Guruhga junating !

Qoʻllanma bilan toʻliq tanishib chiqing'''
    else:
        try:
            await message.delete()
        except Exception:
            pass

        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [message.chat.id])

        if cursor.rowcount == 0:
            return
            # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
            # return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])

        admins = cursor.fetchone()[0]
        if str(message.from_user.id) not in admins and message.from_user.id not in config.admin:
            return

        sql = "SELECT `full_name`, `user_id`, `quantity` FROM `added_members` WHERE `chat_id` = %s ORDER BY `quantity` DESC LIMIT %s"
        cursor.execute(sql, [message.chat.id, 10])
        chat_title = message.chat.title
        
        delete_time = 0
        
        if cursor.rowcount == 0:
            delete_time = 10
            text  = "<b>Gruhga hali hechkim odam qo'shmagan!</b>"
        else:
            text = f"👥 <code>{chat_title}</code> <b>guruhiga odam qo'shgan TOP 10 talik:</b>\n"
            top_list = cursor.fetchall()
            n = 0
            for user in top_list:
                n += 1
                
                full_name, user_id, quantity = user
                ahref = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
                text += f'\n<b>{n}.</b> {ahref} - {quantity}'

        res = await message.answer(text, 'html')
        if delete_time > 0:
            sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
            return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + delete_time])



@dp.message_handler(chat_type=['supergroup'])
async def group_messages(message: types.Message):
    # res =  await bot.leave_chat(message.chat.id)
    # try:
    #     print(res.as_json)
    # except Exception:
    #     print(res)
        
    # return
    
    if message.from_user.id in config.admin:
        return

    sql = "SELECT `add_quantity`, `admins` FROM `groups` WHERE `chat_id` = %s"
    cursor.execute(sql, [message.chat.id])
    
    if cursor.rowcount == 0:
        return
        # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        # return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])

    add_quantity, admins = cursor.fetchone()

    if add_quantity == 0 or str(message.from_user.id) in admins:
        return

    if config.bot_id not in admins:
        return

    
    sql = "SELECT `id` FROM `allowed_members` WHERE `chat_id` = %s AND `user_id` = %s"
    cursor.execute(sql, [message.chat.id, message.from_user.id])

    if cursor.rowcount > 0:
        return
    

    sql = "SELECT `required_members` FROM `added_members` WHERE `chat_id` = %s AND `user_id` = %s"
    cursor.execute(sql, [message.chat.id, message.from_user.id])

    mute = False
    if cursor.rowcount > 0:
        required_members = cursor.fetchone()[0]
        if required_members < add_quantity:
            mute = True
    else:
        required_members = 0
        mute = True

    if mute:
        sql = "SELECT `admins` FROM `groups` WHERE `chat_id` = %s"
        cursor.execute(sql, [message.chat.id])
        
        if cursor.rowcount == 0:
            return
            # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
            # return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 30])
        
        admins = cursor.fetchone()[0]
        if str(message.from_user.id) in admins:
            return

        await message.delete()

        permissions = types.ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_send_polls=False,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            permissions=permissions,
            until_date=time() + 300
        )

        full_name = message.from_user.full_name
        ahref = f"<a href='tg://user?id={message.from_user.id}'>{full_name}</a>"
        text = f"<b>Kechirasiz!</b> {ahref} <b>gruhga yozish uchun avval {add_quantity-required_members} odam qo'shishingiz kerak</b>"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="✅ Odam qo'shdim", callback_data=f'i_am_added {message.from_user.id}'))
        res = await message.answer(text, 'html', reply_markup=markup)
        sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        return cursor.execute(sql, [None, message.chat.id, res.message_id, int(time()) + 300])


@dp.callback_query_handler(lambda call: 'i_am_added' in call.data)
async def i_am_added(callback: types.CallbackQuery):
    if str(callback.from_user.id) not in callback.data:
        text = '❌ Ushbu tugma siz uchun emas!'
        return await callback.answer(text, show_alert=True)
    
    sql = "SELECT `add_quantity`, `admins` FROM `groups` WHERE `chat_id` = %s"
    cursor.execute(sql, [callback.message.chat.id])

    if cursor.rowcount == 0:
        return
        # sql = "INSERT INTO `delete_messages` VALUES (%s, %s, %s, %s)"
        # return cursor.execute(sql, [None, callback.message.chat.id, res.message_id, int(time()) + 30])
    
    
    add_quantity, admins = cursor.fetchone()
    if config.bot_id not in admins:
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    if add_quantity == 0:
        text = "Gruhda majburiy odam qo'shish rejimi ishga tushmagan, bemalol yozavering!"
        await callback.answer(text, show_alert=True)
        
        permissions = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_send_polls=True,
            can_invite_users=True
        )

        await bot.restrict_chat_member(
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
            permissions=permissions   
        )

        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    sql = "SELECT `required_members` FROM `added_members` WHERE `chat_id` = %s AND `user_id` = %s"
    cursor.execute(sql, [callback.message.chat.id, callback.from_user.id])

    if cursor.rowcount == 0:
        required_members = 0
    else:
        required_members = cursor.fetchone()[0]
    
    if required_members >= add_quantity:
        text = f"Rahmat!\nEndi bemalol yozavering."
    else:
        text = f"Siz hali gruhga {add_quantity-required_members} odam qo'shishingiz kerak"
    await callback.answer(text, show_alert=True)


@dp.message_handler(commands='panel', chat_type='private', state='*')
async def admin_panel(message: types.Message, state: FSMContext):
    await state.finish()

    sql = "SELECT `admin` FROM `users` WHERE `user_id` = %s"
    cursor.execute(sql, [message.chat.id])

    is_admin = False
    if cursor.rowcount > 0:
        if cursor.fetchone()[0]:
            is_admin = True

    if is_admin:
        text = '<b>Admin panel</b>'
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            types.InlineKeyboardButton('🚫 Ban', callback_data='ban'),
            types.InlineKeyboardButton('📛 Unban', callback_data='unban'),
        )
        markup.row(
            types.InlineKeyboardButton('👨‍💼 Userlar', callback_data='users_statistic'),
            types.InlineKeyboardButton('📊 Guruhlar', callback_data='groups_statistic')
        )
        markup.add(types.InlineKeyboardButton('📧 Habar yuborish', callback_data='mail'))
        await message.answer(text, 'html', reply_markup=markup)


@dp.callback_query_handler(text='panel', state='*')
async def admin_panel_c(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    sql = "SELECT `admin` FROM `users` WHERE `user_id` = %s"
    cursor.execute(sql, [callback.message.chat.id])

    is_admin = False
    if cursor.rowcount > 0:
        if cursor.fetchone()[0]:
            is_admin = True

    if is_admin:
        text = '<b>Admin panel</b>'
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.row(
            types.InlineKeyboardButton('🚫 Ban', callback_data='ban'),
            types.InlineKeyboardButton('📛 Unban', callback_data='unban'),
        )
        markup.row(
            types.InlineKeyboardButton('👨‍💼 Userlar', callback_data='users_statistic'),
            types.InlineKeyboardButton('📊 Guruhlar', callback_data='groups_statistic')
        )
        markup.add(types.InlineKeyboardButton('📧 Habar yuborish', callback_data='mail'))
        await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(text='ban', state='*')
async def choice_ban_type(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('🧑‍💼 Userga', callback_data='ban_user'),
        types.InlineKeyboardButton('👥 Gruhga', callback_data='ban_group'),
    )
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='panel'))
    await callback.message.edit_text('<b>Bannni kimga beramiz?</b>', 'html', reply_markup=markup)


@dp.callback_query_handler(text='unban', state='*')
async def choice_ban_type(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('🧑‍💼 Userdan', callback_data='unban_user'),
        types.InlineKeyboardButton('👥 Gruhdan', callback_data='unban_group'),
    )
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='panel'))
    await callback.message.edit_text('<b>Bannni kimdan ob tashlaymiz?</b>', 'html', reply_markup=markup)


@dp.callback_query_handler(text='ban_user', state='*')
async def ban_user(callback: types.CallbackQuery):
    await SetState.ban_user.set()
    
    text = f"<b>Ban bermoqchi bo'lgan userni id raqamini yuboring.</b>\n\n Misol: <code>{callback.from_user.id}</code>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='ban'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(text='ban_group', state='*')
async def ban_group(callback: types.CallbackQuery):
    await SetState.ban_group.set()
    
    text = f"<b>Ban bermoqchi bo'lgan guruhni id raqamini yuboring.</b>\n\n Misol: <code>-100{callback.from_user.id}</code>"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='ban'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(lambda c: 'unban_group' in c.data, state='*')
async def unban_group(callback: types.CallbackQuery, state: FSMContext):
    text = ''
    
    user_data = await state.get_data()
    last_id = user_data.get('last_id')
    current_page = user_data.get('current_page')

    if last_id is None:
        last_id = 0
    if current_page is None:
        current_page = 0


    sql = "SELECT COUNT(`id`) FROM `groups_blacklist`"
    cursor.execute(sql)
    rows_count = cursor.fetchone()[0]
    rows_count = rows_count / 30

    try:
        res = str(rows_count).split('.')[1]
        pages_count = int(rows_count) + 1
    except (IndexError, AttributeError):
        pages_count = rows_count

    if callback.data == 'unban_group_start':
        last_id = 0
        current_page = 0
    elif callback.data == 'unban_group_end':
        last_id = 999**999
        current_page = pages_count-1

    if callback.data == 'unban_group_prev':
        current_page -= 1
    else:
        current_page += 1


    if callback.data == 'unban_group_prev' or callback.data == 'unban_group_end':
        sql = "SELECT * FROM  `groups_blacklist` WHERE `id` < %s ORDER BY `id` DESC LIMIT 30"
    else:
        sql = "SELECT * FROM  `groups_blacklist` WHERE `id` > %s LIMIT 30"
    cursor.execute(sql, [last_id])


    if cursor.rowcount > 0 and current_page > 0:
        banned_users = cursor.fetchall()

        for banned_user in banned_users:
            id = banned_user[0]
            user_id = banned_user[1]
            full_name = banned_user[2]
            text += '<code>' + str(user_id) + '</code>' + ' ' + str(full_name) + '\n'

        if text:
            await state.update_data(last_id=id, current_page=current_page)
    else:
        return await callback.answer('Ban topilmadi!', show_alert=True)

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('<<', callback_data='unban_group_prev'),
        types.InlineKeyboardButton(f'{current_page}/{pages_count}', callback_data='.'),
        types.InlineKeyboardButton('>>', callback_data='unban_group_next')
    )
    markup.row(
        types.InlineKeyboardButton('<<<', callback_data='unban_group_start'),
        types.InlineKeyboardButton('>>>', callback_data='unban_group_end'),
    )
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='unban'))
    try:
        await SetState.unban_group.set()
        text += '\n' + "<b>Ban olib tashlamoqchi bo'lgan guruhni id raqamini yuboring.</b>"
        await callback.message.edit_text(text, 'html', reply_markup=markup)
    except MessageNotModified:
        return await callback.answer('Ban topilmadi', show_alert=True)


@dp.callback_query_handler(lambda c: 'unban_user' in c.data, state='*')
async def unban_user(callback: types.CallbackQuery, state: FSMContext):
    text = ''
    
    user_data = await state.get_data()
    last_id = user_data.get('last_id')
    current_page = user_data.get('current_page')

    if last_id is None:
        last_id = 0
    if current_page is None:
        current_page = 0


    sql = "SELECT COUNT(`id`) FROM `users_blacklist`"
    cursor.execute(sql)
    rows_count = cursor.fetchone()[0]
    rows_count = rows_count / 30

    try:
        res = str(rows_count).split('.')[1]
        pages_count = int(rows_count) + 1
    except (IndexError, AttributeError):
        pages_count = rows_count

    if callback.data == 'unban_user_start':
        last_id = 0
        current_page = 0
    elif callback.data == 'unban_user_end':
        last_id = 999**999
        current_page = pages_count-1

    if callback.data == 'unban_user_prev':
        current_page -= 1
    else:
        current_page += 1


    if callback.data == 'unban_user_prev' or callback.data == 'unban_user_end':
        sql = "SELECT * FROM  `users_blacklist` WHERE `id` < %s ORDER BY `id` DESC LIMIT 30"
    else:
        sql = "SELECT * FROM  `users_blacklist` WHERE `id` > %s LIMIT 30"
    cursor.execute(sql, [last_id])


    if cursor.rowcount > 0 and current_page > 0:
        banned_users = cursor.fetchall()

        for banned_user in banned_users:
            id = banned_user[0]
            user_id = banned_user[1]
            full_name = banned_user[2]
            text_link = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
            text += '<code>' + str(user_id) + '</code>' + ' ' + full_name + '\n'

        if text:
            await state.update_data(last_id=id, current_page=current_page)
    else:
        return await callback.answer('Ban topilmadi!', show_alert=True)

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('<<', callback_data='unban_user_prev'),
        types.InlineKeyboardButton(f'{current_page}/{pages_count}', callback_data='.'),
        types.InlineKeyboardButton('>>', callback_data='unban_user_next')
    )
    markup.row(
        types.InlineKeyboardButton('<<<', callback_data='unban_user_start'),
        types.InlineKeyboardButton('>>>', callback_data='unban_user_end'),
    )
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='unban'))
    try:
        await SetState.unban_user.set()
        text += '\n' + "<b>Ban olib tashlamoqchi bo'lgan userni id raqamini yuboring.</b>"
        await callback.message.edit_text(text, 'html', reply_markup=markup)
    except MessageNotModified:
        return await callback.answer('Ban topilmadi!', show_alert=True)


@dp.callback_query_handler(text='users_statistic', state='*')
async def users_statistic(callback: types.CallbackQuery):
    sql = "SELECT COUNT(`id`) FROM `users`"
    cursor.execute(sql)

    text = f'Barcha userlar soni: {cursor.fetchone()[0]}'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='panel'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(text='groups_statistic', state='*')
async def groups_statistic(callback: types.CallbackQuery):
    sql = "SELECT COUNT(`id`) FROM `groups`"
    cursor.execute(sql)

    text = f'Barcha guruhlar soni: {cursor.fetchone()[0]}'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='panel'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(text='mail', state='*')
async def mail(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    text = '<b>Habarni kimga yuboramz?</b>'
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('🧑‍💼 Userlarga', callback_data='mail_users'),
        types.InlineKeyboardButton('👥 Gruhlarga', callback_data='mail_groups')
    )
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='panel'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(lambda c: 'mail_users' in c.data, state='*')
async def mail_users(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split(' ')
    try:
        pause_or_resume = data[1]
        if pause_or_resume == 'pause':
            pause_or_resume = 0
        elif pause_or_resume == 'resume':
            pause_or_resume = 1
        elif pause_or_resume == 'delete':
            sql = "DELETE FROM `mailing`"
            cursor.execute(sql)
            await callback.answer("Habar yuborish bekor qilindi", show_alert=True)
            return await mail(callback, state)

        sql = "UPDATE `mailing` SET `status` = %s"
        cursor.execute(sql, [pause_or_resume])
    except IndexError:
        pass

    sql = "SELECT `last_user_id`, `status`, `mail_type` FROM `mailing`"
    cursor.execute(sql)

    if cursor.rowcount > 0:
        last_user_id, status, mail_type = cursor.fetchone()

        if mail_type == 'users':
            table = 'users'
            mail_type = 'odamlarga'
        else:
            table = 'groups'
            mail_type == 'guruhlarga'

        sql = f"SELECT COUNT(`id`) FROM `{table}`"
        cursor.execute(sql)
        users_count = cursor.fetchone()[0]

        sql = f"SELECT COUNT(`id`) FROM `{table}` WHERE `id` < %s"
        cursor.execute(sql, [last_user_id])
        sended_users_count = cursor.fetchone()[0]
        
        pause_or_resume = 'Davom etish ▶️'
        pause_or_resume_c = 'resume'
        if status:
            pause_or_resume = "To'xtatish ⏸"
            pause_or_resume_c = 'pause'

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(pause_or_resume, callback_data=f'mail_users {pause_or_resume_c}'),
            types.InlineKeyboardButton("🗑 O'chirish", callback_data=f'mail_users delete')
        )
        markup.add(types.InlineKeyboardButton(text='🔙 Orqaga', callback_data='mail'))

        pause_or_resume = "To'xtatilgan"
        if pause_or_resume_c == 'pause':
            pause_or_resume = 'Yuborilmoqda'

        text = f"<b>Yuborildi:</b> <code>{sended_users_count}/{users_count}</code>\n<b>Qayerga yuborilmoqda:</b> <code>{mail_type}</code>\n<b>Status:</b> <code>{pause_or_resume}</code>"
        return await callback.message.edit_text(text, 'html', reply_markup=markup)
    
    await SetState.mail_users.set()
    text = 'Odamlarga yuboriladigan habarni yuboring...'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='🔙 Orqaga', callback_data='mail'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.callback_query_handler(lambda c: 'mail_groups' in c.data, state='*')
async def mail_groups(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split(' ')
    try:
        pause_or_resume = data[1]
        if pause_or_resume == 'pause':
            pause_or_resume = 0
        elif pause_or_resume == 'resume':
            pause_or_resume = 1
        elif pause_or_resume == 'delete':
            sql = "DELETE FROM `mailing`"
            cursor.execute(sql)
            await callback.answer("Habar yuborish bekor qilindi", show_alert=True)
            return await mail(callback, state)

        sql = "UPDATE `mailing` SET `status` = %s"
        cursor.execute(sql, [pause_or_resume])
    except IndexError:
        pass

    sql = "SELECT `last_user_id`, `status`, `mail_type` FROM `mailing`"
    cursor.execute(sql)

    if cursor.rowcount > 0:
        last_user_id, status, mail_type = cursor.fetchone()

        if mail_type == 'users':
            table = 'users'
            mail_type = 'odamlarga'
        else:
            table = 'groups'
            mail_type == 'guruhlarga'

        sql = f"SELECT COUNT(`id`) FROM `{table}`"
        cursor.execute(sql)
        users_count = cursor.fetchone()[0]

        sql = f"SELECT COUNT(`id`) FROM `{table}` WHERE `id` < %s"
        cursor.execute(sql, [last_user_id])
        sended_users_count = cursor.fetchone()[0]
        
        pause_or_resume = 'Davom etish ▶️'
        pause_or_resume_c = 'resume'
        if status:
            pause_or_resume = "To'xtatish ⏸"
            pause_or_resume_c = 'pause'

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(pause_or_resume, callback_data=f'mail_users {pause_or_resume_c}'),
            types.InlineKeyboardButton("🗑 O'chirish", callback_data=f'mail_groups delete')
        )
        markup.add(types.InlineKeyboardButton(text='🔙 Orqaga', callback_data='mail'))

        pause_or_resume = "To'xtatilgan"
        if pause_or_resume_c == 'pause':
            pause_or_resume = 'Yuborilmoqda'

        text = f"<b>Yuborildi:</b> <code>{sended_users_count}/{users_count}</code>\n<b>Qayerga yuborilmoqda:</b> <code>{mail_type}</code>\n<b>Status:</b> <code>{pause_or_resume}</code>"
        return await callback.message.edit_text(text, 'html', reply_markup=markup)
    
    await SetState.mail_groups.set()
    text = 'Guruhlarga yuboriladigan habarni yuboring...'
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='🔙 Orqaga', callback_data='mail'))
    await callback.message.edit_text(text, 'html', reply_markup=markup)


@dp.message_handler(state=SetState.mail_users, chat_type='private', content_types=['any'])
async def user_ban(message: types.Message):
    sql = "SELECT `status` FROM `mailing`"
    cursor.execute(sql)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='🔙 Orqaga', callback_data='mail'))

    if cursor.rowcount > 0:
        text = "<b>Hozirgi vaqtda habar yuborilmoqda. Habar hammaga yetkazilgandan so'ng urunib ko'ring</b>"
        return await message.answer(text, 'html', reply_markup=markup)

    reply_markup = ''
    if message.reply_markup:
        reply_markup = json.dumps(message.reply_markup.as_json(), ensure_ascii=False)

    sql = "INSERT INTO `mailing` VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, [message.message_id, message.from_user.id, reply_markup, 0, 'users', 1])

    text = '<b>Habar yuborish boshlandi!</b>'
    await message.answer(text, 'html', reply_markup=markup)


@dp.message_handler(state=SetState.mail_groups, chat_type='private', content_types=['any'])
async def user_ban(message: types.Message):
    sql = "SELECT `status` FROM `mailing`"
    cursor.execute(sql)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='🔙 Orqaga', callback_data='mail'))

    if cursor.rowcount > 0:
        text = "<b>Hozirgi vaqtda habar yuborilmoqda. Habar hammaga yetkazilgandan so'ng urunib ko'ring</b>"
        return await message.answer(text, 'html', reply_markup=markup)

    reply_markup = ''
    if message.reply_markup:
        reply_markup = json.dumps(message.reply_markup.as_json(), ensure_ascii=False)

    sql = "INSERT INTO `mailing` VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, [message.message_id, message.from_user.id, reply_markup, 0, 'groups', 1])

    text = '<b>Habar yuborish boshlandi!</b>'
    await message.answer(text, 'html', reply_markup=markup)


@dp.message_handler(state=SetState.ban_user, chat_type='private')
async def user_ban(message: types.Message):
    # if not message.text.isdigit():
    #     return await message.answer("<b>Id faqat sonlardan iborat bo'lishi kerak</b>", 'html')

    user_id = message.text
    sql = "SELECT `full_name` FROM `users` WHERE `user_id` = %s"
    cursor.execute(sql, [user_id])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='ban'))

    if cursor.rowcount == 0:
        return await message.answer('<b>User topilmadi!</b>', 'html', reply_markup=markup)
    
    full_name = cursor.fetchone()[0]

    sql = "DELETE FROM `users` WHERE `user_id` = %s"
    cursor.execute(sql, [user_id])

    sql = "INSERT INTO `users_blacklist` VALUES (%s, %s, %s)"
    cursor.execute(sql, [None, user_id, full_name])
    
    text_link = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
    text = f"<b>{text_link} muvaffaqiyatli banlandi</b>!"
    await message.answer(text, 'html', reply_markup=markup)

@dp.message_handler(state=SetState.unban_user, chat_type='private')
async def user_ban(message: types.Message):
    # try:
    #     user_id = int(message.text)
    # except ValueError:
    #     return await message.answer("<b>Id faqat sonlardan iborat bo'lishi kerak</b>", 'html')

    user_id = message.text
    sql = "SELECT `full_name` FROM `users_blacklist` WHERE `user_id` = %s"
    cursor.execute(sql, [user_id])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='unban'))

    if cursor.rowcount == 0:
        return await message.answer('<b>Guruh topilmadi!</b>', 'html', reply_markup=markup)
    
    full_name = cursor.fetchone()[0]

    sql = "DELETE FROM `users_blacklist` WHERE `user_id` = %s"
    cursor.execute(sql, [user_id])
    
    text_link = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
    text = f'<b>{text_link} muvaffaqiyatli unban qilindi</b>!'
    await message.answer(text, 'html', reply_markup=markup)
    
@dp.message_handler(state=SetState.ban_group, chat_type='private')
async def user_ban(message: types.Message):
    # if not message.text.isdigit():
    #     return await message.answer("<b>Id faqat sonlardan iborat bo'lishi kerak</b>", 'html')

    group_id = message.text
    sql = "SELECT `title` FROM `groups` WHERE `chat_id` = %s"
    cursor.execute(sql, [group_id])
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='ban'))

    if cursor.rowcount == 0:
        return await message.answer('<b>Guruh topilmadi!</b>', 'html', reply_markup=markup)
    
    title = cursor.fetchone()[0]

    sql = "DELETE FROM `groups` WHERE `chat_id` = %s"
    cursor.execute(sql, [group_id])

    sql = "INSERT INTO `groups_blacklist` VALUES (%s, %s, %s)"
    cursor.execute(sql, [None, group_id, title])
    
    text = f'<b>{title} muvaffaqiyatli banlandi</b>'
    
    await message.answer(text, 'html', reply_markup=markup)
    try:
        await bot.leave_chat(group_id)
    except Exception:
        pass
        
@dp.message_handler(state=SetState.unban_group, chat_type='private')
async def user_ban(message: types.Message):
    # try:
    #     group_id = int(message.text)
    # except ValueError:
    #     return await message.answer("<b>Id faqat sonlardan iborat bo'lishi kerak</b>", 'html')

    group_id = message.text
    sql = "SELECT `title` FROM `groups_blacklist` WHERE `group_id` = %s"
    cursor.execute(sql, [group_id])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Orqaga', callback_data='unban'))

    if cursor.rowcount == 0:
        return await message.answer('<b>Guruh topilmadi!</b>', 'html', reply_markup=markup)
    
    title = cursor.fetchone()[0]

    sql = "DELETE FROM `groups_blacklist` WHERE `group_id` = %s"
    cursor.execute(sql, [group_id])
    
    text = f'<b>{title} muvaffaqiyatli unban qilindi</b>!'
    await message.answer(text, 'html', reply_markup=markup)    
    


if __name__ == '__main__':
    allowed_updates = ['message', 'callback_query', 'chat_member', 'my_chat_member']
    executor.start_polling(dp, skip_updates=False, allowed_updates=allowed_updates)