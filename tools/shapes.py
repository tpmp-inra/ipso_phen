"""Point and Rectangle classes.

This code is in the public domain.

Point  -- point with (x,y) coordinates
Rect  -- two points, forming a rectangle
"""

from abc import ABC, abstractmethod

import cv2
import math


def tag_to_color(tag: str):
    if tag.lower() == 'keep':
        return 0, 128, 0
    elif tag.lower() == 'erode':
        return 80, 127, 255
    elif tag.lower() == 'safe':
        return 0, 255, 0
    elif tag.lower() == 'delete':
        return 0, 0, 255
    elif tag.lower() == 'enforce':
        return 255, 0, 255
    elif tag.lower() == 'dilate':
        return 255, 190, 84
    elif tag.lower() == 'open':
        return 255, 33, 0
    elif tag.lower() == 'close':
        return 0, 146, 255
    elif tag.lower() == 'process_roi':
        return 255, 255, 0
    else:
        return 255, 255, 255


class Point:
    """A point identified by (x,y) coordinates.

    supports: +, -, *, /, str, repr

    length  -- calculate length of vector to point from origin
    distance_to  -- calculate distance between two points
    as_tuple  -- construct tuple (x,y)
    clone  -- construct a duplicate
    integerize  -- convert x & y to integers
    floatize  -- convert x & y to floats
    move_to  -- reset x & y
    slide  -- move (in place) +dx, +dy, as spec'd by point
    slide_xy  -- move (in place) +dx, +dy
    rotate  -- rotate around the origin
    rotate_about  -- rotate around another point
    """

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, p):
        """Point(x1+x2, y1+y2)"""
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        """Point(x1-x2, y1-y2)"""
        return Point(self.x - p.x, self.y - p.y)

    def __mul__(self, scalar):
        """Point(x1*x2, y1*y2)"""
        return Point(self.x * scalar, self.y * scalar)

    def __div__(self, scalar):
        """Point(x1/x2, y1/y2)"""
        return Point(self.x / scalar, self.y / scalar)

    def __str__(self):
        return "(%s, %s)" % (self.x, self.y)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.x, self.y)

    def length(self):
        """Returns distance from origin to self

        Returns:
            float -- distance
        """

        return math.sqrt(self.x**2 + self.y**2)

    def distance_to(self, p):
        """Calculate the distance between two points."""
        return (self - p).length()

    def as_tuple(self):
        """(x, y)"""
        return self.x, self.y

    def copy(self):
        """Return a full copy of this point."""
        return Point(self.x, self.y)

    def integerize(self):
        """Convert co-ordinate values to integers."""
        self.x = int(self.x)
        self.y = int(self.y)

    def floatize(self):
        """Convert co-ordinate values to floats."""
        self.x = float(self.x)
        self.y = float(self.y)

    def move_to(self, x, y):
        """Reset x & y coordinates."""
        self.x = x
        self.y = y

    def slide(self, p):
        """Move to new (x+dx,y+dy).

        Can anyone think up a better name for this function?
        slide? shift? delta? move_by?
        """
        self.x = self.x + p.x
        self.y = self.y + p.y

    def slide_xy(self, dx, dy):
        """Move to new (x+dx,y+dy).

        Can anyone think up a better name for this function?
        slide? shift? delta? move_by?
        """
        self.x = self.x + dx
        self.y = self.y + dy

    def rotate(self, rad):
        """Rotate counter-clockwise by rad radians.

        Positive y goes *up,* as in traditional mathematics.

        Interestingly, you can use this in y-down computer graphics, if
        you just remember that it turns clockwise, rather than
        counter-clockwise.

        The new position is returned as a new Point.
        """
        s, c = [f(rad) for f in (math.sin, math.cos)]
        x, y = (c * self.x - s * self.y, s * self.x + c * self.y)
        return Point(x, y)

    def rotate_about(self, p, theta):
        """Rotate counter-clockwise around a point, by theta degrees.

        Positive y goes *up,* as in traditional mathematics.

        The new position is returned as a new Point.
        """
        result = self.copy()
        result.slide_xy(-p.x, -p.y)
        result.rotate(theta)
        result.slide_xy(p.x, p.y)
        return result


