import os
import threading
import urllib.request
import time
import math
import random
import sqlite3
import numpy as np
from scipy.io import wavfile

import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.utils import platform

import speech_recognition as sr
from gtts import gTTS
import pygame

# Dynamic Font Manager
FONT_PATH = "NotoSansHindi.ttf"
if not os.path.exists(FONT_PATH):
    try:
        url = "https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth%2Cwght%5D.ttf"
        urllib.request.urlretrieve(url, FONT_PATH)
    except Exception:
        FONT_PATH = 'Roboto'

pygame.mixer.init()

# ----------------- ANDROID PERMISSIONS -----------------
def request_android_permissions():
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.RECORD_AUDIO,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        except Exception as e:
            print("Android Permission Error:", e)

# ----------------- SQLITE DATABASE MANAGEMENT (AUTO-MIGRATION) -----------------
DB_FILE = "voice_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # अगर पुरानी Table में 'badge' कॉलम मौजूद नहीं है, तो Table रीसेट होगी
    cursor.execute("PRAGMA table_info(history)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if columns and "badge" not in columns:
        cursor.execute("DROP TABLE history")
        conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            avatar TEXT,
            pitch REAL,
            emotion TEXT,
            badge TEXT,
            result TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(name, age, gender, avatar, pitch, emotion, badge, result):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (timestamp, name, age, gender, avatar, pitch, emotion, badge, result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (time.strftime('%Y-%m-%d %H:%M'), name, age, gender, avatar, pitch, emotion, badge, result))
    conn.commit()
    conn.close()

def fetch_db_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, name, age, gender, pitch, emotion, badge, result FROM history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()

# Global User State
user_data = {
    "name": "", 
    "age": 0, 
    "gender": "Male", 
    "avatar": "🤖 Cyber Bot",
    "tts_voice": "Female", 
    "pitch": 0.0, 
    "emotion": "Neutral",
    "predicted_age_group": "Unknown",
    "badge": "🎖️ Cyber Novice",
    "voice_filter": "Normal",
    "bgm_enabled": True,
    "language": "hi"
}

THEMES = {
    "dark": {
        "bg": (0.03, 0.05, 0.09, 1),
        "card": (0.08, 0.12, 0.2, 0.95),
        "text": (1, 1, 1, 1),
        "subtext": (0.6, 0.7, 0.8, 1),
        "input_bg": (0.05, 0.08, 0.14, 1)
    },
    "light": {
        "bg": (0.92, 0.94, 0.98, 1),
        "card": (1, 1, 1, 0.95),
        "text": (0.1, 0.1, 0.1, 1),
        "subtext": (0.4, 0.5, 0.6, 1),
        "input_bg": (0.85, 0.88, 0.92, 1)
    }
}
current_theme = "dark"

def play_click_sound():
    def synth_sound():
        try:
            sample_rate = 22050
            duration = 0.05
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 30)
            audio = (tone * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(np.repeat(audio[:, np.newaxis], 2, axis=1))
            sound.play()
        except Exception:
            pass
    threading.Thread(target=synth_sound, daemon=True).start()

def trigger_vibration():
    play_click_sound()
    try:
        from plyer import vibrator
        vibrator.vibrate(0.05)
    except Exception:
        pass

# ----------------- ADVANCED VISUALIZER WIDGET -----------------
class AdvancedVisualizerWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_animating = False
        self.bars = 16
        self.heights = [10] * self.bars
        self.bind(size=self.draw_spectrum, pos=self.draw_spectrum)

    def draw_spectrum(self, *args):
        self.canvas.clear()
        with self.canvas:
            w, h = self.size
            cx, cy = self.pos
            spacing = w / (self.bars + 1)
            for i in range(self.bars):
                x = cx + spacing * (i + 1)
                bar_h = self.heights[i] if self.is_animating else 6
                Color(0, 0.8, 1 - (i/self.bars)*0.5, 0.9 if self.is_animating else 0.25)
                Line(points=[x, cy + (h / 2) - bar_h, x, cy + (h / 2) + bar_h], width=3.5)

    def start_animation(self):
        self.is_animating = True
        self.event = Clock.schedule_interval(self._animate_step, 0.08)

    def stop_animation(self):
        self.is_animating = False
        if hasattr(self, 'event'):
            self.event.cancel()
        self.draw_spectrum()

    def _animate_step(self, dt):
        self.heights = [random.randint(5, 45) for _ in range(self.bars)]
        self.draw_spectrum()

# ----------------- BASE UI LAYOUT WITH NEON PARTICLES -----------------
class CardLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            t = THEMES[current_theme]
            self.card_color = Color(*t["card"])
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[18,])
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

    def refresh_theme(self):
        t = THEMES[current_theme]
        self.card_color.rgba = t["card"]

