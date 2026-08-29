"""
Utility functions for the AI Desktop Automation Agent.
Contains helper functions for Bezier curves, random generation, and window management.
"""

import ctypes
import math
import random
import time
from typing import List, Tuple, Optional
import pyautogui


def bezier_curve(
    start: Tuple[int, int],
    end: Tuple[int, int],
    control_points: List[Tuple[int, int]],
    num_points: int = 50
) -> List[Tuple[int, int]]:
    """
    Generate points along a Bezier curve for smooth mouse movement.
    
    Args:
        start: Starting point (x, y)
        end: Ending point (x, y)
        control_points: List of control points for curve shape
        num_points: Number of points to generate
    
    Returns:
        List of (x, y) points along the curve
    """
    points = [start] + control_points + [end]
    n = len(points) - 1
    
    def binomial(n: int, k: int) -> int:
        """Calculate binomial coefficient."""
        if k < 0 or k > n:
            return 0
        if k == 0 or k == n:
            return 1
        return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
    
    def bezier_point(t: float) -> Tuple[int, int]:
        """Calculate point on Bezier curve at parameter t."""
        x = sum(binomial(n, i) * ((1 - t) ** (n - i)) * (t ** i) * points[i][0]
                for i in range(n + 1))
        y = sum(binomial(n, i) * ((1 - t) ** (n - i)) * (t ** i) * points[i][1]
                for i in range(n + 1))
        return (int(x), int(y))
    
    return [bezier_point(t / num_points) for t in range(num_points + 1)]


def generate_human_curve(
    start: Tuple[int, int],
    end: Tuple[int, int],
    variation: float = 100.0
) -> List[Tuple[int, int]]:
    """
    Generate a human-like curved path between two points.
    
    Args:
        start: Starting point
        end: Ending point
        variation: Amount of randomness in the curve
    
    Returns:
        List of points forming a human-like path
    """
    # Calculate distance for determining number of control points
    distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
    
    # More control points for longer distances
    num_control = max(1, min(4, int(distance / 200)))
    
    control_points = []
    for i in range(num_control):
        # Interpolate along the line and add random offset
        t = (i + 1) / (num_control + 1)
        mid_x = start[0] + (end[0] - start[0]) * t
        mid_y = start[1] + (end[1] - start[1]) * t
        
        # Add random variation perpendicular to the line
        offset_x = random.uniform(-variation, variation)
        offset_y = random.uniform(-variation, variation)
        
        control_points.append((int(mid_x + offset_x), int(mid_y + offset_y)))
    
    # Generate more points for longer distances
    num_points = max(20, int(distance / 10))
    
    return bezier_curve(start, end, control_points, num_points)


def random_delay(min_delay: float, max_delay: float) -> None:
    """
    Sleep for a random duration between min and max.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def human_delay(base: float = 0.1, variance: float = 0.05) -> None:
    """
    Add a human-like micro-delay with some variance.
    
    Args:
        base: Base delay time
        variance: Random variance to add
    """
    delay = base + random.uniform(-variance, variance)
    if delay > 0:
        time.sleep(delay)


def get_screen_size() -> Tuple[int, int]:
    """Get the screen resolution."""
    return pyautogui.size()


def get_random_screen_position(margin: int = 50) -> Tuple[int, int]:
    """
    Get a random position on screen within safe margins.
    
    Args:
        margin: Pixels to avoid from screen edges
    
    Returns:
        Random (x, y) position
    """
    width, height = get_screen_size()
    x = random.randint(margin, width - margin)
    y = random.randint(margin, height - margin)
    return (x, y)


def get_current_mouse_position() -> Tuple[int, int]:
    """Get current mouse cursor position."""
    return pyautogui.position()


def is_near_corner(position: Tuple[int, int], threshold: int = 5) -> bool:
    """
    Check if position is near any corner (failsafe check).
    
    Args:
        position: (x, y) position to check
        threshold: Pixels from corner to trigger
    
    Returns:
        True if near a corner
    """
    width, height = get_screen_size()
    x, y = position
    
    corners = [
        (0, 0),                    # Top-left
        (width - 1, 0),           # Top-right
        (0, height - 1),          # Bottom-left
        (width - 1, height - 1)   # Bottom-right
    ]
    
    for corner in corners:
        if abs(x - corner[0]) <= threshold and abs(y - corner[1]) <= threshold:
            return True
    return False


def get_active_window_title() -> str:
    """
    Get the title of the currently active window.
    
    Returns:
        Window title string
    """
    try:
        # Windows-specific implementation
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value
    except Exception:
        return ""


def get_active_window_process() -> str:
    """
    Get the process name of the currently active window.
    
    Returns:
        Process name string
    """
    try:
        import psutil
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        
        # Get process ID
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Get process name
        process = psutil.Process(pid.value)
        return process.name()
    except Exception:
        return ""


def weighted_random_choice(weights: dict) -> str:
    """
    Make a weighted random choice from a dictionary of options.
    
    Args:
        weights: Dictionary of {option: weight}
    
    Returns:
        Selected option
    """
    options = list(weights.keys())
    weight_values = list(weights.values())
    total = sum(weight_values)
    
    r = random.uniform(0, total)
    cumulative = 0
    
    for option, weight in zip(options, weight_values):
        cumulative += weight
        if r <= cumulative:
            return option
    
    return options[-1]


def add_noise_to_position(
    position: Tuple[int, int],
    noise_range: int = 5
) -> Tuple[int, int]:
    """
    Add small random noise to a position.
    
    Args:
        position: Original (x, y) position
        noise_range: Maximum pixels to offset
    
    Returns:
        Position with added noise
    """
    x, y = position
    x += random.randint(-noise_range, noise_range)
    y += random.randint(-noise_range, noise_range)
    return (max(0, x), max(0, y))


def generate_typing_variation(text: str) -> List[Tuple[str, float]]:
    """
    Generate typing sequence with varied delays for human-like typing.
    
    Args:
        text: Text to type
    
    Returns:
        List of (character, delay) tuples
    """
    result = []
    
    for i, char in enumerate(text):
        # Base delay
        delay = random.uniform(0.05, 0.15)
        
        # Longer delay after punctuation
        if char in '.!?':
            delay += random.uniform(0.2, 0.5)
        elif char in ',;:':
            delay += random.uniform(0.1, 0.2)
        
        # Longer delay after space (word boundary)
        if char == ' ':
            delay += random.uniform(0.05, 0.1)
        
        # Occasional longer pause (thinking)
        if random.random() < 0.02:
            delay += random.uniform(0.3, 0.8)
        
        result.append((char, delay))
    
    return result


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation between start and end."""
    return start + (end - start) * t


def ease_in_out(t: float) -> float:
    """Ease-in-out function for smooth acceleration/deceleration."""
    if t < 0.5:
        return 2 * t * t
    return 1 - ((-2 * t + 2) ** 2) / 2
