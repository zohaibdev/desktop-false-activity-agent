"""
Actions Module for AI Desktop Automation Agent (Enhanced Version)
==================================================================

Advanced human-like actions including:
- Curved mouse movements with micro-jitter
- Variable typing speed with typos and corrections
- Hesitation and thinking pauses
- Realistic scrolling patterns
- Application-specific behaviors

All actions are designed to mimic natural human behavior.
"""

import random
import time
from typing import List, Tuple, Optional, Dict, Any

import pyautogui

from config import config
from logger import get_logger
from utils import (
    generate_human_curve,
    random_delay,
    human_delay,
    get_screen_size,
    get_random_screen_position,
    get_current_mouse_position,
    add_noise_to_position,
    generate_typing_variation,
    ease_in_out,
    get_active_window_title
)


# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01  # Small pause between pyautogui calls


class HumanBehavior:
    """
    Provides human-like micro-behaviors that make automation appear natural.
    These are subtle additions that differentiate bots from humans.
    """
    
    @staticmethod
    def add_micro_jitter(position: Tuple[int, int], intensity: int = 3) -> Tuple[int, int]:
        """Add small random jitter to a position."""
        x, y = position
        jitter_x = random.randint(-intensity, intensity)
        jitter_y = random.randint(-intensity, intensity)
        return (max(0, x + jitter_x), max(0, y + jitter_y))
    
    @staticmethod
    def hesitate(min_time: float = 0.2, max_time: float = 0.8) -> None:
        """Simulate brief hesitation before action."""
        delay = random.uniform(min_time, max_time)
        time.sleep(delay)
    
    @staticmethod
    def think(min_time: float = 1.0, max_time: float = 3.0) -> None:
        """Simulate thinking or reading pause."""
        delay = random.uniform(min_time, max_time)
        time.sleep(delay)
    
    @staticmethod
    def get_variable_delay(base: float, variance: float = 0.3) -> float:
        """Get a delay with human-like variance."""
        return base * random.uniform(1 - variance, 1 + variance)
    
    @staticmethod
    def should_make_mistake(probability: float = 0.05) -> bool:
        """Determine if a mistake should occur."""
        return random.random() < probability
    
    @staticmethod
    def get_typing_rhythm() -> str:
        """Get current typing rhythm (fast, normal, slow)."""
        r = random.random()
        if r < 0.2:
            return "fast"
        elif r < 0.8:
            return "normal"
        return "slow"