class BaseScreen(Screen):
    def __init__(self, title="", step_val=0, **kwargs):
        super().__init__(**kwargs)
        self.step_val = step_val
        self.layout = BoxLayout(orientation='vertical', padding=[20, 15, 20, 20], spacing=12)
        
        self.particles = []
        for _ in range(12):
            self.particles.append({
                'x': random.random(),
                'y': random.random(),
                'r': random.randint(2, 5),
                'speed': random.uniform(0.001, 0.003)
            })

        with self.layout.canvas.before:
            t = THEMES[current_theme]
            self.bg_color = Color(*t["bg"])
            self.bg = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self._update_bg, pos=self._update_bg)

        Clock.schedule_interval(self._update_particles, 0.05)

        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=6)
        
        self.title_label = Label(
            text="CYBER VOICE AI PRO", 
            font_size=14, 
            bold=True, 
            color=(0, 0.9, 1, 1),
            halign='left',
            font_name=FONT_PATH
        )
        
        self.lang_btn = Button(
            text="🌐 HI", 
            size_hint=(0.18, 1), 
            background_normal='', 
            background_color=(0.8, 0.3, 0.2, 1),
            bold=True
        )
        self.lang_btn.bind(on_press=self.toggle_language)

        bgm_btn = Button(
            text="🎵 BGM", 
            size_hint=(0.18, 1), 
            background_normal='', 
            background_color=(0.1, 0.6, 0.7, 1),
            bold=True
        )
        bgm_btn.bind(on_press=self.toggle_bgm)

        theme_btn = Button(
            text="Theme", 
            size_hint=(0.18, 1), 
            background_normal='', 
            background_color=(0.2, 0.6, 0.9, 1),
            bold=True
        )
        theme_btn.bind(on_press=self.toggle_theme)

        header.add_widget(self.title_label)
        header.add_widget(self.lang_btn)
        header.add_widget(bgm_btn)
        header.add_widget(theme_btn)
        self.layout.add_widget(header)

        if step_val > 0:
            prog_box = BoxLayout(orientation='vertical', size_hint=(1, 0.05), spacing=3)
            pb = ProgressBar(max=100, value=step_val, size_hint=(1, 0.3))
            prog_box.add_widget(pb)
            self.step_label = Label(
                text=f"Step {int(step_val/33.33)} of 3", 
                font_size=11, 
                color=THEMES[current_theme]["subtext"]
            )
            prog_box.add_widget(self.step_label)
            self.layout.add_widget(prog_box)

        self.add_widget(self.layout)

    def _update_particles(self, dt):
        self.layout.canvas.before.clear()
        with self.layout.canvas.before:
            t = THEMES[current_theme]
            self.bg_color = Color(*t["bg"])
            self.bg = Rectangle(size=self.layout.size, pos=self.layout.pos)
            
            Color(0, 0.8, 1, 0.15)
            w, h = self.layout.size
            for p in self.particles:
                p['y'] += p['speed']
                if p['y'] > 1.0:
                    p['y'] = 0.0
                    p['x'] = random.random()
                Ellipse(pos=(p['x'] * w, p['y'] * h), size=(p['r'], p['r']))

    def _update_bg(self, instance, value):
        self.bg.size = instance.size
        self.bg.pos = instance.pos

    def toggle_language(self, instance):
        trigger_vibration()
        if user_data["language"] == "hi":
            user_data["language"] = "en"
            instance.text = "🌐 EN"
        else:
            user_data["language"] = "hi"
            instance.text = "🌐 HI"

    def toggle_theme(self, instance):
        global current_theme
        trigger_vibration()
        current_theme = "light" if current_theme == "dark" else "dark"
        app = App.get_running_app()
        app.update_app_theme()

    def toggle_bgm(self, instance):
        trigger_vibration()
        user_data["bgm_enabled"] = not user_data["bgm_enabled"]
        instance.text = "🎵 BGM" if user_data["bgm_enabled"] else "🔇 Mute"

    def apply_theme(self):
        t = THEMES[current_theme]
        self.bg_color.rgba = t["bg"]
        if hasattr(self, 'step_label'):
            self.step_label.color = t["subtext"]

