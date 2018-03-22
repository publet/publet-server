"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
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
