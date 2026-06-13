import pygame
import sys
import pyperclip
from core import (
    Vault,
    generate_passwd,
    check_passwd_strength,
)

pygame.init()

BG_DEEP = (24, 24, 38)
BG_CARD = (36, 36, 54)
FG_WHITE = (230, 230, 240)
FG_DIM = (140, 140, 160)
ACCENT_BLUE = (100, 140, 255)
ACCENT_HOVER = (130, 165, 255)
RED = (255, 70, 85)
GREEN = (80, 200, 120)
YELLOW = (255, 200, 50)
WHITE = (255, 255, 255)

WIDTH = 900
HEIGHT = 650
MIN_WIDTH = 700
MIN_HEIGHT = 500
FPS = 30


def get_font(size, bold=False):
    name = "Segoe UI" if sys.platform == "win32" else "Arial"
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


FONT_TITLE = get_font(36, bold=True)
FONT_HEADING = get_font(24, bold=True)
FONT_BODY = get_font(18)
FONT_SMALL = get_font(14)
FONT_MONO = pygame.font.SysFont("Consolas", 18) if sys.platform == "win32" else get_font(18)


class TextInput:
    def __init__(self, x, y, w, h, placeholder="", password=False, font=FONT_BODY):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.password = password
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor = 0
        self.sel_anchor = None
        self.font = font

    def _display_string(self):
        if self.password:
            return "•" * len(self.text)
        return self.text

    def _selection_range(self):
        if self.sel_anchor is None:
            return None
        lo = min(self.sel_anchor, self.cursor)
        hi = max(self.sel_anchor, self.cursor)
        if lo == hi:
            return None
        return lo, hi

    def _reset_blink(self):
        self.cursor_visible = True
        self.cursor_timer = 0

    def _delete_selection(self):
        rng = self._selection_range()
        if rng is None:
            return False
        lo, hi = rng
        self.text = self.text[:lo] + self.text[hi:]
        self.cursor = lo
        self.sel_anchor = None
        return True

    def _index_from_x(self, mouse_x):
        display = self._display_string()
        rel = mouse_x - (self.rect.x + 8)
        best_i = 0
        best_dist = abs(rel)
        for i in range(1, len(display) + 1):
            x = self.font.size(display[:i])[0]
            dist = abs(rel - x)
            if dist < best_dist:
                best_dist = dist
                best_i = i
        return best_i

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            if self.active:
                self.cursor = self._index_from_x(event.pos[0])
                self.sel_anchor = None
                self._reset_blink()
        if event.type == pygame.KEYDOWN and self.active:
            ctrl = event.mod & pygame.KMOD_CTRL
            shift = event.mod & pygame.KMOD_SHIFT
            if event.key == pygame.K_a and ctrl:
                self.sel_anchor = 0
                self.cursor = len(self.text)
            elif event.key == pygame.K_c and ctrl:
                rng = self._selection_range()
                if rng is None:
                    copied = self.text
                else:
                    lo, hi = rng
                    copied = self.text[lo:hi]
                try:
                    pyperclip.copy(copied)
                except pyperclip.PyperclipException:
                    pass
            elif event.key == pygame.K_v and ctrl:
                try:
                    pasted = pyperclip.paste()
                except pyperclip.PyperclipException:
                    pasted = ""
                if pasted:
                    self._delete_selection()
                    self.text = self.text[:self.cursor] + pasted + self.text[self.cursor:]
                    self.cursor += len(pasted)
                    self.sel_anchor = None
            elif event.key == pygame.K_LEFT:
                if shift:
                    if self.sel_anchor is None:
                        self.sel_anchor = self.cursor
                    self.cursor = max(0, self.cursor - 1)
                else:
                    self.cursor = max(0, self.cursor - 1)
                    self.sel_anchor = None
            elif event.key == pygame.K_RIGHT:
                if shift:
                    if self.sel_anchor is None:
                        self.sel_anchor = self.cursor
                    self.cursor = min(len(self.text), self.cursor + 1)
                else:
                    self.cursor = min(len(self.text), self.cursor + 1)
                    self.sel_anchor = None
            elif event.key == pygame.K_HOME:
                self.cursor = 0
                self.sel_anchor = None
            elif event.key == pygame.K_END:
                self.cursor = len(self.text)
                self.sel_anchor = None
            elif event.key == pygame.K_BACKSPACE:
                if not self._delete_selection():
                    if self.cursor > 0:
                        self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                        self.cursor -= 1
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                if event.unicode.isprintable() and event.unicode:
                    self._delete_selection()
                    self.text = self.text[:self.cursor] + event.unicode + self.text[self.cursor:]
                    self.cursor += 1
                    self.sel_anchor = None
            self.cursor = max(0, min(self.cursor, len(self.text)))
            self._reset_blink()

    def update(self):
        if self.active:
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_timer = 0
                self.cursor_visible = not self.cursor_visible
        else:
            self.cursor_visible = False

    def draw(self, surface):
        color = BG_CARD if not self.active else (50, 50, 70)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, ACCENT_BLUE if self.active else FG_DIM, self.rect, 2, border_radius=8)

        display = self._display_string()
        if not self.text and not self.active:
            text_surf = self.font.render(self.placeholder, True, FG_DIM)
        else:
            text_surf = self.font.render(display, True, FG_WHITE)

        clip = surface.get_clip()
        surface.set_clip(self.rect)
        text_y = self.rect.y + (self.rect.h - text_surf.get_height()) // 2

        rng = self._selection_range()
        if self.active and rng is not None:
            lo, hi = rng
            x1 = self.rect.x + 8 + self.font.size(display[:lo])[0]
            x2 = self.rect.x + 8 + self.font.size(display[:hi])[0]
            sel_rect = pygame.Rect(x1, self.rect.y + 6, x2 - x1, self.rect.h - 12)
            pygame.draw.rect(surface, ACCENT_BLUE, sel_rect)

        if self.text or self.active:
            surface.blit(text_surf, (self.rect.x + 8, text_y))
        else:
            surface.blit(text_surf, (self.rect.x + 8, text_y))

        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 8 + self.font.size(display[:self.cursor])[0]
            pygame.draw.line(surface, FG_WHITE,
                             (cursor_x, self.rect.y + 8),
                             (cursor_x, self.rect.y + self.rect.h - 8), 2)
        surface.set_clip(clip)

    def get_text(self):
        return self.text

    def clear(self):
        self.text = ""
        self.active = False
        self.cursor = 0
        self.sel_anchor = None

    def toggle_password_visibility(self):
        self.password = not self.password


