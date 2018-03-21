from django.test import TestCase
from publet.outputs.templatetags.output_tags import is_alpha, is_omega


class TemplateTagTest(TestCase):

    def test_is_alpha(self):
        self.assertTrue(is_alpha(1, 3))
        self.assertTrue(is_alpha(4, 3))
        self.assertTrue(is_alpha(7, 3))

        self.assertFalse(is_alpha(2, 3))
        self.assertFalse(is_alpha(3, 3))
        self.assertFalse(is_alpha(5, 3))

    def test_is_omega(self):
        self.assertTrue(is_omega(3, 3))
        self.assertTrue(is_omega(6, 3))

        self.assertFalse(is_omega(1, 3))
        self.assertFalse(is_omega(2, 3))
        self.assertFalse(is_omega(4, 3))
        self.assertFalse(is_omega(5, 3))
        self.assertFalse(is_omega(7, 3))
