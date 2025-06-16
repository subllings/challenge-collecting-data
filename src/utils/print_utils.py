"""Utility module to print colored text and background colors in the terminal."""
from enum import Enum


class Color(Enum):
    """Enum for text colors"""
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BLACK = "\033[90m"


class BgColor(Enum):
    """Enum for background colors"""
    GREEN = "\033[42m"
    BLUE = "\033[44m"
    RED = "\033[41m"
    YELLOW = "\033[43m"
    CYAN = "\033[46m"
    MAGENTA = "\033[45m"
    WHITE = "\033[47m"
    BLACK = "\033[40m"


class PrintUtils:
    """Utility class for printing text with colors"""

    @staticmethod
    def print_color(text: str, color: Color) -> None:
        """
        Print text in the given color using the Color Enum.

        :param text: The text to print.
        :param color: The color from the Color Enum.
        """
        print(color.value + text + "\033[0m")  # Reset formatting at the end

    @staticmethod
    def print_bg_color(text: str, bg_color: BgColor) -> None:
        """
        Print text with the given background color, adjusting text color for contrast.

        :param text: The text to print.
        :param bg_color: The background color from the BgColor Enum.
        """
        # Define contrast text colors: light text for dark backgrounds,
        # dark text for light backgrounds
        contrast_colors = {
          BgColor.BLACK: Color.WHITE.value,
          BgColor.RED: Color.WHITE.value,
          BgColor.BLUE: Color.WHITE.value,
          BgColor.GREEN: Color.WHITE.value,
          BgColor.MAGENTA: Color.WHITE.value,
          BgColor.CYAN: Color.BLACK.value,
          BgColor.YELLOW: Color.WHITE.value,  # Use White instead of Black
          BgColor.WHITE: Color.BLACK.value
        }

        # Default to normal if undefined
        text_color = contrast_colors.get(bg_color, "\033[0m")
        print(
            bg_color.value + text_color + text + "\033[0m",
            flush=True
        )  # Reset formatting at the end
