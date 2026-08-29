"""
Vision Module for AI Desktop Automation Agent
==============================================

Advanced screen awareness system using OpenCV for:
- Application detection (Chrome, VS Code, etc.)
- UI element recognition (tabs, buttons, scroll areas)
- Template matching for specific targets
- Screen change detection
- Color-based region identification

This module provides the "eyes" for the intelligent agent.
"""

import os
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageGrab
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    cv2 = None
    np = None

import pyautogui

from logger import get_logger


class ApplicationType(Enum):
    """Detected application types."""
    UNKNOWN = "unknown"
    CHROME = "chrome"
    VSCODE = "vscode"
    EXPLORER = "explorer"
    NOTEPAD = "notepad"
    TERMINAL = "terminal"
    DESKTOP = "desktop"


class UIElement(Enum):
    """Detectable UI elements."""
    TAB_BAR = "tab_bar"
    ADDRESS_BAR = "address_bar"
    SCROLL_AREA = "scroll_area"
    BUTTON = "button"
    TEXT_AREA = "text_area"
    MENU = "menu"
    SIDEBAR = "sidebar"
    TOOLBAR = "toolbar"


@dataclass
class ScreenRegion:
    """Represents a detected region on screen."""
    x: int
    y: int
    width: int
    height: int
    element_type: UIElement = UIElement.SCROLL_AREA
    confidence: float = 1.0
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get center point of region."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Get (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class ScreenContext:
    """
    Complete context of current screen state.
    Used by brain for decision making.
    """
    timestamp: float = 0.0
    
    # Application detection
    detected_app: ApplicationType = ApplicationType.UNKNOWN
    app_confidence: float = 0.0
    window_title: str = ""
    
    # Detected regions
    regions: List[ScreenRegion] = field(default_factory=list)
    
    # Screen characteristics
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    brightness: float = 0.5
    has_dark_theme: bool = False
    
    # Change detection
    screen_changed: bool = False
    change_intensity: float = 0.0
    
    # Clickable areas (for intelligent clicking)
    clickable_areas: List[Tuple[int, int]] = field(default_factory=list)
    
    @property
    def active_app(self) -> str:
        """Alias for detected_app as string."""
        return self.detected_app.value
    
    @property
    def visible_elements(self) -> List[ScreenRegion]:
        """Alias for regions."""
        return self.regions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM context."""
        return {
            "app": self.detected_app.value,
            "app_confidence": self.app_confidence,
            "window_title": self.window_title,
            "num_regions": len(self.regions),
            "brightness": self.brightness,
            "dark_theme": self.has_dark_theme,
            "screen_changed": self.screen_changed,
            "num_clickable": len(self.clickable_areas),
        }


class ApplicationDetector:
    """
    Detects which application is currently active using visual cues.
    Uses color analysis, UI patterns, and template matching.
    """
    
    # Color signatures for different applications
    APP_SIGNATURES = {
        ApplicationType.CHROME: {
            "toolbar_colors": [(222, 225, 230), (241, 243, 244), (255, 255, 255)],
            "has_address_bar": True,
            "tab_position": "top",
        },
        ApplicationType.VSCODE: {
            "sidebar_colors": [(37, 37, 38), (51, 51, 51), (30, 30, 30)],
            "has_activity_bar": True,
            "dark_theme_likely": True,
        },
        ApplicationType.TERMINAL: {
            "background_colors": [(12, 12, 12), (0, 0, 0), (30, 30, 30)],
            "text_colors": [(204, 204, 204), (255, 255, 255)],
        },
    }
    
    def __init__(self):
        self.logger = get_logger()
        self._last_detection: Optional[ApplicationType] = None
        self._detection_history: List[ApplicationType] = []
    
    def detect(self, screenshot: 'np.ndarray') -> Tuple[ApplicationType, float]:
        """
        Detect the current application from screenshot.
        
        Args:
            screenshot: BGR image array
        
        Returns:
            Tuple of (ApplicationType, confidence)
        """
        if not VISION_AVAILABLE or screenshot is None:
            return ApplicationType.UNKNOWN, 0.0
        
        scores = {}
        
        # Analyze different regions
        height, width = screenshot.shape[:2]
        
        # Top region (toolbar/tabs)
        top_region = screenshot[0:80, :]
        top_colors = self._get_dominant_colors(top_region, 3)
        
        # Left region (sidebar)
        left_region = screenshot[:, 0:60]
        left_colors = self._get_dominant_colors(left_region, 3)
        
        # Main area
        main_region = screenshot[80:height-50, 60:width-20]
        main_brightness = self._calculate_brightness(main_region)
        
        # Chrome detection
        chrome_score = 0.0
        for color in top_colors:
            if self._color_distance(color, (241, 243, 244)) < 30:
                chrome_score += 0.3
            if self._color_distance(color, (222, 225, 230)) < 30:
                chrome_score += 0.2
        scores[ApplicationType.CHROME] = min(chrome_score, 1.0)
        
        # VS Code detection
        vscode_score = 0.0
        for color in left_colors:
            if self._color_distance(color, (51, 51, 51)) < 20:
                vscode_score += 0.3
            if self._color_distance(color, (37, 37, 38)) < 20:
                vscode_score += 0.2
        if main_brightness < 0.3:
            vscode_score += 0.2
        scores[ApplicationType.VSCODE] = min(vscode_score, 1.0)
        
        # Terminal detection
        terminal_score = 0.0
        if main_brightness < 0.15:
            terminal_score += 0.4
        for color in self._get_dominant_colors(screenshot, 2):
            if self._color_distance(color, (12, 12, 12)) < 15:
                terminal_score += 0.3
        scores[ApplicationType.TERMINAL] = min(terminal_score, 1.0)
        
        # Get best match
        best_app = max(scores, key=scores.get)
        best_score = scores[best_app]
        
        # Require minimum confidence
        if best_score < 0.3:
            best_app = ApplicationType.UNKNOWN
            best_score = 0.0
        
        # Update history for stability
        self._detection_history.append(best_app)
        if len(self._detection_history) > 5:
            self._detection_history.pop(0)
        
        # Return most common recent detection for stability
        if len(self._detection_history) >= 3:
            from collections import Counter
            most_common = Counter(self._detection_history).most_common(1)[0]
            if most_common[1] >= 2:
                best_app = most_common[0]
        
        self._last_detection = best_app
        return best_app, best_score
    
    def _get_dominant_colors(
        self, 
        image: 'np.ndarray', 
        n_colors: int = 3
    ) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using k-means."""
        if not VISION_AVAILABLE:
            return []
        
        try:
            pixels = image.reshape(-1, 3).astype(np.float32)
            
            # Downsample for speed
            if len(pixels) > 10000:
                indices = np.random.choice(len(pixels), 10000, replace=False)
                pixels = pixels[indices]
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(
                pixels, n_colors, None, criteria, 3, cv2.KMEANS_PP_CENTERS
            )
            
            return [(int(c[2]), int(c[1]), int(c[0])) for c in centers]  # BGR to RGB
        except:
            return []
    
    def _color_distance(
        self, 
        c1: Tuple[int, int, int], 
        c2: Tuple[int, int, int]
    ) -> float:
        """Calculate Euclidean distance between colors."""
        return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2) ** 0.5
    
    def _calculate_brightness(self, image: 'np.ndarray') -> float:
        """Calculate average brightness (0-1)."""
        if not VISION_AVAILABLE:
            return 0.5
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return np.mean(gray) / 255.0
        except:
            return 0.5