class Shape(ABC):

    @classmethod
    @abstractmethod
    def empty(cls):
        pass

    @abstractmethod
    def is_empty(self):
        pass

    @abstractmethod
    def contains(self, other):
        pass

    @abstractmethod
    def as_rect(self):
        pass

    @property
    @abstractmethod
    def top_left(self):
        pass

    @property
    @abstractmethod
    def top_center(self):
        pass

    @property
    @abstractmethod
    def top_right(self):
        pass

    @property
    @abstractmethod
    def middle_left(self):
        pass

    @property
    @abstractmethod
    def middle_center(self):
        pass

    @property
    @abstractmethod
    def middle_right(self):
        pass

    @property
    @abstractmethod
    def bottom_left(self):
        pass

    @property
    @abstractmethod
    def bottom_center(self):
        pass

    @property
    @abstractmethod
    def bottom_right(self):
        pass

    @property
    @abstractmethod
    def center(self):
        pass

    @property
    @abstractmethod
    def width(self):
        pass

    @width.setter
    @abstractmethod
    def width(self, value):
        pass

    @property
    @abstractmethod
    def height(self):
        pass

    @height.setter
    @abstractmethod
    def height(self, value):
        pass

    @property
    @abstractmethod
    def area(self):
        pass

    @property
    def ar(self):
        """Returns aspect ratio"""
        return self.width / self.height

    def point_at_position(self, position: str, round_position: bool = False) -> Point:
        """Return a point on the shape at a position

        :param position: string detailing the position
        :param round_position: if true result will components will be rounded
        :return: Point at position
        """
        if position.upper() == 'TOP_LEFT':
            pt = self.top_left
        elif position.upper() == 'TOP_CENTER':
            pt = self.top_center
        elif position.upper() == 'TOP_RIGHT':
            pt = self.top_right
        elif position.upper() == 'MIDDLE_LEFT':
            pt = self.middle_left
        elif position.upper() == 'MIDDLE_CENTER':
            pt = self.middle_center
        elif position.upper() == 'MIDDLE_RIGHT':
            pt = self.middle_right
        elif position.upper() == 'BOTTOM_LEFT':
            pt = self.bottom_left
        elif position.upper() == 'BOTTOM_CENTER':
            pt = self.bottom_center
        elif position.upper() == 'BOTTOM_RIGHT':
            pt = self.bottom_right
        else:
            pt = self.center

        if round_position:
            return Point(round(pt.x), round(pt.y))
        else:
            return pt

    @abstractmethod
    def draw_to(self, dst_img, color=None, line_width=-1):
        pass


