import asyncio

from aiogram.dispatcher import FSMContext
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import dp, bot
from aiogram.dispatcher.filters import Text
from key.buttons import main_menu
import handlers.quiz as quiz_test


class FSMChatGPT(StatesGroup):
    poll = State()
    question = 0
    ls = 0
    result = 0


async def cm_start(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Привет! Проверим твой уровень по английскому.')
    async with state.proxy() as data:
        data['ls'] = 0
        data['result'] = 0
        data['incorrect'] = {}

    await show_poll(message, state)


async def show_poll(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        ls = data['ls']

    if ls < len(quiz_test.quiz_test):
        question = quiz_test.quiz_test[ls]['question']
        options = quiz_test.quiz_test[ls]['options']

        poll_options = []
        for i, option in enumerate(options):
            button = types.InlineKeyboardButton(text=option, callback_data=f'answer_{i}')
            poll_options.append([button])

        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=poll_options)

        await bot.send_message(message.from_user.id, question, reply_markup=reply_markup)

        async with state.proxy() as data:
            data['ls'] += 1

        await FSMChatGPT.poll.set()

    else:
        async with state.proxy() as data:
            result = data['result']
            text = ''
            for i in data['incorrect']:
                for k, v in data['incorrect'][i].items():
                    if k == 'question':
                        text += f'{v}\n'
                    else:
                        text += f'{k}: {v}\n'
                text += '\n\n'
            level = (result/55)*100
            if 0 <= level < 37:
                res = 'Beginner'
            elif 37 <= level < 55:
                res = 'Elementary'
            elif 55 <= level < 73:
                res = 'Pre Intermediate'
            elif 73 <= level < 100:
                res = 'Intermediate'

        await bot.send_message(message.from_user.id, f"Опрос завершен. \n{result} правильных из 55\nВаш уровень {res.upper()}")
        await bot.send_message(message.from_user.id, f"\n\nОтчет по неправильным:\n")
        for i in text.split('\n\n'):
            if i.strip():
                await bot.send_message(message.from_user.id, f"{i}")
        await state.finish()


async def process_poll_answer(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        ls = data['ls']-1
        correct_answer = quiz_test.quiz_test[ls]['correct_answer']
        if str(correct_answer) == callback_query.data.replace("answer_", ""):
            data['result'] += 1
        else:
            data['incorrect'][ls] = {}
            data['incorrect'][ls]['question'] = quiz_test.quiz_test[ls]["question"]
            data['incorrect'][ls]['correct answer'] = quiz_test.quiz_test[ls]["options"][int(correct_answer)]
            data['incorrect'][ls]['your answer'] = quiz_test.quiz_test[ls]["options"][int(callback_query.data.replace("answer_", ""))]
    await show_poll(callback_query, state)


def register_quiz(dp: Dispatcher):
    dp.register_message_handler(cm_start, commands=['start'])
    dp.register_callback_query_handler(process_poll_answer, state=FSMChatGPT.poll)