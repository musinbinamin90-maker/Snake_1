from kivy.config import Config

# Настройки окна
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

import copy
import math
from math import atan2, cos, degrees, radians, sin
import random
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    Mesh,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Rotate,
    RoundedRectangle,
    Triangle,
)
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget

GRID = 20
MOVE_INTERVAL = 0.14


class ArrowButton(Button):
  """Кнопка со стрелкой, нарисованной через Canvas"""

  def __init__(self, direction='up', **kwargs):
    super().__init__(**kwargs)
    self.direction = direction
    self.bind(pos=self._update_arrow, size=self._update_arrow)

  def _update_arrow(self, *args):
    self.canvas.after.clear()
    with self.canvas.after:
      Color(1, 1, 1, 1)
      cx, cy = self.center_x, self.center_y
      s = dp(10)

      if self.direction == 'up':
        Triangle(points=[cx - s, cy - s, cx + s, cy - s, cx, cy + s])
      elif self.direction == 'down':
        Triangle(points=[cx - s, cy + s, cx + s, cy + s, cx, cy - s])
      elif self.direction == 'left':
        Triangle(points=[cx + s, cy - s, cx + s, cy + s, cx - s, cy])
      elif self.direction == 'right':
        Triangle(points=[cx - s, cy - s, cx - s, cy + s, cx + s, cy])


