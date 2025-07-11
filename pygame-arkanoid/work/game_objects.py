import pygame
import random
import math

# Initialize the font module for the power-up letters
# This initialization is placed here because PowerUp class uses it.
# In a larger project, font initialization might be centralized.
pygame.font.init()
POWERUP_FONT = pygame.font.Font(None, 20)

class Paddle(pygame.sprite.Sprite):
    """
    Represents the player's paddle. Handles movement, power-up effects,
    and drawing.
    """
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original_width = 100
        self.height = 10
        self.speed = 7
        self.color = (200, 200, 200) # Light grey

        self.width = self.original_width
        
        # Dictionary to manage power-up timers (in frames)
        self.power_up_timers = {
            'grow': 0,
            'laser': 0,
            'glue': 0
        }
        self.has_laser = False
        self.has_glue = False

        # Create the paddle's rectangle for position and collision
        self.rect = pygame.Rect(
            self.screen_width // 2 - self.width // 2,
            self.screen_height - 30,
            self.width,
            self.height
        )

    def reset(self):
        """Resets the paddle to its initial state."""
        self.rect.x = self.screen_width // 2 - self.original_width // 2
        self.width = self.original_width
        self.rect.width = self.width # Update rect width after changing self.width
        self.has_laser = False
        self.has_glue = False
        for power_up in self.power_up_timers:
            self.power_up_timers[power_up] = 0

    def update(self):
        """Updates the paddle's position based on keyboard input and power-up timers."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # Keep paddle within screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
            
        self._update_power_ups()

    def draw(self, screen):
        """Draws the paddle on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)
        
    def activate_power_up(self, type):
        """
        Activates a specific power-up for a set duration.
        Duration is in frames (600 frames = 10 seconds at 60 FPS).
        """
        duration = 600 
        if type == 'grow':
            # Only apply grow effect if not already active to prevent multiple resizing
            if self.power_up_timers['grow'] <= 0:
                current_center = self.rect.centerx
                self.width = 150 # Wider paddle
                self.rect.width = self.width
                self.rect.centerx = current_center # Maintain center position
            self.power_up_timers['grow'] = duration
        elif type == 'laser':
            self.has_laser = True
            self.power_up_timers['laser'] = duration
        elif type == 'glue':
            self.has_glue = True
            self.power_up_timers['glue'] = duration
            
    def _update_power_ups(self):
        """Decrements power-up timers and deactivates effects when timers run out."""
        if self.power_up_timers['grow'] > 0:
            self.power_up_timers['grow'] -= 1
            if self.power_up_timers['grow'] <= 0:
                # Revert to original width when timer expires
                current_center = self.rect.centerx
                self.width = self.original_width
                self.rect.width = self.width
                self.rect.centerx = current_center
        if self.power_up_timers['laser'] > 0:
            self.power_up_timers['laser'] -= 1
            if self.power_up_timers['laser'] <= 0:
                self.has_laser = False
        if self.power_up_timers['glue'] > 0:
            self.power_up_timers['glue'] -= 1
            if self.power_up_timers['glue'] <= 0:
                self.has_glue = False