class Rect(Shape):
    """A rectangle identified by two points.

    The rectangle stores left, top, right, and bottom values.

    Coordinates are based on screen coordinates.

    origin                               top
       +-----> x increases                |
       |                           left  -+-  right
       v                                  |
    y increases                         bottom

    set_points  -- reset rectangle coordinates
    contains  -- is a point inside?
    overlaps  -- does a rectangle overlap?
    top_left  -- get top-left corner
    bottom_right  -- get bottom-right corner
    expanded_by  -- grow (or shrink)
    """

    def __init__(self, pt1, pt2):
        """Initialize a rectangle from two points."""
        (x1, y1) = pt1.as_tuple()
        (x2, y2) = pt2.as_tuple()
        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)

    def copy(self):
        return Rect.from_coordinates(left=self.left, right=self.right, top=self.top, bottom=self.bottom)

    @classmethod
    def from_coordinates(cls, left, right, top, bottom):
        """Create rectangle independent coordinates"""
        return cls(Point(int(left), int(top)), Point(int(right), int(bottom)))

    @classmethod
    def from_lwth(cls, left, width, top, height):
        """Creates region of interrest from left, width, top, height

        Arguments:
            left {int} -- Left coordinate
            width {int} -- ROI width
            top {int} -- Right coordinate
            height {int} -- ROI height

        Raises:
            NotImplementedError -- Empty rects are not allowed
        """
        """Create rectangle independent coordinates"""
        return cls(Point(int(left), int(top)), Point(int(left + width), int(top + height)))

    @classmethod
    def empty(cls):
        """Create an empty rectangle"""
        return cls.from_coordinates(0, 0, 0, 0)

    def as_rect(self):
        return self

    def to_opencv(self):
        return self.left, self.top, self.width, self.height

    def is_empty(self):
        return (self.width == 0) or (self.height == 0)

    def contains(self, other):
        """Return true if a point or rectangle is inside the rectangle."""
        if isinstance(other, Point):
            x, y = other.as_tuple()
            return (self.left <= x <= self.right and self.top <= y <= self.bottom)
        elif isinstance(other, Rect):
            return (self.left <= other.left) and (self.right >= other.right) and (self.top <= other.top
                                                                                 ) and (self.bottom >= other.bottom)

    def overlaps(self, other):
        """Return true if a rectangle overlaps this rectangle."""
        return (
            self.right > other.left and self.left < other.right and self.top < other.bottom and self.bottom > other.top
        )

    def union(self, other):
        """Retrun the union of 2 rectangles"""
        self.left = min(self.left, other.left)
        self.right = max(self.right, other.right)
        self.top = min(self.top, other.top)
        self.bottom = max(self.bottom, other.bottom)

    def bound(self, other):
        """Retrun the intersection of 2 rectangles"""
        self.left = max(self.left, other.left)
        self.right = min(self.right, other.right)
        self.top = max(self.top, other.top)
        self.bottom = min(self.bottom, other.bottom)

    def inflate(self, dl, dr, dt, db):
        """Inflates self by d- in each direccion"""
        self.left -= dl
        self.right += dr
        self.top -= dt
        self.bottom += db

    def expanded_by(self, n):
        """Return a rectangle with extended borders.

        Create a new rectangle that is wider and taller than the
        immediate one. All sides are extended by "n" points.
        """
        p1 = Point(self.left - n, self.top - n)
        p2 = Point(self.right + n, self.bottom + n)
        return Rect(p1, p2)

    def __str__(self):
        return f'Rect:[l:{self.left}, w:{self.width}/t:{self.top}, h:{self.bottom}]'

    def __repr__(self):
        return f'Rect:[l:{self.left}, w:{self.width}/t:{self.top}, h:{self.bottom}]'

    def __eq__(self, other):
        return (self.left == other.left) and (self.right == other.right) and (self.top == other.top
                                                                             ) and (self.bottom == other.bottom)

    def __ne__(self, other):
        return (self.left != other.left) or (self.right != other.right) or (self.top !=
                                                                            other.top) or (self.bottom != other.bottom)

    def draw_to(self, dst_img, line_width=-1, color=None):
        if not color:
            color = 255
        return cv2.rectangle(dst_img.copy(), (self.left, self.top), (self.right, self.bottom), color, line_width)

    @property
    def top_left(self):
        return Point(self.left, self.top)

    @property
    def top_center(self):
        return Point(self.left + self.width / 2, self.top)

    @property
    def top_right(self):
        return Point(self.left + self.width, self.top)

    @property
    def middle_left(self):
        return Point(self.left, self.top + self.height / 2)

    @property
    def middle_center(self):
        return self.center

    @property
    def middle_right(self):
        return Point(self.right, self.top + self.height / 2)

    @property
    def bottom_left(self):
        return Point(self.left, self.bottom)

    @property
    def bottom_center(self):
        return Point(self.left + self.width / 2, self.bottom)

    @property
    def bottom_right(self):
        return Point(self.right, self.bottom)

    @property
    def center(self):
        return Point(self.left + round(self.width / 2), self.top + round(self.height / 2))

    @property
    def width(self):
        return self.right - self.left

    @width.setter
    def width(self, value):
        self.right = self.left + value

    @property
    def height(self):
        return self.bottom - self.top

    @height.setter
    def height(self, value):
        self.bottom = self.top + value

    @property
    def area(self):
        return self.width * self.height


