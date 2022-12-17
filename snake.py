import random
import pygame
import time
import pygame.gfxdraw
import rx
import rx.operators as rx_ops

class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Snake:
    def __init__(self):
        self.__position = Position(100, 50)

        self.size = 10
        self.body_color: pygame.Color = pygame.Color("green")
        self.body = [[100, 50], [90, 50], [80, 50], [70, 50]]
    
    def get_position(self):
        return self.__position

    def move(self, dx: int, dy: int) -> None:
        self.__position.x += dx
        self.__position.y += dy
        self.body.insert(0, [self.__position.x, self.__position.y])
        self.body.pop()

    def grow(self) -> None:
        self.body.insert(0, [self.__position.x, self.__position.y])
    
    def draw(self, surface: pygame.Surface) -> None:
        for block in self.body:
            block_rect = pygame.Rect(block[0], block[1], self.size, self.size)
            pygame.draw.rect(surface, self.body_color, block_rect)

    def has_eaten_itself(self):
        for i in range(1, len(self.body)):
            block = self.body[i]
            if block[0] == self.__position.x and block[1] == self.__position.y:
                return True
        return False


class Fruit:
    def __init__(self, position: Position, size: int=10):
        self.__position = position
        self.__size = size
        self.__color = pygame.Color("red")
        self.__fruit = pygame.Rect(self.__position.x, self.__position.y, self.__size, self.__size)
    
    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.__color, self.__fruit)
    
    def move(self, dx: int, dy: int) -> None:
        self.__position.x += dx
        self.__position.y += dy
        self.__fruit.move_ip(self.__position.x, self.__position.y)

    def get_position(self) -> Position:
        return self.__position


