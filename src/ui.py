import pygame
import sys
import secrets
from core import (
    load_passwords,
    save_password,
    delete_password,
    generate_passwd,
    check_passwd_strength,
    is_master_created,
    authenticate_user,
)

# -------------------------------
# Pygame UI Configuration
# -------------------------------

pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (70, 130, 180)
RED = (220, 20, 60)
GREEN = (60, 180, 75)
LIGHT_BLUE = (173, 216, 230)

# Screen dimensions
WIDTH, HEIGHT = 800, 600

# Fonts
FONT = pygame.font.Font(None, 28)
TITLE_FONT = pygame.font.Font(None, 48)
SMALL_FONT = pygame.font.Font(None, 22)

# -------------------------------
# Helper UI Components
# -------------------------------

class TextInput:
    def __init__(self, x, y, width, height, placeholder="", mask_char=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.placeholder = placeholder
        self.mask_char = mask_char

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                self.text += event.unicode
        return self.text

    def draw(self, surface):
        color = LIGHT_BLUE if self.active else WHITE
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        display_text = self.text
        if self.mask_char and not self.active:
            display_text = self.mask_char * len(self.text)
        if not display_text and not self.active:
            text_surf = FONT.render(self.placeholder, True, DARK_GRAY)
        else:
            text_surf = FONT.render(display_text, True, BLACK)
        surface.blit(text_surf, (self.rect.x + 5, self.rect.y + self.rect.height//2 - text_surf.get_height()//2))

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text


class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)
        text_surf = FONT.render(self.text, True, self.text_color)
        surface.blit(text_surf, (self.rect.x + self.rect.width//2 - text_surf.get_width()//2,
                                 self.rect.y + self.rect.height//2 - text_surf.get_height()//2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class ScrollableList:
    def __init__(self, x, y, width, height, items):
        self.rect = pygame.Rect(x, y, width, height)
        self.items = items
        self.scroll = 0
        self.item_height = 30

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * self.item_height
            max_scroll = max(0, len(self.items) * self.item_height - self.rect.height)
            self.scroll = max(0, min(self.scroll, max_scroll))

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        start_idx = self.scroll // self.item_height
        for i, item in enumerate(self.items[start_idx:]):
            y = self.rect.y + i * self.item_height - (self.scroll % self.item_height)
            if y + self.item_height > self.rect.bottom:
                break
            color = GRAY if i % 2 == 0 else WHITE
            pygame.draw.rect(surface, color, (self.rect.x, y, self.rect.width, self.item_height))
            text_surf = SMALL_FONT.render(str(item), True, BLACK)
            surface.blit(text_surf, (self.rect.x + 5, y + 5))
        surface.set_clip(old_clip)

    def set_items(self, items):
        self.items = items
        self.scroll = 0


# -------------------------------
# Main GUI Application
# -------------------------------

class PasswordManagerUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Password Manager")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "AUTH"  # AUTH, MAIN, ADD, VIEW, DELETE, GENERATE
        self.message = ""
        self.message_until = 0

        # Authentication widgets
        self.master_input = TextInput(WIDTH//2 - 150, HEIGHT//2 - 40, 300, 40, "Master Password", mask_char="•")
        self.login_btn = Button(WIDTH//2 - 80, HEIGHT//2 + 20, 160, 40, "Login")
        self.create_btn = Button(WIDTH//2 - 80, HEIGHT//2 + 80, 160, 40, "Create Account")

        # Main menu buttons
        self.add_btn = Button(WIDTH//2 - 100, 150, 200, 50, "Add Password")
        self.view_btn = Button(WIDTH//2 - 100, 230, 200, 50, "View Passwords")
        self.del_btn = Button(WIDTH//2 - 100, 310, 200, 50, "Delete Password")
        self.gen_btn = Button(WIDTH//2 - 100, 390, 200, 50, "Generate Password")
        self.quit_btn = Button(WIDTH//2 - 100, 470, 200, 50, "Quit", color=RED)

        # Add screen widgets
        self.service_input = TextInput(100, 200, 300, 40, "Service name")
        self.password_input = TextInput(100, 280, 300, 40, "Password")
        self.save_btn = Button(100, 360, 120, 40, "Save")
        self.back_btn = Button(250, 360, 120, 40, "Back", color=DARK_GRAY)

        # View screen
        self.view_list = ScrollableList(100, 150, 600, 350, [])
        self.back_from_view = Button(100, 520, 120, 40, "Back", color=DARK_GRAY)

        # Delete screen
        self.del_service_input = TextInput(100, 200, 300, 40, "Service to delete")
        self.del_confirm_btn = Button(100, 280, 120, 40, "Delete", color=RED)
        self.back_from_del = Button(250, 280, 120, 40, "Back", color=DARK_GRAY)

        # Generate screen
        self.length_input = TextInput(100, 200, 100, 40, "Length")
        self.generate_btn = Button(220, 200, 150, 40, "Generate")
        self.generated_display = ""
        self.strength_display = ""
        self.save_gen_btn = Button(100, 360, 180, 40, "Save this password", color=GREEN)
        self.back_from_gen = Button(300, 360, 120, 40, "Back", color=DARK_GRAY)

        self.master_exists = is_master_created()

    def set_message(self, msg, duration=2):
        self.message = msg
        self.message_until = pygame.time.get_ticks() + duration * 1000

    def draw_message(self):
        if self.message and pygame.time.get_ticks() < self.message_until:
            text = SMALL_FONT.render(self.message, True, RED)
            self.screen.blit(text, (20, HEIGHT - 40))

    def draw_background(self):
        self.screen.fill(LIGHT_BLUE)
        title = TITLE_FONT.render("Password Manager", True, BLACK)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if self.state == "AUTH":
                    self.master_input.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.login_btn.is_clicked(event.pos) and self.master_exists:
                            pwd = self.master_input.get_text()
                            if authenticate_user(pwd):
                                self.state = "MAIN"
                                self.master_input.set_text("")
                                self.set_message("Login successful!")
                            else:
                                self.set_message("Wrong master password!")
                        elif self.create_btn.is_clicked(event.pos) and not self.master_exists:
                            pwd = self.master_input.get_text()
                            if len(pwd) < 4:
                                self.set_message("Password must be at least 4 characters")
                            else:
                                if authenticate_user(pwd):
                                    self.master_exists = True
                                    self.state = "MAIN"
                                    self.master_input.set_text("")
                                    self.set_message("Account created!")
                                else:
                                    self.set_message("Error creating account")

                elif self.state == "MAIN":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.add_btn.is_clicked(event.pos):
                            self.state = "ADD"
                        elif self.view_btn.is_clicked(event.pos):
                            try:
                                passwords = load_passwords()
                                items = [f"{s}: {p}" for s, p in passwords.items()]
                                if not items:
                                    items = ["No passwords stored"]
                                self.view_list.set_items(items)
                                self.state = "VIEW"
                            except Exception as e:
                                self.set_message(f"Error loading: {e}")
                        elif self.del_btn.is_clicked(event.pos):
                            self.state = "DELETE"
                        elif self.gen_btn.is_clicked(event.pos):
                            self.state = "GENERATE"
                            self.generated_display = ""
                            self.strength_display = ""
                        elif self.quit_btn.is_clicked(event.pos):
                            self.running = False

                elif self.state == "ADD":
                    self.service_input.handle_event(event)
                    self.password_input.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.save_btn.is_clicked(event.pos):
                            service = self.service_input.get_text().strip()
                            password = self.password_input.get_text()
                            if service and password:
                                try:
                                    save_password(service, password)
                                    self.set_message(f"Password for '{service}' saved!")
                                    self.service_input.set_text("")
                                    self.password_input.set_text("")
                                except Exception as e:
                                    self.set_message(f"Error: {e}")
                            else:
                                self.set_message("Service and password cannot be empty!")
                        elif self.back_btn.is_clicked(event.pos):
                            self.state = "MAIN"

                elif self.state == "VIEW":
                    self.view_list.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.back_from_view.is_clicked(event.pos):
                            self.state = "MAIN"

                elif self.state == "DELETE":
                    self.del_service_input.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.del_confirm_btn.is_clicked(event.pos):
                            service = self.del_service_input.get_text().strip()
                            if service:
                                if delete_password(service):
                                    self.set_message(f"Deleted '{service}'")
                                    self.del_service_input.set_text("")
                                else:
                                    self.set_message("Service not found!")
                            else:
                                self.set_message("Enter a service name!")
                        elif self.back_from_del.is_clicked(event.pos):
                            self.state = "MAIN"

                elif self.state == "GENERATE":
                    self.length_input.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.generate_btn.is_clicked(event.pos):
                            try:
                                length = int(self.length_input.get_text())
                                if length < 4:
                                    self.set_message("Length must be at least 4")
                                else:
                                    pwd = generate_passwd(length)
                                    self.generated_display = pwd
                                    strength = check_passwd_strength(pwd)
                                    self.strength_display = f"Strength: {strength}%"
                            except ValueError:
                                self.set_message("Please enter a valid number")
                        elif self.save_gen_btn.is_clicked(event.pos) and self.generated_display:
                            self.state = "ADD"
                            self.password_input.set_text(self.generated_display)
                            self.service_input.set_text("")
                        elif self.back_from_gen.is_clicked(event.pos):
                            self.state = "MAIN"

            # Drawing
            self.draw_background()
            if self.state == "AUTH":
                if not self.master_exists:
                    title = FONT.render("Create a new master password", True, BLACK)
                else:
                    title = FONT.render("Enter master password", True, BLACK)
                self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 120))
                self.master_input.draw(self.screen)
                if not self.master_exists:
                    self.create_btn.draw(self.screen)
                else:
                    self.login_btn.draw(self.screen)

            elif self.state == "MAIN":
                self.add_btn.draw(self.screen)
                self.view_btn.draw(self.screen)
                self.del_btn.draw(self.screen)
                self.gen_btn.draw(self.screen)
                self.quit_btn.draw(self.screen)

            elif self.state == "ADD":
                self.screen.blit(FONT.render("Add new password", True, BLACK), (100, 140))
                self.service_input.draw(self.screen)
                self.password_input.draw(self.screen)
                self.save_btn.draw(self.screen)
                self.back_btn.draw(self.screen)

            elif self.state == "VIEW":
                self.screen.blit(FONT.render("Stored passwords", True, BLACK), (100, 100))
                self.view_list.draw(self.screen)
                self.back_from_view.draw(self.screen)

            elif self.state == "DELETE":
                self.screen.blit(FONT.render("Delete a password", True, BLACK), (100, 140))
                self.del_service_input.draw(self.screen)
                self.del_confirm_btn.draw(self.screen)
                self.back_from_del.draw(self.screen)

            elif self.state == "GENERATE":
                self.screen.blit(FONT.render("Generate secure password", True, BLACK), (100, 140))
                self.length_input.draw(self.screen)
                self.generate_btn.draw(self.screen)
                if self.generated_display:
                    gen_text = FONT.render(f"Generated: {self.generated_display}", True, BLACK)
                    self.screen.blit(gen_text, (100, 280))
                    strength_text = FONT.render(self.strength_display, True, BLACK)
                    self.screen.blit(strength_text, (100, 320))
                    self.save_gen_btn.draw(self.screen)
                self.back_from_gen.draw(self.screen)

            self.draw_message()
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()


def run_gui():
    """Entry point for the GUI from project.py"""
    ui = PasswordManagerUI()
    ui.run()


if __name__ == "__main__":
    run_gui()
