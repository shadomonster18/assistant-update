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
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QMovie
from selenium import webdriver
from selenium.webdriver.common.by import By
from ddgs import DDGS
import requests
import speech_recognition as sr
import wikipedia
import edge_tts
import asyncio
import pygame
import time
import pywhatkit as kit
from tkinter import messagebox, Tk


BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
API_KEY = "037ba4f97795497e172cbc0a510c17c0"

def web_monitor(speak, words):
    stop = False
    articles = []
    command = words[1]
    while True:
           content = get_news(" ".join(words[1:]), False)
           if content not in articles:
                   articles.append(content)
                   say(summarize(content), True)
                   if stop: break
                   sleep(5)
    

def summarize(text):
    response = ollama.chat(model="llama3", messages=[{"role": "system", "content": "summarize the contents of this article in a few lines. go straight to the summary, dont say here is a summary:."},{"role": "user","content": text}])

    return response['message']['content']

def move_files(speak, words):
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
        say(f"moved {len(files)} files", speak)
    except Exception as e:
        print(e)

def play_audio(file):
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy(): sleep(0.1)
    pygame.mixer.quit()

async def say_async(text):
    communicate = edge_tts.Communicate(
        text,
        voice="en-GB-RyanNeural",
        rate="+20%",
        pitch="+1Hz"
    )
    await communicate.save("speech.mp3")

def say(text, shouldSpeak):
    try:
        asyncio.run(say_async(text))
        play_audio("speech.mp3")
    except Exception as e:
        print(e)
        import pyttsx3
        engine = pyttsx3.init()
        print("preparing")
        if shouldSpeak:
            print("speaking now")
            engine.setProperty('rate', 250)
            engine.setProperty('volume', 1.0)
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[0].id)
            engine.say(text)
            engine.runAndWait()
            engine.runAndWait()
            
def wiki(speak, words, threshold=1500):
    try:
        title = " ".join(words[1:])
        results = wikipedia.search(title);
        if not results:
            print("none")
            return
        print(words)
        title = results[0]
        print("\n".join(results))
        print("title:", title)
        #summary = wikipedia.summary(" ".join(words[1:]), auto_suggest=False)
        summary = wikipedia.summary(title, auto_suggest=False)
        print(summary)
        if len(summary) > threshold:
            print("length: " + str(len(summary)))
            summary = summarize(summary) # shorten the summary if it is too long
            print(summary)
            threading.Thread(target=message_box, args=(summary,)).start()
            say(summary, speak)
        else:
            threading.Thread(target=message_box, args=(summary,)).start()
            say(summary, speak)
    except wikipedia.DisambiguationError as e:
        say(f"Multiple matches found. Try: {e.options[0]}", speak)
    except Exception as e:
        print(f"No articles found({e})\n")
        say("No articles found", speak)
    
def get_weather(speak, words):
    response = requests.get(BASE_URL + "appid=" + API_KEY + "&q=" + " ".join(words[1:])).json()
    try:
        temp = int()
        temp = int(response["main"]["temp"]-273)
        feels_like = int(response["main"]["feels_like"]-273)
        humidity = response["main"]["humidity"]
        description = response["weather"][0]["description"]
        weather_info = f"temperature: {temp}C, feels like: {feels_like}C, description: {description}. location: {' '.join(words[1:])}."
        print(weather_info)
        threading.Thread(target=message_box, args=(weather_info,)).start()
        response = ollama.chat(model="llama3", messages=[{"role": "system", "content": f"you are an assistant named Jarvis. Keep your answers short and clear. refer to the user as sir. your current task is to clearly inform the user of the current weather data, be simple and direct, dont ask any follow up questions, and mention the location the weather is in. however, the response must be conversational so dont just output the exact information, but be acccurate. here is the info: {weather_info}"}])

        say(response["message"]["content"], speak)
    except Exception as e:
        say("Error while retrieving weather data", speak)
        print(e)

def get_news(speak, words):
    try:
        search = " ".join(words[1:])
        url = "https://www.edition.cnn.com/search?q="
        say("searching now", speak)
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
        say("Found article,", speak)
        driver.quit()
        print(article_text)
        summary = summarize(article_text)
        print(summary)
        threading.Thread(target=message_box, args=(summary,)).start()
        say(summary, speak)
    except Exception as e:
        print("⚠️ Error:", e)
        say("Sir, I unfortunately couldn't retrieve the news, if you need anything else just ask", speak)
        
def message_box(text):
    root = Tk()
    root.withdraw()
    messagebox.showinfo("Jarvis", text, parent=root)

def gui(get_output):
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
