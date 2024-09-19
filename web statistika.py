from flask import Flask, render_template, request
import json
import os
import time

app = Flask(__name__, template_folder='web')

# JSON fayllarni oxirgi o'zgarish vaqtini saqlash
last_modified_times = {}

def load_json_data(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def check_and_reload_data():
    global kutubhona_data, itpark_data, kutubhona_reg_data, itpark_reg_data
    file_paths = {
        'kutubhona_data': 'data/data kundalik tekshiruv kutubhona/data.json',
        'itpark_data': 'data/data kundalik tekshiruv it park/data.json',
        'kutubhona_reg_data': 'data/registratsiya/kutubhona.json',
        'itpark_reg_data': 'data/registratsiya/dada.json'
    }

    for key, path in file_paths.items():
        if os.path.exists(path):
            last_modified_time = os.path.getmtime(path)
            if key not in last_modified_times or last_modified_times[key] < last_modified_time:
                last_modified_times[key] = last_modified_time
                if key == 'kutubhona_data':
                    kutubhona_data = load_json_data(path)
                elif key == 'itpark_data':
                    itpark_data = load_json_data(path)
                elif key == 'kutubhona_reg_data':
                    kutubhona_reg_data = load_json_data(path)
                elif key == 'itpark_reg_data':
                    itpark_reg_data = load_json_data(path)
        else:
            # Fayl yo'q bo'lsa, bo'sh obyektni yuklaymiz
            if key == 'kutubhona_data':
                kutubhona_data = {}
            elif key == 'itpark_data':
                itpark_data = {}
            elif key == 'kutubhona_reg_data':
                kutubhona_reg_data = {}
            elif key == 'itpark_reg_data':
                itpark_reg_data = {}

def merge_data(main_data, reg_data):
    merged_data = {}
    for user_id, records in main_data.items():
        if user_id in reg_data:
            for record in records:
                record.update(reg_data[user_id])
        merged_data[user_id] = records
    return merged_data

@app.route('/')
def index():
    check_and_reload_data()
    return render_template('index.html')

@app.route('/show_data', methods=['POST'])
def show_data():
    check_and_reload_data()
    selected_data = request.form.get('data_type')
    if selected_data == 'kutubhona':
        data = merge_data(kutubhona_data, kutubhona_reg_data)
    elif selected_data == 'itpark':
        data = merge_data(itpark_data, itpark_reg_data)
    else:
        data = {}

    return render_template('table.html', data=data)

if __name__ == '__main__':
    kutubhona_data = load_json_data('data/data kundalik tekshiruv kutubhona/data.json')
    itpark_data = load_json_data('data/data kundalik tekshiruv it park/data.json')
    kutubhona_reg_data = load_json_data('data/registratsiya/kutubhona.json')
    itpark_reg_data = load_json_data('data/registratsiya/dada.json')
    
    app.run(debug=True)
