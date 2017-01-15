import argparse
import math
import numpy as np
import sys


class FingerJointMaker(object):
    """
    Creates SVGs of laser-cuttable components that add up to boxes built with finger joints.

    width: Width of the panel. Refers to interior dimension.
    height: Height of the panel. Refers to interior dimension.
    finger_width: How wide each finger joint is. Often set to the material thickness.
    suppressed_fingers: length-4 tuple of ints; numbers of fingers to lop off each side (CSS ordering). Often
    aesthetically desirable.
    kerf: Anticipated width of the material lost to the cutting beam.
    finger_width_safety_margin: Additional material to add to each finger. Useful for accounting for unanticipated
    variations in material thickness. Often set to 10% of finger_width.
    """

    SVG_UNIT = 'mm'
    STROKE_WIDTH = 0.1
    STROKE_COLOR = 'black'
    SVG_MARGIN = 10  # purely for prettiness of the output SVGs -- padding around emitted points

    def __init__(
            self, width, height, finger_width, suppressed_fingers=(0, 0, 0, 0), kerf=0, finger_width_safety_margin=0):
        self.width = width
        self.height = height
        self.finger_width = finger_width
        self.suppressed_fingers = suppressed_fingers
        self.kerf = kerf
        self.finger_width_safety_margin = finger_width_safety_margin
        self.svg_width = None
        self.svg_height = None

        self.points = None

    def _make_edge(self, length, suppressed_fingers):
        """ Internal method to construct an edge beginning at the origin """
        points = np.array([[0.0, 0.0]], float)

        num_fingers = int(math.floor(length / self.finger_width) - suppressed_fingers)
        if (num_fingers % 2) == 0:
            num_fingers -= 1

        spare_change = length - (num_fingers * self.finger_width)

        current_x = (self.kerf + spare_change) / 2.0
        y = (self.kerf / 2.0)

        y_offset = self.finger_width + self.finger_width_safety_margin
        x_offset_abs = self.kerf / 2.0

        i = 0
        while current_x <= ((length + self.kerf) - (spare_change / 2.0)):

            if (i % 2) == 0:
                # this is a finger interval!
                x_offset = -1 * x_offset_abs
                points = np.append(points, [[current_x + x_offset, y], [current_x + x_offset, y + y_offset]], 0)
            else:
                # this is a non-finger interval
                x_offset = x_offset_abs
                points = np.append(points, [[current_x + x_offset, y + y_offset], [current_x + x_offset, y]], 0)

            current_x += self.finger_width

            i += 1

        points = np.append(points, [[length + self.kerf, y]], 0)

        return points

    def make(self):
        """ Construct a panel in the object's points collection """
        edge_length = (self.width, self.height, self.width, self.height)
        for (i, el) in enumerate(edge_length):
            new_points = self._make_edge(el, self.suppressed_fingers[i])
            if self.points is None:
                self.points = new_points.copy()
            else:
                self.points = np.append(self.points, new_points, 0)
            self.translate(-1 * (el + self.kerf), 0)
            self.rotate(math.pi / 2.0)

    def rotate(self, angle):
        """ Rotate the collection of points counterclockwise """
        m_rotate = np.array([[math.cos(angle), math.sin(angle)], [-1 * math.sin(angle), math.cos(angle)]], float)
        for (i, p) in enumerate(self.points):
            self.points[i] = np.dot(m_rotate, p)

    def translate(self, x, y):
        """ Move the collection of points by x and y """
        self.points += np.array([x, y])

    def center_points(self):
        """ Move the points into positive coordinate space and set the SVG viewport bounds """
        # find extents
        smallest = self.points[0].copy()
        largest = self.points[0].copy()

        for p in self.points:
            smallest[0] = min(p[0], smallest[0])
            smallest[1] = min(p[1], smallest[1])
            largest[0] = max(p[0], largest[0])
            largest[1] = max(p[1], largest[1])

        # translate, apply margin
        self.points = self.points - smallest + np.array([self.SVG_MARGIN, self.SVG_MARGIN])
        largest = largest - smallest + np.array([2 * self.SVG_MARGIN, 2 * self.SVG_MARGIN])

        # set internal extents
        (self.svg_width, self.svg_height) = largest

    def svg(self, filename=None):
        """ Emit some SVG markup, optionally to a filename """
        self.center_points()

        s = '<svg width="%d%s" height="%d%s">' % (self.svg_width, self.SVG_UNIT, self.svg_height, self.SVG_UNIT)

        s += """
        <defs>
            <style type="text/css"><![CDATA[
              line {
                stroke:%s;
                stroke-width:%f%s;
              }
              polygon {
                stroke:%s;
                strong-width:%f%s;
              }
            ]]></style>
        </defs>""" % (
            self.STROKE_COLOR, self.STROKE_WIDTH, self.SVG_UNIT, self.STROKE_COLOR, self.STROKE_WIDTH, self.SVG_UNIT)

        for i in range(0, len(self.points) - 1):
            x1 = self.points[i % len(self.points)][0]
            y1 = self.points[i % len(self.points)][1]
            x2 = self.points[(i + 1) % len(self.points)][0]
            y2 = self.points[(i + 1) % len(self.points)][1]
            s += '<line x1="%f%s" y1="%f%s" x2="%f%s" y2="%f%s" />' % (
                x1, self.SVG_UNIT, y1, self.SVG_UNIT, x2, self.SVG_UNIT, y2, self.SVG_UNIT)
        s += '</svg>'

        if filename is not None:
            f = open(filename, 'w')
            f.write(s)
            f.close()
        else:
            return s

    def embed_svgs_in_html(self, svgs, filename=None):
        """ Embed SVG markup in HTML, optionally emitted to a filename """
        s = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<html>%s</html>""" % "\n".join(svgs)

        if filename is not None:
            f = open(filename, 'w')
            f.write(s)
            f.close()
        else:
            return s


def parse_arguments(arguments):
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--width', required=True, type=float)
    argument_parser.add_argument('--height', required=True, type=float)
    argument_parser.add_argument('--finger_width', required=True, type=float)
    argument_parser.add_argument(
        '--suppressed_fingers', type=comma_separated_list_of_four_integers, default=(0, 0, 0, 0))
    argument_parser.add_argument('--kerf', default=0, type=float)
    argument_parser.add_argument('--finger_width_safety_margin', default=0, type=float)
    return argument_parser.parse_args(args=arguments)


def comma_separated_list_of_four_integers(string):
    elements = string.split(',')
    assert len(elements) == 4
    return map(int, map(str.strip, elements))


def main():
    arguments = parse_arguments(sys.argv[1:])
    finger_joint_maker = FingerJointMaker(
        arguments.width,
        arguments.height,
        arguments.finger_width,
        suppressed_fingers=arguments.suppressed_fingers,
        kerf=arguments.kerf,
        finger_width_safety_margin=arguments.finger_width_safety_margin)
    finger_joint_maker.make()
    print finger_joint_maker.svg()


if __name__ == '__main__':
    main()
