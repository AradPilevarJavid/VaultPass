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

WIDTH, HEIGHT = 900, 650
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
    def __init__(self, x, y, w, h, placeholder="", password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.password = password
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                if event.unicode.isprintable():
                    self.text += event.unicode
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

        display = self.text
        if self.password:
            display = "•" * len(self.text)
        if not self.text and not self.active:
            text_surf = FONT_BODY.render(self.placeholder, True, FG_DIM)
        else:
            text_surf = FONT_BODY.render(display, True, FG_WHITE)

        clip = surface.get_clip()
        surface.set_clip(self.rect)
        surface.blit(text_surf, (self.rect.x + 8, self.rect.y + (self.rect.h - text_surf.get_height()) // 2))
        if self.active and self.cursor_visible and self.text:
            cursor_x = self.rect.x + 8 + FONT_BODY.size(display)[0]
            pygame.draw.line(surface, FG_WHITE,
                             (cursor_x, self.rect.y + 8),
                             (cursor_x, self.rect.y + self.rect.h - 8), 2)
        surface.set_clip(clip)

    def get_text(self):
        return self.text

    def clear(self):
        self.text = ""
        self.active = False


class Button:
    def __init__(self, x, y, w, h, text, color=ACCENT_BLUE, text_color=WHITE, callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = ACCENT_HOVER
        self.text_color = text_color
        self.callback = callback
        self.hover = False
        self.click_scale = 1.0

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
        text_surf = FONT_BODY.render(self.text, True, self.text_color)
        surface.blit(text_surf, (x + (w - text_surf.get_width()) // 2,
                                 y + (h - text_surf.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Slider:
    def __init__(self, x, y, w, min_val=4, max_val=32, init_val=16):
        self.rect = pygame.Rect(x, y, w, 16)
        self.handle_rect = pygame.Rect(0, 0, 20, 28)
        self.min = min_val
        self.max = max_val
        self.value = init_val
        self.dragging = False
        self.update_handle_pos()

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
        label = FONT_SMALL.render(f"{self.value} ({percent}%)", True, FG_WHITE)
        surface.blit(label, (self.rect.x + self.rect.width + 12, self.rect.y - 4))


class StrengthMeter:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.percentage = 0

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
        label = FONT_SMALL.render(f"{self.percentage}%", True, FG_WHITE)
        surface.blit(label, (self.rect.x + self.rect.width + 12, self.rect.y - 2))


class ScrollableList:
    def __init__(self, x, y, w, h, item_height=35):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = []
        self.item_height = item_height
        self.scroll = 0
        self.scrollbar_dragging = False

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
                serv_text = FONT_BODY.render(service.strip(), True, FG_WHITE)
                pwd_text = FONT_MONO.render(pwd.strip(), True, FG_DIM)
                surface.blit(serv_text, (self.rect.x + 10, y + 5))
                surface.blit(pwd_text, (self.rect.x + 200, y + 5))
            else:
                txt = FONT_BODY.render(item, True, FG_WHITE)
                surface.blit(txt, (self.rect.x + 10, y + 5))
        surface.set_clip(old_clip)
        total_h = len(self.items) * self.item_height
        if total_h > self.rect.height:
            bar_rect = self._scrollbar_rect()
            pygame.draw.rect(surface, FG_DIM, bar_rect, border_radius=4)


class SelectableList(ScrollableList):
    def __init__(self, x, y, w, h, item_height=40):
        super().__init__(x, y, w, h, item_height)
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
            txt = FONT_BODY.render(item, True, FG_WHITE)
            surface.blit(txt, (self.rect.x + 15, y + (self.item_height - txt.get_height()) // 2))
        surface.set_clip(old_clip)
        total_h = len(self.items) * self.item_height
        if total_h > self.rect.height:
            bar_rect = self._scrollbar_rect()
            pygame.draw.rect(surface, FG_DIM, bar_rect, border_radius=4)


class PasswordManagerApp:
    def __init__(self, vault=None):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(" VaultPass")
        self.clock = pygame.time.Clock()
        self.running = True
        self.vault = None
        self.state = "LOGIN"
        self.message = ""
        self.message_timer = 0
        self.message_color = FG_WHITE

        self.master_input = TextInput(WIDTH//2 - 150, 280, 300, 40, "Master Password", password=True)
        self.confirm_input = TextInput(WIDTH//2 - 150, 340, 300, 40, "Confirm Password", password=True)
        self.login_btn = Button(WIDTH//2 - 75, 400, 150, 40, "Login", callback=self.do_login)
        self.setup_btn = Button(WIDTH//2 - 75, 400, 150, 40, "Create Vault", callback=self.do_setup)
        self.create_shortcut_btn = Button(WIDTH//2 - 75, 440, 150, 40, "Create Vault", color=BG_CARD, text_color=ACCENT_BLUE, callback=lambda: self.goto("SETUP"))

        self.add_btn = Button(WIDTH//2 - 120, 180, 240, 50, "Add Password", callback=lambda: self.goto("ADD"))
        self.del_btn = Button(WIDTH//2 - 120, 250, 240, 50, "View and delete Password", callback=lambda: self.goto("DELETE"))
        self.gen_btn = Button(WIDTH//2 - 120, 320, 240, 50, "Generate Password", callback=lambda: self.goto("GENERATE"))
        self.quit_btn = Button(WIDTH//2 - 120, 480, 240, 50, "Quit", color=RED, callback=self.quit)

        self.add_service = TextInput(100, 180, 320, 40, "Service name")
        self.add_password = TextInput(100, 250, 320, 40, "Password", password=True)
        self.add_save = Button(100, 320, 140, 40, "Save", callback=self.do_add)
        self.add_back = Button(260, 320, 140, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

        self.del_list = SelectableList(100, 160, 400, 300)
        self.del_confirm = Button(100, 480, 140, 40, "Delete", color=RED, callback=self.do_delete)
        self.del_back = Button(260, 480, 140, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

        self.slider = Slider(100, 200, 400, min_val=4, max_val=32, init_val=16)
        self.gen_display = ""
        self.strength_meter = StrengthMeter(100, 300, 400, 20)
        self.gen_button = Button(100, 350, 130, 40, "Generate", callback=self.do_generate)
        self.gen_copy = Button(245, 350, 110, 40, "Copy", callback=self.do_copy_generated)
        self.gen_save = Button(370, 350, 150, 40, "Save to Vault", color=GREEN, callback=self.do_save_generated)
        self.gen_back = Button(535, 350, 100, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

    def goto(self, state):
        self.state = state
        self.message = ""
        if state == "DELETE":
            self.refresh_delete_list()
        elif state == "GENERATE":
            self.gen_display = ""
            self.strength_meter.set_value(0)

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
        self.set_message(f"Saved '{service}'", GREEN)

    def refresh_delete_list(self):
        try:
            pwds = self.vault.load_passwords()
            self.del_list.set_items(list(pwds.keys()))
            self.del_list.selected_index = -1
        except Exception:
            self.del_list.set_items([])

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

    def do_generate(self):
        self.gen_display = generate_passwd(self.slider.value)
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
                    self.del_list.handle_event(event)
                elif self.state == "GENERATE":
                    self.slider.handle_event(event)
                for btn in self._state_buttons():
                    btn.handle_event(event)
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
            return [self.add_save, self.add_back]
        if self.state == "DELETE":
            return [self.del_confirm, self.del_back]
        if self.state == "GENERATE":
            return [self.gen_button, self.gen_copy, self.gen_save, self.gen_back]
        return []

    def draw(self):
        self.screen.fill(BG_DEEP)
        title = FONT_TITLE.render(" VaultPass", True, ACCENT_BLUE)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))

        if self.state in ("LOGIN", "SETUP"):
            pygame.draw.rect(self.screen, BG_CARD, (WIDTH//2 - 200, 200, 400, 280 if self.state == "SETUP" else 300), border_radius=16)
            sub = "Enter master password" if self.state == "LOGIN" else "Create master password"
            sub_text = FONT_HEADING.render(sub, True, FG_WHITE)
            self.screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, 210))
            self.master_input.draw(self.screen)
            if self.state == "SETUP":
                self.confirm_input.draw(self.screen)
            if self.state == "LOGIN":
                self.login_btn.draw(self.screen)
                if not Vault.is_master_created():
                    hint = FONT_SMALL.render("No vault found.", True, FG_DIM)
                    self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 460))
                    self.create_shortcut_btn.draw(self.screen)
            else:
                self.setup_btn.draw(self.screen)

        elif self.state == "MAIN":
            for b in [self.add_btn, self.del_btn, self.gen_btn, self.quit_btn]:
                b.draw(self.screen)

        elif self.state == "ADD":
            self.screen.blit(FONT_HEADING.render("Add New Password", True, FG_WHITE), (100, 120))
            self.add_service.draw(self.screen)
            self.add_password.draw(self.screen)
            self.add_save.draw(self.screen)
            self.add_back.draw(self.screen)

        elif self.state == "DELETE":
            self.screen.blit(FONT_HEADING.render("Select Service to Delete", True, FG_WHITE), (100, 110))
            self.del_list.draw(self.screen)
            self.del_confirm.draw(self.screen)
            self.del_back.draw(self.screen)

        elif self.state == "GENERATE":
            self.screen.blit(FONT_HEADING.render("Generate Password", True, FG_WHITE), (100, 120))
            self.screen.blit(FONT_BODY.render("Length:", True, FG_WHITE), (100, 175))
            self.slider.draw(self.screen)
            if self.gen_display:
                self.screen.blit(FONT_MONO.render("Result: " + self.gen_display, True, FG_WHITE), (100, 260))
                self.strength_meter.draw(self.screen)
            self.gen_button.draw(self.screen)
            self.gen_copy.draw(self.screen)
            self.gen_save.draw(self.screen)
            self.gen_back.draw(self.screen)

        if self.message and self.message_timer > 0:
            msg_surf = FONT_BODY.render(self.message, True, self.message_color)
            pygame.draw.rect(self.screen, (0, 0, 0), (WIDTH//2 - msg_surf.get_width()//2 - 10, HEIGHT - 70, msg_surf.get_width() + 20, 40), border_radius=8)
            self.screen.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT - 62))


def run_gui(vault=None):
    app = PasswordManagerApp(vault)
    app.run()

if __name__ == "__main__":
    run_gui()