# ----------------- SPLASH SCREEN -----------------
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        with layout.canvas.before:
            Color(0.03, 0.05, 0.09, 1)
            self.bg = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update, pos=self._update)

        lbl = Label(text="CYBER VOICE AI", font_size=28, bold=True, color=(0, 0.9, 1, 1), font_name=FONT_PATH)
        sub = Label(text="Loading AI Voice Engine...", font_size=13, color=(0.6, 0.7, 0.8, 1))
        
        self.wave = AdvancedVisualizerWidget(size_hint=(1, 0.3))
        
        layout.add_widget(lbl)
        layout.add_widget(self.wave)
        layout.add_widget(sub)
        self.add_widget(layout)

    def _update(self, instance, value):
        self.bg.size = instance.size
        self.bg.pos = instance.pos

    def on_enter(self):
        request_android_permissions()
        self.wave.start_animation()
        Clock.schedule_once(self.goto_main, 2.5)

    def goto_main(self, dt):
        self.wave.stop_animation()
        self.manager.current = 'name_screen'

# ----------------- PAGE 1: PROFILE & AI PITCH AGE DETECTION -----------------
class NameScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Name Screen", step_val=33, **kwargs)

        self.card = CardLayout(orientation='vertical', padding=15, spacing=10, size_hint=(1, 0.78))
        self.heading = Label(
            text="User Profile & Voice Analysis", 
            font_size=17, 
            bold=True, 
            color=THEMES[current_theme]["text"],
            size_hint=(1, 0.12),
            font_name=FONT_PATH
        )
        self.card.add_widget(self.heading)

        avatar_box = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.15))
        self.avatars = ["🤖 Cyber Bot", "⚡ Electro Man", "👑 Cyber Queen", "👽 Alien Cyber"]
        self.avatar_btns = []
        for av in self.avatars:
            btn = Button(text=av, font_size=10, background_normal='', background_color=(0.12, 0.16, 0.24, 1))
            btn.bind(on_press=lambda x, a=av: self.select_avatar(a))
            self.avatar_btns.append(btn)
            avatar_box.add_widget(btn)
        self.card.add_widget(avatar_box)

        input_box = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.18))
        self.name_input = TextInput(
            hint_text="Type or Speak Name...", 
            multiline=False, 
            font_size=15, 
            background_color=THEMES[current_theme]["input_bg"], 
            foreground_color=THEMES[current_theme]["text"], 
            padding=[10, 8, 10, 8],
            cursor_color=(0, 0.95, 1, 1),
            font_name=FONT_PATH
        )
        
        mic_btn = Button(
            text="[ Mic ]", 
            size_hint=(0.22, 1), 
            background_normal='', 
            background_color=(0, 0.7, 0.9, 1),
            bold=True
        )
        mic_btn.bind(on_press=self.listen_and_analyze_voice)

        input_box.add_widget(self.name_input)
        input_box.add_widget(mic_btn)
        self.card.add_widget(input_box)

        self.wave_widget = AdvancedVisualizerWidget(size_hint=(1, 0.18))
        self.pitch_lbl = Label(
            text="Pitch: -- Hz | AI Age Est: --", 
            font_size=12, 
            color=(0, 0.9, 0.6, 1),
            size_hint=(1, 0.1)
        )
        self.card.add_widget(self.wave_widget)
        self.card.add_widget(self.pitch_lbl)

        gender_box = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.15))
        self.male_btn = Button(text="Male", font_size=14, bold=True, background_normal='', background_color=(0, 0.7, 1, 1))
        self.female_btn = Button(text="Female", font_size=14, bold=True, background_normal='', background_color=(0.12, 0.16, 0.24, 1))

        self.male_btn.bind(on_press=self.select_male)
        self.female_btn.bind(on_press=self.select_female)

        gender_box.add_widget(self.male_btn)
        gender_box.add_widget(self.female_btn)
        self.card.add_widget(gender_box)

        self.layout.add_widget(self.card)

        nav_box = BoxLayout(orientation='horizontal', spacing=12, size_hint=(1, 0.12))
        history_btn = Button(text="Logs History", font_size=14, bold=True, background_normal='', background_color=(0.15, 0.2, 0.3, 1))
        history_btn.bind(on_press=self.open_history)
        
        next_btn = Button(text="Next Step >", font_size=15, bold=True, background_normal='', background_color=(0.3, 0.2, 0.9, 1))
        next_btn.bind(on_press=self.go_to_age)

        nav_box.add_widget(history_btn)
        nav_box.add_widget(next_btn)
        self.layout.add_widget(nav_box)

    def select_avatar(self, avatar):
        trigger_vibration()
        user_data["avatar"] = avatar
        for btn in self.avatar_btns:
            if btn.text == avatar:
                btn.background_color = (0, 0.8, 0.5, 1)
            else:
                btn.background_color = (0.12, 0.16, 0.24, 1)

    def listen_and_analyze_voice(self, instance):
        trigger_vibration()
        self.name_input.hint_text = "Listening & Analyzing..."
        self.wave_widget.start_animation()
        
        def process_audio():
            r = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.listen(source, timeout=4)
                    
                    wav_data = audio.get_wav_data()
                    temp_wav = "temp_input.wav"
                    with open(temp_wav, "wb") as f:
                        f.write(wav_data)

                    rate, data = wavfile.read(temp_wav)
                    if len(data.shape) > 1:
                        data = data[:, 0]
                    
                    fft_spectrum = np.abs(np.fft.rfft(data))
                    freqs = np.fft.rfftfreq(len(data), d=1.0/rate)
                    peak_freq = freqs[np.argmax(fft_spectrum)]
                    
                    user_data["pitch"] = round(float(peak_freq), 2)
                    
                    # AI Age & Emotion Estimation from Voice Frequency
                    if peak_freq > 260:
                        user_data["predicted_age_group"] = "Child / Youngster"
                        user_data["emotion"] = "Energetic"
                    elif peak_freq > 160:
                        user_data["predicted_age_group"] = "Young Adult"
                        user_data["emotion"] = "Happy / Active"
                    else:
                        user_data["predicted_age_group"] = "Adult / Senior"
                        user_data["emotion"] = "Calm / Deep"

                    text = r.recognize_google(audio, language='en-IN')
                    Clock.schedule_once(lambda dt: setattr(self.name_input, 'text', text))
                    Clock.schedule_once(lambda dt: setattr(self.pitch_lbl, 'text', f"Pitch: {user_data['pitch']} Hz | Est: {user_data['predicted_age_group']}"))

                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)

            except Exception:
                Clock.schedule_once(lambda dt: setattr(self.name_input, 'hint_text', "Voice Input Failed"))
            finally:
                Clock.schedule_once(lambda dt: self.wave_widget.stop_animation())

        threading.Thread(target=process_audio, daemon=True).start()

    def select_male(self, instance):
        trigger_vibration()
        user_data["gender"] = "Male"
        self.male_btn.background_color = (0, 0.7, 1, 1)
        self.female_btn.background_color = (0.12, 0.16, 0.24, 1)

    def select_female(self, instance):
        trigger_vibration()
        user_data["gender"] = "Female"
        self.female_btn.background_color = (0.9, 0.2, 0.6, 1)
        self.male_btn.background_color = (0.12, 0.16, 0.24, 1)

    def open_history(self, instance):
        trigger_vibration()
        self.manager.current = 'history_screen'

    def go_to_age(self, instance):
        trigger_vibration()
        if not self.name_input.text.strip():
            return
        user_data["name"] = self.name_input.text.strip()
        self.manager.current = 'age_screen'

    def apply_theme(self):
        super().apply_theme()
        t = THEMES[current_theme]
        self.card.refresh_theme()
        self.heading.color = t["text"]
        self.name_input.background_color = t["input_bg"]
        self.name_input.foreground_color = t["text"]