class MouseActions:
    """Human-like mouse control with natural movements."""
    
    @staticmethod
    def move_smooth(
        target: Tuple[int, int],
        duration: Optional[float] = None,
        with_jitter: bool = True
    ) -> None:
        """
        Move mouse smoothly along a curved path to target.
        
        Args:
            target: Target (x, y) position
            duration: Optional movement duration override
            with_jitter: Add micro-jitter during movement
        """
        logger = get_logger()
        start = get_current_mouse_position()
        
        # Ensure target is within screen bounds
        width, height = get_screen_size()
        target = (
            max(0, min(width - 1, target[0])),
            max(0, min(height - 1, target[1]))
        )
        
        # Optional hesitation before moving
        if random.random() < 0.2:
            HumanBehavior.hesitate(0.1, 0.3)
        
        # Generate human-like curved path
        path = generate_human_curve(
            start, 
            target, 
            variation=config.mouse.curve_variation
        )
        
        # Calculate duration if not provided
        if duration is None:
            duration = random.uniform(
                config.mouse.move_duration_min,
                config.mouse.move_duration_max
            )
        
        # Move along the path
        num_points = len(path)
        start_time = time.time()
        
        # VirtualBox mode: use relative movements
        if config.virtualbox.virtualbox_mode:
            prev_point = start
            for i, point in enumerate(path):
                # Calculate relative movement
                dx = point[0] - prev_point[0]
                dy = point[1] - prev_point[1]
                
                if dx != 0 or dy != 0:
                    pyautogui.moveRel(dx, dy, _pause=False)
                    time.sleep(config.virtualbox.vm_mouse_delay)
                
                prev_point = point
                
                # Add micro-jitter occasionally
                if with_jitter and random.random() < 0.05:
                    jx = random.randint(-2, 2)
                    jy = random.randint(-2, 2)
                    pyautogui.moveRel(jx, jy, _pause=False)
        else:
            # Normal mode: absolute movements
            for i, point in enumerate(path):
                # Calculate progress with easing
                progress = i / (num_points - 1) if num_points > 1 else 1
                eased_progress = ease_in_out(progress)
                
                # Add micro-jitter occasionally
                if with_jitter and random.random() < 0.1:
                    point = HumanBehavior.add_micro_jitter(point, 2)
                
                # Move to point
                pyautogui.moveTo(point[0], point[1], _pause=False)
                
                # Calculate appropriate delay
                elapsed = time.time() - start_time
                target_time = duration * eased_progress
                sleep_time = target_time - elapsed
                
                if sleep_time > 0:
                    time.sleep(sleep_time / (num_points - i) if i < num_points - 1 else sleep_time)
        
        logger.action("mouse_move", f"Moved to ({target[0]}, {target[1]})")
    
    @staticmethod
    def move_random() -> Tuple[int, int]:
        """Move mouse to a random position on screen."""
        target = get_random_screen_position(margin=config.mouse.margin)
        MouseActions.move_smooth(target)
        return target
    
    @staticmethod
    def micro_movement(pixel_range: int = 10) -> None:
        """
        Small mouse movement simulating natural hand jitter.
        Used during idle periods.
        """
        logger = get_logger()
        
        # Small random offset
        offset_x = random.randint(-pixel_range, pixel_range)
        offset_y = random.randint(-pixel_range, pixel_range)
        
        # VirtualBox mode: use relative movement directly
        if config.virtualbox.virtualbox_mode:
            pyautogui.moveRel(offset_x, offset_y, duration=random.uniform(0.1, 0.3))
        else:
            current = get_current_mouse_position()
            target = (
                max(0, current[0] + offset_x),
                max(0, current[1] + offset_y)
            )
            duration = random.uniform(0.1, 0.3)
            pyautogui.moveTo(target[0], target[1], duration=duration)
        
        logger.action("micro_movement", f"Jitter by ({offset_x}, {offset_y})")
    
    @staticmethod
    def click(
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.1
    ) -> None:
        """Perform mouse click with human-like behavior."""
        logger = get_logger()
        
        # Small random delay before click
        HumanBehavior.hesitate(0.03, 0.1)
        
        pyautogui.click(button=button, clicks=clicks, interval=interval)
        
        # Small delay after click
        time.sleep(random.uniform(0.05, 0.15))
        
        click_type = f"{clicks}x" if clicks > 1 else "single"
        logger.action("mouse_click", f"{click_type} {button} click")
    
    @staticmethod
    def random_click(allow_double: bool = True) -> None:
        """Perform a click with random parameters."""
        # Determine click type
        if allow_double and random.random() < config.mouse.double_click_probability:
            MouseActions.click(clicks=2, interval=random.uniform(0.08, 0.15))
        else:
            MouseActions.click()
    
    @staticmethod
    def click_with_mistake() -> None:
        """
        Simulate a misclick and correction.
        Click wrong spot, pause, then click correct spot.
        """
        logger = get_logger()
        
        # Get current target
        target = get_current_mouse_position()
        
        # Calculate wrong position (slight offset)
        wrong_x = target[0] + random.randint(20, 50) * random.choice([-1, 1])
        wrong_y = target[1] + random.randint(20, 50) * random.choice([-1, 1])
        
        # Move to wrong position
        MouseActions.move_smooth((wrong_x, wrong_y), duration=random.uniform(0.2, 0.4))
        
        # Click wrong spot
        MouseActions.click()
        
        # Pause (realizing mistake)
        time.sleep(random.uniform(0.3, 0.7))
        
        # Move back to correct position
        MouseActions.move_smooth(target, duration=random.uniform(0.3, 0.5))
        
        # Click correct spot
        MouseActions.click()
        
        logger.action("mistake_correction", "Misclick corrected")
    
    @staticmethod
    def drag(
        start: Tuple[int, int],
        end: Tuple[int, int],
        button: str = "left"
    ) -> None:
        """Perform a drag operation."""
        logger = get_logger()
        
        # Move to start position
        MouseActions.move_smooth(start)
        HumanBehavior.hesitate(0.1, 0.2)
        
        # Perform drag
        pyautogui.mouseDown(button=button)
        time.sleep(random.uniform(0.05, 0.1))
        MouseActions.move_smooth(end, with_jitter=False)
        time.sleep(random.uniform(0.05, 0.1))
        pyautogui.mouseUp(button=button)
        
        logger.action("mouse_drag", f"Dragged from {start} to {end}")
    
    @staticmethod
    def drag_select() -> None:
        """Perform a text selection drag."""
        current = get_current_mouse_position()
        
        # Drag horizontally (like selecting text)
        drag_length = random.randint(50, 200)
        end = (current[0] + drag_length, current[1] + random.randint(-5, 5))
        
        MouseActions.drag(current, end)