class ToggleButton:
    def __init__(self, x, y, w, h, text, active=True, font=FONT_SMALL):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = active
        self.hover = False
        self.font = font

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.active = not self.active

    def draw(self, surface):
        if self.active:
            color = ACCENT_HOVER if self.hover else ACCENT_BLUE
            text_color = WHITE
        else:
            color = (60, 60, 80) if self.hover else BG_CARD
            text_color = FG_DIM
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, ACCENT_BLUE if self.active else FG_DIM, self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, text_color)
        surface.blit(text_surf, (self.rect.x + (self.rect.width - text_surf.get_width()) // 2,
                                 self.rect.y + (self.rect.height - text_surf.get_height()) // 2))

    def reset_hover(self):
        self.hover = False


class Button:
    def __init__(self, x, y, w, h, text, color=ACCENT_BLUE, text_color=WHITE, callback=None, font=FONT_BODY):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = ACCENT_HOVER
        self.text_color = text_color
        self.callback = callback
        self.hover = False
        self.click_scale = 1.0
        self.font = font

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.click_scale = 0.95
            if self.callback:
                self.callback()
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.click_scale = 1.0

    def draw(self, surface):
        w = int(self.rect.width * self.click_scale)
        h = int(self.rect.height * self.click_scale)
        x = self.rect.x + (self.rect.width - w) // 2
        y = self.rect.y + (self.rect.height - h) // 2
        color = self.hover_color if self.hover else self.color
        pygame.draw.rect(surface, color, (x, y, w, h), border_radius=10)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, (x + (w - text_surf.get_width()) // 2,
                                 y + (h - text_surf.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def reset_hover(self):
        self.hover = False


class Slider:
    def __init__(self, x, y, w, min_val=4, max_val=32, init_val=16):
        self.rect = pygame.Rect(x, y, w, 16)
        self.handle_rect = pygame.Rect(0, 0, 20, 28)
        self.min = min_val
        self.max = max_val
        self.value = init_val
        self.dragging = False
        self.update_handle_pos()
        self.label_font = FONT_SMALL

    def update_handle_pos(self):
        ratio = (self.value - self.min) / (self.max - self.min)
        x = self.rect.x + int(ratio * (self.rect.width - self.handle_rect.width))
        self.handle_rect.centerx = x + self.handle_rect.width // 2
        self.handle_rect.centery = self.rect.centery

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
            elif self.rect.collidepoint(event.pos):
                self.dragging = True
                self._set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0])

    def _set_from_mouse(self, mouse_x):
        rel_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
        ratio = (rel_x - self.rect.x) / self.rect.width
        self.value = int(self.min + ratio * (self.max - self.min))
        self.value = max(self.min, min(self.max, self.value))
        self.update_handle_pos()

    def draw(self, surface):
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=8)
        filled_w = int(self.rect.width * (self.value - self.min) / (self.max - self.min))
        if filled_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, filled_w, self.rect.height)
            pygame.draw.rect(surface, ACCENT_BLUE, fill_rect, border_radius=8)
        handle_color = ACCENT_HOVER if self.dragging else ACCENT_BLUE
        pygame.draw.rect(surface, handle_color, self.handle_rect, border_radius=6)
        pygame.draw.rect(surface, WHITE, self.handle_rect, 2, border_radius=6)
        percent = int((self.value - self.min) / (self.max - self.min) * 100)
        label = self.label_font.render(f"{self.value} ({percent}%)", True, FG_WHITE)
        surface.blit(label, (self.rect.x + self.rect.width + 12, self.rect.y - 4))