# ----------------- PAGE 2: AGE SCREEN -----------------
class AgeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Age Screen", step_val=66, **kwargs)

        self.card = CardLayout(orientation='vertical', padding=25, spacing=15, size_hint=(1, 0.72))
        self.heading = Label(
            text="Enter Your Age Target", 
            font_size=20, 
            bold=True, 
            color=THEMES[current_theme]["text"],
            size_hint=(1, 0.3),
            font_name=FONT_PATH
        )
        self.card.add_widget(self.heading)

        self.age_input = TextInput(
            hint_text="Enter age (e.g. 21)...", 
            multiline=False, 
            input_filter='int', 
            font_size=18, 
            background_color=THEMES[current_theme]["input_bg"], 
            foreground_color=THEMES[current_theme]["text"], 
            padding=[12, 10, 12, 10],
            cursor_color=(0, 0.95, 1, 1),
            size_hint=(1, 0.22)
        )
        self.card.add_widget(self.age_input)
        self.layout.add_widget(self.card)

        nav_box = BoxLayout(orientation='horizontal', spacing=15, size_hint=(1, 0.14))
        back_btn = Button(text="< Back", font_size=15, bold=True, background_normal='', background_color=(0.15, 0.2, 0.3, 1))
        back_btn.bind(on_press=self.go_back)
        
        check_btn = Button(text="Analyze AI Result", font_size=16, bold=True, background_normal='', background_color=(0.3, 0.2, 0.9, 1))
        check_btn.bind(on_press=self.go_to_result)

        nav_box.add_widget(back_btn)
        nav_box.add_widget(check_btn)
        self.layout.add_widget(nav_box)

    def go_back(self, instance):
        trigger_vibration()
        self.manager.current = 'name_screen'

    def go_to_result(self, instance):
        trigger_vibration()
        if not self.age_input.text.strip():
            return
        user_data["age"] = int(self.age_input.text.strip())
        self.manager.current = 'result_screen'

    def apply_theme(self):
        super().apply_theme()
        t = THEMES[current_theme]
        self.card.refresh_theme()
        self.heading.color = t["text"]
        self.age_input.background_color = t["input_bg"]
        self.age_input.foreground_color = t["text"]

