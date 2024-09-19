import telebot
import json
import os
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import face_recognition
from PIL import Image
import hashlib
import io

# Bot tokeningizni kiriting
TOKEN = '7430723694:AAEAmuaj-Zf_2SQDJt_Gp0uT6PfsMRI7dks'
bot = telebot.TeleBot(TOKEN)

# API kalitlari va URL manzillari
it_park_api_key = "f9dae870-7487-41ce-8a13-3e994f2d8f65"
kutubhona_api_key = "41a8617d-9e6a-4b68-b96a-dc936ab96617"

# API manzili
url_base = "http://192.168.79.128:8000/api/v1/recognition/"
subject_url_base = url_base + "subjects"
face_url_base = url_base + "faces"

# Foydalanuvchi ma'lumotlarini saqlash uchun vaqtinchalik lug'at
user_data = {}

# Ma'lumotlarni saqlash uchun papkani yaratish
data_directory = "data/registratsiya"
os.makedirs(data_directory, exist_ok=True)

# Fayldan mavjud foydalanuvchilarni yuklash
def load_registered_users(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

registered_it_park = load_registered_users(os.path.join(data_directory, 'dada.json'))
registered_library = load_registered_users(os.path.join(data_directory, 'kutubhona.json'))

# Start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    register_button = KeyboardButton("📝 Ro'yhatdan o'tish")
    markup.add(register_button)
    
    bot.send_message(message.chat.id, "👋 Xush kelibsiz! Iltimos, ro'yhatdan o'tish uchun quyidagi tugmani bosing:", reply_markup=markup)

# Ro'yhatdan o'tish tugmasi uchun handler
@bot.message_handler(func=lambda message: message.text == "📝 Ro'yhatdan o'tish")
def register(message):
    markup = InlineKeyboardMarkup()
    library_button = InlineKeyboardButton("📚 Kutubxona uchun Ro'yhatdan o'tish", callback_data='register_library')
    it_park_button = InlineKeyboardButton("🏢 IT PARK uchun Ro'yhatdan o'tish", callback_data='register_it_park')
    markup.add(library_button)
    markup.add(it_park_button)
    
    bot.send_message(message.chat.id, "📋 Ro'yhatdan o'tish turini tanlang:", reply_markup=markup)

# Callback funksiyasi
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.message.chat.id)
    
    if call.data == 'register_library':
        if user_id in registered_library:
            bot.send_message(call.message.chat.id, "✅ Siz allaqachon Kutubxona uchun ro'yhatdan o'tgansiz.")
        else:
            bot.send_message(call.message.chat.id, "📝 Iltimos, ismingizni va familiyangizni kiriting:")
            bot.register_next_step_handler(call.message, get_name, os.path.join(data_directory, 'kutubhona.json'), registered_library, kutubhona_api_key, is_kutubhona=True)
    
    elif call.data == 'register_it_park':
        if user_id in registered_it_park:
            bot.send_message(call.message.chat.id, "✅ Siz allaqachon IT PARK uchun ro'yhatdan o'tgansiz.")
        else:
            bot.send_message(call.message.chat.id, "📝 Iltimos, ismingizni va familiyangizni kiriting:")
            bot.register_next_step_handler(call.message, get_name, os.path.join(data_directory, 'dada.json'), registered_it_park, it_park_api_key, is_kutubhona=False)

# Ism va familiyani so'rash
def get_name(message, file_name, registered_users, api_key, is_kutubhona):
    user_id = str(message.chat.id)
    user_data[user_id] = {}
    user_data[user_id]['id'] = user_id  # Telegram ID'ni sub'ekt nomi sifatida ishlatamiz
    user_data[user_id]['name'] = message.text
    
    # Fakultetlar ro'yxati uchun tugmachalar yaratish
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("1-fakultet"))
    markup.add(KeyboardButton("2-fakultet"))
    markup.add(KeyboardButton("3-fakultet"))
    markup.add(KeyboardButton("4-fakultet"))
    markup.add(KeyboardButton("5-fakultet"))
    
    bot.send_message(message.chat.id, "🏫 Universitetda o'qiyotgan fakultetingizni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(message, get_faculty, file_name, registered_users, api_key, is_kutubhona)

# Fakultetni tanlash
def get_faculty(message, file_name, registered_users, api_key, is_kutubhona):
    user_id = str(message.chat.id)
    user_data[user_id]['faculty'] = message.text
    
    # Kurslar ro'yxati uchun tugmachalar yaratish
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("1-kurs"))
    markup.add(KeyboardButton("2-kurs"))
    markup.add(KeyboardButton("3-kurs"))
    markup.add(KeyboardButton("4-kurs"))
    
    bot.send_message(message.chat.id, "📚 Universitetda nechinchi kursda o'qiyapsiz? Tanlang:", reply_markup=markup)
    bot.register_next_step_handler(message, get_course, file_name, registered_users, api_key, is_kutubhona)

