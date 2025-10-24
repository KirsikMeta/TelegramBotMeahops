from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json

#Метод для загрузки вопросов из файла questions
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            #open('questions.json', 'r', encoding='utf-8') as f:data = json.load(f)
        if not isinstance(data, dict) or "questions" not in data:
            raise ValueError("JSON должен содержать ключ 'questions'")
        for i, q in enumerate(data["questions"]):
            if not isinstance(q, dict):
                raise ValueError(f"Вопрос {i+1} не является объектом")
            if "options" not in q:
                raise ValueError(f"Вопрос {i+1} не имеет поля 'options'")
        return data["questions"]
    except Exception as e:
        print(f" Ошибка загрузки вопросов: {e}")
        exit(1)

questions = load_questions()
current_q_index = {}
user_results = {}

#Обычная загрузка бота при вводе /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q_index[user_id] = 0
    user_results[user_id] = {"answers": [], "score": 0}
    await ask_question_from_message(update.effective_message, context, user_id)

async def ask_question_from_message(message, context, user_id):
    q = questions[current_q_index[user_id]]

    keyboard = [[InlineKeyboardButton(opt, callback_data=str(i))] for i, opt in enumerate(q["options"])]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(q["question"], reply_markup=reply_markup)

#Это асинх код.который позволяет загружать вопросы без ошибок
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    option_index = int(query.data)
    selected_option = questions[current_q_index[user_id]]["options"][option_index]
    q = questions[current_q_index[user_id]]

    user_results[user_id]["answers"].append({
        "question": q["question"],
        "user_answer": selected_option,
        "correct": selected_option == q["correct_answer"]
    })

    if selected_option == q["correct_answer"]:
        user_results[user_id]["score"] += 1
        await query.edit_message_text(text=f"Правильно! {q['question']}\nТвой ответ: {selected_option}")
    else:
        await query.edit_message_text(text=f"Неправильно!\nПравильный ответ: {q['correct_answer']}")

    current_q_index[user_id] += 1

    if current_q_index[user_id] < len(questions):
        await ask_question_from_message(query.message, context, user_id)
    else:
        await show_results(query.message, user_id)
#Обычная кнопка чтобы показать результаты теста
async def show_results(message, user_id):
    results = user_results[user_id]
    total = len(questions)
    score = results["score"]
    passed = score >= total // 2

    result_text = f"""
🏁 Тест завершён!

✅ Правильных ответов: {score}/{total}
{'🎉 Тест пройден!' if passed else 'Тест не пройден.'}
    """

    keyboard = [
        [InlineKeyboardButton("Скачать результаты", callback_data="download_results")],
        [InlineKeyboardButton("Пройти снова", callback_data="restart_test")],
        [InlineKeyboardButton("Проверить прошлые попытки", callback_data="show_past_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(result_text, reply_markup=reply_markup)

    # Сохраняем в лог
    from logs import log_user_session
    log_user_session(user_id, score, total)

async def handle_end_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "download_results":
        result_text = format_results(user_id)
        await query.message.reply_text("Ваши результаты:\n\n" + result_text)
    elif query.data == "restart_test":
        current_q_index[user_id] = 0
        user_results[user_id] = {"answers": [], "score": 0}
        await ask_question_from_message(query.message, context, user_id)
    elif query.data == "show_past_results":
        from logs import get_user_past_results
        past_results = get_user_past_results(user_id)
        await query.message.reply_text(past_results)

#Формат ответа результатов ( когда выбрал вариант ответа)
def format_results(user_id):
    results = user_results[user_id]
    lines = []
    for i, ans in enumerate(results["answers"]):
        lines.append(f"{i+1}. {ans['question']}\n   Ваш ответ: {ans['user_answer']}\n   Правильно: {ans['correct']}\n")
    return "\n".join(lines)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    from logs import get_user_stats
    stats_text = get_user_stats(user_id)
    await update.message.reply_text(stats_text)

def main():
    app = Application.builder().token("Секретик").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^(?!download_results|restart_test|show_past_results)"))
    app.add_handler(CallbackQueryHandler(handle_end_buttons, pattern=r"^(download_results|restart_test|show_past_results)$"))
    app.run_polling()

if __name__ == '__main__':
    main()
