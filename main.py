import pygame
import multiprocessing

pygame.init()

SIZE = WIDTH, HEIGHT = 750, 750
HALF_WIDTH, HALF_HEIGHT = WIDTH // 2, HEIGHT // 2

class Pickler:
    @staticmethod
    def pickle_surface(surface, color):
        return {'size': surface.get_size(), 'width': surface.get_width(), 'height': surface.get_height(), 'color': color}

    @staticmethod
    def unpickle_surface(surface):
        #print(surface)
        new_surface = pygame.Surface(surface['size'])
        new_surface.fill(surface['color'])
        return new_surface

class Entity:
    def __init__(self):
        self.surface = self.surface = {'size': (100, 100), 'width': 100, 'height': 100, 'color': 'purple'} #pygame.Surface((50, 50))
        self.position = pygame.Vector2(100, 100)
        self.rect = pygame.Rect(self.position, (self.surface['size'])) #self.surface.get_rect(center=(100, 100))

    def update(self, positions):
        """ Can't use pygame.Vector2 since it gets pickled into a tuple """
        key = pygame.key.get_pressed()

        if key[pygame.K_w]:
            positions['player'] = positions['player'][0], positions['player'][1] - 1
        if key[pygame.K_s]:
            positions['player'] = positions['player'][0], positions['player'][1] + 1
        if key[pygame.K_a]:
            positions['player'] = positions['player'][0] - 1, positions['player'][1]
        if key[pygame.K_d]:
            positions['player'] = positions['player'][0] + 1, positions['player'][1]

    def draw(self, surface, screen_position, self_surface, positions):
        offset = screen_position[0] + positions['player'][0], screen_position[1] + positions['player'][1]
        self.rect = self_surface.get_rect(center=offset)
        self_surface.fill(self.surface['color'])

        surface.blit(self_surface, self.rect)

class Screen:
    """ Maybe screen should hold it's own objects """
    def __init__(self, index, position, color):
        self.index = index
        self.color = color
        self.surface = {'size': (HALF_WIDTH, HALF_HEIGHT), 'width': HALF_WIDTH, 'height': HALF_HEIGHT, 'color': color}
        self.position = position
        #self.surface = pygame.Surface((HALF_WIDTH, HALF_HEIGHT))
        #self.surface.fill(color)
        self.rect = pygame.Rect(self.position, (self.surface['size'])) #self.surface.get_rect(topleft=position)

        self._selected = False

    @property
    def selected(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def update(self, selections, window_focused):
        """ Must use keys() Flashing due to windows resetting selected values """
        if window_focused:
            for selected in selections.keys():
                if selected == self.index:
                    selections[selected] = True
                else:
                    selections[selected] = False


    def draw(self, surface, self_surface, selections):
        self.rect = self_surface.get_rect(topleft=self.position)
        self_surface.fill(self.color)
        if selections[self.index]:
            rect = self_surface.get_rect()
            pygame.draw.rect(self_surface, 'white', rect, 10)
        surface.blit(self_surface, self.rect)


def update_everything(screens, objects, positions, selected, window_focused):
    for screen in screens:
        screen.update(selected, window_focused)
    for obj in objects:
        obj.update(positions)

def draw_to_all_screens(window, screens, objects, positions, selections):
    """ Recreate every surface in every window then blit
        Can no longer blit to individual screens, they are destroyed when function ends
    """
    unpickled_screen_surfaces = [Pickler.unpickle_surface(screen.surface) for screen in screens]
    unpickled_object_surfaces = [Pickler.unpickle_surface(obj.surface) for obj in objects]
    window.fill('black')

    for i, (screen, unpickled_screen_surface) in enumerate(zip(screens, unpickled_screen_surfaces)):
        screen.draw(window, unpickled_screen_surface, selections)
    # screens index might be shifting around, need testing, maybe use dict
    for selected in selections.keys():
        if selections[selected]:
            for obj, unpickled_obj_surface in zip(objects, unpickled_object_surfaces):
                obj.draw(window, screens[selected].rect.topleft, unpickled_obj_surface, positions)


def main(shared_screens, shared_objects, shared_positions, selected):
    window = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()
    window_focused = False  # Needs to be shared?

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.WINDOWFOCUSGAINED:
                window_focused = True
            elif event.type == pygame.WINDOWFOCUSLOST:
                window_focused = False

        update_everything(shared_screens, shared_objects, shared_positions, selected, window_focused)
        draw_to_all_screens(window, shared_screens, shared_objects, shared_positions, selected)
        pygame.display.update()
        pygame.display.set_caption(f"FPS: {clock.get_fps():.0f}")

def do_multiprocessing():
    total_windows = 4
    manager = multiprocessing.Manager()
    #lock = multiprocessing.Lock()
    shared_positions = manager.dict()
    shared_screens = manager.list()
    shared_objects = manager.list()
    selected = manager.dict()

    player = Entity()
    screen_one = Screen(0, (0, 0), 'red')
    screen_two = Screen(1, (HALF_WIDTH, 0), 'green')
    screen_three = Screen(0, (0, HALF_HEIGHT), 'yellow')
    screen_four = Screen(0, (HALF_WIDTH, HALF_HEIGHT), 'cyan')

    shared_positions.update({'player': pygame.Vector2(100, 100)})
    shared_screens += [screen_one, screen_two, screen_three, screen_four]
    shared_objects += [player]
    selected.update({i: False for i, screen in enumerate(shared_screens)})
    processes = [multiprocessing.Process(target=main, args=(shared_screens, shared_objects, shared_positions, selected)) for _ in range(total_windows)]
    [process.start() for process in processes]
    [process.join() for process in processes]

if __name__ == '__main__':
    #main()
    do_multiprocessing()
