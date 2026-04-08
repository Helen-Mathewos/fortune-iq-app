import json
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.core.text import LabelBase
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader

# ---------------- FONT FIX ----------------
LabelBase.register(name="CustomFont", fn_regular="DejaVuSans.ttf")

# Load JSON
with open("questions.json",encoding="utf-8") as f:
    data = json.load(f)


# ---------------- BACKGROUND FUNCTION ----------------
def add_background(screen):
    bg = Image(source="background2.jpg",
               allow_stretch=True,
               keep_ratio=False)
    screen.add_widget(bg)

# ---------------- CUSTOM BUTTON ----------------
class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.3, 0.3, 0.3, 0.9)  # gray color
        self.color = (0, 1, 1, 1)
        with self.canvas.before:
            self.rect_color = Color(0.3, 0.3, 0.3, 0.9)
            self.rect = RoundedRectangle(radius=[20])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# ---------------- HOME ----------------
class HomeScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        add_background(self)
        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        # Spacer to push title to vertical center
        main_layout.add_widget(Widget())

        # Centered title
        title_layout = BoxLayout(size_hint_y=None, height=100)
        title_label = Label(text="FORTUNE IQ", font_size=40, size_hint=(1, 1), halign="center", valign="middle",)
        title_label.bind(size=title_label.setter('text_size'))  # keep text centered
        title_layout.add_widget(title_label)
        main_layout.add_widget(title_layout)

        # Spacer to push buttons below title
        main_layout.add_widget(Widget())

        # Buttons (kept unchanged)
        for level in data.keys():
            btn = RoundedButton(
                text=level, size_hint=(0.6, None), height=50, pos_hint={"center_x": 0.5}
            )
            btn.bind(on_release=lambda x, lvl=level: self.select_level(lvl))
            main_layout.add_widget(btn)

        self.add_widget(main_layout)

        if hasattr(self, "music") and self.music:
            self.music.stop()

        self.music = SoundLoader.load("background1.mp3")
        if self.music:
            self.music.loop = True
            self.music.play()

        

    def select_level(self, level):
        self.manager.get_screen('subject').level = level
        self.manager.current = 'subject'

# ---------------- SUBJECT ----------------
class SubjectScreen(Screen):
    level = ""
    def on_enter(self):
        self.clear_widgets()
        add_background(self)
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Top-left Home Button
        top_bar = BoxLayout(size_hint_y=None, height=50)
        home_btn = RoundedButton(text="Home", size_hint=(None, None), size=(100, 40))
        home_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        top_bar.add_widget(home_btn)
        main_layout.add_widget(top_bar)

        # Centered subjects
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=f"{self.level} Subjects", font_size=30, size_hint_y=None, height=50))
        for subject in data[self.level].keys():
            btn = RoundedButton(text=subject, size_hint=(0.7, None), height=45, pos_hint={"center_x":0.5})
            btn.bind(on_release=lambda x, sub=subject: self.start_quiz(sub))
            content.add_widget(btn)
        main_layout.add_widget(content)
        self.add_widget(main_layout)

    def start_quiz(self, subject):
        self.manager.get_screen('quiz').setup_quiz(self.level, subject)
        self.manager.current = 'quiz'