class UIElementDetector:
    """
    Detects UI elements like tabs, buttons, and scroll areas.
    Uses edge detection, contour analysis, and heuristics.
    """
    
    def __init__(self, templates_dir: str = "templates"):
        self.logger = get_logger()
        self.templates_dir = templates_dir
        self.templates: Dict[str, 'np.ndarray'] = {}
        
        if VISION_AVAILABLE and os.path.exists(templates_dir):
            self._load_templates()
    
    def _load_templates(self) -> None:
        """Load template images."""
        for filename in os.listdir(self.templates_dir):
            if filename.lower().endswith(('.png', '.jpg')):
                name = os.path.splitext(filename)[0]
                path = os.path.join(self.templates_dir, filename)
                try:
                    template = cv2.imread(path)
                    if template is not None:
                        self.templates[name] = template
                except:
                    pass
    
    def detect_regions(
        self, 
        screenshot: 'np.ndarray',
        app_type: ApplicationType
    ) -> List[ScreenRegion]:
        """
        Detect UI regions based on application type.
        
        Args:
            screenshot: BGR image
            app_type: Detected application type
        
        Returns:
            List of detected ScreenRegions
        """
        if not VISION_AVAILABLE or screenshot is None:
            return []
        
        regions = []
        height, width = screenshot.shape[:2]
        
        # Generic regions based on app type
        if app_type == ApplicationType.CHROME:
            # Top tab bar
            regions.append(ScreenRegion(
                x=0, y=0, width=width, height=40,
                element_type=UIElement.TAB_BAR,
                confidence=0.9
            ))
            # Address bar
            regions.append(ScreenRegion(
                x=100, y=40, width=width-200, height=35,
                element_type=UIElement.ADDRESS_BAR,
                confidence=0.8
            ))
            # Main scroll area
            regions.append(ScreenRegion(
                x=0, y=80, width=width, height=height-100,
                element_type=UIElement.SCROLL_AREA,
                confidence=0.95
            ))
            
        elif app_type == ApplicationType.VSCODE:
            # Activity bar (left icons)
            regions.append(ScreenRegion(
                x=0, y=0, width=50, height=height,
                element_type=UIElement.SIDEBAR,
                confidence=0.9
            ))
            # File explorer sidebar
            regions.append(ScreenRegion(
                x=50, y=35, width=200, height=height-35,
                element_type=UIElement.SIDEBAR,
                confidence=0.7
            ))
            # Editor area
            regions.append(ScreenRegion(
                x=250, y=35, width=width-250, height=height-60,
                element_type=UIElement.TEXT_AREA,
                confidence=0.9
            ))
            # Tab bar
            regions.append(ScreenRegion(
                x=250, y=0, width=width-250, height=35,
                element_type=UIElement.TAB_BAR,
                confidence=0.8
            ))
        else:
            # Generic scroll area for unknown apps
            regions.append(ScreenRegion(
                x=50, y=50, width=width-100, height=height-100,
                element_type=UIElement.SCROLL_AREA,
                confidence=0.5
            ))
        
        # Try template matching for specific elements
        regions.extend(self._match_templates(screenshot))
        
        return regions
    
    def _match_templates(self, screenshot: 'np.ndarray') -> List[ScreenRegion]:
        """Match loaded templates against screenshot."""
        regions = []
        
        if not VISION_AVAILABLE:
            return regions
        
        for name, template in self.templates.items():
            try:
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > 0.7:
                    h, w = template.shape[:2]
                    regions.append(ScreenRegion(
                        x=max_loc[0],
                        y=max_loc[1],
                        width=w,
                        height=h,
                        element_type=UIElement.BUTTON,
                        confidence=max_val
                    ))
            except:
                pass
        
        return regions
    
    def find_clickable_areas(
        self, 
        screenshot: 'np.ndarray'
    ) -> List[Tuple[int, int]]:
        """
        Find potentially clickable areas using edge detection.
        
        Returns list of (x, y) center points of clickable regions.
        """
        if not VISION_AVAILABLE or screenshot is None:
            return []
        
        clickable = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by size (button-like)
                if 500 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Button-like aspect ratio
                    if 0.5 < aspect_ratio < 10:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        clickable.append((center_x, center_y))
            
            # Limit results
            if len(clickable) > 20:
                import random
                clickable = random.sample(clickable, 20)
                
        except Exception as e:
            self.logger.debug(f"Clickable detection failed: {e}")
        
        return clickable


