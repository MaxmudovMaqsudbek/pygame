# import pygame
# import sys

# # -- General Setup --
# # This is the basic setup that initializes all the modules required for PyGame.
# # We also need to set up a clock to control the frame rate of our game.
# pygame.init()
# clock = pygame.time.Clock()

# # -- Screen Setup --
# # Here we define the dimensions of our game window.
# # Using variables for width and height makes it easier to change them later.
# screen_width = 800
# screen_height = 600
# screen = pygame.display.set_mode((screen_width, screen_height))

# # We can set a caption for the window to give our game a title.
# pygame.display.set_caption("PyGame Arkanoid")

# # -- Main Game Loop --
# # The game loop is the heart of any PyGame program. It's a `while` loop that
# # runs continuously, handling events, updating game state, and drawing to the screen.
# while True:
#     # --- Event Handling ---
#     # This `for` loop checks for any events that have happened since the last frame.
#     # Events can be key presses, mouse movements, or, in this case, closing the window.
#     for event in pygame.event.get():
#         # The `pygame.QUIT` event is triggered when the user clicks the 'X' button
#         # on the window.
#         if event.type == pygame.QUIT:
#             # If the QUIT event is detected, we first shut down PyGame cleanly.
#             pygame.quit()
#             # Then, we exit the program using `sys.exit()`.
#             sys.exit()

#     # --- Drawing ---
#     # This is where all the rendering will happen in later steps.
#     # For now, we'll just fill the screen with a solid color.
#     # Colors are represented by RGB tuples (Red, Green, Blue).
#     # (0, 0, 0) is black.
#     screen.fill((0, 0, 0))

#     # --- Updating the Display ---
#     # `pygame.display.flip()` updates the entire screen with everything we've drawn
#     # in the current frame. This is what makes our drawings visible.
#     pygame.display.flip()

#     # --- Frame Rate Control ---
#     # `clock.tick(60)` tells PyGame to pause for the right amount of time to ensure
#     # our game runs at a maximum of 60 frames per second (FPS). This keeps the
#     # game's speed consistent across different computers.
#     clock.tick(60)













































import pygame
import sys
import random
import math # Not directly used here, but good to keep if game_objects needs it

# Import all game object classes from the separate file
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