class ScrollActions:
    """Scrolling behavior with human-like patterns."""
    
    @staticmethod
    def scroll(
        amount: int,
        direction: str = "down",
        smooth: bool = True
    ) -> None:
        """Perform scrolling action."""
        logger = get_logger()
        
        # Convert direction to signed amount
        scroll_amount = amount if direction == "down" else -amount
        
        if smooth and abs(amount) > 1:
            # Smooth scrolling with multiple small steps
            steps = config.scroll.smooth_scroll_steps
            
            for i in range(steps):
                # Variable step size
                step = scroll_amount / steps
                step *= random.uniform(0.8, 1.2)  # Add variance
                
                pyautogui.scroll(int(step))
                
                # Variable delay between steps
                delay = random.uniform(0.03, 0.08)
                time.sleep(delay)
        else:
            pyautogui.scroll(scroll_amount)
        
        logger.action("scroll", f"Scrolled {direction} by {amount}")
    
    @staticmethod
    def random_scroll() -> None:
        """Perform a random scroll action."""
        # Determine direction based on weights
        direction = "down" if random.random() < config.scroll.scroll_down_weight else "up"
        
        # Random amount
        amount = random.randint(
            config.scroll.scroll_min,
            config.scroll.scroll_max
        )
        
        # Random smooth setting
        smooth = random.random() < 0.7
        
        ScrollActions.scroll(amount, direction, smooth)
    
    @staticmethod
    def scroll_with_read() -> None:
        """Scroll with reading pauses (for browsing behavior)."""
        logger = get_logger()
        
        for _ in range(random.randint(2, 4)):
            # Random direction - scroll up sometimes too
            direction = "down" if random.random() < 0.6 else "up"
            
            # Scroll
            ScrollActions.scroll(
                random.randint(1, 3),
                direction=direction,
                smooth=True
            )
            
            # Read/pause - shorter
            HumanBehavior.think(0.3, 1.0)
        
        logger.action("scroll_read", "Scroll with reading pattern")


