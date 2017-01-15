from unittest import TestCase

from fingerjoint import FingerJointMaker, parse_arguments

DEFAULT_REQUIRED_ARGUMENTS = ['--width=1', '--height=2', '--finger_width=3']


class TestFingerjoint(TestCase):
    def test_full(self):
        finger_joint_maker = FingerJointMaker(
            300, 150, 20, suppressed_fingers=(3, 0, 3, 0), kerf=1, finger_width_safety_margin=5)
        finger_joint_maker.make()
        finger_joint_maker.svg(filename='test.svg')
        finger_joint_maker.embed_svgs_in_html((finger_joint_maker.svg(),), filename='test.html')

    def test_should_accept_minimal_parameters(self):
        arguments = parse_arguments(['--width=1.1', '--height=2.1', '--finger_width=3.1'])
        self.assertAlmostEqual(arguments.width, 1.1)
        self.assertAlmostEqual(arguments.height, 2.1)
        self.assertAlmostEqual(arguments.finger_width, 3.1)

    def test_should_accept_optional_parameters(self):
        optional_arguments = ['--suppressed_fingers=4,5,6,7', '--kerf=8.1', '--finger_width_safety_margin=9.1']
        arguments = parse_arguments(DEFAULT_REQUIRED_ARGUMENTS + optional_arguments)
        self.assertEqual(arguments.suppressed_fingers, [4, 5, 6, 7])
        self.assertAlmostEqual(arguments.kerf, 8.1)
        self.assertAlmostEqual(arguments.finger_width_safety_margin, 9.1)
