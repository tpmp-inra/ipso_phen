import cv2
import math
import numpy as np

import ipso_phen.ipapi.base.ip_common as ipc


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

    def as_list(self):
        """[x, y]"""
        return [self.x, self.y]

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
        """
        s, c = [f(rad) for f in (math.sin, math.cos)]
        self.x, self.y = (c * self.x - s * self.y, s * self.x + c * self.y)

    def rotate_about(self, p, rad):
        """Rotate counter-clockwise around a point, by rad radians.

        Positive y goes *up,* as in traditional mathematics.
        """
        self.slide_xy(-p.x, -p.y)
        self.rotate(rad)
        self.slide_xy(p.x, p.y)


class AbstractRegion(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.tag = kwargs.get("tag", "None")
        self.target = kwargs.get("target", "")
        self.color = kwargs.get("color", tag_to_color(self.tag))
        self.apply_case = kwargs.get("apply_case", {})

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

    def intersects_contour(self, contour) -> bool:
        for pt in contour:
            if self.contains(Point(pt[0][0], pt[0][1])):
                return True
        else:
            return False

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

    def crop(
        self,
        src_image,
        erase_outside_if_not_rect: bool = False,
        fixed_width: int = 0,
        fixed_height: int = 0,
    ):
        if (fixed_width != 0) and (fixed_width != self.width):
            width_delta = fixed_width - self.width
            dl = width_delta // 2
            dr = width_delta // 2 + (1 if width_delta % 2 != 0 else 0)
        else:
            dl = 0
            dr = 0
        if (fixed_height != 0) and (fixed_height != self.width):
            height_delta = fixed_height - self.width
            dt = height_delta // 2
            db = height_delta // 2 + (1 if height_delta % 2 != 0 else 0)
        else:
            dt = 0
            db = 0
        tmp_roi = self.copy()
        if erase_outside_if_not_rect is True and not isinstance(self, RectangleRegion):
            img = tmp_roi.keep(src_image)
        else:
            img = src_image.copy()
        tmp_roi = tmp_roi.as_rect()
        tmp_roi.inflate(dl=dl, dr=dr, dt=dt, db=db)

        return img[tmp_roi.top : tmp_roi.bottom, tmp_roi.left : tmp_roi.right].copy(
            order="C"
        )


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
            left=0,
            width=0,
            top=0,
            height=0,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_circle(self):
        return CircleRegion(
            cx=0,
            cy=0,
            radius=0,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_annulus(self):
        return AnnulusRegion(
            cx=0,
            cy=0,
            radius=0,
            in_radius=0,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    @property
    def area(self) -> float:
        return 2 * math.pi * math.pow(self.radius, 2) - 2 * math.pi * math.pow(
            self.in_radius, 2
        )


class RectangleRegion(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        left = kwargs.get("left", None)
        top = kwargs.get("top", None)
        width = kwargs.get("width", None)
        height = kwargs.get("height", None)
        right = kwargs.get("right", None)
        source_width = kwargs.get("source_width", None)
        bottom = kwargs.get("bottom", None)
        source_height = kwargs.get("source_height", None)
        height = kwargs.get("height", None)
        height = kwargs.get("height", None)

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
        return f"Rect:[l:{self.left},w:{self.width}/t:{self.top},h:{self.bottom} - name:{self.name}, tag:{self.tag}]"

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
        old_left = self.left
        old_right = self.right
        old_top = self.top
        old_bottom = self.bottom
        self.left = old_left - dl
        self.right = old_right + dr
        self.top = old_top - dt
        self.bottom = old_bottom + db

    def expand(self, n):
        self.left -= n
        self.top -= n
        self.right += n
        self.bottom += n

    def to_mask(self, width, height):
        mask = np.zeros((height, width), dtype=np.uint8)
        return cv2.rectangle(
            mask,
            (self.left, self.top),
            (self.right, self.bottom),
            (255,),
            -1,
        )

    def draw_to(self, dst_img, line_width=-1, color=None):
        return cv2.rectangle(
            dst_img.copy(),
            (self.left, self.top),
            (self.right, self.bottom),
            self.color if color is None else color,
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


class RotatedRectangle(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        left = kwargs.get("left", None)
        top = kwargs.get("top", None)
        width = kwargs.get("width", None)
        height = kwargs.get("height", None)
        right = kwargs.get("right", None)
        source_width = kwargs.get("source_width", None)
        bottom = kwargs.get("bottom", None)
        source_height = kwargs.get("source_height", None)
        height = kwargs.get("height", None)
        height = kwargs.get("height", None)

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

        self._left = left
        self._top = top
        self._width = width
        self._height = height
        self.angle = kwargs.get("angle", 0)

    def __repr__(self) -> str:
        return f"Rect:[l:{self._left},w:{self._width}/t:{self._top},h:{self._height},a:{self.angle} - name:{self.name}, tag:{self.tag}]"

    def inflate(self, dl, dr, dt, db):
        """Inflates self by d- in each direction"""
        self._left -= dl
        self._width += 2 * dr
        self._top -= dt
        self._height += 2 * db

    def expand(self, n):
        self._left -= n
        self._top -= n
        self._width += 2 * n
        self._height += 2 * n

    def as_poly(self) -> list:
        points = [
            Point(self._left, self._top),
            Point(self._left + self._width, self._top),
            Point(self._left + self._width, self._top + self._height),
            Point(self._left, self._top + self._height),
        ]
        for point in points:
            point.rotate_about(self.center, math.radians(self.angle))
        return points

    def to_contour(self) -> np.array:
        return np.array(
            [point.as_list() for point in self.as_poly()],
            dtype=np.int32,
        )

    def to_mask(self, width, height):
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.drawContours(mask, [self.to_contour()], 0, (255,), -1)
        return mask

    def draw_to(self, dst_img, line_width=-1, color=None):
        res = dst_img.copy()
        cv2.drawContours(
            res,
            [self.to_contour()],
            0,
            self.color if color is None else color,
            line_width,
        )
        return res

    def fill(self, dst_img, color):
        return self.draw_to(dst_img=dst_img, line_width=-1, color=color)

    def is_empty(self) -> bool:
        return self._width == 0 or self._height == 0

    def as_rect(self):
        points = self.as_poly()
        left = min([p.x for p in points])
        top = min([p.y for p in points])
        return RectangleRegion(
            left=left,
            width=max([p.x for p in points]) - left,
            top=top,
            height=max([p.y for p in points]) - top,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_circle(self):
        return self.as_rect().as_circle()

    def as_annulus(self):
        return self.as_rect().as_annulus()

    @property
    def radius(self) -> int:
        return max(self._width, self._height) // 2

    @property
    def center(self) -> Point:
        return Point(self._left + self._width // 2, self._top + self._height // 2)

    @property
    def area(self) -> float:
        return self._width * self._height

    @property
    def ar(self) -> float:
        """Returns aspect ratio"""
        return self._width / self._height


class CircleRegion(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.center = kwargs.get(
            "center",
            Point(kwargs.get("cx"), kwargs.get("cy")),
        )
        self.radius = kwargs.get("radius")

    def __repr__(self) -> str:
        return (
            f"Circle:[c:{self.center},r:{self.radius} - name:{self.name}, tag:{self.tag}]"
        )

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
            dst_img.copy(),
            (self.center.x, self.center.y),
            self.radius,
            self.color,
            line_width,
        )

    def fill(self, dst_img, color):
        return cv2.circle(
            dst_img.copy(),
            (self.center.x, self.center.y),
            self.radius,
            color,
            -1,
        )

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
        return f"Annulus:[c:{self.center},r:{self.radius},r_in:{self.in_radius} - name:{self.name}, tag:{self.tag}]"

    def to_mask(self, width, height):
        mask = cv2.circle(
            np.zeros((height, width), dtype=np.uint8),
            (self.center.x, self.center.y),
            self.radius,
            (255,),
            -1,
        )
        return cv2.circle(
            mask,
            (self.center.x, self.center.y),
            self.in_radius,
            (0,),
            -1,
        )

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color is None:
            color = self.color
        if line_width > 0:
            img_ = cv2.circle(
                dst_img.copy(),
                (self.center.x, self.center.y),
                self.radius,
                color,
                line_width,
            )
            return cv2.circle(
                img_,
                (self.center.x, self.center.y),
                self.in_radius,
                color,
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
            cx=self.center.x,
            cy=self.center.y,
            radius=self.radius,
            in_radius=self.in_radius,
        )

    @property
    def area(self) -> float:
        return 2 * math.pi * math.pow(self.radius, 2) - 2 * math.pi * math.pow(
            self.in_radius, 2
        )

    @property
    def ar(self) -> float:
        """Returns aspect ratio"""
        return 1


class CompositeRegion(AbstractRegion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items = kwargs.get("items", [])
        self.op = kwargs.get("op", "intersection")
        self.width = kwargs.get("width", 0)
        self.height = kwargs.get("height", 0)

    def __repr__(self):
        return "".join(repr(i) for i in self.items)

    def to_mask(self, width, height):

        masks = [i.to_mask(width, height) for i in self.items]
        if self.op == "intersection":
            return ipc.multi_and(masks)
        if self.op == "union":
            return ipc.multi_or(masks)

    def draw_to(self, dst_img, line_width=-1, color=None):
        if color is None:
            color = self.color
        mask = self.to_mask(dst_img.shape[1], dst_img.shape[0])
        if mask is None:
            return np.zeros((dst_img.shape[0], dst_img.shape[1]), dtype=np.uint8)
        if line_width > 0:
            mask = ipc.morphological_gradient(image=mask, kernel_size=line_width)
        if len(dst_img.shape) == 3 and dst_img.shape[2] == 3:
            mask = np.dstack((mask, mask, mask))
            mask = cv2.inRange(mask, (1, 1, 1), (255, 255, 255))
        else:
            cv2.inRange(mask, 1, 255)
        res = dst_img.copy()
        res[mask > 0] = color
        return res

    def fill(self, dst_img, color):
        return self.draw_to(dst_img=dst_img, color=color)

    def is_empty(self):
        for i in self.items:
            if not i.is_empty():
                return False
        else:
            return True

    def as_rect(self):
        cnt = ipc.group_contours(mask=self.to_mask(self.width, self.height))
        x, y, w, h = cv2.boundingRect(cnt)
        return RectangleRegion(
            left=x,
            width=w,
            top=y,
            height=h,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_circle(self):
        cnt = ipc.group_contours(mask=self.to_mask(self.width, self.height))
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        return CircleRegion(
            cx=x,
            cy=y,
            radius=radius,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    def as_annulus(self):
        cnt = ipc.group_contours(mask=self.to_mask(self.width, self.height))
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        return AnnulusRegion(
            cx=x,
            cy=y,
            radius=radius,
            in_radius=0,
            tag=self.tag,
            color=self.color,
            target=self.target,
        )

    @property
    def area(self) -> float:
        mask = self.to_mask(self.width, self.height)
        return np.count_non_zero(mask)

    @property
    def ar(self) -> float:
        """Returns aspect ratio"""
        return self.as_rect().ar


def copy_rois(rois: list, src, dst):
    return cv2.bitwise_or(
        delete_rois(rois=rois, image=dst),
        keep_rois(rois=rois, image=src),
    )


def draw_rois(rois: list, image, line_width=-1, color=None):
    for roi in rois:
        image = roi.draw_to(
            dst_img=image,
            line_width=line_width,
            color=color,
        )
    return image


def fill_rois(rois: list, image, color):
    return draw_rois(
        rois=rois,
        image=image,
        line_width=-1,
        color=color,
    )


def keep_rois(rois: list, image):
    cp = image.copy()

    if (len(cp.shape) == 2) or (len(cp.shape) == 3 and cp.shape[2] == 1):
        cr = np.zeros_like(cp)
    else:
        cr = np.zeros_like(cp[:, :, 0])
    cr = fill_rois(rois=rois, image=cr, color=255)

    return cv2.bitwise_and(cp, cp, mask=cr)


def delete_rois(rois: list, image):
    for roi in rois:
        image = roi.delete(src_image=image)
    return image