class KeyboardActions:
    """Keyboard typing and shortcuts with human-like behavior."""
    
    # Common typo pairs (adjacent keys)
    TYPO_PAIRS = {
        'a': ['s', 'q', 'w'],
        'e': ['w', 'r', 'd'],
        'i': ['u', 'o', 'k'],
        'o': ['i', 'p', 'l'],
        'n': ['b', 'm', 'h'],
        't': ['r', 'y', 'g'],
    }
    
    @staticmethod
    def type_text(
        text: str = None,
        realistic: bool = True,
        include_typos: bool = False
    ) -> None:
        """
        Type text with human-like delays.
        
        Args:
            text: Text to type (if None, uses sample)
            realistic: Use varied delays
            include_typos: Include occasional typos
        """
        logger = get_logger()
        
        if text is None:
            text = random.choice(config.keyboard.typing_samples)
        
        # Determine typing rhythm
        rhythm = HumanBehavior.get_typing_rhythm()
        
        if rhythm == "fast":
            base_delay = 0.03
            variance = 0.02
        elif rhythm == "slow":
            base_delay = 0.15
            variance = 0.08
        else:
            base_delay = 0.08
            variance = 0.04
        
        typed_count = 0
        
        for i, char in enumerate(text):
            # Calculate delay for this character
            delay = base_delay + random.uniform(-variance, variance)
            
            # Longer delay after punctuation
            if i > 0 and text[i-1] in '.!?':
                delay += random.uniform(0.3, 0.8)
            elif i > 0 and text[i-1] in ',;:':
                delay += random.uniform(0.1, 0.3)
            
            # Occasional thinking pause
            if random.random() < 0.02:
                delay += random.uniform(0.5, 1.5)
            
            # Handle typos
            if include_typos and char.lower() in KeyboardActions.TYPO_PAIRS:
                if random.random() < 0.03:
                    # Make typo
                    wrong_char = random.choice(KeyboardActions.TYPO_PAIRS[char.lower()])
                    pyautogui.typewrite(wrong_char, interval=0)
                    time.sleep(random.uniform(0.1, 0.3))
                    
                    # Correct it
                    pyautogui.press('backspace')
                    time.sleep(random.uniform(0.1, 0.2))
            
            # Type the character
            if char.isalnum() or char in ' .,!?-_':
                pyautogui.typewrite(char, interval=0)
            else:
                # Use press for special characters
                try:
                    pyautogui.press(char)
                except:
                    pass
            
            typed_count += 1
            time.sleep(delay)
        
        logger.action("type_text", f"Typed {typed_count} characters")
    
    @staticmethod
    def type_with_bursts(text: str = None) -> None:
        """Type with variable speed bursts (fast then slow)."""
        if text is None:
            text = random.choice(config.keyboard.typing_samples)
        
        words = text.split()
        
        for word in words:
            # Random speed for this word
            if random.random() < 0.3:
                # Fast burst
                pyautogui.typewrite(word, interval=random.uniform(0.02, 0.05))
            else:
                # Normal typing
                KeyboardActions.type_text(word, realistic=True)
            
            # Space between words
            pyautogui.typewrite(' ', interval=0)
            time.sleep(random.uniform(0.1, 0.3))
    
    @staticmethod
    def type_realistic() -> None:
        """Type a random realistic text sample."""
        text = random.choice(config.keyboard.typing_samples)
        include_typos = random.random() < 0.15
        KeyboardActions.type_text(text, realistic=True, include_typos=include_typos)
    
    @staticmethod
    def press_key(key: str) -> None:
        """Press a single key."""
        logger = get_logger()
        HumanBehavior.hesitate(0.03, 0.08)
        pyautogui.press(key)
        logger.action("key_press", f"Pressed {key}")
    
    @staticmethod
    def press_escape() -> None:
        """Press Escape key."""
        KeyboardActions.press_key('escape')
    
    @staticmethod
    def hotkey(*keys: str) -> None:
        """Press a keyboard shortcut."""
        logger = get_logger()
        HumanBehavior.hesitate(0.03, 0.08)
        pyautogui.hotkey(*keys)
        time.sleep(random.uniform(0.05, 0.15))
        logger.action("hotkey", f"Pressed {'+'.join(keys)}")
    
    @staticmethod
    def execute_shortcut(shortcut: str) -> None:
        """Execute shortcut from string like 'ctrl+s'."""
        keys = shortcut.lower().split('+')
        KeyboardActions.hotkey(*keys)
    
    @staticmethod
    def copy() -> None:
        """Perform Ctrl+C."""
        KeyboardActions.hotkey('ctrl', 'c')
    
    @staticmethod
    def paste() -> None:
        """Perform Ctrl+V."""
        KeyboardActions.hotkey('ctrl', 'v')
    
    @staticmethod
    def cut() -> None:
        """Perform Ctrl+X."""
        KeyboardActions.hotkey('ctrl', 'x')
    
    @staticmethod
    def undo() -> None:
        """Perform Ctrl+Z."""
        KeyboardActions.hotkey('ctrl', 'z')
    
    @staticmethod
    def select_all() -> None:
        """Perform Ctrl+A."""
        KeyboardActions.hotkey('ctrl', 'a')
    
    @staticmethod
    def save() -> None:
        """Perform Ctrl+S."""
        KeyboardActions.hotkey('ctrl', 's')
    
    @staticmethod
    def alt_tab() -> None:
        """Switch windows with Alt+Tab - Fast."""
        logger = get_logger()
        
        # Hold alt and press tab - faster
        pyautogui.keyDown('alt')
        time.sleep(0.05)
        pyautogui.press('tab')
        
        # Optional: press tab again for different window
        if random.random() < 0.3:
            time.sleep(0.1)
            pyautogui.press('tab')
        
        time.sleep(0.1)
        pyautogui.keyUp('alt')
        
        logger.action("switch_window", "Alt+Tab")
    
    @staticmethod
    def ctrl_tab() -> None:
        """Switch browser tabs with Ctrl+Tab - Fast."""
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(0.05)
    
    @staticmethod
    def ctrl_shift_tab() -> None:
        """Switch browser tabs backward."""
        KeyboardActions.hotkey('ctrl', 'shift', 'tab')
    
    @staticmethod
    def random_shortcut() -> str:
        """Execute a random keyboard shortcut - no save in browsers."""
        shortcuts = [
            ('copy', KeyboardActions.copy),
            ('ctrl_tab', KeyboardActions.ctrl_tab),
            ('ctrl_tab', KeyboardActions.ctrl_tab),
            ('undo', KeyboardActions.undo),
        ]
        
        name, func = random.choice(shortcuts)
        func()
        return name