class StrengthMeter:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.percentage = 0
        self.label_font = FONT_SMALL

    def set_value(self, percent):
        self.percentage = max(0, min(100, percent))

    def draw(self, surface):
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=4)
        if self.percentage > 0:
            fill_w = int(self.rect.width * self.percentage / 100)
            if self.percentage < 50:
                r = 255
                g = int(255 * (self.percentage / 50))
            else:
                r = int(255 * (1 - (self.percentage - 50) / 50))
                g = 255
            color = (r, g, 50)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(surface, color, fill_rect, border_radius=4)
        pygame.draw.rect(surface, FG_DIM, self.rect, 1, border_radius=4)
        label = self.label_font.render(f"{self.percentage}%", True, FG_WHITE)
        surface.blit(label, (self.rect.x + self.rect.width + 12, self.rect.y - 2))


class ScrollableList:
    def __init__(self, x, y, w, h, item_height=35, body_font=FONT_BODY, mono_font=FONT_MONO):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = []
        self.item_height = item_height
        self.scroll = 0
        self.scrollbar_dragging = False
        self.body_font = body_font
        self.mono_font = mono_font

    def set_items(self, items):
        self.items = items
        self.scroll = 0
        self._clamp_scroll()

    def _clamp_scroll(self):
        total_h = len(self.items) * self.item_height
        max_scroll = max(0, total_h - self.rect.height)
        self.scroll = max(0, min(self.scroll, max_scroll))

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 30
            self._clamp_scroll()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                total_h = len(self.items) * self.item_height
                if total_h > self.rect.height:
                    bar_rect = self._scrollbar_rect()
                    if bar_rect.collidepoint(event.pos):
                        self.scrollbar_dragging = True
                        self._scrollbar_move(event.pos[1])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.scrollbar_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.scrollbar_dragging:
            self._scrollbar_move(event.pos[1])

    def _scrollbar_rect(self):
        total_h = len(self.items) * self.item_height
        if total_h <= self.rect.height:
            return pygame.Rect(0, 0, 0, 0)
        bar_h = max(20, self.rect.height * self.rect.height / total_h)
        scrollable = total_h - self.rect.height
        scroll_ratio = self.scroll / scrollable if scrollable else 0
        bar_y = self.rect.y + scroll_ratio * (self.rect.height - bar_h)
        return pygame.Rect(self.rect.x + self.rect.width - 8, bar_y, 8, bar_h)

    def _scrollbar_move(self, mouse_y):
        total_h = len(self.items) * self.item_height
        if total_h <= self.rect.height:
            return
        bar_h = max(20, self.rect.height * self.rect.height / total_h)
        scrollable = total_h - self.rect.height
        rel_y = max(self.rect.y, min(mouse_y - bar_h / 2, self.rect.y + self.rect.height - bar_h))
        denom = self.rect.height - bar_h
        ratio = (rel_y - self.rect.y) / denom if denom else 0
        self.scroll = int(ratio * scrollable)
        self._clamp_scroll()

    def draw(self, surface):
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=8)
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        start = self.scroll // self.item_height
        for i, item in enumerate(self.items[start:], start=start):
            y = self.rect.y + i * self.item_height - self.scroll
            if y + self.item_height < self.rect.y:
                continue
            if y > self.rect.bottom:
                break
            row_color = BG_DEEP if i % 2 == 0 else BG_CARD
            pygame.draw.rect(surface, row_color, (self.rect.x, y, self.rect.width, self.item_height))
            if ":" in item:
                service, pwd = item.split(":", 1)
                serv_text = self.body_font.render(service.strip(), True, FG_WHITE)
                pwd_text = self.mono_font.render(pwd.strip(), True, FG_DIM)
                surface.blit(serv_text, (self.rect.x + 10, y + 5))
                surface.blit(pwd_text, (self.rect.x + 200, y + 5))
            else:
                txt = self.body_font.render(item, True, FG_WHITE)
                surface.blit(txt, (self.rect.x + 10, y + 5))
        surface.set_clip(old_clip)
        total_h = len(self.items) * self.item_height
        if total_h > self.rect.height:
            bar_rect = self._scrollbar_rect()
            pygame.draw.rect(surface, FG_DIM, bar_rect, border_radius=4)


