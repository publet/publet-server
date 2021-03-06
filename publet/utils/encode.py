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
#!/usr/bin/env python
#
# Source: https://gist.github.com/bhelx/778542
#
# Converts any integer into a base [BASE] number. I have chosen 62
# as it is meant to represent the integers using all the alphanumeric
# characters, [no special characters] = {0..9}, {A..Z}, {a..z}
#
# I plan on using this to shorten the representation of possibly long ids,
# a la url shortenters
#
# saturate()
#     takes the base 62 key, as a string, and turns it back into an integer
# dehydrate()
#     takes an integer and turns it into the base 62 string
#
import math

BASE = 62

UPPERCASE_OFFSET = 55
LOWERCASE_OFFSET = 61
DIGIT_OFFSET = 48


def true_ord(char):
    """
    Turns a digit [char] in character representation
    from the number system with base [BASE] into an integer.
    """

    if char.isdigit():
        return ord(char) - DIGIT_OFFSET
    elif 'A' <= char <= 'Z':
        return ord(char) - UPPERCASE_OFFSET
    elif 'a' <= char <= 'z':
        return ord(char) - LOWERCASE_OFFSET
    else:
        raise ValueError("%s is not a valid character" % char)


def true_chr(integer):
    """
    Turns an integer [integer] into digit in base [BASE]
    as a character representation.
    """
    if integer < 10:
        return chr(integer + DIGIT_OFFSET)
    elif 10 <= integer <= 35:
        return chr(integer + UPPERCASE_OFFSET)
    elif 36 <= integer < 62:
        return chr(integer + LOWERCASE_OFFSET)
    else:
        raise ValueError("%d is not a valid integer in the range of base %d" %
                         (integer, BASE))


def encode(key):
    """
    Turn the base [BASE] number [key] into an integer
    """
    int_sum = 0
    reversed_key = key[::-1]
    for idx, char in enumerate(reversed_key):
        int_sum += true_ord(char) * int(math.pow(BASE, idx))
    return int_sum


def decode(integer):
    """
    Turn an integer [integer] into a base [BASE] number
    in string representation
    """

    # we won't step into the while if integer is 0
    # so we just solve for that case here
    if integer == 0:
        return '0'

    string = ""
    while integer > 0:
        remainder = integer % BASE
        string = true_chr(remainder) + string
        integer /= BASE
    return string
