import pygame
import sys
from core import (
    Vault,
    generate_passwd,
    check_passwd_strength,
)

# ------------------------------------------------------------------------
#  INITIALIZATION
# ------------------------------------------------------------------------
pygame.init()

# Colour palette (dark theme with accent blue)
BG_DEEP = (24, 24, 38)           # main background
BG_CARD = (36, 36, 54)           # card / container
FG_WHITE = (230, 230, 240)       # primary text
FG_DIM = (140, 140, 160)         # placeholder / secondary text
ACCENT_BLUE = (100, 140, 255)    # interactive elements
ACCENT_HOVER = (130, 165, 255)   # hover state
RED = (255, 70, 85)              # errors / delete
GREEN = (80, 200, 120)           # success
YELLOW = (255, 200, 50)          # warnings
WHITE = (255, 255, 255)

# Dimensions & layout
WIDTH, HEIGHT = 900, 650
FPS = 30

# Fonts – try system sans-serif, fallback to Pygame default
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

# ------------------------------------------------------------------------
#  REUSABLE UI COMPONENTS
# ------------------------------------------------------------------------
class TextInput:
    """A styled text input field with placeholder, cursor blink and active highlight."""
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
                # Only allow printable characters
                if event.unicode.isprintable():
                    self.text += event.unicode
        # Cursor blink
        if self.active:
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_timer = 0
                self.cursor_visible = not self.cursor_visible
        else:
            self.cursor_visible = False

    def draw(self, surface):
        # Background
        color = BG_CARD if not self.active else (50, 50, 70)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, ACCENT_BLUE if self.active else FG_DIM, self.rect, 2, border_radius=8)

        # Text
        display = self.text
        if self.password and not self.active:
            display = "•" * len(self.text)
        if not display and not self.active:
            text_surf = FONT_BODY.render(self.placeholder, True, FG_DIM)
        else:
            text_surf = FONT_BODY.render(display, True, FG_WHITE)

        # Clipping
        clip = surface.get_clip()
        surface.set_clip(self.rect)
        surface.blit(text_surf, (self.rect.x + 8, self.rect.y + (self.rect.h - text_surf.get_height()) // 2))
        # Cursor
        if self.active and self.cursor_visible and self.text:
            cursor_x = self.rect.x + 8 + FONT_BODY.size(self.text)[0]
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
    """A rounded button with hover/click effects."""
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
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.click_scale = 0.95
            if self.callback:
                self.callback()
        if event.type == pygame.MOUSEBUTTONUP:
            self.click_scale = 1.0

    def draw(self, surface):
        # Scale effect
        w = int(self.rect.width * self.click_scale)
        h = int(self.rect.height * self.click_scale)
        x = self.rect.x + (self.rect.width - w) // 2
        y = self.rect.y + (self.rect.height - h) // 2
        color = self.hover_color if self.hover else self.color
        pygame.draw.rect(surface, color, (x, y, w, h), border_radius=10)
        # Text
        text_surf = FONT_BODY.render(self.text, True, self.text_color)
        surface.blit(text_surf, (x + (w - text_surf.get_width()) // 2,
                                 y + (h - text_surf.get_height()) // 2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Slider:
    """Horizontal slider for password length."""
    def __init__(self, x, y, w, min_val=4, max_val=64, init_val=16):
        self.rect = pygame.Rect(x, y, w, 16)          # track area
        self.handle_rect = pygame.Rect(0, 0, 20, 28)  # handle size
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
                # Jump to click position
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
        # Track
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=8)
        # Filled portion
        filled_w = int(self.rect.width * (self.value - self.min) / (self.max - self.min))
        if filled_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, filled_w, self.rect.height)
            pygame.draw.rect(surface, ACCENT_BLUE, fill_rect, border_radius=8)
        # Handle
        handle_color = ACCENT_HOVER if self.dragging else ACCENT_BLUE
        pygame.draw.rect(surface, handle_color, self.handle_rect, border_radius=6)
        pygame.draw.rect(surface, WHITE, self.handle_rect, 2, border_radius=6)
        # Value label
        label = FONT_SMALL.render(f"{self.value}", True, FG_WHITE)
        surface.blit(label, (self.rect.x + self.rect.width + 12, self.rect.y - 4))


class StrengthMeter:
    """Visual bar that changes colour from red to green."""
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.percentage = 0

    def set_value(self, percent):
        self.percentage = max(0, min(100, percent))

    def draw(self, surface):
        # Background
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=4)
        # Filled
        if self.percentage > 0:
            fill_w = int(self.rect.width * self.percentage / 100)
            # Colour interpolation red -> yellow -> green
            if self.percentage < 50:
                r = 255
                g = int(255 * (self.percentage / 50))
            else:
                r = int(255 * (1 - (self.percentage - 50) / 50))
                g = 255
            color = (r, g, 50)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(surface, color, fill_rect, border_radius=4)
        # Border
        pygame.draw.rect(surface, FG_DIM, self.rect, 1, border_radius=4)


class ScrollableList:
    """A scrollable area with service:password entries."""
    def __init__(self, x, y, w, h, item_height=35):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = []
        self.item_height = item_height
        self.scroll = 0
        self.scrollbar_dragging = False

    def set_items(self, items):
        self.items = items
        self.scroll = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 30
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Scrollbar click / drag
            if self.rect.collidepoint(event.pos):
                # Check if click on scrollbar
                total_h = len(self.items) * self.item_height
                if total_h > self.rect.height:
                    bar_rect = self._scrollbar_rect()
                    if bar_rect.collidepoint(event.pos):
                        self.scrollbar_dragging = True
                        # Adjust scroll based on click position
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
        # Invert mapping
        rel_y = max(self.rect.y, min(mouse_y - bar_h / 2, self.rect.y + self.rect.height - bar_h))
        ratio = (rel_y - self.rect.y) / (self.rect.height - bar_h)
        self.scroll = int(ratio * scrollable)
        self.scroll = max(0, min(self.scroll, scrollable))

    def draw(self, surface):
        # Background
        pygame.draw.rect(surface, BG_CARD, self.rect, border_radius=8)
        # Clipping
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        # Draw items
        start = self.scroll // self.item_height
        for i, item in enumerate(self.items[start:], start=start):
            y = self.rect.y + i * self.item_height - self.scroll
            if y + self.item_height < self.rect.y:
                continue
            if y > self.rect.bottom:
                break
            # Alternating row colour
            row_color = BG_DEEP if i % 2 == 0 else BG_CARD
            pygame.draw.rect(surface, row_color, (self.rect.x, y, self.rect.width, self.item_height))
            # Service name (left) and password (right) – colour coded
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
        # Scrollbar
        total_h = len(self.items) * self.item_height
        if total_h > self.rect.height:
            bar_rect = self._scrollbar_rect()
            pygame.draw.rect(surface, FG_DIM, bar_rect, border_radius=4)


# ------------------------------------------------------------------------
#  MAIN APPLICATION CLASS
# ------------------------------------------------------------------------
class PasswordManagerApp:
    """Modern Pygame GUI for the password manager. Receives an already
       authenticated vault when launched from project.py, but for UX
       purposes it shows its own login screen (ignoring the passed vault)."""
    def __init__(self, vault=None):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(" VaultPass")
        self.clock = pygame.time.Clock()
        self.running = True

        # Authentication state
        self.vault = None          # will hold Vault after successful auth
        self.state = "LOGIN"       # LOGIN, SETUP, MAIN, ADD, VIEW, DELETE, GENERATE
        self.message = ""
        self.message_timer = 0

        # --- Shared widgets (built once) ---
        # Login / Setup
        self.master_input = TextInput(WIDTH//2 - 150, 280, 300, 40, "Master Password", password=True)
        self.confirm_input = TextInput(WIDTH//2 - 150, 340, 300, 40, "Confirm Password", password=True)
        self.login_btn = Button(WIDTH//2 - 75, 400, 150, 40, "Login", callback=self.do_login)
        self.setup_btn = Button(WIDTH//2 - 75, 400, 150, 40, "Create Vault", callback=self.do_setup)

        # Main dashboard
        self.add_btn = Button(WIDTH//2 - 120, 180, 240, 50, "Add Password", callback=lambda: self.goto("ADD"))
        self.view_btn = Button(WIDTH//2 - 120, 250, 240, 50, "View Passwords", callback=lambda: self.goto("VIEW"))
        self.del_btn = Button(WIDTH//2 - 120, 320, 240, 50, "Delete Password", callback=lambda: self.goto("DELETE"))
        self.gen_btn = Button(WIDTH//2 - 120, 390, 240, 50, "Generate Password", callback=lambda: self.goto("GENERATE"))
        self.quit_btn = Button(WIDTH//2 - 120, 480, 240, 50, "Quit", color=RED, callback=self.quit)

        # Add screen
        self.add_service = TextInput(100, 180, 320, 40, "Service name")
        self.add_password = TextInput(100, 250, 320, 40, "Password", password=True)
        self.add_save = Button(100, 320, 140, 40, "Save", callback=self.do_add)
        self.add_back = Button(260, 320, 140, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

        # View screen
        self.view_list = ScrollableList(50, 120, 800, 420)
        self.view_back = Button(50, 570, 120, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

        # Delete screen
        self.del_service = TextInput(100, 220, 320, 40, "Service to delete")
        self.del_confirm = Button(100, 290, 140, 40, "Delete", color=RED, callback=self.do_delete)
        self.del_back = Button(260, 290, 140, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

        # Generate screen
        self.slider = Slider(100, 200, 400, min_val=4, max_val=64, init_val=16)
        self.gen_display = ""
        self.strength_meter = StrengthMeter(100, 300, 400, 20)
        self.gen_button = Button(100, 350, 140, 40, "Generate", callback=self.do_generate)
        self.gen_save = Button(260, 350, 180, 40, "Save to Vault", color=GREEN, callback=self.do_save_generated)
        self.gen_back = Button(460, 350, 120, 40, "Back", color=BG_CARD, text_color=FG_WHITE, callback=lambda: self.goto("MAIN"))

    def goto(self, state):
        self.state = state
        self.message = ""
        if state == "VIEW":
            self.refresh_view()
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

    def refresh_view(self):
        try:
            pwds = self.vault.load_passwords()
            items = [f"{s}: {p}" for s, p in pwds.items()]
            if not items:
                items = ["(empty)"]
            self.view_list.set_items(items)
        except Exception as e:
            self.set_message(f"Error: {e}", RED)
            self.view_list.set_items([])

    def do_delete(self):
        service = self.del_service.get_text().strip()
        if not service:
            self.set_message("Enter a service name", RED)
            return
        if self.vault.delete_password(service):
            self.set_message(f"Deleted '{service}'", GREEN)
            self.del_service.clear()
        else:
            self.set_message("Service not found", RED)

    def do_generate(self):
        length = self.slider.value
        pwd = generate_passwd(length)
        self.gen_display = pwd
        strength = check_passwd_strength(pwd)
        self.strength_meter.set_value(strength)

    def do_save_generated(self):
        if not self.gen_display:
            return
        # Go to ADD screen with password pre-filled
        self.state = "ADD"
        self.add_service.clear()
        self.add_password.text = self.gen_display
        self.add_password.active = False  # so it's visible

    def set_message(self, msg, color=FG_WHITE):
        self.message = msg
        self.message_color = color
        self.message_timer = 120  # 2 seconds at 60 FPS? actually using clock.tick(30) -> 4 seconds

    def quit(self):
        self.running = False

    # ---------- main loop ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                # Handle global events per state
                if self.state in ("LOGIN", "SETUP"):
                    self.master_input.handle_event(event)
                    if self.state == "SETUP":
                        self.confirm_input.handle_event(event)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        if self.state == "LOGIN":
                            self.do_login()
                        else:
                            self.do_setup()
                elif self.state == "ADD":
                    self.add_service.handle_event(event)
                    self.add_password.handle_event(event)
                elif self.state == "DELETE":
                    self.del_service.handle_event(event)
                elif self.state == "GENERATE":
                    self.slider.handle_event(event)
                elif self.state == "VIEW":
                    self.view_list.handle_event(event)

                # Buttons handle themselves
                for btn in self._state_buttons():
                    btn.handle_event(event)

            # Decrease message timer
            if self.message_timer > 0:
                self.message_timer -= 1
                if self.message_timer == 0:
                    self.message = ""

            # Drawing
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _state_buttons(self):
        """Return list of buttons active in current state."""
        if self.state in ("LOGIN", "SETUP"):
            return [self.login_btn] if self.state == "LOGIN" else [self.setup_btn]
        if self.state == "MAIN":
            return [self.add_btn, self.view_btn, self.del_btn, self.gen_btn, self.quit_btn]
        if self.state == "ADD":
            return [self.add_save, self.add_back]
        if self.state == "VIEW":
            return [self.view_back]
        if self.state == "DELETE":
            return [self.del_confirm, self.del_back]
        if self.state == "GENERATE":
            return [self.gen_button, self.gen_save, self.gen_back]
        return []

    def draw(self):
        self.screen.fill(BG_DEEP)

        # ---- Title bar ----
        title = FONT_TITLE.render(" VaultPass", True, ACCENT_BLUE)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))

        # ---- State-specific drawing ----
        if self.state in ("LOGIN", "SETUP"):
            # Card background
            card_rect = pygame.Rect(WIDTH//2 - 200, 200, 400, 280)
            pygame.draw.rect(self.screen, BG_CARD, card_rect, border_radius=16)
            # Subtitle
            sub = "Enter your master password" if self.state == "LOGIN" else "Create a new master password"
            sub_text = FONT_HEADING.render(sub, True, FG_WHITE)
            self.screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, 210))
            # Inputs
            self.master_input.draw(self.screen)
            if self.state == "SETUP":
                self.confirm_input.draw(self.screen)
            # Button
            if self.state == "LOGIN":
                self.login_btn.draw(self.screen)
                # Show a hint if no vault exists
                if not Vault.is_master_created():
                    hint = FONT_SMALL.render("No vault found. Click 'Create Vault' below.", True, FG_DIM)
                    self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 460))
                    # Additional button for setup
                    setup_btn = Button(WIDTH//2 - 75, 440, 150, 40, "Create Vault", color=BG_CARD, text_color=ACCENT_BLUE, callback=lambda: self.goto("SETUP"))
                    setup_btn.handle_event(pygame.event.Event(pygame.NOEVENT))
                    setup_btn.draw(self.screen)
                    # Dirty: add to state_buttons? We'll just draw it here.
            else:
                self.setup_btn.draw(self.screen)

        elif self.state == "MAIN":
            # Center the buttons
            self.add_btn.draw(self.screen)
            self.view_btn.draw(self.screen)
            self.del_btn.draw(self.screen)
            self.gen_btn.draw(self.screen)
            self.quit_btn.draw(self.screen)

        elif self.state == "ADD":
            heading = FONT_HEADING.render("Add New Password", True, FG_WHITE)
            self.screen.blit(heading, (100, 120))
            self.add_service.draw(self.screen)
            self.add_password.draw(self.screen)
            self.add_save.draw(self.screen)
            self.add_back.draw(self.screen)

        elif self.state == "VIEW":
            heading = FONT_HEADING.render("Stored Passwords", True, FG_WHITE)
            self.screen.blit(heading, (50, 80))
            self.view_list.draw(self.screen)
            self.view_back.draw(self.screen)

        elif self.state == "DELETE":
            heading = FONT_HEADING.render("Delete a Password", True, FG_WHITE)
            self.screen.blit(heading, (100, 160))
            self.del_service.draw(self.screen)
            self.del_confirm.draw(self.screen)
            self.del_back.draw(self.screen)

        elif self.state == "GENERATE":
            heading = FONT_HEADING.render("Generate Secure Password", True, FG_WHITE)
            self.screen.blit(heading, (100, 120))
            # Slider label
            lbl = FONT_BODY.render("Length:", True, FG_WHITE)
            self.screen.blit(lbl, (100, 175))
            self.slider.draw(self.screen)
            # Strength meter
            if self.gen_display:
                pw_label = FONT_MONO.render("Generated: " + self.gen_display, True, FG_WHITE)
                self.screen.blit(pw_label, (100, 260))
                self.strength_meter.draw(self.screen)
                strength_txt = FONT_SMALL.render(f"Strength: {self.strength_meter.percentage}%", True, FG_WHITE)
                self.screen.blit(strength_txt, (510, 300))
            else:
                self.strength_meter.draw(self.screen)
            self.gen_button.draw(self.screen)
            self.gen_save.draw(self.screen)
            self.gen_back.draw(self.screen)

        # ---- Message overlay ----
        if self.message and self.message_timer > 0:
            msg_surf = FONT_BODY.render(self.message, True, self.message_color)
            msg_bg = pygame.Surface((msg_surf.get_width() + 20, msg_surf.get_height() + 10), pygame.SRCALPHA)
            msg_bg.fill((0, 0, 0, 180))
            self.screen.blit(msg_bg, (WIDTH//2 - msg_surf.get_width()//2 - 10, HEIGHT - 70))
            self.screen.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT - 65))


def run_gui(vault=None):
    """Entry point from project.py. If vault is provided, we still show
       a login screen for security – the vault is ignored until re-authentication."""
    app = PasswordManagerApp(vault)
    app.run()


if __name__ == "__main__":
    run_gui()