class Game:
    """
    The main Game class, orchestrating all game logic, states, and rendering.
    This is the core of the advanced application architecture.
    """
    def __init__(self):
        """Initializes Pygame, screen, fonts, sounds, and game objects."""
        pygame.init()
        pygame.mixer.init() # Initialize mixer for sounds

        # Screen setup
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("PyGame Arkanoid")
        self.clock = pygame.time.Clock() # To control frame rate

        # Colors
        self.BG_COLOR = pygame.Color('grey12') # Dark grey background
        self.BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)] # Red, Orange, Gold, Green

        # Font Setup
        self.title_font = pygame.font.Font(None, 70) # For title screen
        self.game_font = pygame.font.Font(None, 40) # For score, lives, and game over/win messages
        self.message_font = pygame.font.Font(None, 30) # For power-up messages

        # Sound Setup - Robust loading with dummy sound fallback
        self.bounce_sound = self._load_sound('bounce.wav')
        self.brick_break_sound = self._load_sound('brick_break.wav')
        self.game_over_sound = self._load_sound('game_over.wav')
        self.laser_sound = self._load_sound('laser.wav')

        # Game State Management
        # Define game states as class attributes for clarity
        self.GAME_STATE_TITLE = 'title_screen'
        self.GAME_STATE_PLAYING = 'playing'
        self.GAME_STATE_WIN = 'you_win'
        self.GAME_STATE_GAME_OVER = 'game_over'
        self.GAME_STATE_LEVEL_COMPLETE = 'level_complete'
        self.game_state = self.GAME_STATE_TITLE # Initial game state

        # Game Objects (initialized in _reset_game or _initialize_game_elements)
        self.paddle = Paddle(self.screen_width, self.screen_height)
        self.balls = [] # List to hold multiple balls for multi-ball feature
        self.bricks = [] # List to hold brick objects
        self.power_ups = [] # List to hold active power-ups
        self.lasers = [] # List to hold active laser beams
        self.particles = [] # List to hold particles for explosions/sparks
        self.fireworks = [] # List to hold fireworks for win screen

        # Game Variables
        self.score = 0
        self.lives = 3
        self.level = 1
        self.max_level = 5
        self.display_message = "" # Message for power-up activations
        self.message_timer = 0 # Timer for displaying messages
        self.firework_timer = 0 # Timer for spawning fireworks on win screen
        self.level_complete_timer = 0 # Timer for level complete screen
        
        # Sound control
        self.sound_enabled = True
        self.mute_button_rect = pygame.Rect(10, self.screen_height - 40, 80, 30)

        # Flag to control the main game loop
        self.running = True

    def _load_sound(self, path):
        """Helper to load sound files with error handling."""
        try:
            # Try loading from current directory first
            return pygame.mixer.Sound(path)
        except pygame.error:
            try:
                # Try loading from script directory
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                full_path = os.path.join(script_dir, path)
                return pygame.mixer.Sound(full_path)
            except pygame.error as e:
                print(f"Warning: Sound file '{path}' not found or could not be loaded. {e}")
                class DummySound: # Dummy class if sound fails to load
                    def play(self): pass
                    def set_volume(self, volume): pass
                return DummySound()

    def _play_sound(self, sound):
        """Play sound only if sound is enabled."""
        if self.sound_enabled:
            sound.play()

    def _toggle_mute(self):
        """Toggle sound on/off."""
        self.sound_enabled = not self.sound_enabled
        # Set volume for all individual sound objects
        volume = 1.0 if self.sound_enabled else 0.0
        try:
            self.bounce_sound.set_volume(volume)
            self.brick_break_sound.set_volume(volume)
            self.game_over_sound.set_volume(volume)
            self.laser_sound.set_volume(volume)
        except AttributeError:
            # Handle case where sounds are DummySound objects
            pass

    def _create_brick_wall(self):
        """Generates a new set of bricks for a level."""
        bricks = []
        brick_rows = min(4 + self.level // 2, 8)  # More rows in higher levels
        brick_cols = 10
        brick_width = 75
        brick_height = 20
        brick_padding = 5
        wall_start_y = 50 # Y-coordinate to start drawing bricks
        
        # Calculate horizontal offset to center the brick wall
        total_brick_wall_width = brick_cols * (brick_width + brick_padding) - brick_padding
        start_x_offset = (self.screen_width - total_brick_wall_width) // 2

        for row in range(brick_rows):
            for col in range(brick_cols):
                # Create some gaps in higher levels for more challenge
                if self.level > 2 and random.random() < 0.1:
                    continue
                    
                x = start_x_offset + col * (brick_width + brick_padding)
                y = row * (brick_height + brick_padding) + wall_start_y
                color = self.BRICK_COLORS[row % len(self.BRICK_COLORS)] # Cycle through colors per row
                bricks.append(Brick(x, y, brick_width, brick_height, color))
        return bricks

    def _reset_game(self):
        """Resets all game elements and variables for a new game."""
        self.paddle.reset()
        # Initialize with one ball
        self.balls = [Ball(self.screen_width, self.screen_height)]
        self.bricks = self._create_brick_wall() # Recreate the brick wall
        self.score = 0
        self.lives = 3
        self.level = 1
        self.power_ups.clear()
        self.lasers.clear()
        self.particles.clear()
        self.fireworks.clear()
        self.display_message = ""
        self.message_timer = 0
        self.firework_timer = 0
        self.level_complete_timer = 0
        self.game_state = self.GAME_STATE_PLAYING # Transition to playing state

    def _next_level(self):
        """Advance to the next level."""
        self.level += 1
        if self.level > self.max_level:
            self.game_state = self.GAME_STATE_WIN
        else:
            self.game_state = self.GAME_STATE_LEVEL_COMPLETE
            self.level_complete_timer = 180  # 3 seconds
            self.paddle.reset()
            # Reset to single ball for new level
            self.balls = [Ball(self.screen_width, self.screen_height)]
            self.bricks = self._create_brick_wall()
            self.power_ups.clear()
            self.lasers.clear()
            # Increase ball speed slightly each level
            for ball in self.balls:
                ball.base_speed = min(6 + self.level * 0.5, 10)

    def _handle_input(self):
        """Processes user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check mute button click
                if self.mute_button_rect.collidepoint(event.pos):
                    self._toggle_mute()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # M key to toggle mute
                    self._toggle_mute()
                if event.key == pygame.K_SPACE:
                    if self.game_state == self.GAME_STATE_TITLE:
                        self._reset_game() # Start game from title screen
                    elif self.game_state in [self.GAME_STATE_GAME_OVER, self.GAME_STATE_WIN]:
                        # After game over or win, pressing space returns to title screen
                        self.game_state = self.GAME_STATE_TITLE 
                        self._reset_game() # Reset game state for next play, but stay on title
                        for ball in self.balls:
                            ball.is_glued = True # Ensure balls are stuck on title screen
                    elif self.game_state == self.GAME_STATE_LEVEL_COMPLETE:
                        self.game_state = self.GAME_STATE_PLAYING
                        self.level_complete_timer = 0
                    elif self.game_state == self.GAME_STATE_PLAYING:
                        # Launch all glued balls
                        for ball in self.balls:
                            if ball.is_glued:
                                ball.is_glued = False 
                
                # Laser firing only in playing state with laser power-up
                if self.game_state == self.GAME_STATE_PLAYING and event.key == pygame.K_f and self.paddle.has_laser:
                    self.lasers.append(Laser(self.paddle.rect.centerx - 30, self.paddle.rect.top))
                    self.lasers.append(Laser(self.paddle.rect.centerx + 30, self.paddle.rect.top))
                    self._play_sound(self.laser_sound)

    def _update_game_logic(self):
        """Updates the state of all game objects and checks for game conditions."""
        if self.game_state == self.GAME_STATE_PLAYING:
            self.paddle.update()
            keys = pygame.key.get_pressed() # Check keys for ball launch if glued
            
            # Update all balls
            balls_lost = 0
            for ball in self.balls[:]:  # Iterate over copy to allow removal
                ball_status, collision_object = ball.update(self.paddle, keys[pygame.K_SPACE])
                
                # Handle ball status (lost life)
                if ball_status == 'lost':
                    self.balls.remove(ball)
                    balls_lost += 1
                elif collision_object in ['wall', 'paddle']:
                    self._play_sound(self.bounce_sound)
                    # Generate sparks on ball collision with wall/paddle
                    for _ in range(5):
                        self.particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

            # Check if all balls are lost
            if not self.balls:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_state = self.GAME_STATE_GAME_OVER
                    self._play_sound(self.game_over_sound)
                else:
                    # Reset with new ball if lives remain
                    self.balls = [Ball(self.screen_width, self.screen_height)]
                    self.paddle.reset() # Reset paddle size/powerups on losing a life

            # Ball and Brick Collision
            for ball in self.balls:
                for brick in self.bricks[:]: # Iterate over a copy to allow removal
                    if ball.rect.colliderect(brick.rect):
                        ball.speed_y *= -1 # Reverse ball direction
                        # Generate brick explosion particles
                        for _ in range(15):
                            self.particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                        self.bricks.remove(brick) # Remove the hit brick
                        self.score += 10 * self.level # Score increases with level
                        self._play_sound(self.brick_break_sound)
                        
                        # Increased power-up chance in higher levels
                        power_up_chance = min(0.3 + self.level * 0.05, 0.6)
                        if random.random() < power_up_chance:
                            power_up_types = list(PowerUp.PROPERTIES.keys())
                            # Add new power-ups for higher levels
                            if self.level >= 3:
                                power_up_types.extend(['multi_ball', 'shield'])
                            power_up_type = random.choice(power_up_types)
                            power_up = PowerUp(brick.rect.centerx, brick.rect.centery, power_up_type)
                            self.power_ups.append(power_up)
                        break # Only hit one brick per ball update

            # Power-Up Logic
            for power_up in self.power_ups[:]:
                power_up.update()
                if power_up.rect.top > self.screen_height: # Remove if falls off screen
                    self.power_ups.remove(power_up)
                elif self.paddle.rect.colliderect(power_up.rect): # If paddle collects power-up
                    if power_up.type in PowerUp.PROPERTIES:
                        self.display_message = power_up.PROPERTIES[power_up.type]['message']
                        self.message_timer = 120 # Display message for 2 seconds (120 frames)
                        if power_up.type in ['grow', 'laser', 'glue']:
                            self.paddle.activate_power_up(power_up.type)
                        elif power_up.type == 'slow':
                            # Apply slow to all balls
                            for ball in self.balls:
                                ball.activate_power_up(power_up.type)
                        elif power_up.type == 'multi_ball':
                            self.display_message = 'MULTI BALL!'
                            # Add extra balls (proper implementation)
                            if self.balls:  # Only if there are existing balls
                                main_ball = self.balls[0]
                                for _ in range(2):
                                    new_ball = Ball(self.screen_width, self.screen_height)
                                    new_ball.rect.center = main_ball.rect.center
                                    new_ball.speed_x = random.choice([-6, 6])
                                    new_ball.speed_y = -6
                                    new_ball.is_glued = False
                                    self.balls.append(new_ball)
                        elif power_up.type == 'shield':
                            self.display_message = 'SHIELD ACTIVATED!'
                            # Shield power-up gives an extra life
                            self.lives = min(self.lives + 1, 5)
                    self.power_ups.remove(power_up)

            # Laser Logic
            for laser in self.lasers[:]:
                laser.update()
                if laser.rect.bottom < 0: # Remove if goes off screen
                    self.lasers.remove(laser)
                else:
                    for brick in self.bricks[:]:
                        if laser.rect.colliderect(brick.rect):
                            # Generate brick explosion particles for laser hits
                            for _ in range(10):
                                self.particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                            self.bricks.remove(brick)
                            self.lasers.remove(laser) # Laser disappears after hitting a brick
                            self.score += 10 * self.level
                            self._play_sound(self.brick_break_sound)
                            break # Laser can only hit one brick

            # Check win condition (level complete)
            if not self.bricks:
                self._next_level()

        elif self.game_state == self.GAME_STATE_LEVEL_COMPLETE:
            self.level_complete_timer -= 1
            if self.level_complete_timer <= 0:
                self.game_state = self.GAME_STATE_PLAYING

        # Update message timer (active in all states)
        if self.message_timer > 0:
            self.message_timer -= 1
            
        # Update particles (active in all states for continuous effects)
        for particle in self.particles[:]:
            particle.update()
            if particle.size <= 0:
                self.particles.remove(particle)

        # Firework logic for win screen
        if self.game_state == self.GAME_STATE_WIN:
            self.firework_timer -= 1
            if self.firework_timer <= 0:
                self.fireworks.append(Firework(self.screen_width, self.screen_height))
                self.firework_timer = random.randint(20, 50) # Spawn new firework every 0.3-0.8 seconds
            
            for firework in self.fireworks[:]:
                firework.update()
                if firework.is_dead():
                    self.fireworks.remove(firework)

    def _draw_elements(self):
        """Draws all game elements to the screen based on the current game state."""
        self.screen.fill(self.BG_COLOR) # Fill background

        # Draw elements based on game state
        if self.game_state == self.GAME_STATE_TITLE:
            self._draw_title_screen()
        elif self.game_state == self.GAME_STATE_PLAYING:
            self._draw_playing_screen()
        elif self.game_state == self.GAME_STATE_LEVEL_COMPLETE:
            self._draw_level_complete_screen()
        elif self.game_state in [self.GAME_STATE_GAME_OVER, self.GAME_STATE_WIN]:
            self._draw_end_screen()
        
        # Draw elements that are always visible (like particles, messages)
        for particle in self.particles:
            particle.draw(self.screen)

        # Draw mute button (always visible)
        self._draw_mute_button()

        if self.message_timer > 0:
            message_surface = self.message_font.render(self.display_message, True, (255, 255, 255))
            message_rect = message_surface.get_rect(center=(self.screen_width / 2, self.screen_height - 60))
            self.screen.blit(message_surface, message_rect)

        pygame.display.flip() # Update the full display Surface to the screen

    def _draw_title_screen(self):
        """Draws the title screen elements."""
        title_surface = self.title_font.render("ARKANOID", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2 - 100))
        self.screen.blit(title_surface, title_rect)
        
        subtitle_surface = self.game_font.render("Python Arkanoid Game", True, (200, 200, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2 - 50))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        start_surface = self.game_font.render("Press SPACE to Start", True, (255, 255, 255))
        start_rect = start_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2 + 20))
        self.screen.blit(start_surface, start_rect)
        
        controls_text = [
            "Controls:",
            "Arrow Keys - Move Paddle",
            "SPACE - Launch Ball(s)",
            "F - Fire Laser (when available)",
            "M - Toggle Mute / Click Mute Button"
        ]
        
        for i, line in enumerate(controls_text):
            color = (255, 255, 255) if i == 0 else (200, 200, 200)
            font = self.message_font if i == 0 else pygame.font.Font(None, 24)
            text_surface = font.render(line, True, color)
            text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2 + 80 + i * 25))
            self.screen.blit(text_surface, text_rect)

    def _draw_playing_screen(self):
        """Draws elements specific to the 'playing' state."""
        self.paddle.draw(self.screen)
        
        # Draw all balls
        for ball in self.balls:
            ball.draw(self.screen)
            
        for brick in self.bricks:
            brick.draw(self.screen)
        for power_up in self.power_ups:
            power_up.draw(self.screen)
        for laser in self.lasers:
            laser.draw(self.screen)
        
        # Improved UI Layout - Professional game UI
        ui_margin = 15
        ui_top = 15
        ui_font_size = 32
        ui_font = pygame.font.Font(None, ui_font_size)
        
        # Score (top-left)
        score_text = ui_font.render(f"SCORE: {self.score:,}", True, (255, 255, 255))
        self.screen.blit(score_text, (ui_margin, ui_top))
        
        # Level (top-center)
        level_text = ui_font.render(f"LEVEL: {self.level}", True, (255, 255, 255))
        level_rect = level_text.get_rect(centerx=self.screen_width // 2, y=ui_top)
        self.screen.blit(level_text, level_rect)
        
        # Lives (top-right) - Fixed positioning above bricks
        lives_text = ui_font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
        lives_rect = lives_text.get_rect(topright=(self.screen_width - ui_margin, ui_top))
        self.screen.blit(lives_text, lives_rect)
        
        # Multi-ball indicator
        if len(self.balls) > 1:
            multi_ball_text = self.message_font.render(f"BALLS: {len(self.balls)}", True, (255, 255, 0))
            multi_ball_rect = multi_ball_text.get_rect(topright=(self.screen_width - ui_margin, ui_top + 40))
            self.screen.blit(multi_ball_text, multi_ball_rect)
        
        # Power-up indicators (right side, below lives)
        indicator_y = ui_top + 70
        if self.paddle.has_laser:
            laser_indicator = self.message_font.render("⚡ LASER", True, (255, 60, 60))
            laser_rect = laser_indicator.get_rect(topright=(self.screen_width - ui_margin, indicator_y))
            self.screen.blit(laser_indicator, laser_rect)
            indicator_y += 25
        if self.paddle.has_glue:
            glue_indicator = self.message_font.render("🔗 CATCH", True, (60, 255, 60))
            glue_rect = glue_indicator.get_rect(topright=(self.screen_width - ui_margin, indicator_y))
            self.screen.blit(glue_indicator, glue_rect)
            indicator_y += 25
        if self.paddle.power_up_timers['grow'] > 0:
            grow_indicator = self.message_font.render("📏 GROW", True, (60, 60, 255))
            grow_rect = grow_indicator.get_rect(topright=(self.screen_width - ui_margin, indicator_y))
            self.screen.blit(grow_indicator, grow_rect)

    def _draw_level_complete_screen(self):
        """Draws the level complete screen."""
        self._draw_playing_screen()  # Draw game elements in background
        
        # Semi-transparent overlay with better styling
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 50))  # Dark blue tint
        self.screen.blit(overlay, (0, 0))
        
        # Stylized level complete text
        level_complete_text = self.game_font.render(f"LEVEL {self.level - 1} COMPLETE!", True, (255, 215, 0))  # Gold
        level_complete_rect = level_complete_text.get_rect(center=(self.screen_width / 2, self.screen_height / 2 - 40))
        self.screen.blit(level_complete_text, level_complete_rect)
        
        # Score bonus display
        bonus_score = 100 * (self.level - 1)
        bonus_text = self.message_font.render(f"Level Bonus: +{bonus_score} points", True, (100, 255, 100))
        bonus_rect = bonus_text.get_rect(center=(self.screen_width / 2, self.screen_height / 2))
        self.screen.blit(bonus_text, bonus_rect)
        
        next_level_text = self.message_font.render(f"Preparing Level {self.level}...", True, (200, 200, 200))
        next_level_rect = next_level_text.get_rect(center=(self.screen_width / 2, self.screen_height / 2 + 40))
        self.screen.blit(next_level_text, next_level_rect)

    def _draw_end_screen(self):
        """Draws elements for 'game over' or 'you win' screens."""
        if self.game_state == self.GAME_STATE_WIN:
            for firework in self.fireworks:
                firework.draw(self.screen)

        if self.game_state == self.GAME_STATE_GAME_OVER:
            message = "GAME OVER"
            color = (255, 100, 100)  # Red
        else:
            message = "CONGRATULATIONS!"
            color = (100, 255, 100)  # Green
            
        text_surface = self.game_font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2 - 50))
        self.screen.blit(text_surface, text_rect)
        
        if self.game_state == self.GAME_STATE_WIN:
            win_text = self.message_font.render("You completed all levels!", True, (255, 255, 255))
            win_rect = win_text.get_rect(center=(self.screen_width / 2, self.screen_height / 2 - 10))
            self.screen.blit(win_text, win_rect)
        
        score_text = self.message_font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.screen_width / 2, self.screen_height / 2 + 20))
        self.screen.blit(score_text, score_rect)
        
        restart_surface = self.message_font.render("Press SPACE to return to Title", True, (200, 200, 200))
        restart_rect = restart_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2 + 60))
        self.screen.blit(restart_surface, restart_rect)

    def _draw_mute_button(self):
        """Draws the mute button with improved styling."""
        # Enhanced mute button styling
        button_color = (70, 130, 180) if self.sound_enabled else (220, 20, 60)  # Steel blue or crimson
        border_color = (255, 255, 255)
        
        # Draw button with rounded corners effect
        pygame.draw.rect(self.screen, button_color, self.mute_button_rect)
        pygame.draw.rect(self.screen, border_color, self.mute_button_rect, 2)
        
        # Add subtle shadow effect
        shadow_rect = pygame.Rect(self.mute_button_rect.x + 2, self.mute_button_rect.y + 2, 
                                  self.mute_button_rect.width, self.mute_button_rect.height)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_rect)
        pygame.draw.rect(self.screen, button_color, self.mute_button_rect)
        pygame.draw.rect(self.screen, border_color, self.mute_button_rect, 2)
        
        # Better button text
        button_text = "🔊 ON" if self.sound_enabled else "🔇 OFF"
        font_size = 18
        button_font = pygame.font.Font(None, font_size)
        text_surface = button_font.render(button_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.mute_button_rect.center)
        self.screen.blit(text_surface, text_rect)

    def run(self):
        """The main game loop."""
        while self.running:
            self._handle_input() # Process user input
            self._update_game_logic() # Update game state
            self._draw_elements() # Render graphics
            self.clock.tick(60) # Control frame rate to 60 FPS

        pygame.quit() # Uninitialize Pygame modules
        sys.exit() # Exit the program

# Main execution block
if __name__ == "__main__":
    game = Game() # Create an instance of the Game class
    game.run() # Start the game loop

