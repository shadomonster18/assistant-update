import os
import sys
print(sys.executable)
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
import difflib

from functions import say, gui, say_async, play_audio, move_files, get_news, summarize, move_files, web_monitor, wiki, get_weather, message_box


messages = [{"role": "system", "content": "You are an assistant named Jarvis. Keep your answers short and clear. refer to the user as sir."}]

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
            "cpu-stop","db-delete","web-monitor", "web-search", "wiki", "system-stats", "stop"
        ]
        COMMANDS = {
            "cnn" : get_news,
            "web-monitor": web_monitor,
            "move-files": move_files,
            "wiki": wiki,
            "weather": get_weather
            }
            


        closest_matches = difflib.get_close_matches(command, built_in_commands, n=1, cutoff=0.8) # tolerate typos
        if closest_matches:#[0] != command and len(command) > 3:
            print(f"Typo... ({command})\n closest match: {closest_matches[0]}")
            command = closest_matches[0] # get closest match
        if command in COMMANDS:
            COMMANDS[command](speak, words)
        else:
            say("thinking", speak)
            messages.append({"role":"user","content":user_input})
            last_messages = messages[-5:]
            response = ollama.chat(model="llama3", messages=last_messages, options={"temperature": 0.1})
            assistant_reply = response['message']['content']
            print("Assistant:", assistant_reply)
            messages.append({"role":"assistant","content":assistant_reply})
            threading.Thread(target=message_box, args=(assistant_reply,)).start()
            if speak: say(assistant_reply, speak)

    except Exception as e:
        print("Error:", e)



if __name__ == "__main__":
    gui(get_output)
