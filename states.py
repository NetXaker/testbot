from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()


class SetState(StatesGroup):
    ban_user = State()
    ban_group = State()
    
    unban_user = State()
    unban_group = State()

    mail_users = State()
    mail_groups = State()