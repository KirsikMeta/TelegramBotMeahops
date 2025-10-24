import json
from datetime import datetime

LOG_FILE = "logs.json"

def load_logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_logs(logs):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def log_user_session(user_id, score, total):
    logs = load_logs()
    user_key = f"user_{user_id}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    passed = score >= total // 2

    test_number = len(logs.get(user_key, [])) + 1

    if user_key not in logs:
        logs[user_key] = []

    logs[user_key].append({
        "timestamp": timestamp,
        "test_number": test_number,
        "score": score,
        "total": total,
        "passed": passed
    })

    save_logs(logs)

def get_user_stats(user_id):
    logs = load_logs()
    user_key = f"user_{user_id}"
    user_logs = logs.get(user_key, [])
    if not user_logs:
        return "У вас пока нет пройденных тестов."
    
    total_tests = len(user_logs)
    passed_tests = sum(1 for log in user_logs if log["passed"])
    avg_score = sum(log["score"] for log in user_logs) / total_tests if total_tests > 0 else 0

    stats_text = f"""
 Ваша статистика:

Пройдено тестов: {total_tests}
 Пройдено успешно: {passed_tests}
 Не пройдено: {total_tests - passed_tests}
Средний балл: {avg_score:.2f}/50
    """
    
    stats_text += "\n📝 История тестов:\n"
    for log in user_logs:
        status = "+" if log["passed"] else "-"
        stats_text += f"{log['test_number']}. {log['timestamp']} — {log['score']}/{log['total']} {status}\n"

    return stats_text

def get_user_past_results(user_id):
    logs = load_logs()
    user_key = f"user_{user_id}"
    user_logs = logs.get(user_key, [])
    if not user_logs:
        return "У вас пока нет пройденных тестов."

    result_text = "Ваши прошлые попытки:\n\n"
    for log in user_logs:
        status = "Пройден" if log["passed"] else "Не пройден"
        result_text += f" {log['timestamp']}\n Результат: {log['score']}/{log['total']} — {status}\n\n"
    return result_text