class Ball(pygame.sprite.Sprite):
    """
    Represents the game ball. Handles movement, collisions with walls/paddle,
    and power-up effects (slow).
    """
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 10
        self.color = (200, 200, 200) # Light grey
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        
        self.is_glued = False # True if ball is stuck to paddle (from glue power-up)
        self.is_slowed = False # True if ball speed is reduced (from slow power-up)
        self.slow_timer = 0 # Timer for slow power-up
        self.base_speed = 6 # Normal speed of the ball
        
        self.reset()

    def reset(self):
        """Resets the ball to its initial position and speed."""
        self.rect.center = (self.screen_width // 2, self.screen_height // 2 + 100) # Start slightly lower
        self.speed_x = self.base_speed * random.choice((1, -1)) # Random horizontal direction
        self.speed_y = -self.base_speed # Always start moving upwards
        self.is_glued = True # Ball starts glued to the paddle
        self.is_slowed = False
        self.slow_timer = 0

    def update(self, paddle, launch_ball=False):
        """
        Updates the ball's position and handles collisions.
        Returns game status ('playing', 'lost') and collision object ('wall', 'paddle', None).
        """
        collision_object = None

        if self.is_glued:
            # If glued, follow the paddle's center
            self.rect.centerx = paddle.rect.centerx
            self.rect.bottom = paddle.rect.top
            if launch_ball: # If spacebar is pressed while glued
                self.is_glued = False
                # Re-initialize speed to ensure consistent launch angle
                self.speed_x = self.base_speed * random.choice((1, -1))
                self.speed_y = -self.base_speed
            return 'playing', None # No further movement or collision if glued

        if self.is_slowed:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                # Revert to normal speed when slow timer expires
                self.speed_x = self.speed_x * 2
                self.speed_y = self.speed_y * 2
                self.is_slowed = False

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Wall collisions
        if self.rect.top <= 0:
            self.speed_y *= -1
            self.rect.top = 0 # Prevent sticking
            collision_object = 'wall'
        if self.rect.left <= 0:
            self.speed_x *= -1
            self.rect.left = 0 # Prevent sticking
            collision_object = 'wall'
        if self.rect.right >= self.screen_width:
            self.speed_x *= -1
            self.rect.right = self.screen_width # Prevent sticking
            collision_object = 'wall'

        # Paddle collision
        # Check if ball collides with paddle and is moving downwards
        if self.rect.colliderect(paddle.rect) and self.speed_y > 0:
            if paddle.has_glue:
                self.is_glued = True
            self.speed_y *= -1 # Reverse vertical direction

            # Calculate bounce angle based on hit position on paddle
            # This makes the game more dynamic and skill-based
            relative_intersect_x = self.rect.centerx - paddle.rect.centerx
            normalized_intersect_x = relative_intersect_x / (paddle.width / 2)
            bounce_angle = normalized_intersect_x * (math.pi / 3) # Max 60 degrees from vertical
            
            # Ensure minimum speed to prevent horizontal stalling
            min_speed = 0.5 
            self.speed_x = self.base_speed * math.sin(bounce_angle)
            self.speed_y = -self.base_speed * math.cos(bounce_angle)
            
            # Prevent ball from getting stuck in paddle
            self.rect.bottom = paddle.rect.top 
            collision_object = 'paddle'
        
        # Check if ball falls below the screen (lose condition)
        if self.rect.top > self.screen_height:
            return 'lost', None
        
        return 'playing', collision_object

    def draw(self, screen):
        """Draws the ball on the screen."""
        pygame.draw.ellipse(screen, self.color, self.rect)
        
    def activate_power_up(self, type):
        """Activates a power-up effect on the ball."""
        if type == 'slow' and not self.is_slowed:
            self.speed_x /= 2
            self.speed_y /= 2
            self.is_slowed = True
            self.slow_timer = 600 # 10 seconds duration


class Brick(pygame.sprite.Sprite):
    """
    Represents a single brick.
    """
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, screen):
        """Draws the brick on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)


class PowerUp(pygame.sprite.Sprite):
    """
    Represents a power-up item that drops from destroyed bricks.
    """
    # Static dictionary to define properties for different power-up types
    PROPERTIES = {
        'grow': {'color': (60, 60, 255), 'char': 'G', 'message': 'PADDLE GROW'},
        'laser': {'color': (255, 60, 60), 'char': 'L', 'message': 'LASER CANNONS'},
        'glue': {'color': (60, 255, 60), 'char': 'C', 'message': 'CATCH PADDLE'},
        'slow': {'color': (255, 165, 0), 'char': 'S', 'message': 'SLOW BALL'},
        'multi_ball': {'color': (255, 60, 255), 'char': 'M', 'message': 'MULTI BALL'},
        'shield': {'color': (60, 255, 255), 'char': 'H', 'message': 'SHIELD (+1 LIFE)'},
    }
    
    def __init__(self, x, y, type):
        super().__init__()
        self.width = 30
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.speed_y = 3 # Speed at which power-up drops
        self.type = type # Type of power-up (e.g., 'grow', 'laser')
        self.color = self.PROPERTIES[type]['color']
        self.char = self.PROPERTIES[type]['char'] # Character to display on the power-up

    def update(self):
        """Updates the power-up's vertical position."""
        self.rect.y += self.speed_y

    def draw(self, screen):
        """Draws the power-up and its character on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)
        text_surf = POWERUP_FONT.render(self.char, True, (255, 255, 255)) # White text
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class Laser(pygame.sprite.Sprite):
    """
    Represents a laser beam fired by the paddle.
    """
    def __init__(self, x, y):
        super().__init__()
        self.width = 5
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = (255, 255, 0) # Yellow laser
        self.speed_y = -8 # Laser moves upwards

    def update(self):
        """Updates the laser's vertical position."""
        self.rect.y += self.speed_y

    def draw(self, screen):
        """Draws the laser on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)


class Particle:
    """
    Represents a single particle for visual effects (explosions, sparks).
    """
    def __init__(self, x, y, color, min_size, max_size, min_speed, max_speed, gravity):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(min_size, max_size)
        self.gravity = gravity # Affects vertical movement over time
        
        # Random initial velocity and angle for explosion effect
        angle = random.uniform(0, 360)
        speed = random.uniform(min_speed, max_speed)
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))

    def update(self):
        """Updates the particle's position and size."""
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity # Apply gravity
        self.size -= 0.1 # Particles shrink over time, eventually disappearing

    def draw(self, screen):
        """Draws the particle on the screen."""
        if self.size > 0: # Only draw if visible
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))


class Firework:
    """
    Represents a firework effect for the 'YOU WIN!' screen.
    Consists of a rocket phase and an explosion phase with particles.
    """
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = random.randint(0, screen_width) # Random horizontal starting position
        self.y = screen_height # Start from bottom of the screen
        self.vy = -random.uniform(8, 12) # Initial upward speed of the rocket
        self.color = (255, 255, 255) # White rocket
        self.exploded = False
        self.particles = [] # Particles for the explosion
        
        # Random height for explosion to occur
        self.explosion_y = random.uniform(screen_height * 0.2, screen_height * 0.5)

    def update(self):
        """Updates the firework's state (rocket flight or particle explosion)."""
        if not self.exploded:
            self.y += self.vy
            if self.y <= self.explosion_y:
                self.exploded = True
                # Generate explosion particles with a random color
                explosion_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in range(50): # Create 50 particles on explosion
                    self.particles.append(Particle(self.x, self.y, explosion_color, 2, 4, 1, 4, 0.1))
        else:
            # Update and remove dead particles
            for particle in self.particles[:]:
                particle.update()
                if particle.size <= 0:
                    self.particles.remove(particle)

    def draw(self, screen):
        """Draws the firework (rocket or explosion particles) on the screen."""
        if not self.exploded:
            # Draw the rocket as a small circle
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)
        else:
            # Draw all explosion particles
            for particle in self.particles:
                particle.draw(screen)

    def is_dead(self):
        """Checks if the firework has exploded and all its particles have disappeared."""
        return self.exploded and not self.particles

