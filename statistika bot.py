import telebot
import json
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

bot = telebot.TeleBot("7481190708:AAE3Ek-gxbC9wq3Mr_K-Iggr0q4DeC26ot0")

def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            return {}
    return data

def calculate_time(data, user_id):
    total_time = 0
    for entry in data.get(user_id, []):
        kirish_vaqt = datetime.strptime(entry['kirish'], "%Y-%m-%dT%H:%M:%S.%f")
        chiqish_vaqt = entry.get('chiqish')
        if chiqish_vaqt:
            chiqish_vaqt = datetime.strptime(chiqish_vaqt, "%Y-%m-%dT%H:%M:%S.%f")
            total_time += (chiqish_vaqt - kirish_vaqt).total_seconds()
    return total_time / 60  # Total time in minutes

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=1)
    btn1 = KeyboardButton("📚 Kutubhona Statistika")
    btn2 = KeyboardButton("🏢 IT Park Statistika")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📚 Kutubhona Statistika")
def kutubhona_statistika(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=1)
    btn1 = KeyboardButton("📊 Kutubhona Fakultetlar Statistika")
    btn2 = KeyboardButton("📈 Kutubhona Kurslar Statistika")
    btn3 = KeyboardButton("🔙 Orqaga Qaytish")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "📚 Kutubhona Statistika:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 Kutubhona Fakultetlar Statistika")
def kutubhona_fakultet_statistika(message):
    data = load_data('data/registratsiya/kutubhona.json')
    time_data = load_data('data/data kundalik tekshiruv kutubhona/data.json')
    faculty_count = {}
    faculty_time = {}

    for record in data.values():
        faculty = record.get("faculty", "Noma'lum")
        user_id = record.get("id", "")
        if faculty in faculty_count:
            faculty_count[faculty] += 1
            faculty_time[faculty] += calculate_time(time_data, user_id)
        else:
            faculty_count[faculty] = 1
            faculty_time[faculty] = calculate_time(time_data, user_id)

    response = "📊 *Kutubhona Fakultetlar Bo'yicha Statistika:*\n\n"
    for faculty, count in faculty_count.items():
        total_time = faculty_time.get(faculty, 0)
        response += f"🏫 *{faculty}*\n- {count} ta ro'yxatdan o'tgan\n- Umumiy vaqt: {total_time:.2f} daqiqa\n\n"

    if not faculty_count:
        response += "Hech qanday ma'lumot topilmadi.\n"

    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📈 Kutubhona Kurslar Statistika")
def kutubhona_kurs_statistika(message):
    data = load_data('data/registratsiya/kutubhona.json')
    time_data = load_data('data/data kundalik tekshiruv kutubhona/data.json')
    course_count = {}
    course_time = {}

    for record in data.values():
        course = record.get("course", "Noma'lum")
        user_id = record.get("id", "")
        if course in course_count:
            course_count[course] += 1
            course_time[course] += calculate_time(time_data, user_id)
        else:
            course_count[course] = 1
            course_time[course] = calculate_time(time_data, user_id)

    response = "📈 *Kutubhona Kurslar Bo'yicha Statistika:*\n\n"
    for course, count in course_count.items():
        total_time = course_time.get(course, 0)
        response += f"🎓 *{course}*\n- {count} ta ro'yxatdan o'tgan\n- Umumiy vaqt: {total_time:.2f} daqiqa\n\n"

    if not course_count:
        response += "Hech qanday ma'lumot topilmadi.\n"

    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🏢 IT Park Statistika")
def it_park_statistika(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=1)
    btn1 = KeyboardButton("📊 IT Park Fakultetlar Statistika")
    btn2 = KeyboardButton("📈 IT Park Kurslar Statistika")
    btn3 = KeyboardButton("🔙 Orqaga Qaytish")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "🏢 IT Park Statistika:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 IT Park Fakultetlar Statistika")
def it_park_fakultet_statistika(message):
    data = load_data('data/registratsiya/dada.json')
    time_data = load_data('data/data kundalik tekshiruv it park/data.json')
    faculty_count = {}
    faculty_time = {}

    for record in data.values():
        faculty = record.get("faculty", "Noma'lum")
        user_id = record.get("id", "")
        if faculty in faculty_count:
            faculty_count[faculty] += 1
            faculty_time[faculty] += calculate_time(time_data, user_id)
        else:
            faculty_count[faculty] = 1
            faculty_time[faculty] = calculate_time(time_data, user_id)

    response = "📊 *IT Park Fakultetlar Bo'yicha Statistika:*\n\n"
    for faculty, count in faculty_count.items():
        total_time = faculty_time.get(faculty, 0)
        response += f"🏫 *{faculty}*\n- {count} ta ro'yxatdan o'tgan\n- Umumiy vaqt: {total_time:.2f} daqiqa\n\n"

    if not faculty_count:
        response += "Hech qanday ma'lumot topilmadi.\n"

    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📈 IT Park Kurslar Statistika")
def it_park_kurs_statistika(message):
    data = load_data('data/registratsiya/dada.json')
    time_data = load_data('data/data kundalik tekshiruv it park/data.json')
    course_count = {}
    course_time = {}

    for record in data.values():
        course = record.get("course", "Noma'lum")
        user_id = record.get("id", "")
        if course in course_count:
            course_count[course] += 1
            course_time[course] += calculate_time(time_data, user_id)
        else:
            course_count[course] = 1
            course_time[course] = calculate_time(time_data, user_id)

    response = "📈 *IT Park Kurslar Bo'yicha Statistika:*\n\n"
    for course, count in course_count.items():
        total_time = course_time.get(course, 0)
        response += f"🎓 *{course}*\n- {count} ta ro'yxatdan o'tgan\n- Umumiy vaqt: {total_time:.2f} daqiqa\n\n"

    if not course_count:
        response += "Hech qanday ma'lumot topilmadi.\n"

    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔙 Orqaga Qaytish")
def orqaga_qaytish(message):
    send_welcome(message)

bot.polling()