# ---------------- QUIZ ----------------
class QuizScreen(Screen):
    prize_ladder = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000,
                    125000, 250000, 500000, 1000000]

    def setup_quiz(self, level, subject):
        self.questions = data[level][subject][:len(self.prize_ladder)+1]
        random.shuffle(self.questions)
        self.current = 0
        self.money = 0
        self.lifelines = {"50-50": True, "Audience": True, "Phone": True}
        self.time_left = 15
        self.timer_event = None
        self.timer_running = False
        self.is_game_over = False

        self.correct_sound = SoundLoader.load("correct.mp3")
        self.wrong_sound = SoundLoader.load("wrong.wav")
        self.win_sound = SoundLoader.load("win.mp3")
        self.countdown_sound = SoundLoader.load("countdown.wav")
        self.coin_sound = SoundLoader.load("coin1.mp3")
        self.game_over_sound = SoundLoader.load("gameover.wav")  # your file

        self.show_question()

        

    def go_home(self, instance):
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = None
        self.timer_running = False
        self.manager.current = 'home'

    def start_timer(self):
        if self.timer_running:
            return
        self.time_left = 15
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        self.timer_running = True
    def update_timer(self, dt):
        if self.is_game_over:
            return

        if not self.timer_running:
            return
        self.time_left -= 1

        self.timer_label.text = f"Time: {max(self.time_left, 0)}"

        if self.time_left == 5:
            if self.countdown_sound:
                self.countdown_sound.stop()
                self.countdown_sound.play()

        if self.time_left <= 0:
            self.time_left = 0

            if self.timer_event:
                self.timer_event.cancel()
                self.timer_event = None
            self.timer_running = False
            self.game_over()

       

    def show_question(self):
        self.clear_widgets()
        add_background(self)
        self.is_game_over = False
        

        self.qdata = self.questions[self.current]
        self.options = self.qdata["options"][:]
        random.shuffle(self.options)

        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        # ---------------- Top Bar ----------------
        top_bar = BoxLayout(size_hint_y=None, height=50)
        home_btn = RoundedButton(text="Home", size_hint=(None, None), size=(100, 40))
        home_btn.bind(on_release=self.go_home)
        top_bar.add_widget(home_btn)

        top_bar.add_widget(Widget(size_hint_x=None, width=20))  # spacing

        # Timer in the top-middle
        self.timer_label = Label(text=f"Time: {self.time_left}", size_hint=(1, 1), font_size=20, halign="center", valign="middle")
        top_bar.add_widget(self.timer_label)

        top_bar.add_widget(Widget(size_hint_x=None, width=20))  # spacing

        # Lifelines
        for name in self.lifelines:
            btn = RoundedButton(text=name, size_hint=(None, 1), width=100)
            btn.disabled = not self.lifelines[name]
            if name == "50-50":
                btn.bind(on_release=self.use_5050)
            elif name == "Audience":
                btn.bind(on_release=self.use_audience)
            else:
                btn.bind(on_release=self.use_phone)
            top_bar.add_widget(btn)

        layout.add_widget(top_bar)

        # Centered Question and Answers
        center_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        center_layout.add_widget(Label(text=f"Q{self.current+1}: {self.qdata['question']}", font_size=24, size_hint_y=None, height=80))

        self.option_buttons = []
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for opt in self.options:
            btn = RoundedButton(text=opt, height=50, size_hint_y=None)
            btn.bind(on_release=lambda x, ans=opt: self.check_answer(ans))
            grid.add_widget(btn)
            self.option_buttons.append(btn)

        center_layout.add_widget(grid)
        layout.add_widget(center_layout)
        self.add_widget(layout)

        self.start_timer()

    def check_answer(self, selected):
        correct = self.qdata["answer"]

        for btn in self.option_buttons:
            if btn.text == correct:
                btn.background_color = (0,1,0,1)
            elif btn.text == selected:
                btn.background_color = (1,0,0,1)

        if selected == correct:
            if self.countdown_sound:
                self.countdown_sound.stop()
            if self.correct_sound:
                self.correct_sound.play()
                
            self.money = self.prize_ladder[min(self.current, len(self.prize_ladder)-1)]     

             # ✅ STOP TIMER
            if self.timer_event:
                self.timer_event.cancel()         



        # ✅ FIX: check if this is the LAST question
            if self.current == len(self.questions) - 1:
                if self.win_sound:
                    self.win_sound.play()
                    
                Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'win'), 1)
                return
            if self.coin_sound:
                self.coin_sound.stop()
                self.coin_sound.play()

        # OTHERWISE go to ladder
            ladder_screen = self.manager.get_screen('ladder')
            ladder_screen.current_question = self.current
            ladder_screen.quiz_screen = self
            self.manager.current = 'ladder'

        else:
            if self.wrong_sound:
                self.wrong_sound.play()
            Clock.schedule_once(lambda dt: self.game_over(), 1)

   
    def game_over(self):
        self.is_game_over = True

        if self.game_over_sound:
            self.game_over_sound.stop()  # stop in case it's still playing
            self.game_over_sound.play()

        if self.countdown_sound:
            self.countdown_sound.stop()
        if self.correct_sound:
            self.correct_sound.stop()
        if self.wrong_sound:
            self.wrong_sound.stop()
        if self.win_sound:
            self.win_sound.stop()

        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self.timer_running = False
        
        self.clear_widgets()
        add_background(self)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        top = BoxLayout(size_hint_y=None, height=50)
        home_btn = RoundedButton(text="Home", size_hint=(None, None), size=(100, 40))

        home_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        top.add_widget(home_btn)
        
        layout.add_widget(top)

        layout.add_widget(Label(text=f"Game Over!\nYou won: ${self.money}", font_size=30))

       
        self.add_widget(layout)

    # Lifelines
    def use_5050(self, instance):
        correct = self.qdata["answer"]
        wrong = [o for o in self.options if o != correct]
        remove = random.sample(wrong, 2)
        for btn in self.option_buttons:
            if btn.text in remove:
                btn.disabled = True
        self.lifelines["50-50"] = False
        instance.disabled = True

    def use_audience(self, instance):
        self.show_popup(f"Audience thinks: {self.qdata['answer']}")
        self.lifelines["Audience"] = False
        instance.disabled = True

    def use_phone(self, instance):
        self.show_popup(f"Friend thinks: {self.qdata['answer']}")
        self.lifelines["Phone"] = False
        instance.disabled = True

    def show_popup(self, text):
        self.clear_widgets()
        add_background(self)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        layout.add_widget(Label(text=text, font_size=25))
        btn = RoundedButton(text="Continue",size_hint=(None, None),height=100, pos_hint={"center_x":0.5},size=(400,100))
        btn.bind(on_release=lambda x: self.show_question())
        layout.add_widget(btn)
        self.add_widget(layout)

