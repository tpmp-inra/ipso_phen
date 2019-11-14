import cv2
import math
import numpy as np


def tag_to_color(tag: str):
    if tag.lower() == "keep":
        return 0, 128, 0
    elif tag.lower() == "erode":
        return 80, 127, 255
    elif tag.lower() == "safe":
        return 0, 255, 0
    elif tag.lower() == "delete":
        return 0, 0, 255
    elif tag.lower() == "enforce":
        return 255, 0, 255
    elif tag.lower() == "dilate":
        return 255, 190, 84
    elif tag.lower() == "open":
        return 255, 33, 0
    elif tag.lower() == "close":
        return 0, 146, 255
    elif tag.lower() == "process_roi":
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
    to_int  -- convert x & y to integers
    to_float  -- convert x & y to floats
    move_to  -- reset x & y
    slide  -- move (in place) +dx, +dy, as specified by point
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

        return math.sqrt(self.x ** 2 + self.y ** 2)

    def distance_to(self, p):
        """Calculate the distance between two points."""
        return (self - p).length()

    def as_tuple(self):
        """(x, y)"""
        return self.x, self.y

    def copy(self):
        """Return a full copy of this point."""
        return Point(self.x, self.y)

    def to_int(self):
        """Convert co-ordinate values to integers."""
        self.x = int(self.x)
        self.y = int(self.y)

    def to_float(self):
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