# ----------------- PAGE 3: RESULT, VOICE FILTERS & BADGES -----------------
class ResultScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Result Screen", step_val=100, **kwargs)
        self.current_message = ""
        self.typewriter_event = None

        self.card = CardLayout(orientation='vertical', padding=20, spacing=10, size_hint=(1, 0.72))
        
        self.wave = AdvancedVisualizerWidget(size_hint=(1, 0.18))
        self.card.add_widget(self.wave)

        self.meta_label = Label(
            text="", 
            font_size=11, 
            color=(0, 0.8, 1, 0.8),
            size_hint=(1, 0.1)
        )
        self.card.add_widget(self.meta_label)

        self.badge_label = Label(
            text="", 
            font_size=13, 
            bold=True, 
            color=(1, 0.84, 0, 1),
            size_hint=(1, 0.1)
        )
        self.card.add_widget(self.badge_label)

        self.result_label = Label(
            text="", 
            font_size=17, 
            bold=True, 
            color=(0, 0.95, 0.6, 1),
            halign='center',
            valign='middle',
            font_name=FONT_PATH
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        self.card.add_widget(self.result_label)

        # Voice Filter Selection Bar
        filter_box = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1, 0.12))
        filters = ["Normal", "Robotic", "Chipmunk"]
        for f in filters:
            btn = Button(text=f, font_size=10, background_normal='', background_color=(0.15, 0.2, 0.3, 1))
            btn.bind(on_press=lambda x, flt=f: self.set_voice_filter(flt))
            filter_box.add_widget(btn)
        self.card.add_widget(filter_box)

        self.layout.add_widget(self.card)

        btn_box = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.14))
        
        replay_btn = Button(text="Replay", font_size=11, bold=True, background_normal='', background_color=(0, 0.8, 0.5, 1))
        replay_btn.bind(on_press=self.replay_voice)

        png_btn = Button(text="Save PNG", font_size=11, bold=True, background_normal='', background_color=(0.1, 0.7, 0.8, 1))
        png_btn.bind(on_press=self.export_png_card)
        
        share_btn = Button(text="Share Card", font_size=11, bold=True, background_normal='', background_color=(0.9, 0.5, 0.1, 1))
        share_btn.bind(on_press=self.share_result)

        restart_btn = Button(text="Restart", font_size=11, bold=True, background_normal='', background_color=(0.3, 0.2, 0.9, 1))
        restart_btn.bind(on_press=self.restart_app)

        btn_box.add_widget(replay_btn)
        btn_box.add_widget(png_btn)
        btn_box.add_widget(share_btn)
        btn_box.add_widget(restart_btn)
        self.layout.add_widget(btn_box)

    def set_voice_filter(self, flt):
        trigger_vibration()
        user_data["voice_filter"] = flt

    def export_png_card(self, instance):
        trigger_vibration()
        try:
            filename = f"cyber_card_{int(time.time())}.png"
            self.card.export_to_png(filename)
            instance.text = "Saved!"
            Clock.schedule_once(lambda dt: setattr(instance, 'text', "Save PNG"), 2)
        except Exception as e:
            print("PNG Export Error:", e)

    def share_result(self, instance):
        trigger_vibration()
        summary = f"🎮 Cyber Voice AI Result 🎮\nAvatar: {user_data['avatar']}\nName: {user_data['name']}\nAge: {user_data['age']}\nBadge: {user_data['badge']}\nPitch: {user_data['pitch']} Hz\nResult: {self.current_message}"
        Clipboard.copy(summary)
        instance.text = "Copied!"
        Clock.schedule_once(lambda dt: setattr(instance, 'text', "Share Card"), 2)

    def animate_typewriter(self, full_text):
        self.result_label.text = ""
        self.char_index = 0
        if self.typewriter_event:
            self.typewriter_event.cancel()

        def update_char(dt):
            if self.char_index < len(full_text):
                self.result_label.text += full_text[self.char_index]
                self.char_index += 1
            else:
                return False

        self.typewriter_event = Clock.schedule_interval(update_char, 0.04)

    def speak_gtts(self, text):
        self.wave.start_animation()
        def run_speech():
            try:
                lang_code = user_data.get("language", "hi")
                tts = gTTS(text=text, lang=lang_code, slow=False)
                audio_file = "temp_voice.mp3"
                tts.save(audio_file)

                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.music.unload()
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception as e:
                print("gTTS Error:", e)
            finally:
                Clock.schedule_once(lambda dt: self.wave.stop_animation())

        threading.Thread(target=run_speech, daemon=True).start()

    def on_enter(self):
        age = user_data["age"]
        name = user_data["name"]

        # Custom Dialogues
        if 1 <= age <= 5:
            message = f"{name}, Welcome! chhote bacche ho tum"
            badge = "👶 Little Cyber Champ"
        elif 6 <= age <= 18:
            message = f"{name}, maje ker lo yahi jindagi hai"
            badge = "🚀 Young Explorer"
        elif 19 <= age <= 22:
            message = f"{name}, ab maje ki bari nahin hai kuch kar dikhane ke bare hai"
            badge = "🔥 High Achiever"
        elif 23 <= age <= 59:
            message = f"{name}, shaadi ki bari ab tumahari hi hai"
            badge = "💍 Life Titan"
        elif 60 <= age <= 100:
            message = f"{name}, buddhe ho gaye ho tum"
            badge = "👑 Cyber Mastermind"
        else:
            message = f"{name}, kripya sahi umar darj karein."
            badge = "❓ Unknown Legend"

        user_data["badge"] = badge
        self.current_message = message
        self.meta_label.text = f"Avatar: {user_data['avatar']} | Pitch: {user_data['pitch']} Hz | Est: {user_data['predicted_age_group']}"
        self.badge_label.text = f"Unlocked Badge: {badge}"
        self.animate_typewriter(message)
        
        save_to_db(name, age, user_data["gender"], user_data["avatar"], user_data["pitch"], user_data["emotion"], badge, message)
        self.speak_gtts(message)

    def replay_voice(self, instance):
        trigger_vibration()
        if self.current_message:
            self.speak_gtts(self.current_message)

    def restart_app(self, instance):
        trigger_vibration()
        self.manager.current = 'name_screen'

    def apply_theme(self):
        super().apply_theme()
        self.card.refresh_theme()