# ---------------- MONEY LADDER ----------------
class MoneyLadderScreen(Screen):
    current_question = 0
    prize_ladder = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000,
                    64000, 125000, 250000, 500000, 1000000]
    quiz_screen = None  # reference to QuizScreen

    def on_enter(self):
        self.clear_widgets()
        add_background(self)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        layout.add_widget(Label(text="$Money Ladder$", font_size=30, size_hint_y=None, height=50))

        # Ladder display (highest to lowest)
        ladder_layout = BoxLayout(orientation='vertical', spacing=5)
        for i, prize in reversed(list(enumerate(self.prize_ladder))):
            color = (0, 1, 0, 1) if i == self.current_question else (0.5, 0.5, 0.5, 1)
            lbl = Label(text=f"${prize}", font_size=22, color=color, size_hint_y=None, height=30)
            ladder_layout.add_widget(lbl)

        layout.add_widget(ladder_layout)

        # Continue button
        btn = RoundedButton(text="Continue", size_hint=(0.5, None), height=50, pos_hint={"center_x":0.5})
        btn.bind(on_release=self.continue_quiz)
        layout.add_widget(btn)
        self.add_widget(layout)

    def continue_quiz(self, instance):
        if self.quiz_screen:

            # ✅ STOP TIMER BEFORE MOVING
            if self.quiz_screen.timer_event:
                self.quiz_screen.timer_event.cancel()
            self.quiz_screen.timer_event = None
            self.quiz_screen.timer_running = False

            
            # Increment current question and show it
            self.quiz_screen.current += 1

            if self.quiz_screen.current >= len(self.quiz_screen.questions):
                self.manager.current = 'win'
            else:
                self.manager.current = 'quiz'
                self.quiz_screen.show_question()

    
# ---------------- SCORE ----------------
class ScoreScreen(Screen):
    money = 0
    def on_enter(self):
        self.clear_widgets()
        add_background(self)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        layout.add_widget(Label(text="You Finished!", font_size=30))
        layout.add_widget(Label(text=f"Total Money: ${self.money}", font_size=25))
        btn = RoundedButton(text="Home")
        btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        layout.add_widget(btn)
        self.add_widget(layout)


    # ---------------- WIN SCREEN (NEW) ----------------
class WinScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        add_background(self)

        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        # Top home button
        top = BoxLayout(size_hint_y=None, height=50)
        home_btn = RoundedButton(text="Home", size_hint=(None, None), size=(100, 40))
        home_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        top.add_widget(home_btn)

        layout.add_widget(top)

        # Message
        layout.add_widget(Label(text="Great Job!\nYou have won $1000000",
                                font_size=30))

        self.add_widget(layout)



# ---------------- APP ----------------
class FortuneIQApp(App):
    def build(self):    
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(SubjectScreen(name='subject'))
        sm.add_widget(QuizScreen(name='quiz'))
        sm.add_widget(MoneyLadderScreen(name='ladder'))
        sm.add_widget(ScoreScreen(name='score'))
        sm.add_widget(WinScreen(name='win'))
        return sm

if __name__ == '__main__':
    FortuneIQApp().run()
