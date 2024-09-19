import cv2
import requests
import json
import os
import time
from datetime import datetime

# CompreFace API uchun URL va kalit
compreface_api_url = "http://192.168.79.128:8000/api/v1/recognition/recognize"
api_key = "41a8617d-9e6a-4b68-b96a-dc936ab96617"

# Mahalliy fayl va server uchun API manzillari
# Yangi statistika fayli
local_data_file = 'statistika/data.json'  # O'ZGARTIRILDI
server_url = 'http://192.168.79.128:8083/save_data'

# JSON fayl va katalogni yaratish
if not os.path.exists(os.path.dirname(local_data_file)):
    os.makedirs(os.path.dirname(local_data_file))

if not os.path.exists(local_data_file):
    with open(local_data_file, 'w') as file:
        json.dump({}, file)

# Kamerani ochish
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Kamerani ochib bo'lmadi!")
    exit()

# Oyna nomi va to'liq ekran rejimi o'rnatish
cv2.namedWindow("Kamera testi", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Kamera testi", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Yuzlar uchun oxirgi tanilgan vaqtni saqlash
last_recognized = {}
blocked_until = {}  # Foydalanuvchilar uchun bloklangan vaqtni saqlash
recognition_interval = 20  # 20 soniya ichida ma'lumotlarni saqlamaydi
block_duration = 30  # 30 soniya davomida foydalanuvchi uchun qayta kirishni bloklash
expiry_duration = 12 * 3600  # 12 soat (sekundda) cheklov qo'shildi

similarity_threshold = 0.9  # O'xshashlik mezoni (threshold)

# Kirish va chiqish vaqtlarini qayd qilish funksiyasi
def remove_expired_entries(data, subject, current_time):
    if data[subject]:
        for entry in data[subject][:]:
            # Agar foydalanuvchi 12 soat ichida chiqmagan bo'lsa, kirish yozuvini o'chiramiz
            kirish_vaqt = datetime.fromisoformat(entry["kirish"])
            if entry["chiqish"] is None and (current_time - kirish_vaqt.timestamp()) > expiry_duration:
                print(f"{subject} uchun 12 soatdan oshgan kirish yozuvi o'chirildi")
                data[subject].remove(entry)

def process_recognition(data, subject, current_time):
    if subject not in data:
        data[subject] = []

    remove_expired_entries(data, subject, current_time)

    # Agar subject hali last_recognized'da mavjud bo'lmasa, uni qo'shamiz
    if subject not in last_recognized:
        last_recognized[subject] = current_time

    # Agar foydalanuvchi chiqib ketgan bo'lsa va bloklanmagan bo'lsa, kirish vaqtini yozmaslik
    if subject in blocked_until and current_time < blocked_until[subject]:
        print(f"Foydalanuvchi {subject} uchun kirish bloklangan, {blocked_until[subject] - current_time:.2f} soniya qoldi.")
        return
    
    # Oxirgi yozuvni tekshiramiz, agar chiqish qiymati hali `null` bo'lsa, yangi kirish yozuvi yaratmaymiz
    if data[subject] and data[subject][-1]["chiqish"] is None:
        # Chiqish vaqtini hisoblaymiz
        elapsed_time = current_time - last_recognized[subject]
        if elapsed_time > recognition_interval:
            # Chiqish vaqtini qo'shamiz, agar kirish va chiqish bir xil bo'lmasa
            if data[subject][-1]["kirish"] != datetime.now().isoformat():
                data[subject][-1]["chiqish"] = datetime.now().isoformat()

                # Kirish va chiqish vaqtlarini datetime formatida hisoblash
                kirish_vaqt = datetime.fromisoformat(data[subject][-1]["kirish"])
                chiqish_vaqt = datetime.fromisoformat(data[subject][-1]["chiqish"])
                honada_vaqt = (chiqish_vaqt - kirish_vaqt).total_seconds()

                # Agar foydalanuvchi 20 soniyadan ko'p vaqt honada bo'lgan bo'lsa, saqlash
                if honada_vaqt > 20:
                    data[subject][-1]["honada_vaqt"] = round(honada_vaqt / 60.0, 2)  # daqiqalarda
                else:
                    # Agar 20 soniyadan kam bo'lsa, bu yozuvni o'chirish
                    data[subject].pop(-1)

                # Foydalanuvchini qayd etilganlar ro'yxatidan olib tashlash
                last_recognized.pop(subject)
                
                # Foydalanuvchiga 30 soniya davomida yangi kirishni bloklash
                blocked_until[subject] = current_time + block_duration
        return

    # Agar kirish yozuvi yakunlangan bo'lsa, yangi kirish yozuvini qo'shamiz
    data[subject].append({
        "kirish": datetime.now().isoformat(),
        "chiqish": None,
        "honada_vaqt": None
    })
    
    last_recognized[subject] = current_time

# Asosiy sikl
while True:
    ret, frame = cap.read()
    if not ret:
        print("Kadrni o'qib bo'lmadi!")
        break
    
    # Kadrni API'ga yuborish uchun kodlash
    _, img_encoded = cv2.imencode('.jpg', frame)
    files = {
        'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')
    }
    headers = {
        "x-api-key": api_key
    }
    response = requests.post(compreface_api_url, files=files, headers=headers)
    result = response.json()
    print(result)

    # Yuz aniqlanganda ma'lumotlarni saqlash
    if "result" in result and len(result["result"]) > 0:
        for face in result['result']:
            box = face['box']
            top_left = (box['x_min'], box['y_min'])
            bottom_right = (box['x_max'], box['y_max'])
            cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 3)

            if face['subjects'] and 'subject' in face['subjects'][0]:
                similarity = face['subjects'][0]['similarity']
                subject = face['subjects'][0]['subject']
                current_time = time.time()

                if similarity > similarity_threshold:
                    label = "Talaba"  # Yuzni tanigan foydalanuvchiga "Talaba" deb yoziladi
                    with open(local_data_file, 'r+') as file:
                        data = json.load(file)

                        # Foydalanuvchini qayta ishlash
                        process_recognition(data, subject, current_time)

                        file.seek(0)
                        json.dump(data, file, indent=4)
                        file.truncate()

                    # Ma'lumotlarni serverga yuborish
                    # Bu joyda faqat oxirgi uchta qiymatni yuborish: kirish, chiqish, va honada_vaqt
                    if data[subject] and data[subject][-1]["chiqish"] is not None:
                        latest_record = data[subject][-1]
                        filtered_data = {
                            subject: [{
                                "kirish": latest_record["kirish"],
                                "chiqish": latest_record["chiqish"],
                                "honada_vaqt": latest_record["honada_vaqt"]
                            }]
                        }
                        response = requests.post(server_url, json=filtered_data)
                        if response.status_code == 200:
                            print("Ma'lumot serverga muvaffaqiyatli yuborildi!")
                        else:
                            print("Ma'lumot yuborishda xatolik: ", response.text)

                else:
                    label = "Begona"  # Agar yuzni tanimasa "Begona" deb yoziladi

            else:
                label = "Begona"

            # Ekranga "Talaba" yoki "Begona" yozamiz
            cv2.putText(frame, label, (top_left[0], top_left[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

    # Kamera oynasini ko'rsatish
    cv2.imshow('Kamera testi', frame)

    # "q" tugmasi bosilganda chiqish
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