class Circle(Shape):

    def __init__(self, center, radius):
        self._center = center
        self._radius = radius

    def __str__(self):
        return f"<Circle {repr(self.center)} - {self.radius}"

    def __repr__(self):
        return f'{self.__class__.__name__}, {repr(self.center)} - {self.radius}'

    def copy(self):
        return Circle(center=self.center.copy(), radius=self.radius)

    @classmethod
    def empty(cls):
        return Circle(0, 0)

    def is_empty(self):
        return self.radius == 0

    def contains(self, other):
        """Return true if a point is inside the rectangle."""
        if isinstance(other, Point):
            return self.center.distance_to(other) <= self.radius
        else:
            return False

    def point_at_angle(self, angle: float) -> Point:
        """Calculates the point in the border of the circle at a given angle

        :param angle: in radians
        :return: Point
        """
        return Point(self.center.x + self.radius * math.cos(angle), self.center.y + self.radius * math.sin(angle))

    def as_rect(self):
        return Rect.from_lwth(
            self.center.x - self.radius, 2 * self.radius, self.center.y - self.radius, 2 * self.radius
        )

    def draw_to(self, dst_img, line_width=-1, color=None):
        if not color:
            color = 255
        return cv2.circle(dst_img, (self.left, self.top), self.radius, color, line_width)

    @property
    def center(self):
        return self._center

    @property
    def radius(self):
        return self._radius

    @property
    def area(self):
        return 2 * math.pi * math.pow(self.radius, 2)

    @property
    def left(self):
        return self.center.x

    @property
    def top(self):
        return self.center.y

    @property
    def width(self):
        return self.radius * 2

    @width.setter
    def width(self, value):
        self._radius = value / 2

    @property
    def height(self):
        return self.radius * 2

    @height.setter
    def height(self, value):
        self._radius = value / 2

    @property
    def ar(self):
        """Returns aspect ratio"""
        return 1

    @property
    def top_left(self):
        return self.point_at_angle(3 * math.pi / 4)

    @property
    def top_center(self):
        return self.point_at_angle(math.pi / 2)

    @property
    def top_right(self):
        return self.point_at_angle(math.pi / 4)

    @property
    def middle_left(self):
        return self.point_at_angle(math.pi)

    @property
    def middle_center(self):
        return self.center

    @property
    def middle_right(self):
        return self.point_at_angle(0)

    @property
    def bottom_left(self):
        return self.point_at_angle(5 * math.pi / 4)

    @property
    def bottom_center(self):
        return self.point_at_angle(3 * math.pi / 2)

    @property
    def bottom_right(self):
        return self.point_at_angle(7 * math.pi / 4)