class ScreenChangeDetector:
    """Detects significant changes in screen content."""
    
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold
        self._previous_frame: Optional['np.ndarray'] = None
        self._previous_hash: Optional[str] = None
    
    def detect_change(
        self, 
        current: 'np.ndarray'
    ) -> Tuple[bool, float]:
        """
        Detect if screen has changed significantly.
        
        Returns:
            Tuple of (has_changed, change_intensity)
        """
        if not VISION_AVAILABLE or current is None:
            return False, 0.0
        
        if self._previous_frame is None:
            self._previous_frame = current.copy()
            return False, 0.0
        
        try:
            # Resize for faster comparison
            scale = 0.25
            curr_small = cv2.resize(current, None, fx=scale, fy=scale)
            prev_small = cv2.resize(self._previous_frame, None, fx=scale, fy=scale)
            
            # Calculate difference
            diff = cv2.absdiff(curr_small, prev_small)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Calculate change intensity
            non_zero = np.count_nonzero(gray_diff > 30)
            total = gray_diff.size
            intensity = non_zero / total
            
            # Update previous frame
            self._previous_frame = current.copy()
            
            changed = intensity > self.threshold
            return changed, intensity
            
        except:
            return False, 0.0


class Vision:
    """
    Main vision system that combines all detection capabilities.
    Provides unified interface for screen awareness.
    """
    
    def __init__(self, templates_dir: str = "templates"):
        self.logger = get_logger()
        self.enabled = VISION_AVAILABLE
        
        if not self.enabled:
            self.logger.warning("Vision system disabled - OpenCV not available")
            return
        
        # Initialize detectors
        self.app_detector = ApplicationDetector()
        self.ui_detector = UIElementDetector(templates_dir)
        self.change_detector = ScreenChangeDetector()
        
        # State
        self._last_capture: Optional['np.ndarray'] = None
        self._last_context: Optional[ScreenContext] = None
        self._capture_interval = 1.0  # Minimum seconds between captures
        self._last_capture_time = 0.0
    
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional['np.ndarray']:
        """
        Capture screenshot.
        
        Args:
            region: Optional (x, y, width, height)
        
        Returns:
            BGR numpy array or None
        """
        if not self.enabled:
            return None
        
        try:
            screenshot = pyautogui.screenshot(region=region)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            self._last_capture = img
            self._last_capture_time = time.time()
            return img
        except Exception as e:
            self.logger.debug(f"Screenshot failed: {e}")
            return None
    
    def analyze(self, force_capture: bool = False) -> ScreenContext:
        """
        Perform full screen analysis.
        
        Args:
            force_capture: Force new screenshot even if recent one exists
        
        Returns:
            ScreenContext with all detection results
        """
        context = ScreenContext(timestamp=time.time())
        
        if not self.enabled:
            return context
        
        # Capture if needed
        time_since_capture = time.time() - self._last_capture_time
        if force_capture or time_since_capture > self._capture_interval or self._last_capture is None:
            screenshot = self.capture()
        else:
            screenshot = self._last_capture
        
        if screenshot is None:
            return context
        
        # Detect application
        app_type, app_conf = self.app_detector.detect(screenshot)
        context.detected_app = app_type
        context.app_confidence = app_conf
        
        # Detect UI regions
        context.regions = self.ui_detector.detect_regions(screenshot, app_type)
        
        # Find clickable areas
        context.clickable_areas = self.ui_detector.find_clickable_areas(screenshot)
        
        # Detect screen changes
        changed, intensity = self.change_detector.detect_change(screenshot)
        context.screen_changed = changed
        context.change_intensity = intensity
        
        # Analyze colors and brightness
        try:
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            context.brightness = np.mean(gray) / 255.0
            context.has_dark_theme = context.brightness < 0.3
        except:
            pass
        
        # Get window title
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            context.window_title = buffer.value
        except:
            pass
        
        self._last_context = context
        return context
    
    def get_last_context(self) -> Optional[ScreenContext]:
        """Get most recent screen context without new analysis."""
        return self._last_context
    
    def get_screen_context(self) -> ScreenContext:
        """
        Get screen context, performing analysis if needed.
        This is the main interface used by agent.py.
        """
        return self.analyze()
    
    def get_scroll_region(self) -> Optional[ScreenRegion]:
        """Get the main scrollable region if detected."""
        if self._last_context:
            for region in self._last_context.regions:
                if region.element_type in [UIElement.SCROLL_AREA, UIElement.TEXT_AREA]:
                    return region
        return None
    
    def get_click_target(self) -> Optional[Tuple[int, int]]:
        """Get a random clickable target."""
        if self._last_context and self._last_context.clickable_areas:
            import random
            return random.choice(self._last_context.clickable_areas)
        return None
    
    def save_template(
        self, 
        name: str, 
        region: Tuple[int, int, int, int]
    ) -> bool:
        """Save a screen region as template."""
        if not self.enabled:
            return False
        
        try:
            screenshot = self.capture(region=region)
            if screenshot is not None:
                path = os.path.join(self.ui_detector.templates_dir, f"{name}.png")
                cv2.imwrite(path, screenshot)
                self.ui_detector.templates[name] = screenshot
                self.logger.info(f"Saved template: {name}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to save template: {e}")
        return False


# Global vision instance
_vision: Optional[Vision] = None


def get_vision() -> Vision:
    """Get or create global vision instance."""
    global _vision
    if _vision is None:
        _vision = Vision()
    return _vision


def is_vision_available() -> bool:
    """Check if vision system is available."""
    return VISION_AVAILABLE