class ApplicationActions:
    """Application-specific actions for Chrome and VS Code."""
    
    # Chrome actions
    @staticmethod
    def chrome_new_tab() -> None:
        KeyboardActions.hotkey('ctrl', 't')
    
    @staticmethod
    def chrome_close_tab() -> None:
        KeyboardActions.hotkey('ctrl', 'w')
    
    @staticmethod
    def chrome_next_tab() -> None:
        KeyboardActions.ctrl_tab()
    
    @staticmethod
    def chrome_prev_tab() -> None:
        KeyboardActions.ctrl_shift_tab()
    
    @staticmethod
    def chrome_address_bar() -> None:
        KeyboardActions.hotkey('ctrl', 'l')
    
    @staticmethod
    def chrome_refresh() -> None:
        KeyboardActions.hotkey('ctrl', 'r')
    
    @staticmethod
    def chrome_back() -> None:
        KeyboardActions.hotkey('alt', 'left')
    
    @staticmethod
    def chrome_forward() -> None:
        KeyboardActions.hotkey('alt', 'right')
    
    # VS Code actions
    @staticmethod
    def vscode_command_palette() -> None:
        KeyboardActions.hotkey('ctrl', 'shift', 'p')
    
    @staticmethod
    def vscode_quick_open() -> None:
        KeyboardActions.hotkey('ctrl', 'p')
    
    @staticmethod
    def vscode_toggle_terminal() -> None:
        KeyboardActions.hotkey('ctrl', '`')
    
    @staticmethod
    def vscode_go_to_line() -> None:
        KeyboardActions.hotkey('ctrl', 'g')
    
    @staticmethod
    def vscode_find() -> None:
        KeyboardActions.hotkey('ctrl', 'f')
    
    @staticmethod
    def vscode_find_replace() -> None:
        KeyboardActions.hotkey('ctrl', 'h')
    
    @staticmethod
    def vscode_comment_line() -> None:
        KeyboardActions.hotkey('ctrl', '/')
    
    @staticmethod
    def vscode_format_document() -> None:
        KeyboardActions.hotkey('shift', 'alt', 'f')
    
    @staticmethod
    def get_context_actions() -> List[callable]:
        """Get relevant actions based on active window."""
        title = get_active_window_title().lower()
        
        if 'chrome' in title or 'edge' in title or 'firefox' in title:
            return [
                ApplicationActions.chrome_next_tab,
                ApplicationActions.chrome_prev_tab,
                ApplicationActions.chrome_refresh,
                ApplicationActions.chrome_back,
                ScrollActions.random_scroll,
            ]
        elif 'visual studio code' in title or 'code' in title:
            return [
                ApplicationActions.vscode_command_palette,
                ApplicationActions.vscode_quick_open,
                ApplicationActions.vscode_toggle_terminal,
                ApplicationActions.vscode_find,
                KeyboardActions.type_realistic,
                ScrollActions.random_scroll,
            ]
        else:
            return [
                MouseActions.move_random,
                ScrollActions.random_scroll,
                KeyboardActions.random_shortcut,
            ]