class RectangleOfInterest(Rect):
    """Rectangle of interest

    Arguments:
        pt1 {Point} -- Top left corner
        pt2 {Point} -- Bottom right corner
        name {str} -- ROI name

    Keyword Arguments:
        tag {str} -- Tag attached to ROI (default: {'None'})
        color {tuple} -- Print color (default: {(255,255,255)})

    Raises:
        NotImplementedError -- Empty rectangles are not allowed
    """

    def __init__(self, pt1, pt2, name, tag='None', color=None, target: str = ''):
        super().__init__(pt1, pt2)
        self._name = name
        self._tag = tag
        self._target = target

        if not color:
            color = tag_to_color(tag)
        self._color = color

    def __str__(self):
        return f'RectOI:[l:{self.left}, w:{self.width}/t:{self.top}, h:{self.bottom}-name:{self.name}, tag:{self.tag}]'

    def __repr__(self):
        return f'RectOI:[l:{self.left},w:{self.width}/t:{self.top},h:{self.bottom} - name:{self.name}, tag:{self.tag}]'

    def copy(self):
        return RectangleOfInterest.from_coordinates(
            left=self.left,
            right=self.right,
            top=self.top,
            bottom=self.bottom,
            name=self.name,
            tag=self.tag,
            color=self.color
        )

    @classmethod
    def from_coordinates(cls, left, right, top, bottom, name, tag='None', color=None, target: str = ''):
        """Creates region of interest from coordinates

        Arguments:
            left {int} -- Left coordinate
            top {int} -- Top coordinate
            right {int} -- Right coordinate
            bottom {int} -- Bottom coordinate
            name {str} -- ROI name

        Keyword Arguments:
            tag {str} -- Tag attached to ROI (default: {'None'})
            color {tuple} -- Print color (default: {(255,255,255)})

        Raises:
            NotImplementedError -- Empty rects are not allowed
        """
        """Create rectangle independent coordinates"""
        return cls(
            pt1=Point(int(left), int(top)),
            pt2=Point(int(right), int(bottom)),
            name=name,
            tag=tag,
            color=color,
            target=target
        )

    @classmethod
    def from_lwth(cls, left, width, top, height, name, tag='None', color=None, target: str = ''):
        """Creates region of interrest from left, width, top, height

        Arguments:
            left {int} -- Left coordinate
            width {int} -- ROI width
            top {int} -- Right coordinate
            height {int} -- ROI height
            name {str} -- ROI name

        Keyword Arguments:
            tag {str} -- Tag attached to ROI (default: {'None'})
            color {tuple} -- Print color (default: {(255,255,255)})

        Raises:
            NotImplementedError -- Empty rects are not allowed
        """
        """Create rectangle independent coordinates"""
        return cls(
            pt1=Point(int(left), int(top)),
            pt2=Point(int(left + width), int(top + height)),
            name=name,
            tag=tag,
            color=color,
            target=target
        )

    @classmethod
    def empty(cls):
        """Create an empty rectangle"""
        return cls.from_coordinates(0, 0, 0, 0, 'empty', 'empty', (0, 0, 255))

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color:
            return super(RectangleOfInterest, self).draw_to(dst_img, line_width, color)
        else:
            return super(RectangleOfInterest, self).draw_to(dst_img, line_width, self.color)

    def fill(self, dst_img, color):
        return cv2.rectangle(dst_img.copy(), (self.left, self.top), (self.right, self.bottom), color, -1)

    # Properties
    @property
    def radius(self):
        return math.sqrt(pow(self.width, 2) + pow(self.height, 2)) / 2

    def _get_name(self):
        return self._name

    def _get_tag(self):
        return self._tag

    def _get_color(self):
        return self._color

    @property
    def target(self):
        return self._target

    name = property(_get_name)
    tag = property(_get_tag)
    color = property(_get_color)


class CircleOfInterest(Circle):
    """Circle of interest

    Arguments:
        center {Point} -- center
        radius {integer} -- radius
        name {str} -- ROI name

    Keyword Arguments:
        tag {str} -- Tag attached to ROI (default: {'None'})
        color {tuple} -- Print color (default: {(255,255,255)})

    Raises:
        NotImplementedError -- Empty circles are not allowed
    """

    def __init__(self, center, radius, name, tag='None', color=None, target: str = ''):
        super().__init__(center, radius)
        self._name = name
        self._tag = tag
        self._target = target

        if not color:
            color = tag_to_color(tag)
        self._color = color

    def copy(self):
        return CircleOfInterest(
            center=self.center.copy(), radius=self.radius, tag=self.tag, color=self.color, target=self.target
        )

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color:
            return super(CircleOfInterest, self).draw_to(dst_img, line_width, color)
        else:
            return super(CircleOfInterest, self).draw_to(dst_img, line_width, self.color)

    def fill(self, dst_img, color):
        return cv2.circle(dst_img, (self.left, self.top), self.radius, color, -1)

    def as_rect(self):
        return RectangleOfInterest.from_lwth(
            left=self.center.x - self.radius,
            width=2 * self.radius,
            top=self.center.y - self.radius,
            height=2 * self.radius,
            name=self.name,
            tag=self.tag,
            color=self.color,
            target=self.target
        )

    # Properties
    @property
    def name(self):
        return self._name

    @property
    def tag(self):
        return self._tag

    @property
    def color(self):
        return self._color

    @property
    def target(self):
        return self._target