# Kursni tanlash
def get_course(message, file_name, registered_users, api_key, is_kutubhona):
    user_id = str(message.chat.id)
    user_data[user_id]['course'] = message.text
    
    # Tugmalarni olib tashlash uchun bo'sh markup yaratish
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    bot.send_message(message.chat.id, "📋 Guruh raqamingizni kiriting:", reply_markup=markup)
    bot.register_next_step_handler(message, get_group, file_name, registered_users, api_key, is_kutubhona)

# Guruh raqamini so'rash
def get_group(message, file_name, registered_users, api_key, is_kutubhona):
    user_id = str(message.chat.id)
    user_data[user_id]['group'] = message.text
    
    bot.send_message(message.chat.id, "📸 Iltimos, o'z rasmingizni yuklang. Namuna sifatida quyidagi rasmni ko'rishingiz mumkin:")
    
    # Namuna rasmini yuborish
    sample_image_path = os.path.join('namuna', 'rasim.jpg')
    with open(sample_image_path, 'rb') as sample_image:
        bot.send_photo(message.chat.id, sample_image, caption="⬆️ Shu ko'rinishdagi rasmni yuklang.")
    
    bot.register_next_step_handler(message, get_photo, file_name, registered_users, api_key, is_kutubhona)

# Foydalanuvchining rasmini qabul qilish va saqlash
def get_photo(message, file_name, registered_users, api_key, is_kutubhona):
    user_id = str(message.chat.id)
    
    if message.content_type == 'photo':
        # Foydalanuvchining rasmini saqlash
        photo_file_id = message.photo[-1].file_id
        user_data[user_id]['photo'] = photo_file_id

        # Agar Kutubhona uchun bo'lsa, photos_kutubhona papkasiga saqlanadi
        if is_kutubhona:
            user_folder = os.path.join('data', 'photos_kutubhona', user_id)
        else:
            user_folder = os.path.join('data', 'photos', user_id)

        os.makedirs(user_folder, exist_ok=True)
        
        file_info = bot.get_file(photo_file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        photo_path = os.path.join(user_folder, 'user_photo.jpg')
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        bot.send_message(message.chat.id, "📸 Iltimos, pasport rasmingizni yuklang. Namuna sifatida quyidagi rasmni ko'rishingiz mumkin:")

        # Pasport namuna rasmini yuborish
        sample_passport_image_path = os.path.join('pasportnamuna', 'pasport_namuna.jpg')
        with open(sample_passport_image_path, 'rb') as sample_image:
            bot.send_photo(message.chat.id, sample_image, caption="⬆️ Shu ko'rinishdagi pasport rasmini yuklang.")
        
        bot.register_next_step_handler(message, get_passport_photo, file_name, registered_users, photo_path, is_kutubhona)
    else:
        bot.send_message(message.chat.id, "⚠️ Iltimos, rasm formatida yuklang.")

# Pasport rasmini qabul qilish va saqlash va taqqoslash
def get_passport_photo(message, file_name, registered_users, photo_path, is_kutubhona):
    user_id = str(message.chat.id)

    if message.content_type == 'photo':
        # Foydalanuvchining pasport rasmini saqlash
        passport_photo_file_id = message.photo[-1].file_id
        user_data[user_id]['passport_photo'] = passport_photo_file_id

        # Agar Kutubhona uchun bo'lsa, passports_kutubhona papkasiga saqlanadi
        if is_kutubhona:
            passport_folder = os.path.join('data', 'passports_kutubhona', user_id)
        else:
            passport_folder = os.path.join('data', 'passports', user_id)

        os.makedirs(passport_folder, exist_ok=True)

        file_info = bot.get_file(passport_photo_file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        passport_path = os.path.join(passport_folder, 'passport_photo.jpg')
        with open(passport_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Rasmlarni taqqoslash
        compare_user_and_passport(message, photo_path, passport_path, file_name, registered_users, is_kutubhona)

    else:
        bot.send_message(message.chat.id, "⚠️ Iltimos, pasport rasm formatida yuklang.")

# Yuzlarni taqqoslash funksiyasi
def compare_user_and_passport(message, citizen_image_path, passport_image_path, file_name, registered_users, is_kutubhona):
    user_id = str(message.chat.id)
    
    citizen_image = load_image(citizen_image_path)
    passport_image = load_image(passport_image_path)

    if citizen_image is None or passport_image is None:
        bot.send_message(message.chat.id, "❌ Rasmlar yuklanishda xatolik.")
        start(message)  # Dastur boshiga qaytish
        return

    # Rasmlar hashini taqqoslash
    if get_image_hash(citizen_image) == get_image_hash(passport_image):
        bot.send_message(message.chat.id, "❌ Bir xil rasmlar yuklandi. Iltimos, turli rasmlar yuklang.")
        start(message)  # Dastur boshiga qaytish
        return

    citizen_encoding = get_face_encoding(citizen_image)
    passport_encoding = get_face_encoding(passport_image)

    if citizen_encoding is None or passport_encoding is None:
        bot.send_message(message.chat.id, "❌ Yuz topilmadi. Iltimos, boshqa rasm yuklang.")
        start(message)  # Dastur boshiga qaytish
        return

    distance = compare_faces(citizen_encoding, passport_encoding)
    similarity_percentage = (1 - distance) * 100

    bot.send_message(message.chat.id, f"Yuzlar o'xshashlik darajasi: {similarity_percentage:.2f}%")

    if similarity_percentage > 35:
        bot.send_message(message.chat.id, "✅ Rasmlar mos keladi. Pasport egasi bu fuqaro bilan bir xil odam.")
        
        # Ma'lumotlarni JSON faylga saqlash faqat moslik muvaffaqiyatli bo'lganda
        registered_users[user_id] = user_data[user_id]  # Foydalanuvchi ID to'g'ri kiritilganligiga ishonch hosil qilish
        with open(file_name, 'w') as file:
            json.dump(registered_users, file, ensure_ascii=False, indent=4)
        
        # API ga rasmlarni yuborish
        send_to_api(user_id, citizen_image_path, it_park_api_key if not is_kutubhona else kutubhona_api_key)

        bot.send_message(message.chat.id, "✅ Ro'yxatdan o'tdingiz.")
        start(message)  # Dastur boshiga qaytish
    else:
        bot.send_message(message.chat.id, "❌ Rasmlar mos kelmaydi. Pasport egasi bu fuqaro bilan bir xil odam emas.")
        start(message)  # Dastur boshiga qaytish

# API ga ma'lumotlarni yuborish
def send_to_api(user_id, photo_path, api_key):
    subject_name = user_id  # Telegram ID'ni sub'ekt nomi sifatida foydalanamiz
    
    # Sub'ektni yaratish yoki mavjudligini tekshirish
    subject_response = requests.post(subject_url_base, headers={"x-api-key": api_key}, json={"subject": subject_name})
    if subject_response.status_code == 201 or subject_response.status_code == 400:
        print("Sub'ekt yaratildi yoki mavjud. Status:", subject_response.status_code)
    
    # Foydalanuvchining rasmni yuborish
    with open(photo_path, "rb") as image_file:
        image_data = image_file.read()

    files = {
        'file': (photo_path, image_data, 'image/jpeg'),
    }

    data = {
        'subject': subject_name,
    }

    response = requests.post(face_url_base, headers={"x-api-key": api_key}, files=files, data=data)

    if response.status_code == 201:
        print("Rasm muvaffaqiyatli qo'shildi.")
        print(response.json())
    else:
        print(f"Rasm qo'shishda xatolik: {response.status_code}")
        print(response.text)

# Rasmlar uchun hash yaratish funksiyasi
def get_image_hash(image):
    buffered = io.BytesIO()
    pil_image = Image.fromarray(image)
    pil_image.save(buffered, format="JPEG")
    image_bytes = buffered.getvalue()
    return hashlib.md5(image_bytes).hexdigest()

# Rasmni yuklash funksiyasi
def load_image(image_path):
    try:
        image_path = image_path.strip('"').strip("'")
        image = face_recognition.load_image_file(image_path)
        return image
    except Exception as e:
        print(f"Rasmni yuklashda xatolik: {e}")
        return None

# Yuzni aniqlash funksiyasi
def get_face_encoding(image):
    try:
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            return face_encodings[0]
        else:
            print("Rasmda yuz topilmadi.")
            return None
    except Exception as e:
        print(f"Yuzlarni aniqlashda xatolik: {e}")
        return None

# Yuzlarni taqqoslash funksiyasi
def compare_faces(image1_encoding, image2_encoding):
    face_distances = face_recognition.face_distance([image1_encoding], image2_encoding)
    return face_distances[0]

# Botni ishga tushirish
bot.polling()