class AbstractRegion(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.tag = kwargs.get("tag", "None")
        self.target = kwargs.get("target", "")
        self.color = kwargs.get("color", tag_to_color(self.tag))

    def __repr__(self) -> str:
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if not self.__class__.__name__ == other.__class__.__name__ or (
            len(self.__dict__) != len(other.__dict__)
        ):
            return False

        for k, v in self.__dict__.items():
            if v != other.__dict__.get(k, None):
                return False
        return True

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def copy(self):
        return self.__class__(**self.__dict__)

    def point_at_position(self, position: str, round_position: bool = False) -> Point:
        """Return a point on the shape at a position

        :param position: string detailing the position
        :param round_position: if true result will components will be rounded
        :return: Point at position
        """
        if position.upper() == "TOP_LEFT":
            pt = self.top_left
        elif position.upper() == "TOP_CENTER":
            pt = self.top_center
        elif position.upper() == "TOP_RIGHT":
            pt = self.top_right
        elif position.upper() == "MIDDLE_LEFT":
            pt = self.middle_left
        elif position.upper() == "MIDDLE_CENTER":
            pt = self.middle_center
        elif position.upper() == "MIDDLE_RIGHT":
            pt = self.middle_right
        elif position.upper() == "BOTTOM_LEFT":
            pt = self.bottom_left
        elif position.upper() == "BOTTOM_CENTER":
            pt = self.bottom_center
        elif position.upper() == "BOTTOM_RIGHT":
            pt = self.bottom_right
        else:
            pt = self.center

        if round_position:
            return Point(round(pt.x), round(pt.y))
        else:
            return pt

    def keep(self, src_image):
        """Delete all data outside of the mask

        Arguments:
            src_image {numpy array} -- binary image
        Returns:
            [numpy array] -- [output mimageask]
        """
        cp = src_image.copy()

        if (len(cp.shape) == 2) or (len(cp.shape) == 3 and cp.shape[2] == 1):
            cr = np.zeros_like(cp)
        else:
            cr = np.zeros_like(cp[:, :, 0])
        cr = self.fill(cr, 255)

        return cv2.bitwise_and(cp, cp, mask=cr)

    def delete(self, src_image):
        """Delete data inside roi

        Arguments:
            src_image {numpy array} -- binary image
        Returns:
            [numpy array] -- [output mimageask]
        """
        cp = src_image.copy()

        if (len(cp.shape) == 2) or (len(cp.shape) == 3 and cp.shape[2] == 1):
            cr = np.full_like(cp, 255)
        else:
            cr = np.full_like(cp[:, :, 0], 255)
        cr = self.fill(cr, 0)
        return cv2.bitwise_and(cp, cp, mask=cr)

    def crop(self, src_image, erase_outside_if_not_rect: bool = False):
        if erase_outside_if_not_rect is True:
            img = self.keep(src_image)
        else:
            img = src_image.copy
        r = self.as_rect()
        if r is None:
            return None
        return img[r.top : r.bottom, r.left : r.right]


class EmptyRegion(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return "Empty ROI"

    def to_mask(self, width, height):
        return np.zeros((height, width), dtype=np.uint8)

    def draw_to(self, dst_img, line_width=-1, color=None):
        return dst_img.copy()

    def fill(self, dst_img, color):
        return dst_img.copy()

    def is_empty(self) -> bool:
        return True

    def as_rect(self):
        return RectangleRegion(
            left=0, width=0, top=0, height=0, tag=self.tag, color=self.color, target=self.target,
        )

    def as_circle(self):
        return CircleRegion(
            cx=0, cy=0, radius=0, tag=self.tag, color=self.color, target=self.target,
        )

    def as_annulus(self):
        return AnnulusRegion(
            cx=0, cy=0, radius=0, in_radius=0, tag=self.tag, color=self.color, target=self.target,
        )

    @property
    def area(self) -> float:
        return 2 * math.pi * math.pow(self.radius, 2) - 2 * math.pi * math.pow(self.in_radius, 2)


class RectangleRegion(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        left = kwargs.get("left")
        top = kwargs.get("top")
        width = kwargs.get("width")
        height = kwargs.get("height")
        right = kwargs.get("right")
        source_width = kwargs.get("source_width")
        bottom = kwargs.get("bottom")
        source_height = kwargs.get("source_height")
        height = kwargs.get("height")
        height = kwargs.get("height")

        if left is None and right is None:
            if width is None or width == 0:
                left = 0
                width = source_width
            elif width > 0:
                left = 0
            elif width < 0:
                left = source_width + width
                width = -width
        elif left is not None:
            if right is not None:
                width = right - left
            elif width is None:
                width = source_width - left
        elif right is not None:
            if width is not None:
                left = right - width
            else:
                left = 0
                width = source_width - right

        if top is None and bottom is None:
            if height is None or height == 0:
                top = 0
                height = source_height
            elif height > 0:
                top = 0
            elif height < 0:
                top = source_height + height
                height = -height
        elif top is not None:
            if bottom is not None:
                height = bottom - top
            elif height is None:
                height = source_height - top
        elif bottom is not None:
            if height is not None:
                top = bottom - height
            else:
                top = 0
                height = source_height - bottom

        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"""
        Rect:[l:{self.left},w:{self.width}/t:{self.top},h:{self.bottom} - name:{self.name}, tag:{self.tag}]
        """

    def to_opencv(self):
        return self.left, self.top, self.width, self.height

    def overlaps(self, other) -> bool:
        """Return true if a rectangle overlaps this rectangle."""
        if isinstance(other, RectangleRegion):
            return (
                self.right > other.left
                and self.left < other.right
                and self.top < other.bottom
                and self.bottom > other.top
            )
        else:
            raise NotImplementedError

    def union(self, other):
        """Retrun the union of 2 rectangles"""
        if isinstance(other, RectangleRegion):
            self.left = min(self.left, other.left)
            self.right = max(self.right, other.right)
            self.top = min(self.top, other.top)
            self.bottom = max(self.bottom, other.bottom)
        else:
            raise NotImplementedError

    def bound(self, other):
        """Retrun the intersection of 2 rectangles"""
        if isinstance(other, RectangleRegion):
            self.left = max(self.left, other.left)
            self.right = min(self.right, other.right)
            self.top = max(self.top, other.top)
            self.bottom = min(self.bottom, other.bottom)
        else:
            raise NotImplementedError

    def inflate(self, dl, dr, dt, db):
        """Inflates self by d- in each direction"""
        self.left -= dl
        self.right += dr
        self.top -= dt
        self.bottom += db

    def expand_by(self, n):
        self.left -= n
        self.top -= n
        self.right += n
        self.bottom += n

    def to_mask(self, width, height):
        mask = np.zeros((height, width), dtype=np.uint8)
        return cv2.rectangle(mask, (self.left, self.top), (self.right, self.bottom), (255,), -1,)

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color is None:
            color = self.color
        return cv2.rectangle(
            dst_img.copy(),
            (self.left, self.top),
            (self.right, self.bottom),
            self.color,
            line_width,
        )

    def fill(self, dst_img, color):
        return cv2.rectangle(
            dst_img.copy(), (self.left, self.top), (self.right, self.bottom), color, -1
        )

    def is_empty(self) -> bool:
        return self.width == 0 or self.height == 0

    def contains(self, other) -> bool:
        """Return true if a point or rectangle is inside the rectangle."""
        if isinstance(other, Point):
            x, y = other.as_tuple()
            return self.left <= x <= self.right and self.top <= y <= self.bottom
        elif isinstance(other, RectangleRegion):
            return (
                (self.left <= other.left)
                and (self.right >= other.right)
                and (self.top <= other.top)
                and (self.bottom >= other.bottom)
            )
        elif isinstance(other, CircleRegion):
            other = other.as_rect()
            return (
                (self.left <= other.left)
                and (self.right >= other.right)
                and (self.top <= other.top)
                and (self.bottom >= other.bottom)
            )

    def as_rect(self):
        return RectangleRegion(
            left=self.left,
            width=self.width,
            top=self.top,
            height=self.height,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_circle(self):
        return CircleRegion(
            cx=self.center.x,
            cy=self.center.y,
            radius=self.radius,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_annulus(self):
        return AnnulusRegion(
            cx=self.center.x,
            cy=self.center.y,
            radius=self.radius,
            in_radius=0,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    @property
    def top_left(self) -> Point:
        return Point(self.left, self.top)

    @property
    def top_center(self) -> Point:
        return Point(self.left + self.width / 2, self.top)

    @property
    def top_right(self) -> Point:
        return Point(self.left + self.width, self.top)

    @property
    def middle_left(self) -> Point:
        return Point(self.left, self.top + self.height / 2)

    @property
    def middle_center(self) -> Point:
        return self.center

    @property
    def middle_right(self) -> Point:
        return Point(self.right, self.top + self.height / 2)

    @property
    def bottom_left(self) -> Point:
        return Point(self.left, self.bottom)

    @property
    def bottom_center(self) -> Point:
        return Point(self.left + self.width / 2, self.bottom)

    @property
    def bottom_right(self) -> Point:
        return Point(self.right, self.bottom)

    @property
    def right(self) -> int:
        return self.left + self.width

    @right.setter
    def right(self, value):
        self.width = value - self.left

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @bottom.setter
    def bottom(self, value):
        self.height = value - self.top

    @property
    def radius(self) -> int:
        return max(self.width, self.height) // 2

    @property
    def center(self) -> Point:
        return Point(self.left + self.width // 2, self.top + self.height // 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def ar(self) -> float:
        """Returns aspect ratio"""
        return self.width / self.height


class CircleRegion(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.center = Point(kwargs.get("cx"), kwargs.get("cy"))
        self.radius = kwargs.get("radius")

    def __repr__(self) -> str:
        return f"""
        Circle:[c:{self.center},r:{self.radius} - name:{self.name}, tag:{self.tag}]
        """

    def to_opencv(self):
        return (self.center.x, self.center.y), self.radius

    def expand_by(self, n):
        self.radius += n

    def to_mask(self, width, height):
        mask = np.zeros((height, width), dtype=np.uint8)
        return cv2.circle(mask, (self.center.x, self.center.y), self.radius, (255,), -1)

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color is None:
            color = self.color
        return cv2.circle(
            dst_img.copy(), (self.center.x, self.center.y), self.radius, self.color, line_width
        )

    def fill(self, dst_img, color):
        return cv2.circle(dst_img.copy(), (self.center.x, self.center.y), self.radius, color, -1)

    def is_empty(self) -> bool:
        return self.radius == 0

    def contains(self, other) -> bool:
        """Return true if a point or rectangle is inside the rectangle."""
        if isinstance(other, Point):
            return self.center.distance_to(other) <= self.radius
        else:
            return self.as_rect().contains(other)

    def as_rect(self):
        return RectangleRegion(
            left=self.left,
            width=self.width,
            top=self.top,
            height=self.height,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_circle(self):
        return CircleRegion(
            cx=self.center.x,
            cy=self.center.y,
            radius=self.radius,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_annulus(self):
        return AnnulusRegion(
            cx=self.center.x,
            cy=self.center.y,
            radius=self.radius,
            in_radius=0,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def point_at_angle(self, angle: float) -> Point:
        """Calculates the point in the border of the circle at a given angle

        :param angle: in radians
        :return: Point
        """
        return Point(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle),
        )

    @property
    def top_left(self) -> Point:
        return self.point_at_angle(3 * math.pi / 4)

    @property
    def top_center(self) -> Point:
        return self.point_at_angle(math.pi / 2)

    @property
    def top_right(self) -> Point:
        return self.point_at_angle(math.pi / 4)

    @property
    def middle_left(self) -> Point:
        return self.point_at_angle(math.pi)

    @property
    def middle_center(self) -> Point:
        return self.center

    @property
    def middle_right(self) -> Point:
        return self.point_at_angle(0)

    @property
    def bottom_left(self) -> Point:
        return self.point_at_angle(5 * math.pi / 4)

    @property
    def bottom_center(self) -> Point:
        return self.point_at_angle(3 * math.pi / 2)

    @property
    def bottom_right(self) -> Point:
        return self.point_at_angle(7 * math.pi / 4)

    @property
    def left(self) -> int:
        return self.center.x - self.radius

    @property
    def top(self) -> int:
        return self.center.y - self.radius

    @property
    def width(self) -> int:
        return self.radius * 2

    @property
    def height(self) -> int:
        return self.radius * 2

    @property
    def right(self) -> int:
        return self.center.x + self.radius

    @property
    def bottom(self) -> int:
        return self.center.y + self.radius

    @property
    def area(self) -> float:
        return 2 * math.pi * math.pow(self.radius, 2)

    @property
    def ar(self) -> float:
        """Returns aspect ratio"""
        return 1


class AnnulusRegion(CircleRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.in_radius = kwargs.get("in_radius")

    def __repr__(self) -> str:
        return f"""
        Annulus:[c:{self.center},r:{self.radius},r_in:{self.in_radius} - name:{self.name}, tag:{self.tag}]
        """

    def to_mask(self, width, height):
        mask = cv2.circle(
            np.zeros((height, width), dtype=np.uint8),
            (self.center.x, self.center.y),
            self.radius,
            (255,),
            -1,
        )
        return cv2.circle(mask, (self.center.x, self.center.y), self.in_radius, (0,), -1)

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color is None:
            color = self.color
        if line_width > 0:
            img_ = cv2.circle(
                dst_img.copy(),
                (self.center.x, self.center.y),
                self.radius,
                self.color,
                line_width,
            )
            return cv2.circle(
                img_,
                (self.center.x, self.center.y),
                self.in_radius,
                self.color,
                line_width,
            )
        else:
            return self.fill(dst_img=dst_img, color=color)

    def fill(self, dst_img, color):
        mask = self.to_mask(dst_img.shape[1], dst_img.shape[0])
        mask = np.dstack((mask, mask, mask))
        img_ = dst_img.copy()
        img_[np.where((mask == [255, 255, 255]).all(axis=2))] = color
        return img_

    def is_empty(self) -> bool:
        return self.radius == 0

    def as_rect(self):
        return RectangleRegion(
            left=self.left,
            width=self.width,
            top=self.top,
            height=self.height,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_circle(self):
        return CircleRegion(cx=self.center.x, cy=self.center.y, radius=self.radius)

    def as_annulus(self):
        return AnnulusRegion(
            cx=self.center.x, cy=self.center.y, radius=self.radius, in_radius=self.in_radius
        )

    @property
    def area(self) -> float:
        return 2 * math.pi * math.pow(self.radius, 2) - 2 * math.pi * math.pow(self.in_radius, 2)

    @property
    def ar(self) -> float:
        """Returns aspect ratio"""
        return 1