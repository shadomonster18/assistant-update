import subprocess
import sys
print(sys.executable)
#subprocess.run("pip uninstall psutil")
#subprocess.run("pip install psutil")
#subprocess.run("pip uninstall opencv-python")
#subprocess.run("pip install opencv-python")

import os
import sys
import time
import shlex
import threading
import subprocess
import sqlite3
from time import sleep
from concurrent.futures import thread
import json
import psutil
import shutil
import torch
import cv2
import pygame
import pyttsx3
import requests
import ollama
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QMovie
from selenium import webdriver
from selenium.webdriver.common.by import By
from ddgs import DDGS
import requests
import speech_recognition as sr
import wikipedia

try:
    import pywhatkit as kit
except:
    pass

import matplotlib

import difflib
matplotlib.use('Agg')
stop = False
monitor = False
limit = 80
delay = 5
BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
API_KEY = "OPEN_WEATHERMAP_KEY"
messages = [{"role": "system", "content": "You are a helpful voice assistant named sirial. Keep your answers short and clear."}]

conn = sqlite3.connect("graph_data.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS percentages (id INTEGER PRIMARY KEY AUTOINCREMENT, value REAL NOT NULL)''')
cursor.execute('SELECT value FROM percentages')
percentages = [row[0] for row in cursor.fetchall()]
conn.commit()
conn.close()

search_folder = ""
move_folder = ""
file_type = ""

engine = pyttsx3.init()

'''
_torch_load = torch.load
def torch_load_patch(*args, **kwargs):
    kwargs["weights_only"] = False
    return _torch_load(*args, **kwargs)
torch.load = torch_load_patch

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.conf = 0.4
'''
recognizer = sr.Recognizer()

def add_percentage(value):
    conn = sqlite3.connect('graph_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO percentages (value) VALUES (?)', (value,))
    conn.commit()
    conn.close()
    print(f'Added percentage value: {value}')

def cpu_monitor(speak):
    global monitor, limit, delay
    while True:
        percent = psutil.cpu_percent()
        if monitor:
            add_percentage(percent)
            if percent > limit:
                txt = f"Warning: cpu usage is exceeding {limit}% ({percent}%)"
                print(txt)
                say(txt, speak)
        sleep(delay)

def get_news(query, speak):
    try:
        url = "https://www.edition.cnn.com/search?q="
        search = query.lower().replace("cnn", "")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = webdriver.Chrome(options=options)
        driver.get(url + search)
        sleep(7)
        try:
            cookies = driver.find_element(By.XPATH, "//*[contains(text(), 'Accept All')]")
            cookies.click()
        except: pass
        sleep(3)
        driver.find_element(By.XPATH, "//*[contains(text(), 'Stories')]").click()
        sleep(2)
        try:
            driver.find_element(By.CLASS_NAME, "container__headline-text").click()
        except: pass
        article_text = driver.find_element(By.CSS_SELECTOR, 'div.article__content').text
        driver.quit()
        print(article_text)
        return article_text
    except Exception as e:
        print("Error:", e)

def summarize(text):
    response = ollama.chat(model="codellama", messages=[{"role": "system", "content": "summarize the contents of this article in a few lines."},{"role": "user","content": text}])

    return response['message']['content']

def get_weather(speak, words):
    response = requests.get(BASE_URL + "appid=" + API_KEY + "&q=" + words[1:]).json()
    try:
        temp = int()
        temp = int(response["main"]["temp"]-273)
        feels_like = int(response["main"]["feels_like"]-273)
        humidity = response["main"]["humidity"]
        description = response["weather"][0]["description"]
    except Exception as e:
        say("Error while retrieving weather data", speak)
        print(e)
    '''
    try:
                    weather = get_weather(" ".join(words[1:]))
                    temp = int(weather["main"]["temp"]-273)
                    feels_like = int(weather["main"]["feels_like"]-273)
                    humidity = weather["main"]["humidity"]
                    description = weather["weather"][0]["description"]
                    say(f"The current weather in {' '.join(words[1:])} is {temp}°C, feels like {feels_like}°C, humidity {humidity}%, and {description}.", speak)
                except:
                    say("Error retrieving weather data.", speak)
                    '''
    

def ddgs_search(query, max_results=5):
    results_list = []
    with DDGS() as ddgs:
        for r in ddgs.text(f"!news {query}", max_results=max_results): # get only news
            results_list.append({
                'title': r.get('title', ''),
                'snippet': r.get('body', ''),
                'link': r.get('link', '')
            })
    return results_list

def wiki(speak, words, threshold=1000):
    try:
        title = words
        summary = wikipedia.summary(title)
        print(summary)
        if len(summary) > threshold:
            print("length: " + str(len(summary)))
            summary = summarize(summary) # shorten the summary if it is too long
            print(summary)
            say(summary, speak)
        else:
            say(summary, speak)
    except Exception as e:
        print(f"No articles found({e})\n")
        say("No articles found", speak)

def stats(speak, words):
    cpu = psutil.cpu_percent(interval=1)
    memory = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    available_memory = round(psutil.virtual_memory().available / (1024 ** 3), 1)
    disk = round(psutil.disk_usage('/').total / (1024 ** 3), 1)
    used = round(psutil.disk_usage('/').used / (1024 ** 3), 1)

    message = f"CPU Usage: {cpu}%, available RAM: {available_memory}GB, total RAM: {memory}GB, total SSD: {disk}GB, SSD used: {used}GB"

    print(message)
    say(message, speak)


def graph(*args):
    import matplotlib.pyplot as plt
    conn = sqlite3.connect('graph_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM percentages')
    data = [row[0] for row in cursor.fetchall()]
    conn.close()
    plt.figure()
    plt.plot(data)
    plt.xlabel('Time')
    plt.ylabel('CPU Usage (%)')
    plt.title('CPU Usage Over Time')
    plt.ylim(0, 100)
    plt.grid(True)
    plt.savefig("cpu_graph.png")
    plt.close()
    os.startfile("cpu_graph.png")
    print("Saved graph as cpu_graph.png")

def move_files(words):
    try:
        search_folder = words[1]  # 
        move_folder = words[2]    
        file_type = words[3]
        files = []


                    # Go through each file in the search directory and check if it has the target type
        for file in os.listdir(search_folder):
            if file.endswith(file_type):
                shutil.move(os.path.join(search_folder, file), os.path.join(move_folder, file))
                print(f"Moved {file} to {move_folder}.\n")
                files.append(file)
                print(f"Moved {len(files)} files from {search_folder} to {move_folder}")
    except Exception as e:
        print(e)
'''
def get_classes():
    class_list = []
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): exit()
    ret, frame = cap.read()
    if ret: cv2.imwrite("captured_image.jpg", frame)
    results = model("captured_image.jpg", size=320)
    for *box, conf, cls in results.xyxy[0]:
        if conf < 0.4: continue
        class_name = model.names[int(cls)]
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        class_list.append(class_name)
    if ret: cv2.imwrite("captured_image.jpg", frame)
    subprocess.call("start captured_image.jpg", shell=True)
    cap.release()
    cv2.destroyAllWindows()
    return class_list
'''

def play_audio(file):
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy(): sleep(0.1)
    pygame.mixer.quit()

def say(text, shouldSpeak=True):
    print("preparing")
    if shouldSpeak:
        print("speaking now")
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        engine.say(text)
        engine.runAndWait()
def stop_speech():
    engine.stop()
    
def format_context(results):
    context = ""
    for i, r in enumerate(results):
        title = r.get('title', '')
        snippet = r.get('body', '')  # DDGS uses 'body', not 'snippet'
        link = r.get('link', '')
        context += f"{i}. {title}\n{snippet}\n{link}\n\n"
    return context

def valid_num(num):
    try:
        num_integer = int(num)
        return num_integer
    except:
        return None

def get_output(text):
    global stop, monitor, limit, delay, move_folder, search_folder, file_type
    try:
        speak = True
        user_input = text
        if "-no-speak" in user_input.lower():
            user_input = user_input.lower().replace("-no-speak", "") 
            speak = False

        words = user_input.lower().split()
        command = words[0] if words else ""
        built_in_commands = [
            "search","youtube","open","weather","camera","cnn",
            "move-files","stream","wm","stop","monitor","graph",
            "cpu-stop","db-delete","wl", "web-search", "wiki", "system-stats", "stop"
        ]
        COMMANDS = {
            ""
            }
            


        closest_matches = difflib.get_close_matches(command, built_in_commands, n=1, cutoff=0.6) # tolerate typos
        if closest_matches:
            print(f"Typo... ({command})\n closest match: {closest_matches[0]}")
            command = closest_matches[0] # get closest match

        if command in built_in_commands:
            if command == "cnn":
                content = get_news(" ".join(words[1:]), False)
                say(summarize(content), speak)
            elif command == "wiki":
                threshold_in_command = valid_num(words[1])
                search = " ".join(words[1:])
                print(search)
                print(threshold_in_command)
                print(speak)
                if (threshold_in_command is not None):
                    wiki(speak, " ".join(words[2:]), str(threshold_in_command))
                else:
                    wiki(speak, " ".join(words[1:]))
            elif command == "stop":
                stop = True
            elif command == "wl":
                stop = False
                articles = []
                while True:
                    content = get_news(" ".join(words[1:]), False)
                    if content not in articles:
                        articles.append(content)
                        say(summarize(content), True)
                    if stop: break
                    sleep(5)
            elif command == "monitor":
                try:
                    limit = int(words[1])
                    delay = int(words[2])
                    monitor = True
                except:
                    say("Invalid input", speak)
            elif command == "stop":
                stop_speech()
            elif command == "cpu-stop":
                monitor = False
            elif command == "graph":
                graph()
            
            elif command == "weather":
                try:
                    weather = get_weather(" ".join(words[1:]))
                    temp = int(weather["main"]["temp"]-273)
                    feels_like = int(weather["main"]["feels_like"]-273)
                    humidity = weather["main"]["humidity"]
                    description = weather["weather"][0]["description"]
                    say(f"The current weather in {' '.join(words[1:])} is {temp}°C, feels like {feels_like}°C, humidity {humidity}%, and {description}.", speak)
                except:
                    say("Error retrieving weather data.", speak)
            elif command == "db-delete":
                conn = sqlite3.connect('graph_data.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM percentages')
                conn.commit()
                conn.close()
                print("Deleted all data from the database.")
            elif command == "move-files":
                move_files(words)
            elif command == "system-stats":
                stats(speak, words)
            else:
                say("thinking", speak)
                local_messages = messages.copy()
                local_messages.append({"role":"user","content":user_input})
                response = ollama.chat(model="codellama", messages=local_messages, options={"temperature": 0.1})
                assistant_reply = response['message']['content']
                print("Assistant:", assistant_reply)
                messages.append({"role":"assistant","content":assistant_reply})
                if speak: say(assistant_reply, speak)

    except Exception as e:
        print(" Error:", e)

def gui():
    import sys
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    window.setAttribute(Qt.WA_TranslucentBackground)
    layout = QVBoxLayout()
    layout.setContentsMargins(10,10,10,10)
    layout.setSpacing(5)
    text_label = QLabel('Voice Assistant')
    text_label.setStyleSheet("font-size: 18px; color: lightblue;")
    layout.addWidget(text_label)
    label = QLabel()
    entry = QLineEdit()
    entry.setPlaceholderText("Type your message...")
    layout.addWidget(entry)
    button = QPushButton("Submit")
    layout.addWidget(button)
    speak = QPushButton("Voice")
    layout.addWidget(speak)
    def on_submit():
        text = entry.text()
        threading.Thread(target=get_output, args=(text,)).start()
        entry.clear()
    def voice():
        r = sr.Recognizer()
        with sr.Microphone() as source:
            say("listening", speak)
            audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            say("got it", speak)
            threading.Thread(target=get_output, args=(text,)).start()
        except: print("voice recognition error")
    def start_voice(): threading.Thread(target=voice).start()
    button.clicked.connect(on_submit)
    speak.clicked.connect(start_voice)
    window.setLayout(layout)
    window.adjustSize()
    screen = app.primaryScreen().availableGeometry()
    x = 30
    y = screen.height()-window.height()-60
    window.move(x,y)
    window.show()
    sys.exit(app.exec_())

threading.Thread(target=cpu_monitor, args=[True], daemon=True).start()

if __name__ == "__main__":
    gui()