class IdleActions:
    """Idle and waiting behaviors."""
    
    @staticmethod
    def short_pause(min_duration: float = 0.1, max_duration: float = 0.5) -> None:
        """Short pause simulating brief thinking - FAST."""
        logger = get_logger()
        duration = random.uniform(min_duration, max_duration)
        logger.action("idle", f"Short pause for {duration:.1f}s")
        time.sleep(duration)
    
    @staticmethod
    def long_pause() -> None:
        """Longer pause simulating reading or thinking."""
        logger = get_logger()
        duration = random.uniform(
            config.timing.long_pause_min,
            config.timing.long_pause_max
        )
        logger.action("idle", f"Long pause for {duration:.1f}s")
        time.sleep(duration)
    
    @staticmethod
    def idle_with_movement(duration: float = 1.0) -> None:
        """Idle period with occasional micro-movements - FAST."""
        logger = get_logger()
        
        elapsed = 0
        movement_interval = random.uniform(0.3, 0.8)
        
        while elapsed < duration:
            # Sleep for interval
            sleep_time = min(movement_interval, duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
            
            # Occasional micro-movement
            if elapsed < duration and random.random() < 0.4:
                MouseActions.micro_movement(pixel_range=8)
        
        logger.action("idle", f"Idle with movement for {duration:.1f}s")
    
    @staticmethod
    def random_idle(params: Dict[str, Any] = None) -> None:
        """Perform random idle behavior - FAST."""
        duration = 0.5
        if params and 'duration' in params:
            duration = params['duration']
        
        behaviors = [
            (lambda: IdleActions.short_pause(0.1, duration), 0.4),
            (lambda: IdleActions.idle_with_movement(duration), 0.4),
            (lambda: MouseActions.micro_movement(), 0.2),
        ]
        
        total_weight = sum(w for _, w in behaviors)
        r = random.uniform(0, total_weight)
        
        cumulative = 0
        for behavior, weight in behaviors:
            cumulative += weight
            if r <= cumulative:
                behavior()
                return
        
        IdleActions.short_pause()


class HesitationActions:
    """Hesitation and uncertainty behaviors."""
    
    @staticmethod
    def hesitate_before_action(params: Dict[str, Any] = None) -> None:
        """Brief hesitation before doing something."""
        logger = get_logger()
        
        duration = random.uniform(0.3, 1.0)
        if params and 'duration' in params:
            duration = params['duration']
        
        # Optional micro-movement during hesitation
        if random.random() < 0.3:
            MouseActions.micro_movement(pixel_range=5)
        
        time.sleep(duration)
        logger.action("hesitate", f"Hesitated for {duration:.2f}s")
    
    @staticmethod
    def hover_hesitate() -> None:
        """Hover over something and hesitate (as if reading/deciding)."""
        logger = get_logger()
        
        # Small movement
        MouseActions.micro_movement(pixel_range=15)
        
        # Pause
        time.sleep(random.uniform(0.5, 1.5))
        
        # Maybe click, maybe not
        if random.random() < 0.3:
            MouseActions.click()
        
        logger.action("hover_hesitate", "Hovered and hesitated")


# Main action execution function
def perform_action(action_type: str, params: Dict[str, Any] = None) -> bool:
    """
    Perform a named action with optional parameters.
    
    Args:
        action_type: Type of action to perform
        params: Optional parameters for the action
    
    Returns:
        True if action was performed successfully
    """
    logger = get_logger()
    params = params or {}
    
    action_map = {
        'mouse_move': lambda: MouseActions.move_random(),
        'mouse_click': lambda: MouseActions.random_click(params.get('double', False)),
        'scroll': lambda: ScrollActions.scroll(
            params.get('amount', random.randint(1, 3)),
            params.get('direction', 'down'),
            params.get('smooth', True)
        ),
        'type_text': lambda: KeyboardActions.type_text(
            params.get('text'),
            params.get('realistic', True),
            params.get('include_typos', False)
        ),
        'keyboard_shortcut': lambda: KeyboardActions.execute_shortcut(
            params.get('shortcut', 'ctrl+tab')
        ),
        'switch_window': KeyboardActions.alt_tab,
        'switch_tab': KeyboardActions.ctrl_tab,
        'idle': lambda: IdleActions.random_idle(params),
        'micro_movement': lambda: MouseActions.micro_movement(
            params.get('range', 10)
        ),
        'hesitate': lambda: HesitationActions.hesitate_before_action(params),
        'mistake_correction': MouseActions.click_with_mistake,
        'drag_select': MouseActions.drag_select,
        'press_key': lambda: KeyboardActions.press_key(params.get('key', 'enter')),
        'press_escape': KeyboardActions.press_escape,
    }
    
    if action_type in action_map:
        try:
            action_map[action_type]()
            return True
        except Exception as e:
            logger.error(f"Action failed: {action_type} - {e}")
            return False
    else:
        logger.warning(f"Unknown action type: {action_type}")
        return False


def execute_task_action(action: str, params: Dict[str, Any]) -> bool:
    """
    Execute an action from a task step.
    
    Args:
        action: Action name
        params: Action parameters
    
    Returns:
        True if successful
    """
    return perform_action(action, params)


class MouseActionsWrapper:
    """Wrapper for mouse actions used by agent."""
    
    @staticmethod
    def random_move():
        MouseActions.move_random()
    
    @staticmethod
    def click_random_area():
        MouseActions.random_click()
    
    @staticmethod
    def move_smooth(x: int, y: int):
        MouseActions.move_smooth(x, y)
    
    @staticmethod
    def click():
        MouseActions.click()


class ScrollActionsWrapper:
    """Wrapper for scroll actions used by agent."""
    
    @staticmethod
    def random_scroll():
        ScrollActions.random_scroll()


class KeyboardActionsWrapper:
    """Wrapper for keyboard actions used by agent."""
    
    @staticmethod
    def type_text(text: str):
        KeyboardActions.type_text(text, realistic=True)


class ApplicationActionsWrapper:
    """Wrapper for application actions used by agent."""
    
    @staticmethod
    def switch_tab():
        KeyboardActions.ctrl_tab()
    
    @staticmethod
    def switch_window():
        KeyboardActions.alt_tab()


class IdleActionsWrapper:
    """Wrapper for idle actions used by agent - FAST."""
    
    @staticmethod
    def micro_break():
        IdleActions.short_pause(0.1, 0.3)
    
    @staticmethod
    def look_around():
        IdleActions.idle_with_movement(random.uniform(0.2, 0.6))


class Actions:
    """
    Main actions interface for the agent.
    Provides organized access to all action types.
    """
    
    def __init__(self):
        self.mouse = MouseActionsWrapper()
        self.scroll = ScrollActionsWrapper()
        self.keyboard = KeyboardActionsWrapper()
        self.application = ApplicationActionsWrapper()
        self.idle = IdleActionsWrapper()
        self.hesitation = HesitationActions()


# Global actions instance
_actions: Actions = None


def get_actions() -> Actions:
    """Get the global Actions instance."""
    global _actions
    if _actions is None:
        _actions = Actions()
    return _actions
