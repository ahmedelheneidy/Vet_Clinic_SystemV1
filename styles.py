"""
styles.py

This module defines common CSS style strings for the application.
It includes a helper function to return style definitions based on the chosen theme.
"""

def get_theme_styles(theme="default"):
    """
    Returns a dictionary with style definitions for the specified theme.
    
    Parameters:
        theme (str): The theme name ("default" or "dark").
    
    Supported Themes:
        - "default": Light-themed styles.
        - "dark": Dark-themed styles for low-light environments.
    
    Returns:
        dict: A dictionary containing style strings for various UI components.
    """
    if theme.lower() == "dark":
        return {
            "TITLE_STYLE": "font-size: 26px; font-weight: bold; color: #FFFFFF;",
            "BUTTON_STYLE": "padding: 10px 20px; font-size: 16px; background-color: #333333; color: #FFFFFF; border: none; border-radius: 5px;",
            "GROUPBOX_STYLE": "background-color: #444444; border: 1px solid #666666; border-radius: 8px; padding: 15px;",
            "HEADER_LABEL_STYLE": "font-size: 18px; color: #DDDDDD;",
            "LISTSTYLE": "font-size: 16px; color: #DDDDDD;",
            "PLACEHOLDER_STYLE": "font-size: 16px; color: #AAAAAA; padding: 40px; border: 2px dashed #888888; border-radius: 8px;"
        }
    else:
        # Default theme (light mode).
        return {
            "TITLE_STYLE": "font-size: 26px; font-weight: bold; color: #2E8B57;",
            "BUTTON_STYLE": "padding: 10px 20px; font-size: 16px; background-color: #4682B4; color: white; border: none; border-radius: 5px;",
            "GROUPBOX_STYLE": "background-color: #FFFFFF; border: 1px solid #dcdcdc; border-radius: 8px; padding: 15px;",
            "HEADER_LABEL_STYLE": "font-size: 18px; color: #333333;",
            "LISTSTYLE": "font-size: 16px; color: #333333;",
            "PLACEHOLDER_STYLE": "font-size: 16px; color: #555555; padding: 40px; border: 2px dashed #aaaaaa; border-radius: 8px;"
        }

# Export default styles based on the "default" theme.
DEFAULT_STYLES = get_theme_styles("default")

# Export individual style constants for backward compatibility.
TITLE_STYLE = DEFAULT_STYLES["TITLE_STYLE"]
BUTTON_STYLE = DEFAULT_STYLES["BUTTON_STYLE"]
GROUPBOX_STYLE = DEFAULT_STYLES["GROUPBOX_STYLE"]
HEADER_LABEL_STYLE = DEFAULT_STYLES["HEADER_LABEL_STYLE"]
LISTSTYLE = DEFAULT_STYLES["LISTSTYLE"]
PLACEHOLDER_STYLE = DEFAULT_STYLES["PLACEHOLDER_STYLE"]

__all__ = [
    "get_theme_styles", "DEFAULT_STYLES", "TITLE_STYLE", "BUTTON_STYLE",
    "GROUPBOX_STYLE", "HEADER_LABEL_STYLE", "LISTSTYLE", "PLACEHOLDER_STYLE"
]