class SelectableList(ScrollableList):
    def __init__(self, x, y, w, h, item_height=40, body_font=FONT_BODY, mono_font=FONT_MONO):
        super().__init__(x, y, w, h, item_height, body_font, mono_font)
        self.selected_index = -1

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.rect.y + self.scroll
                index = rel_y // self.item_height
                if 0 <= index < len(self.items):
                    self.selected_index = index

    def get_selected_item(self):
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def draw(self, surface):
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=8)
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        mouse_pos = pygame.mouse.get_pos()
        for i, item in enumerate(self.items):
            y = self.rect.y + i * self.item_height - self.scroll
            if y + self.item_height < self.rect.y or y > self.rect.bottom:
                continue
            row_rect = pygame.Rect(self.rect.x, y, self.rect.width, self.item_height)
            if i == self.selected_index:
                color = (60, 80, 150)
            elif row_rect.collidepoint(mouse_pos):
                color = (50, 50, 75)
            else:
                color = BG_DEEP if i % 2 == 0 else BG_CARD
            pygame.draw.rect(surface, color, row_rect)
            txt = self.body_font.render(item, True, FG_WHITE)
            surface.blit(txt, (self.rect.x + 15, y + (self.item_height - txt.get_height()) // 2))
        surface.set_clip(old_clip)
        total_h = len(self.items) * self.item_height
        if total_h > self.rect.height:
            bar_rect = self._scrollbar_rect()
            pygame.draw.rect(surface, FG_DIM, bar_rect, border_radius=4)


class PasswordManagerApp:
    def __init__(self, vault=None):
        pygame.init()
        self.width = WIDTH
        self.height = HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(" VaultPass")
        self.clock = pygame.time.Clock()
        self.running = True
        self.vault = vault
        self.state = "LOGIN"
        self.message = ""
        self.message_timer = 0
        self.message_color = FG_WHITE

        self.build_widgets()
        self.layout()

    def build_widgets(self):
        self.title_font = FONT_TITLE
        self.heading_font = FONT_HEADING
        self.body_font = FONT_BODY
        self.small_font = FONT_SMALL
        self.mono_font = FONT_MONO

        self.master_input = TextInput(0, 0, 300, 44, "Master Password", password=True, font=self.body_font)
        self.confirm_input = TextInput(0, 0, 300, 44, "Confirm Password", password=True, font=self.body_font)
        self.login_btn = Button(0, 0, 150, 44, "Unlock", callback=self.do_login, font=self.body_font)
        self.setup_btn = Button(0, 0, 150, 44, "Create Vault", callback=self.do_setup, font=self.body_font)
        self.create_shortcut_btn = Button(0, 0, 150, 44, "Create Vault", color=BG_CARD, text_color=ACCENT_BLUE,
                                          callback=lambda: self.goto("SETUP"), font=self.body_font)

        self.add_btn = Button(0, 0, 240, 50, "Add Password", callback=lambda: self.goto("ADD"), font=self.body_font)
        self.del_btn = Button(0, 0, 240, 50, "Manage Saved Passwords", callback=lambda: self.goto("DELETE"),
                              font=self.body_font)
        self.gen_btn = Button(0, 0, 240, 50, "Generate Password", callback=lambda: self.goto("GENERATE"),
                              font=self.body_font)
        self.quit_btn = Button(0, 0, 240, 50, "Quit", color=RED, callback=self.quit, font=self.body_font)

        self.add_service = TextInput(0, 0, 320, 44, "Service name", font=self.body_font)
        self.add_password = TextInput(0, 0, 320, 44, "Password", password=True, font=self.body_font)
        self.add_save = Button(0, 0, 140, 44, "Save", callback=self.do_add, font=self.body_font)
        self.add_back = Button(0, 0, 140, 44, "Back", color=BG_CARD, text_color=FG_WHITE,
                               callback=lambda: self.goto("MAIN"), font=self.body_font)
        self.add_show_pw_btn = Button(0, 0, 60, 44, "Show", color=BG_CARD, text_color=FG_WHITE,
                                      callback=self.toggle_add_password_visibility, font=self.body_font)

        self.del_search = TextInput(0, 0, 400, 36, placeholder="Search service...", font=self.body_font)
        self.del_list = SelectableList(0, 0, 400, 270, body_font=self.body_font, mono_font=self.mono_font)
        self.del_confirm = Button(0, 0, 140, 44, "Delete", color=RED, callback=self.do_delete, font=self.body_font)
        self.del_copy = Button(0, 0, 140, 44, "Copy", callback=self.do_copy_selected, font=self.body_font)
        self.del_back = Button(0, 0, 140, 44, "Back", color=BG_CARD, text_color=FG_WHITE,
                               callback=lambda: self.goto("MAIN"), font=self.body_font)
        self.del_all_items = []
        self._del_last_query = ""

        self.slider = Slider(0, 0, 400, min_val=4, max_val=32, init_val=16)
        self.gen_toggles = {
            "upper": ToggleButton(0, 0, 110, 34, "ABC", active=True, font=self.small_font),
            "lower": ToggleButton(0, 0, 110, 34, "abc", active=True, font=self.small_font),
            "digits": ToggleButton(0, 0, 110, 34, "123", active=True, font=self.small_font),
            "punctuation": ToggleButton(0, 0, 110, 34, "!@#", active=True, font=self.small_font),
        }
        self.gen_display = ""
        self.strength_meter = StrengthMeter(0, 0, 400, 20)
        self.gen_button = Button(0, 0, 130, 44, "Generate", callback=self.do_generate, font=self.body_font)
        self.gen_copy = Button(0, 0, 110, 44, "Copy", callback=self.do_copy_generated, font=self.body_font)
        self.gen_save = Button(0, 0, 150, 44, "Save to Vault", color=GREEN, callback=self.do_save_generated,
                               font=self.body_font)
        self.gen_back = Button(0, 0, 100, 44, "Back", color=BG_CARD, text_color=FG_WHITE,
                               callback=lambda: self.goto("MAIN"), font=self.body_font)

    def layout(self):
        w, h = self.width, self.height
        cx = w // 2
        margin = 40
        gap = 55

        card_w, card_h = 400, 320
        self.card_rect = pygame.Rect(cx - card_w // 2, 200, card_w, card_h)
        self.title_pos = (cx, 30 + self.title_font.get_height() // 2)
        self.subtitle_y = self.card_rect.top + 10

        self.master_input.rect.size = (300, 44)
        self.master_input.rect.centerx = cx
        self.master_input.rect.top = self.card_rect.top + 55

        self.confirm_input.rect.size = (300, 44)
        self.confirm_input.rect.centerx = cx
        self.confirm_input.rect.top = self.master_input.rect.bottom + 15

        self.login_btn.rect.size = (150, 44)
        self.login_btn.rect.centerx = cx
        self.login_btn.rect.top = self.master_input.rect.bottom + 20

        self.setup_btn.rect.size = (150, 44)
        self.setup_btn.rect.centerx = cx
        self.setup_btn.rect.top = self.confirm_input.rect.bottom + 15

        self.create_shortcut_btn.rect.size = (150, 44)
        self.create_shortcut_btn.rect.centerx = cx
        self.create_shortcut_btn.rect.top = self.login_btn.rect.bottom + 5

        btn_w, btn_h = 240, 50
        start_y = 180
        spacing = 25
        btns = [self.add_btn, self.del_btn, self.gen_btn, self.quit_btn]
        for i, btn in enumerate(btns):
            btn.rect.size = (btn_w, btn_h)
            btn.rect.centerx = cx
            btn.rect.top = start_y + i * (btn_h + spacing)

        left_col = cx - 200
        self.add_service.rect.topleft = (left_col, 180)
        self.add_service.rect.size = (320, 44)

        self.add_password.rect.topleft = (left_col, self.add_service.rect.bottom + 20)
        self.add_password.rect.size = (320, 44)

        self.add_show_pw_btn.rect.midleft = (self.add_password.rect.right + 10, self.add_password.rect.centery)
        self.add_show_pw_btn.rect.size = (60, 44)

        self.add_save.rect.topleft = (left_col, self.add_password.rect.bottom + 30)
        self.add_save.rect.size = (140, 44)

        self.add_back.rect.topleft = (left_col + 160, self.add_password.rect.bottom + 30)
        self.add_back.rect.size = (140, 44)

        self.del_search.rect.topleft = (margin, 150)
        self.del_search.rect.size = (w - 2 * margin, 36)

        list_top = self.del_search.rect.bottom + 10
        list_height = h - list_top - 80
        self.del_list.rect = pygame.Rect(margin, list_top, w - 2 * margin, list_height)
        self.del_list.item_height = 40

        bw = 140
        by = self.del_list.rect.bottom + 10
        self.del_confirm.rect.size = (bw, 44)
        self.del_confirm.rect.topleft = (margin, by)
        self.del_copy.rect.size = (bw, 44)
        self.del_copy.rect.topleft = (margin + bw + 15, by)
        self.del_back.rect.size = (bw, 44)
        self.del_back.rect.topright = (w - margin, by)

        y = 110

        self.length_label_pos = (margin, y)
        y += 25
        self.slider.rect.topleft = (margin, y)
        self.slider.rect.size = (w - 2 * margin - 90, 16)
        self.slider.update_handle_pos()
        y = self.slider.rect.bottom + gap

        self.include_label_pos = (margin, y)
        y += 25
        toggle_w, toggle_gap = 110, 15
        for i, key in enumerate(["upper", "lower", "digits", "punctuation"]):
            btn = self.gen_toggles[key]
            btn.rect.size = (toggle_w, 34)
            btn.rect.topleft = (margin + i * (toggle_w + toggle_gap), y)
        y += 34 + gap

        self.result_label_pos = (margin, y)
        y += 25
        self.result_text_y = y
        y += self.body_font.get_height() + gap

        self.strength_meter.rect.topleft = (margin, y)
        self.strength_meter.rect.size = (w - 2 * margin - 90, 20)

        by = h - margin - 44
        self.gen_button.rect.topleft = (margin, by)
        self.gen_copy.rect.topleft = (self.gen_button.rect.right + 15, by)
        self.gen_save.rect.topleft = (self.gen_copy.rect.right + 15, by)
        self.gen_back.rect.topright = (w - margin, by)

        self.status_pos = (cx, h - 40)

        self.del_list._clamp_scroll()

    def goto(self, state):
        self.state = state
        self.message = ""
        if state == "DELETE":
            self.refresh_delete_list()
        elif state == "GENERATE":
            self.gen_display = ""
            self.strength_meter.set_value(0)
            for tog in self.gen_toggles.values():
                tog.reset_hover()
        for btn in self._state_buttons():
            btn.reset_hover()

    def do_login(self):
        pwd = self.master_input.get_text()
        if Vault.is_master_created():
            self.vault = Vault.login(pwd)
            if self.vault:
                self.goto("MAIN")
                self.master_input.clear()
                self.set_message("Login successful", GREEN)
            else:
                self.set_message("Wrong master password", RED)
        else:
            self.set_message("No vault found. Create one.", YELLOW)

    def do_setup(self):
        pwd = self.master_input.get_text()
        confirm = self.confirm_input.get_text()
        if len(pwd) < 4:
            self.set_message("Password must be at least 4 characters", RED)
            return
        if pwd != confirm:
            self.set_message("Passwords do not match", RED)
            return
        self.vault = Vault.create(pwd)
        self.master_input.clear()
        self.confirm_input.clear()
        self.set_message("Vault created successfully", GREEN)
        self.goto("MAIN")

    def do_add(self):
        service = self.add_service.get_text().strip()
        password = self.add_password.get_text()
        if not service or not password:
            self.set_message("Fill in both fields", RED)
            return
        self.vault.save_password(service, password)
        self.add_service.clear()
        self.add_password.clear()
        self.add_password.password = True
        self.add_show_pw_btn.text = "Show"
        self.set_message(f"Saved '{service}'", GREEN)

    def refresh_delete_list(self):
        try:
            pwds = self.vault.load_passwords()
            self.del_all_items = list(pwds.keys())
        except Exception:
            self.del_all_items = []
        self.del_search.clear()
        self._del_last_query = ""
        self._apply_del_filter()

    def _apply_del_filter(self):
        query = self.del_search.get_text().strip().lower()
        if query:
            items = [s for s in self.del_all_items if query in s.lower()]
        else:
            items = list(self.del_all_items)
        self.del_list.set_items(items)
        self.del_list.selected_index = -1

    def do_delete(self):
        service = self.del_list.get_selected_item()
        if not service:
            self.set_message("Select a service from the list", YELLOW)
            return
        if self.vault.delete_password(service):
            self.set_message(f"Deleted '{service}'", GREEN)
            self.refresh_delete_list()
        else:
            self.set_message("Error deleting service", RED)

    def do_copy_selected(self):
        service = self.del_list.get_selected_item()
        if not service:
            self.set_message("Select a service from the list", YELLOW)
            return
        pwds = self.vault.load_passwords()
        pwd = pwds.get(service)
        if pwd is None:
            self.set_message("Service not found", RED)
            return
        try:
            pyperclip.copy(pwd)
            self.set_message(f"Copied password for '{service}'", GREEN)
        except pyperclip.PyperclipException:
            self.set_message("Clipboard unavailable", RED)

    def do_generate(self):
        t = self.gen_toggles
        self.gen_display = generate_passwd(
            self.slider.value,
            use_upper=t["upper"].active,
            use_lower=t["lower"].active,
            use_digits=t["digits"].active,
            use_punctuation=t["punctuation"].active,
        )
        self.strength_meter.set_value(check_passwd_strength(self.gen_display))

    def do_copy_generated(self):
        if self.gen_display:
            try:
                pyperclip.copy(self.gen_display)
                self.set_message("Copied to clipboard", GREEN)
            except pyperclip.PyperclipException:
                self.set_message("Clipboard unavailable", RED)

    def do_save_generated(self):
        if not self.gen_display:
            return
        self.state = "ADD"
        self.add_service.clear()
        self.add_password.text = self.gen_display
        self.add_password.active = False
        self.add_password.password = True
        self.add_show_pw_btn.text = "Show"

    def toggle_add_password_visibility(self):
        self.add_password.toggle_password_visibility()
        self.add_show_pw_btn.text = "Hide" if not self.add_password.password else "Show"

    def set_message(self, msg, color=FG_WHITE):
        self.message = msg
        self.message_color = color
        self.message_timer = 90

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.width = max(event.w, MIN_WIDTH)
                    self.height = max(event.h, MIN_HEIGHT)
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.layout()

                if self.state in ("LOGIN", "SETUP"):
                    self.master_input.handle_event(event)
                    if self.state == "SETUP":
                        self.confirm_input.handle_event(event)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.do_login() if self.state == "LOGIN" else self.do_setup()
                elif self.state == "ADD":
                    self.add_service.handle_event(event)
                    self.add_password.handle_event(event)
                elif self.state == "DELETE":
                    self.del_search.handle_event(event)
                    if self.del_search.get_text() != self._del_last_query:
                        self._del_last_query = self.del_search.get_text()
                        self._apply_del_filter()
                    self.del_list.handle_event(event)
                elif self.state == "GENERATE":
                    self.slider.handle_event(event)
                    for tog in self.gen_toggles.values():
                        tog.handle_event(event)

                for btn in self._state_buttons():
                    btn.handle_event(event)

            self.master_input.update()
            self.confirm_input.update()
            self.add_service.update()
            self.add_password.update()
            self.del_search.update()

            if self.message_timer > 0:
                self.message_timer -= 1
                if self.message_timer == 0:
                    self.message = ""

            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _state_buttons(self):
        if self.state == "LOGIN":
            btns = [self.login_btn]
            if not Vault.is_master_created():
                btns.append(self.create_shortcut_btn)
            return btns
        if self.state == "SETUP":
            return [self.setup_btn]
        if self.state == "MAIN":
            return [self.add_btn, self.del_btn, self.gen_btn, self.quit_btn]
        if self.state == "ADD":
            return [self.add_save, self.add_back, self.add_show_pw_btn]
        if self.state == "DELETE":
            return [self.del_confirm, self.del_copy, self.del_back]
        if self.state == "GENERATE":
            return [self.gen_button, self.gen_copy, self.gen_save, self.gen_back]
        return []

    def draw_centered(self, surface, text, font, color, center):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=center)
        surface.blit(surf, rect)

    def draw(self):
        self.screen.fill(BG_DEEP)
        margin = 40

        self.draw_centered(self.screen, " VaultPass", self.title_font, ACCENT_BLUE, self.title_pos)

        if self.state in ("LOGIN", "SETUP"):
            pygame.draw.rect(self.screen, BG_CARD, self.card_rect, border_radius=16)

            sub = "Enter master password" if self.state == "LOGIN" else "Create master password"
            self.draw_centered(self.screen, sub, self.heading_font, FG_WHITE,
                               (self.width // 2, self.card_rect.top + 30))

            self.master_input.draw(self.screen)
            if self.state == "SETUP":
                self.confirm_input.draw(self.screen)

            if self.state == "LOGIN":
                self.login_btn.draw(self.screen)
                if not Vault.is_master_created():
                    hint = self.small_font.render("No vault found.", True, FG_DIM)
                    hint_rect = hint.get_rect(center=(self.width // 2, self.create_shortcut_btn.rect.bottom + 20))
                    self.screen.blit(hint, hint_rect)
                    self.create_shortcut_btn.draw(self.screen)
            else:
                self.setup_btn.draw(self.screen)

        elif self.state == "MAIN":
            for b in [self.add_btn, self.del_btn, self.gen_btn, self.quit_btn]:
                b.draw(self.screen)

        elif self.state == "ADD":
            self.draw_centered(self.screen, "Add New Password", self.heading_font, FG_WHITE,
                               (self.width // 2, 120))
            self.add_service.draw(self.screen)
            self.add_password.draw(self.screen)
            self.add_show_pw_btn.draw(self.screen)
            self.add_save.draw(self.screen)
            self.add_back.draw(self.screen)

        elif self.state == "DELETE":
            self.draw_centered(self.screen, "Manage Saved Passwords", self.heading_font, FG_WHITE,
                               (self.width // 2, 110))
            self.del_search.draw(self.screen)
            self.del_list.draw(self.screen)
            self.del_confirm.draw(self.screen)
            self.del_copy.draw(self.screen)
            self.del_back.draw(self.screen)

        elif self.state == "GENERATE":
            self.draw_centered(self.screen, "Generate Password", self.heading_font, FG_WHITE,
                               (self.width // 2, 120))

            self.screen.blit(self.body_font.render("Length:", True, FG_WHITE), self.length_label_pos)
            self.slider.draw(self.screen)

            self.screen.blit(self.body_font.render("Include:", True, FG_WHITE), self.include_label_pos)
            for tog in self.gen_toggles.values():
                tog.draw(self.screen)

            self.screen.blit(self.body_font.render("Result:", True, FG_WHITE), self.result_label_pos)
            if self.gen_display:
                result_text = self.mono_font.render(self.gen_display, True, FG_WHITE)
                self.screen.blit(result_text, (margin, self.result_text_y))
                self.strength_meter.draw(self.screen)

            self.gen_button.draw(self.screen)
            self.gen_copy.draw(self.screen)
            self.gen_save.draw(self.screen)
            self.gen_back.draw(self.screen)

        if self.message and self.message_timer > 0:
            msg_surf = self.body_font.render(self.message, True, self.message_color)
            bg_rect = msg_surf.get_rect(center=self.status_pos)
            bg_rect.inflate_ip(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, border_radius=8)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=self.status_pos))


def run_gui(vault=None):
    app = PasswordManagerApp(vault)
    app.run()

if __name__ == "__main__":
    run_gui()