class SystemFontService:
    def __init__(self, font_size: int, name: str="times new roman"):
        self.__font = pygame.font.SysFont(name, size=font_size)
        self.__font_size = font_size
        self.center_margin = 100

    def draw_text(self, text: str, surface: pygame.Surface, position: Position, color: pygame.Color) -> None:
        text_surface = self.__font.render(text, True, color)
        surface.blit(text_surface, (position.x, position.y))
    
    def draw_text_at_center(self, text: str, surface: pygame.Surface, color: pygame.Color) -> None:
        text_surface = self.__font.render(text, True, color)
        text_rect = text_surface.get_rect()
        surface_dimensions = surface.get_size()
        text_rect.midtop = (surface_dimensions[0]//2, surface_dimensions[1]//2 - self.center_margin)
        surface.blit(text_surface, text_rect)

class SystemFontServiceSmall(SystemFontService):
    def __init__(self, name: str = "times new roman"):
        super().__init__(18, name)

class SystemFontServiceLarge(SystemFontService):
    def __init__(self, name: str = "times new roman"):
        super().__init__(44, name)


class GameSoundService:
    def __init__(self) -> None:
        self.background_music_file: str = "./sounds/background.ogg"
        self.fruit_eaten_sound_file: str = "./sounds/fruit_eaten.wav"
        self.game_over_sound_file: str = "./sounds/game_over.wav"
        self.volume: float = 5.0
        pygame.mixer.music.set_volume(self.volume)

    def play_background_music(self) -> None:
        self.__play(self.background_music_file, loops=-1)
    
    def play_fruit_eaten_sound(self) -> None:
        self.__play(self.fruit_eaten_sound_file)
        pygame.mixer.music.queue(self.background_music_file)
    
    def play_game_over_sound(self) -> None:
        self.__play(self.game_over_sound_file)

    @staticmethod
    def __play(file: str, loops=0) -> None:
        pygame.mixer.music.unload()
        pygame.mixer.music.load(file)
        pygame.mixer.music.play(loops)


class Game:
    def __init__(self):
        self.window_fill_color = pygame.Color("black")
        self.window_top_margin = 30
        self.window_width = 500
        self.window_height = 500
        self.window_dimensions = (self.window_width, self.window_height)
        self.window_caption = "Snake Game By Kirabo Ibrahim <3"
        

        self.snake = None
        self.fruit = None
        self.score_size = 10
        self.score = 0
        self.crawl_size = 10

        self.system_font_service_small = SystemFontServiceSmall()
        self.system_font_service_large = SystemFontServiceLarge()
        self.game_sound_service = GameSoundService()

        self.direction_changes = (self.crawl_size, 0) # The changes in displacement in both x and y direction
        self.direction = "R"
        self.quit_game = False

        self.framerate = 10
        self.clock = pygame.time.Clock()

    def start(self):
        self.window = pygame.display.set_mode(self.window_dimensions)
        self.window.fill(self.window_fill_color)
        pygame.display.set_caption(self.window_caption)
        
        self.game_sound_service.play_background_music()
        
        self.spawn_fruit()
        self.spawn_snake()

        while not self.quit_game:
            self.clear_screen()
            self.draw_score_board()
            self.draw_game_panel_separator()

            for event in pygame.event.get():
                if self.is_quit_event(event):
                    self.quit_game = True
                self.direction_changes = self.get_direction_changes(event)

            self.snake.move(self.direction_changes[0], self.direction_changes[1])
            self.snake.draw(self.window)

            if self.is_game_over():
                self.game_over()
            else:
                if self.has_snake_eaten_fruit():
                    self.update_player_score()
                    self.snake.grow()
                    self.game_sound_service.play_fruit_eaten_sound()
                    self.spawn_fruit()
                else:
                    self.re_draw_fruit()

            pygame.display.update()
            self.clock.tick(self.framerate)

        self.quit()

    def update_player_score(self) -> None:
        self.score += self.score_size

    def draw_score_board(self):
        score_position = Position(10, 5)
        self.system_font_service_small.draw_text("Score: {}".format(self.score), self.window, score_position, pygame.Color("white"))
    
    def draw_game_panel_separator(self):
        pygame.gfxdraw.hline(self.window, 0, self.window_width, self.window_top_margin, 
                            pygame.Color("white"))

    def spawn_fruit(self) -> None:
        fruit_position = self.generate_fruit_position()
        self.fruit = Fruit(fruit_position)
        self.fruit.draw(self.window)

    def generate_fruit_position(self) -> Position:
        """
        Movement of the snake is increments of crawl_size, so the position of the fruit should be a multiple of 
        crawl size in order to avoid misalignment btn the snake body and the fruit
        """
        position_x = random.randint(1, self.window_width//self.crawl_size) * self.crawl_size
        position_y = random.randint(self.window_top_margin//self.crawl_size, self.window_height//self.crawl_size) * self.crawl_size
        return Position(position_x, position_y)

    def re_draw_fruit(self):
        self.fruit.draw(self.window)

    def spawn_snake(self) -> None:
        self.snake = Snake()
        self.snake.draw(self.window)

    def has_snake_eaten_fruit(self) -> bool:
        fruit_position = self.fruit.get_position()
        snake_position = self.snake.get_position()
        if fruit_position.x == snake_position.x and fruit_position.y == snake_position.y:
            return True
        return False

    def is_game_over(self) -> bool:
        if self.has_snake_collided_with_walls() or self.snake.has_eaten_itself():
            return True
        return False

    def has_snake_collided_with_walls(self) -> bool:
        snake_position = self.snake.get_position()
        if snake_position.x < 0 or snake_position.x > self.window_width - self.snake.size:
            return True
        if snake_position.y < self.window_top_margin or snake_position.y > self.window_height - self.snake.size:
            return True
        return False
    
    def game_over(self):
        self.clear_screen()
        self.draw_score_board()
        self.draw_game_panel_separator()
        self.system_font_service_large.draw_text_at_center("Game Over :(", self.window, pygame.Color("red"))
        self.game_sound_service.play_game_over_sound()

    def clear_screen(self) -> None:
        self.window.fill(self.window_fill_color)

    def quit(self) -> None:
        pygame.quit()

    @staticmethod
    def is_quit_event(event: pygame.event.Event) -> bool:
        return event.type == pygame.QUIT
    
    def get_direction_changes(self, event: pygame.event.Event) -> tuple[int, int]:
        if self.is_arrow_key_pressed_event(event):
            if event.key == pygame.K_LEFT and self.direction != "R":
                self.direction = "L"
                return (-1 * self.crawl_size, 0)
            elif event.key == pygame.K_RIGHT and self.direction != "L":
                self.direction = "R"
                return (self.crawl_size, 0)     
            elif event.key == pygame.K_UP and self.direction != "D":
                self.direction = "U"
                return (0, -1 * self.crawl_size)
            elif event.key == pygame.K_DOWN and self.direction != "U":
                self.direction = "D"
                return (0, self.crawl_size)
        return self.direction_changes
    
    @staticmethod
    def is_arrow_key_pressed_event(event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            return (event.key == pygame.K_LEFT) or \
            (event.key == pygame.K_UP) or \
            (event.key == pygame.K_DOWN) or \
            (event.key == pygame.K_RIGHT)
        return False


if __name__ == "__main__":
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    game = Game()
    game.start()


class GameEventsService:
    def __init__(self):
        self.all_events = rx.timer(0, 0).pipe(
            rx_ops.map(lambda _: pygame.event.get()),
            rx_ops.filter(lambda events: events != []),
            rx_ops.filter(lambda events: filter(lambda event: event.type != pygame.NOEVENT, events))
        )
        self.arrow_keys_events = self.all_events.pipe(
            rx_ops.filter(lambda events: filter(lambda event: event.type == pygame.KEYDOWN, events)),
            rx_ops.filter(lambda events: filter(self.is_arrow_key_event, events))
        )
        self.quit_event = self.all_events.pipe(
            rx_ops.filter(lambda events: filter(lambda event: event.type == pygame.QUIT, events))
        )
    
    @staticmethod
    def is_arrow_key_event(event):
        return (event.key == pygame.K_LEFT) or \
        (event.key == pygame.K_UP) or \
        (event.key == pygame.K_DOWN) or \
        (event.key == pygame.K_RIGHT)
