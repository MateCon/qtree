import pygame
import random
from abc import ABC, abstractmethod


class Vector2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def zero():
        return Vector2D(0, 0)

    @staticmethod
    def random(rect):
        return Vector2D(random.randint(rect.position.x, rect.position.x + rect.dimensions.x), random.randint(rect.position.y, rect.position.y + rect.dimensions.y))

    def copy(self):
        return Vector2D(self.x, self.y)

    def asTuple(self):
        return (self.x, self.y)

    def minus(self, point):
        return Vector2D(self.x - point.x, self.y - point.y)
    
    def multiplied(self, point):
        return Vector2D(self.x * point.x, self.y * point.y)

    def divided(self, point):
        return Vector2D(self.x / point.x, self.y / point.y)


class Rectangle:
    def __init__(self, position, dimensions):
        self.position = position.copy()
        self.dimensions = dimensions.copy()

    def copy(self):
        return Rectangle(self.position.copy(), self.dimensions.copy())

    def topLeft(self):
        return Rectangle(Vector2D(self.position.x, self.position.y), Vector2D(self.dimensions.x / 2, self.dimensions.y / 2))

    def topRight(self):
        return Rectangle(Vector2D(self.position.x + self.dimensions.x / 2, self.position.y), Vector2D(self.dimensions.x / 2, self.dimensions.y / 2))

    def bottomLeft(self):
        return Rectangle(Vector2D(self.position.x, self.position.y + self.dimensions.y / 2), Vector2D(self.dimensions.x / 2, self.dimensions.y / 2))

    def bottomRight(self):
        return Rectangle(Vector2D(self.position.x + self.dimensions.x / 2, self.position.y + self.dimensions.y / 2), Vector2D(self.dimensions.x / 2, self.dimensions.y / 2))

    def contains(self, point):
        return point.x >= self.position.x and point.x < self.position.x + self.dimensions.x and point.y >= self.position.y and point.y < self.position.y + self.dimensions.y

    def intersects(self, rect) -> bool:
        return not (self.position.x + self.dimensions.x < rect.position.x or self.position.x > rect.position.x + rect.dimensions.x or self.position.y + self.dimensions.y < rect.position.y or self.position.y > rect.position.y + rect.dimensions.y)


class QTree(ABC):
    @abstractmethod
    def add(self, point) -> "QTree":
        pass

    @abstractmethod
    def contains(self, point) -> bool:
        pass

    @abstractmethod
    def doForAreas(self, action):
        pass

    @abstractmethod
    def doForPoints(self, action):
        pass

    @abstractmethod
    def doForPointsInArea(self, action, area):
        pass


class BaseQTree(QTree):
    def __init__(self, rect):
        self.area = rect.copy()
        self.points = []

    def add(self, point):
        self.points.append(point)
        if len(self.points) >= 10:
            return RecQTree(self.area, self.points)
        return self

    def contains(self, point) -> bool:
        return self.area.contains(point)

    def intersects(self, rect) -> bool:
        return self.area.intersects(rect)

    def doForAreas(self, action):
        action(self.area)

    def doForPoints(self, action):
        for point in self.points:
            action(point)

    def doForPointsInArea(self, action, area):
        for point in self.points:
            if area.contains(point):
                action(point)

    def countPointsInArea(self, area):
        c = 0
        for point in self.points:
            if area.contains(point):
                c += 1
        return c


class RecQTree(QTree):
    def __init__(self, rect, points):
        self.area = rect.copy()
        self.topLeft = BaseQTree(rect.topLeft())
        self.topRight = BaseQTree(rect.topRight())
        self.bottomLeft = BaseQTree(rect.bottomLeft())
        self.bottomRight = BaseQTree(rect.bottomRight())
        for point in points:
            self.add(point)

    def add(self, point):
        if self.topLeft.contains(point):
            self.topLeft = self.topLeft.add(point)
        if self.topRight.contains(point):
            self.topRight = self.topRight.add(point)
        if self.bottomLeft.contains(point):
            self.bottomLeft = self.bottomLeft.add(point)
        if self.bottomRight.contains(point):
            self.bottomRight = self.bottomRight.add(point)
        return self

    def contains(self, point) -> bool:
        return self.area.contains(point)

    def intersects(self, rect) -> bool:
        return self.area.intersects(rect)

    def doForAreas(self, action):
        action(self.area)
        for subtree in [self.topLeft, self.topRight, self.bottomLeft, self.bottomRight]:
            subtree.doForAreas(action)

    def doForPoints(self, action):
        for subtree in [self.topLeft, self.topRight, self.bottomLeft, self.bottomRight]:
            subtree.doForPoints(action)

    def doForPointsInArea(self, action, area):
        for subtree in [self.topLeft, self.topRight, self.bottomLeft, self.bottomRight]:
            if subtree.intersects(area):
                subtree.doForPointsInArea(action, area)

    def countPointsInArea(self, area):
        c = 0
        for subtree in [self.topLeft, self.topRight, self.bottomLeft, self.bottomRight]:
            if subtree.intersects(area):
                c += subtree.countPointsInArea(area)
        return c



def main():
    pygame.init()
    size = Vector2D(1280, 720)
    screenArea = Rectangle(Vector2D.zero(), size)
    screen = pygame.display.set_mode(size.asTuple())
    clock = pygame.time.Clock()
    running = True
    scanRadious = 50

    qtree = BaseQTree(screenArea)

    for _ in range(100000):
        qtree = qtree.add(Vector2D.random(screenArea))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                scanRadious = max(scanRadious + event.y * 4, 0)


        screen.fill("black")

        mousePos = pygame.mouse.get_pos()
        scanArea = Rectangle(Vector2D(mousePos[0] - scanRadious, mousePos[1] - scanRadious), Vector2D(scanRadious * 2, scanRadious * 2))

        # Scan mode
        # qtree.doForAreas(lambda area: pygame.draw.rect(screen, "white", pygame.Rect(area.position.x, area.position.y, area.dimensions.x, area.dimensions.y), 1))
        qtree.doForPoints(lambda point: pygame.draw.circle(screen, "white", point.asTuple(), 1))
        qtree.doForPointsInArea(lambda point: pygame.draw.circle(screen, "green", point.asTuple(), 1), scanArea)
        print(qtree.countPointsInArea(scanArea))
        pygame.draw.rect(screen, "green", pygame.Rect(scanArea.position.x, scanArea.position.y, scanArea.dimensions.x, scanArea.dimensions.y), 2)
        pygame.draw.rect(screen, (0, 255, 0, 0.2), pygame.Rect(scanArea.position.x, scanArea.position.y, scanArea.dimensions.x, scanArea.dimensions.y), 2)

        # Navigate mode
        # qtree.doForPointsInArea(lambda point: pygame.draw.circle(screen, "green", point.minus(scanArea.position).divided(scanArea.dimensions).multiplied(size).asTuple(), 1), scanArea)

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