class SnakeBoard(Widget):
  score = NumericProperty(0)
  losses = NumericProperty(0)
  game_over = BooleanProperty(False)
  is_paused = BooleanProperty(True)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.snake = [(10, 10), (9, 10), (8, 10)]
    self.old_tail = (7, 10)
    self.direction = (1, 0)
    self.next_direction = (1, 0)
    self.food = None
    self._anim_t = 0
    self.move_progress = 1.0

    self.curr_eye_r = 4.5
    self.curr_pupil_r = 1.8
    self.curr_pupil_offset_x = 0.0
    self.curr_pupil_offset_y = 0.0

    self.saved_state = None

    self.eat_sound = None
    self.over_sound = None
    Clock.schedule_once(self._load_sounds, 0)

    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_interval(self.logic_update, MOVE_INTERVAL)
    Clock.schedule_interval(self.frame_update, 1 / 60)

  def _load_sounds(self, dt):
    try:
      self.eat_sound = SoundLoader.load('eat.wav')
      self.over_sound = SoundLoader.load('gameover.wav')
    except Exception:
      pass

  def save_current_state(self):
    self.saved_state = {
        'snake': copy.deepcopy(self.snake),
        'old_tail': self.old_tail,
        'direction': self.direction,
        'next_direction': self.next_direction,
        'food': self.food,
        'score': self.score,
        'losses': self.losses,
    }
    app = App.get_running_app()
    if hasattr(app, 'menu_screen'):
      app.menu_screen.update_continue_button()

  def load_saved_state(self):
    if self.saved_state:
      self.snake = copy.deepcopy(self.saved_state['snake'])
      self.old_tail = self.saved_state['old_tail']
      self.direction = self.saved_state['direction']
      self.next_direction = self.saved_state['next_direction']
      self.food = self.saved_state['food']
      self.score = self.saved_state['score']
      self.losses = self.saved_state['losses']
      self.game_over = False
      self.is_paused = False
      self.move_progress = 1.0
      self.redraw()
      return True
    return False

  def toggle_pause(self):
    if not self.game_over:
      self.is_paused = not self.is_paused
      self.redraw()
      if self.is_paused:
        App.get_running_app().show_pause_menu()

  def pause_game(self):
    self.is_paused = True
    self.redraw()

  def on_size(self, *args):
    self.redraw()

  def frame_update(self, dt):
    if self.is_paused or self.game_over:
      return

    self._anim_t += dt

    if self.move_progress < 1.0:
      self.move_progress += dt / MOVE_INTERVAL
      if self.move_progress > 1.0:
        self.move_progress = 1.0

    near_food = False
    target_look_dx, target_look_dy = self.direction

    if self.food:
      head_x, head_y = self.snake[0]
      food_x, food_y = self.food
      steps = abs(head_x - food_x) + abs(head_y - food_y)

      if steps <= 5:
        near_food = True
        diff_x = food_x - head_x
        diff_y = food_y - head_y
        target_look_dx = 1 if diff_x > 0 else (-1 if diff_x < 0 else 0)
        target_look_dy = 1 if diff_y > 0 else (-1 if diff_y < 0 else 0)

    target_eye_r = 5.5 if near_food else 4.5
    target_pupil_r = 2.2 if near_food else 1.8
    target_shift = 1.2 if near_food else 0.8
    target_offset_x = target_look_dx * target_shift
    target_offset_y = target_look_dy * target_shift

    anim_speed = 12.0 if near_food else 4.5

    self.curr_eye_r += (target_eye_r - self.curr_eye_r) * anim_speed * dt
    self.curr_pupil_r += (target_pupil_r - self.curr_pupil_r) * anim_speed * dt
    self.curr_pupil_offset_x += (
        target_offset_x - self.curr_pupil_offset_x
    ) * anim_speed * dt
    self.curr_pupil_offset_y += (
        target_offset_y - self.curr_pupil_offset_y
    ) * anim_speed * dt

    self.redraw()

  def restart(self):
    self.score = 0
    self.game_over = False
    self.is_paused = False
    self.direction = (1, 0)
    self.next_direction = (1, 0)
    self.snake = [(10, 10), (9, 10), (8, 10)]
    self.old_tail = (7, 10)
    self.move_progress = 1.0
    self.food = None
    self.curr_eye_r = 4.5
    self.curr_pupil_r = 1.8
    self.curr_pupil_offset_x = 0.0
    self.curr_pupil_offset_y = 0.0
    self.spawn_food()
    self.redraw()

  def spawn_food(self):
    cols = max(5, int(self.width // GRID))
    rows = max(5, int(self.height // GRID))
    empty = [
        (x, y)
        for x in range(cols)
        for y in range(rows)
        if (x, y) not in self.snake
    ]
    self.food = random.choice(empty) if empty else None

  def set_direction(self, dx, dy):
    if self.is_paused:
      return
    if (dx, dy) == (-self.direction[0], -self.direction[1]):
      return
    self.next_direction = (dx, dy)

  def logic_update(self, dt):
    if (
        self.game_over
        or self.is_paused
        or self.width <= GRID * 2
        or self.height <= GRID * 2
    ):
      return

    self.direction = self.next_direction
    head_x, head_y = self.snake[0]
    dx, dy = self.direction
    new_head = (head_x + dx, head_y + dy)

    cols = max(5, int(self.width // GRID))
    rows = max(5, int(self.height // GRID))

    if (
        new_head[0] < 0
        or new_head[1] < 0
        or new_head[0] >= cols
        or new_head[1] >= rows
    ):
      self.finish_game()
      return

    if new_head in self.snake:
      self.finish_game()
      return

    self.snake.insert(0, new_head)

    if self.food and new_head == self.food:
      self.score += 1
      if self.eat_sound:
        try:
          self.eat_sound.stop()
          self.eat_sound.play()
        except Exception:
          pass
      self.spawn_food()
      self.old_tail = self.snake[-1]
    else:
      self.old_tail = self.snake.pop()

    self.move_progress = 0.0

  def finish_game(self):
    self.game_over = True
    self.losses += 1
    self.saved_state = None

    if self.over_sound:
      try:
        self.over_sound.stop()
        self.over_sound.play()
      except Exception:
        pass
    self.redraw()

  def cell_center(self, x, y):
    return self.x + x * GRID + GRID / 2, self.y + y * GRID + GRID / 2

  def get_snake_geometry(self):
    if len(self.snake) < 2:
      return [], []

    centers = [self.cell_center(x, y) for x, y in self.snake]

    h_target = centers[0]
    h_neck = centers[1]
    hx = h_neck[0] + (h_target[0] - h_neck[0]) * self.move_progress
    hy = h_neck[1] + (h_target[1] - h_neck[1]) * self.move_progress

    t_curr = centers[-1]
    t_old = self.cell_center(self.old_tail[0], self.old_tail[1])
    tx = t_old[0] + (t_curr[0] - t_old[0]) * self.move_progress
    ty = t_old[1] + (t_curr[1] - t_old[1]) * self.move_progress

    line_path = [(hx, hy)]
    line_path.extend(centers[1:])
    line_path.append((tx, ty))

    joint_centers = centers[1:]

    return line_path, joint_centers

  def redraw(self, *args):
    self.canvas.clear()
    cols = int(self.width // GRID)
    rows = int(self.height // GRID)

    with self.canvas:
      # Фон
      for i in range(cols):
        for j in range(rows):
          px = self.x + i * GRID
          py = self.y + j * GRID
          if (i + j) % 2 == 0:
            Color(0.20, 0.38, 0.18, 1)
          else:
            Color(0.25, 0.45, 0.22, 1)
          Rectangle(pos=(px, py), size=(GRID, GRID))

      # ==========================================
      #  ЕDA: КРАСИВОЕ ЯБЛОКО
      # ==========================================
      if self.food:
        fx, fy = self.food
        cx, cy = self.cell_center(fx, fy)

        # 1. Форма яблока
        Color(0.95, 0.15, 0.15, 1)
        r = GRID * 0.38
        Ellipse(pos=(cx - r * 0.9, cy - r * 0.8), size=(r * 1.3, r * 1.4))
        Ellipse(pos=(cx - r * 0.4, cy - r * 0.8), size=(r * 1.3, r * 1.4))

        # 2. Блик
        Color(1.0, 0.6, 0.6, 0.8)
        Ellipse(
            pos=(cx - r * 0.5, cy + r * 0.1), size=(r * 0.4, r * 0.4)
        )

        # 3. Черенок
        Color(0.4, 0.2, 0.05, 1)
        Line(points=[cx, cy + r * 0.3, cx + 2, cy + r * 0.8], width=1.5)

        # 4. Листик
        Color(0.2, 0.8, 0.2, 1)
        Ellipse(pos=(cx + 1, cy + r * 0.6), size=(r * 0.6, r * 0.3))

      path, joint_centers = self.get_snake_geometry()

      if path and len(path) >= 2:
        snake_width = GRID * 0.42
        snake_radius = snake_width / 2

        # Тело змейки
        Color(0.28, 0.88, 0.35, 1)
        for cx_j, cy_j in joint_centers:
          Ellipse(
              pos=(cx_j - snake_radius, cy_j - snake_radius),
              size=(snake_width, snake_width),
          )

        flat_coords = []
        for pt in path:
          flat_coords.extend([pt[0], pt[1]])

        Line(
            points=flat_coords,
            width=snake_width,
            cap='round',
            joint='round',
        )

        # ==========================================
        #  ГОЛОВА ЗМЕЙКИ
        # ==========================================
        hx, hy = path[0][0], path[0][1]
        dx, dy = self.direction
        angle = degrees(atan2(dy, dx))

        PushMatrix()
        Rotate(angle=angle, origin=(hx, hy))

        # 1. Тёмная подложка-контур головы
        Color(0.12, 0.40, 0.10, 1)
        Ellipse(pos=(hx - 6, hy - 11), size=(18, 22))
        Ellipse(pos=(hx + 2, hy - 7), size=(12, 14))

        # 2. Основная закраска головы
        Color(0.22, 0.68, 0.18, 1)
        Ellipse(pos=(hx - 5, hy - 10), size=(16, 20))
        Ellipse(pos=(hx + 3, hy - 6), size=(10, 12))

        # 3. Салатовые надбровные выпуклости
        Color(0.40, 0.85, 0.20, 1)
        Ellipse(pos=(hx - 2, hy + 4), size=(10, 6))
        Ellipse(pos=(hx - 2, hy - 10), size=(10, 6))

        # 4. Жёлтый узор у основания головы
        Color(0.95, 0.85, 0.15, 1)
        Ellipse(pos=(hx - 5, hy - 2.5), size=(5, 5))
        Ellipse(pos=(hx - 2, hy - 5.5), size=(4, 4))
        Ellipse(pos=(hx - 2, hy + 1.5), size=(4, 4))

        # 5. Глаза
        eye_r = self.curr_eye_r
        pupil_r = self.curr_pupil_r

        Color(0.98, 0.95, 0.70, 1)
        Ellipse(
            pos=(hx - eye_r, hy + 6 - eye_r), size=(eye_r * 2.2, eye_r * 2.2)
        )
        Ellipse(
            pos=(hx - eye_r, hy - 6 - eye_r), size=(eye_r * 2.2, eye_r * 2.2)
        )

        Color(0.1, 0.25, 0.1, 1)
        Line(
            ellipse=(hx - eye_r, hy + 6 - eye_r, eye_r * 2.2, eye_r * 2.2),
            width=1.2,
        )
        Line(
            ellipse=(hx - eye_r, hy - 6 - eye_r, eye_r * 2.2, eye_r * 2.2),
            width=1.2,
        )

        Color(0.05, 0.05, 0.05, 1)
        Ellipse(
            pos=(
                hx - pupil_r + 1 + self.curr_pupil_offset_x,
                hy + 6 - pupil_r + self.curr_pupil_offset_y,
            ),
            size=(pupil_r * 2, pupil_r * 2),
        )
        Ellipse(
            pos=(
                hx - pupil_r + 1 + self.curr_pupil_offset_x,
                hy - 6 - pupil_r + self.curr_pupil_offset_y,
            ),
            size=(pupil_r * 2, pupil_r * 2),
        )

        # 6. Анимированный язык
        tongue_wiggle = sin(self._anim_t * 18) * 2.5

        Color(0.85, 0.20, 0.20, 0.95)
        Line(
            points=[
                hx + 11,
                hy,
                hx + 16,
                hy + tongue_wiggle * 0.5,
                hx + 19,
                hy + tongue_wiggle + 2.5,
                hx + 16,
                hy + tongue_wiggle * 0.5,
                hx + 19,
                hy + tongue_wiggle - 2.5,
            ],
            width=1.4,
        )

        PopMatrix()

    if self.is_paused and not self.game_over:
      with self.canvas:
        Color(0, 0, 0, 0.4)
        Rectangle(pos=self.pos, size=self.size)

    if self.game_over and self.parent:
      self.show_game_over()

  def show_game_over(self):
    if getattr(self, '_game_over_shown', False):
      return
    self._game_over_shown = True

    view = ModalView(
        size_hint=(None, None),
        size=(dp(310), dp(240)),
        background='',
        background_color=(0, 0, 0, 0.7),
        auto_dismiss=False,
    )

    box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

    def update_card_bg(instance, value):
      instance.canvas.before.clear()
      with instance.canvas.before:
        Color(0.12, 0.15, 0.22, 1)
        RoundedRectangle(pos=instance.pos, size=instance.size, radius=[18])

    box.bind(pos=update_card_bg, size=update_card_bg)

    title = Label(
        text='ВЫ ПРОИГРАЛИ!',
        font_size=dp(22),
        bold=True,
        color=(1, 0.35, 0.35, 1),
    )
    text = Label(
        text=f'Счёт: {self.score}\nВсего проигрышей: {self.losses}',
        font_size=dp(16),
        color=(0.9, 0.9, 0.9, 1),
        halign='center',
    )

    btn_restart = Button(
        text='Начать заново',
        size_hint_y=None,
        height=dp(40),
        background_color=(0.18, 0.65, 0.35, 1),
    )
    btn_menu = Button(
        text='Вернуться в меню',
        size_hint_y=None,
        height=dp(40),
        background_color=(0.3, 0.3, 0.4, 1),
    )

    btn_restart.bind(
        on_release=lambda *_: (view.dismiss(), self.reset_after_over())
    )
    btn_menu.bind(
        on_release=lambda *_: (
            view.dismiss(),
            self.reset_after_over(),
            App.get_running_app().open_menu(),
        )
    )

    box.add_widget(title)
    box.add_widget(text)
    box.add_widget(btn_restart)
    box.add_widget(btn_menu)
    view.add_widget(box)
    view.open()

  def reset_after_over(self):
    self._game_over_shown = False
    self.restart()


class MenuScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)

    root = FloatLayout()

    with root.canvas.before:
      try:
        self.bg_rect = Rectangle(
            source='menu_bg.jpeg', pos=self.pos, size=self.size
        )
      except Exception:
        pass

    root.bind(pos=self._update_bg, size=self._update_bg)

    layout = BoxLayout(
        orientation='vertical',
        padding=[dp(30), dp(50), dp(30), dp(40)],
        spacing=dp(15),
        pos_hint={'x': 0, 'y': 0},
        size_hint=(1, 1),
    )

    # ИСПРАВЛЕННЫЙ СТИЛЬНЫЙ ЗАГОЛОВОК С ОБЪЕМНОЙ ТЕНЬЮ И БЕЛОЙ ОБВОДКОЙ
    title_box = RelativeLayout(size_hint_y=0.25)

    shadow_title = Label(
        text=' З М Е Й К А ',
        font_size=dp(38),
        bold=True,
        italic=True,
        color=(0.05, 0.15, 0.05, 0.6),
        pos_hint={'center_x': 0.51, 'center_y': 0.48},
    )

    main_title = Label(
        text=' З М Е Й К А ',
        font_size=dp(38),
        bold=True,
        italic=True,
        color=(0.35, 1, 0.45, 1),
        outline_width=2.5,
        outline_color=(1, 1, 1, 1),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
    )

    title_box.add_widget(shadow_title)
    title_box.add_widget(main_title)
    layout.add_widget(title_box)

    btn_style = {
        'size_hint_y': None,
        'height': dp(52),
        'font_size': dp(18),
        'bold': True,
        'background_normal': '',
        'background_color': (0.08, 0.12, 0.18, 0.85),
        'color': (1, 1, 1, 1),
    }

    self.btn_play = Button(text='Играть', **btn_style)
    self.btn_continue = Button(text='Продолжить начатое', **btn_style)
    self.btn_exit = Button(text='Выйти', **btn_style)

    self.btn_play.bind(on_release=self.start_new_game)
    self.btn_continue.bind(on_release=self.continue_game)
    self.btn_exit.bind(on_release=lambda *_: App.get_running_app().stop())

    layout.add_widget(self.btn_play)
    layout.add_widget(self.btn_continue)
    layout.add_widget(self.btn_exit)

    root.add_widget(layout)
    self.add_widget(root)

  def on_pre_enter(self, *args):
    self.update_continue_button()

  def update_continue_button(self):
    app = App.get_running_app()
    if (
        hasattr(app, 'game_screen')
        and app.game_screen.board
        and app.game_screen.board.saved_state
    ):
      self.btn_continue.disabled = False
      self.btn_continue.opacity = 1.0
      self.btn_continue.height = dp(52)
    else:
      self.btn_continue.disabled = True
      self.btn_continue.opacity = 0.0
      self.btn_continue.height = 0

  def _update_bg(self, instance, value):
    if hasattr(self, 'bg_rect'):
      self.bg_rect.pos = instance.pos
      self.bg_rect.size = instance.size

  def start_new_game(self, *args):
    app = App.get_running_app()
    app.game_screen.board.restart()
    app.sm.current = 'game'

  def continue_game(self, *args):
    app = App.get_running_app()
    board = app.game_screen.board

    if board.saved_state:
      board.load_saved_state()

    board.is_paused = False
    app.sm.current = 'game'


class GameScreen(Screen):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    main = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

    top = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
    self.score_label = Label(
        text='Счёт: 0', font_size=dp(22), color=(1, 1, 1, 1), size_hint_x=0.5
    )
    self.losses_label = Label(
        text='Проигрышей: 0',
        font_size=dp(20),
        color=(1, 0.4, 0.4, 1),
        size_hint_x=0.5,
    )
    top.add_widget(self.score_label)
    top.add_widget(self.losses_label)

    board_container = RelativeLayout(size_hint=(1, 1))
    self.board = SnakeBoard(pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
    self.board.bind(score=self.on_score, losses=self.on_losses)

    board_container.add_widget(self.board)

    controls_wrapper = FloatLayout(size_hint_y=None, height=dp(180))
    controls = GridLayout(
        cols=3,
        rows=3,
        size_hint=(None, None),
        size=(dp(240), dp(170)),
        spacing=dp(6),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
    )

    btn_style = {'background_color': (0.18, 0.22, 0.30, 1)}

    up = ArrowButton(direction='up', **btn_style)
    down = ArrowButton(direction='down', **btn_style)
    left_btn = ArrowButton(direction='left', **btn_style)
    right_btn = ArrowButton(direction='right', **btn_style)

    pause_btn = Button(
        text='||',
        background_color=(0.20, 0.60, 0.35, 1),
        color=(1, 1, 1, 1),
        font_size=dp(22),
        bold=True,
    )

    up.bind(on_release=lambda *_: self.board.set_direction(0, 1))
    down.bind(on_release=lambda *_: self.board.set_direction(0, -1))
    left_btn.bind(on_release=lambda *_: self.board.set_direction(-1, 0))
    right_btn.bind(on_release=lambda *_: self.board.set_direction(1, 0))
    pause_btn.bind(on_release=lambda *_: self.board.toggle_pause())

    controls.add_widget(Widget())
    controls.add_widget(up)
    controls.add_widget(Widget())

    controls.add_widget(left_btn)
    controls.add_widget(pause_btn)
    controls.add_widget(right_btn)

    controls.add_widget(Widget())
    controls.add_widget(down)
    controls.add_widget(Widget())

    controls_wrapper.add_widget(controls)

    main.add_widget(top)
    main.add_widget(board_container)
    main.add_widget(controls_wrapper)

    self.add_widget(main)

  def on_score(self, instance, value):
    self.score_label.text = f'Счёт: {value}'

  def on_losses(self, instance, value):
    self.losses_label.text = f'Проигрышей: {value}'


class SnakeApp(App):

  def build(self):
    self.sm = ScreenManager()

    self.menu_screen = MenuScreen(name='menu')
    self.game_screen = GameScreen(name='game')

    self.sm.add_widget(self.menu_screen)
    self.sm.add_widget(self.game_screen)

    Window.bind(on_key_down=self.on_keyboard)

    self.pause_view = None
    return self.sm

  def open_menu(self):
    self.game_screen.board.pause_game()
    self.sm.current = 'menu'

  def show_pause_menu(self):
    if self.pause_view:
      return

    self.pause_view = ModalView(
        size_hint=(None, None),
        size=(dp(310), dp(270)),
        background='',
        background_color=(0, 0, 0, 0.7),
        auto_dismiss=False,
    )

    box = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))

    def update_card_bg(instance, value):
      instance.canvas.before.clear()
      with instance.canvas.before:
        Color(0.12, 0.15, 0.22, 1)
        RoundedRectangle(pos=instance.pos, size=instance.size, radius=[16])

    box.bind(pos=update_card_bg, size=update_card_bg)

    title = Label(
        text='ПАУЗА',
        font_size=dp(20),
        bold=True,
        color=(1, 1, 1, 1),
        size_hint_y=0.2,
    )

    btn_style = {
        'size_hint_y': None,
        'height': dp(38),
        'font_size': dp(14),
        'bold': True,
    }

    btn_resume = Button(
        text='Продолжить играть',
        background_color=(0.18, 0.65, 0.35, 1),
        **btn_style,
    )
    btn_save_and_menu = Button(
        text='Сохранить и вернуться в меню',
        background_color=(0.2, 0.5, 0.7, 1),
        **btn_style,
    )
    btn_menu_only = Button(
        text='Вернуться в меню',
        background_color=(0.3, 0.3, 0.4, 1),
        **btn_style,
    )
    btn_save_only = Button(
        text='Сохранить', background_color=(0.8, 0.5, 0.2, 1), **btn_style
    )

    def resume_action(*args):
      self.pause_view.dismiss()
      self.pause_view = None
      if self.game_screen.board.is_paused:
        self.game_screen.board.toggle_pause()

    def save_and_menu_action(*args):
      self.game_screen.board.save_current_state()
      self.pause_view.dismiss()
      self.pause_view = None
      self.open_menu()

    def menu_only_action(*args):
      board = self.game_screen.board
      if board.saved_state:
        board.load_saved_state()
      else:
        board.restart()

      self.pause_view.dismiss()
      self.pause_view = None
      self.open_menu()

    def save_only_action(*args):
      self.game_screen.board.save_current_state()
      self.pause_view.dismiss()
      self.pause_view = None
      if self.game_screen.board.is_paused:
        self.game_screen.board.toggle_pause()

    btn_resume.bind(on_release=resume_action)
    btn_save_and_menu.bind(on_release=save_and_menu_action)
    btn_menu_only.bind(on_release=menu_only_action)
    btn_save_only.bind(on_release=save_only_action)

    box.add_widget(title)
    box.add_widget(btn_resume)
    box.add_widget(btn_save_and_menu)
    box.add_widget(btn_menu_only)
    box.add_widget(btn_save_only)

    self.pause_view.add_widget(box)
    self.pause_view.open()

  def on_keyboard(self, window, key, scancode, codepoint, modifier):
    if self.sm.current == 'game':
      board = self.game_screen.board
      if key == 32:
        board.toggle_pause()
      elif key == 273 or codepoint == 'w':
        board.set_direction(0, 1)
      elif key == 274 or codepoint == 's':
        board.set_direction(0, -1)
      elif key == 276 or codepoint == 'a':
        board.set_direction(-1, 0)
      elif key == 275 or codepoint == 'd':
        board.set_direction(1, 0)


if __name__ == '__main__':
  SnakeApp().run()