# ----------------- PAGE 4: SQLITE HISTORY & EXPORT -----------------
class HistoryScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="History", step_val=0, **kwargs)

        self.card = CardLayout(orientation='vertical', padding=15, spacing=10, size_hint=(1, 0.75))
        self.heading = Label(
            text="SQLite Database Records", 
            font_size=18, 
            bold=True, 
            color=THEMES[current_theme]["text"],
            size_hint=(1, 0.1),
            font_name=FONT_PATH
        )
        self.card.add_widget(self.heading)

        scroll = ScrollView(size_hint=(1, 0.72))
        self.history_label = Label(
            text="No SQLite Records Found", 
            font_size=11, 
            size_hint_y=None, 
            color=THEMES[current_theme]["subtext"],
            halign='left',
            valign='top',
            font_name=FONT_PATH
        )
        self.history_label.bind(texture_size=self.history_label.setter('size'))
        scroll.add_widget(self.history_label)
        self.card.add_widget(scroll)

        opt_box = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.12))
        
        export_btn = Button(text="Export CSV", font_size=12, bold=True, background_normal='', background_color=(0.2, 0.7, 0.4, 1))
        export_btn.bind(on_press=self.export_csv)

        clear_logs_btn = Button(text="Clear DB Logs", font_size=12, bold=True, background_normal='', background_color=(0.9, 0.2, 0.3, 1))
        clear_logs_btn.bind(on_press=self.clear_history)

        opt_box.add_widget(export_btn)
        opt_box.add_widget(clear_logs_btn)
        self.card.add_widget(opt_box)

        self.layout.add_widget(self.card)

        back_btn = Button(text="< Return to Home", font_size=15, bold=True, size_hint=(1, 0.12), background_normal='', background_color=(0.3, 0.2, 0.9, 1))
        back_btn.bind(on_press=self.go_home)
        self.layout.add_widget(back_btn)

    def export_csv(self, instance):
        trigger_vibration()
        rows = fetch_db_history()
        if rows:
            try:
                with open("db_export.csv", "w", encoding="utf-8") as f:
                    f.write("Timestamp,Name,Age,Gender,Pitch(Hz),Emotion,Badge,Result\n")
                    for r in rows:
                        f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]},{r[6]},{r[7]}\n")
                instance.text = "CSV Exported!"
                Clock.schedule_once(lambda dt: setattr(instance, 'text', "Export CSV"), 2)
            except Exception as e:
                print("CSV Error:", e)

    def clear_history(self, instance):
        trigger_vibration()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history')
        conn.commit()
        conn.close()
        self.history_label.text = "No SQLite Records Found"

    def go_home(self, instance):
        trigger_vibration()
        self.manager.current = 'name_screen'

    def on_enter(self):
        rows = fetch_db_history()
        if rows:
            formatted_text = ""
            for r in rows:
                formatted_text += f"[{r[0]}] {r[1]} ({r[2]} yrs, {r[3]})\n  Badge: {r[6]} | Pitch: {r[4]}Hz | Emotion: {r[5]}\n  Result: {r[7]}\n----------------------------------------\n"
            self.history_label.text = formatted_text
        else:
            self.history_label.text = "No SQLite Records Found"

    def apply_theme(self):
        super().apply_theme()
        t = THEMES[current_theme]
        self.card.refresh_theme()
        self.heading.color = t["text"]
        self.history_label.color = t["subtext"]

# ----------------- MAIN APP CLASS -----------------
class AgeVoiceApp(App):
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(SplashScreen(name='splash_screen'))
        self.sm.add_widget(NameScreen(name='name_screen'))
        self.sm.add_widget(AgeScreen(name='age_screen'))
        self.sm.add_widget(ResultScreen(name='result_screen'))
        self.sm.add_widget(HistoryScreen(name='history_screen'))
        return self.sm

    def update_app_theme(self):
        for screen in self.sm.screens:
            if hasattr(screen, 'apply_theme'):
                screen.apply_theme()

if __name__ == "__main__":
    AgeVoiceApp().run()