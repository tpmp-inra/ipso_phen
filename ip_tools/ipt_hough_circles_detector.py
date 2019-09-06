import cv2
import numpy as np
from skimage.transform import hough_circle, hough_circle_peaks

from ip_base.ip_common import C_RED, C_BLUE, C_YELLOW, C_ORANGE, build_color_steps, TOOL_GROUP_ROI_DYNAMIC_STR
from ip_base.ip_common import TOOL_GROUP_VISUALIZATION_STR
from ip_base.ipt_abstract import IptBase
from ip_tools.ipt_edge_detector import IptEdgeDetector
from tools import shapes


class IptHoughCircles(IptBase):

    def build_params(self):
        self.add_roi_settings(default_name='unnamed_roi', default_type='keep', default_shape='rectangle')
        self.add_separator(name='s1')
        self.add_source_selector(default_value='source')
        self.add_channel_selector(default_value='l')
        self.add_spin_box(
            name='min_radius',
            desc='Minimal radius to consider',
            default_value=400,
            minimum=0,
            maximum=2000,
            hint='All circles smaller than this will be ignored'
        )
        self.add_spin_box(
            name='max_radius',
            desc='Maximal radius to consider',
            default_value=1000,
            minimum=0,
            maximum=2000,
            hint='All circles bigger than this will be ignored'
        )
        self.add_spin_box(
            name='step_radius',
            desc='Radius granularity',
            default_value=10,
            minimum=0,
            maximum=100,
            hint='Steps for scanning radius'
        )
        self.add_spin_box(
            name='max_peaks',
            desc='Maximum number of detected circles',
            default_value=2,
            minimum=1,
            maximum=20,
            hint='Keeps only n best circles'
        )
        self.add_spin_box(
            name='min_distance',
            desc='Minimum distance between two circles',
            default_value=20,
            minimum=1,
            maximum=2000,
            hint='Remove circles that are too close'
        )
        self.add_spin_box(name='line_width', desc='Draw line width', default_value=4, minimum=1, maximum=20)
        self.add_checkbox(name='keep_only_one', desc='Keep only closest, if not, ROI is larger circle', default_value=0)
        self.add_combobox(
            name='target_position',
            desc='Keep the closest circle closest to',
            default_value='BOTTOM_CENTER',
            values=dict(
                TOP_LEFT='TOP_LEFT',
                TOP_CENTER='TOP_CENTER',
                TOP_RIGHT='TOP_RIGHT',
                MIDDLE_LEFT='MIDDLE_LEFT',
                MIDDLE_CENTER='MIDDLE_CENTER',
                MIDDLE_RIGHT='MIDDLE_RIGHT',
                BOTTOM_LEFT='BOTTOM_LEFT',
                BOTTOM_CENTER='BOTTOM_CENTER',
                BOTTOM_RIGHT='BOTTOM_RIGHT'
            )
        )
        self.add_slider(
            name='max_dist_to_root',
            desc='Maximum distance to root position',
            default_value=1000,
            minimum=0,
            maximum=4000
        )
        self.add_checkbox(name='draw_boundaries', desc='Draw max and min circles', default_value=0)
        self.add_checkbox(name='draw_candidates', desc='Draw discarded candidates', default_value=0)
        self.add_spin_box(
            name='expand_circle', desc='Contract/expand circle', default_value=0, minimum=-1000, maximum=1000
        )
        self.add_checkbox(name='edge_only', desc='Edge detection only', default_value=0)
        self.add_edge_detector()

    def process_wrapper(self, **kwargs):
        """
        Hough circles detector:
        Hough circles detector: Perform a circular Hough transform.
        Can generate ROIs
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * ROI name (roi_name): 
            * Select action linked to ROI (roi_type): no clue
            * Select ROI shape (roi_shape): no clue
            * Target IPT (tool_target): no clue
            * Select source file type (source_file): no clue
            * Channel (channel): 
            * Minimal radius to consider (min_radius): All circles smaller than this will be ignored
            * Maximal radius to consider (max_radius): All circles bigger than this will be ignored
            * Radius granularity (step_radius): Steps for scanning radius
            * Maximum number of detected circles (max_peaks): Keeps only n best circles
            * Minimum distance between two circles (min_distance): Remove circles that are too close
            * Draw line width (line_width): 
            * Keep only closest, if not, ROI is larger circle (keep_only_one): 
            * Keep the closest circle closest to (target_position): 
            * Maximum distance to root position (max_dist_to_root): 
            * Draw max and min circles (draw_boundaries): 
            * Draw discarded candidates (draw_candidates): 
            * Contract/expand circle (expand_circle): 
            * Edge detection only (edge_only): 
            * Select edge detection operator (operator): 
            * Canny's sigma (canny_sigma): Sigma.
            * Canny's first Threshold (canny_first): First threshold for the hysteresis procedure.
            * Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure.
            * Kernel size (kernel_size): 
            * Threshold (threshold): Threshold for kernel based operators
            * Apply threshold (apply_threshold): 
        --------------
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            # Get the edge
            with IptEdgeDetector(wrapper=wrapper, **self.params_to_dict()) as (res, ed):
                if not res:
                    return
                edges = ed.result
                if self.get_value_of('edge_only') == 1:
                    self.result = ed.result
                    return True

            # Read params
            min_radius = self.get_value_of('min_radius')
            max_radius = self.get_value_of('max_radius')
            step_radius = self.get_value_of('step_radius')
            max_peaks = self.get_value_of('max_peaks')
            min_distance = self.get_value_of('min_distance')
            line_width = self.get_value_of('line_width')
            draw_candidates = self.get_value_of('draw_candidates') == 1
            img = self.extract_source_from_args()

            # Detect circles
            edges = self.match_image_size_to_source(img=edges)
            hough_radii = np.arange(min_radius, max_radius, step_radius)
            hough_res = hough_circle(edges, hough_radii)

            # Draw the result
            if len(img.shape) == 2:
                img = np.dstack((img, img, img))

            # Select the most prominent n circles
            accu, cx, cy, radii = hough_circle_peaks(
                hough_res,
                hough_radii,
                min_xdistance=min_distance,
                min_ydistance=min_distance,
                total_num_peaks=max_peaks
            )
            if self.get_value_of('keep_only_one') == 1:
                candidates = [[a, x, y, z] for a, x, y, z in zip(accu, cx, cy, radii)]
                h, w = img.shape[:2]
                roi = shapes.Rect.from_coordinates(0, w, 0, h)
                roi_root = roi.point_at_position(self.get_value_of('target_position'), True)
                min_dist = h * w
                min_idx = -1
                min_accu = -1
                i = 0
                colors = build_color_steps(C_YELLOW, (0, 125, 125), len(candidates))
                max_dist_to_root = self.get_value_of('max_dist_to_root')
                for c_accu, center_x, center_y, radius in candidates:
                    if draw_candidates:
                        cv2.circle(img, (center_x, center_y), radius, colors[i], max(1, line_width // 2))
                    cur_dist = roi_root.distance_to(shapes.Point(center_x, center_y))
                    if (cur_dist < min_dist) and (cur_dist <
                                                  max_dist_to_root) and ((cur_dist / min_dist > min_accu / c_accu) or
                                                                         (min_accu == -1)):
                        min_dist = cur_dist
                        min_idx = i
                        min_accu = c_accu

                    i += 1
                if min_idx >= 0:
                    self.result = [[candidates[min_idx][1], candidates[min_idx][2], candidates[min_idx][3]]]
                    self.result[0][2] += self.get_value_of('expand_circle')
                    if self.get_value_of('draw_boundaries') == 1:
                        cv2.circle(img, (roi_root.x, roi_root.y), min_radius, C_RED, line_width + 4)
                        cv2.circle(img, (roi_root.x, roi_root.y), max_radius, C_BLUE, line_width + 4)
                else:
                    self.result = None
            else:
                self.result = [[x, y, r] for x, y, r in zip(cx, cy, radii)]

            if self.result is not None:
                colors = build_color_steps(C_ORANGE, (0, 0, 255), len(self.result))
                i = 0
                for center_x, center_y, radius in self.result:
                    cv2.circle(img, (center_x, center_y), radius, colors[i], line_width)
                    i += 1
            wrapper.store_image(img, f'circles_{self.input_params_as_str(exclude_defaults=True)}', text_overlay=True)
            res = True
        except Exception as e:
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    def generate_roi(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return None
        if self.process_wrapper(**kwargs):
            roi_shape = self.get_value_of('roi_shape')
            roi_type = self.get_value_of('roi_type')
            roi_name = self.get_value_of('roi_name')
            tool_target = self.get_value_of('tool_target')
            circles = sorted(self.result, key=lambda circle_: circle_[2])
            circle = circles[0]
            if roi_shape == 'rectangle':
                r = shapes.Circle(center=shapes.Point(circle[0], circle[1]), radius=circle[2]).as_rect()
                return shapes.RectangleOfInterest.from_lwth(
                    left=r.left,
                    width=r.width,
                    top=r.top,
                    height=r.height,
                    name=roi_name,
                    tag=roi_type,
                    target=tool_target
                )
            elif roi_shape == 'circle':
                return shapes.CircleOfInterest(
                    center=shapes.Point(circle[0], circle[1]),
                    radius=circle[2],
                    name=roi_name,
                    tag=roi_type,
                    target=tool_target
                )
            else:
                return None
        else:
            return None

    def apply_roy(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return None
        if self.process_wrapper(**kwargs):
            circles = sorted(self.result, key=lambda circle_: circle_[2])
            circle = circles[0]
            roi_name = f'roi_keep_{len(wrapper.rois_list)}'
            wrapper.add_circle_roi(circle[0], circle[1], circle[2], roi_name, 'keep')
            target = kwargs.get('target', 'source')
            if target == 'source':
                res = wrapper.apply_rois(wrapper.current_image)
            elif target == 'mask':
                res = wrapper.apply_rois(wrapper.mask)
            else:
                res = None
                wrapper.error_holder.add_error('Unknown ROI target')
            wrapper.store_image(res, roi_name, text_overlay=False)
            return res
        else:
            return wrapper.current_image

    @property
    def name(self):
        return 'Hough circles detector'

    @property
    def real_time(self):
        return self.get_value_of('edge_only') == 1

    @property
    def result_name(self):
        return 'circles'

    @property
    def output_kind(self):
        return 'data'

    @property
    def use_case(self):
        return [TOOL_GROUP_ROI_DYNAMIC_STR, TOOL_GROUP_VISUALIZATION_STR]

    @property
    def description(self):
        return 'Hough circles detector: Perform a circular Hough transform.\nCan generate ROIs'
