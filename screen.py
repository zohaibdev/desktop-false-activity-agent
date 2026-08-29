"""
Screen awareness module for the AI Desktop Automation Agent.
Provides screenshot-based awareness and basic image detection.
"""

import os
from typing import List, Tuple, Optional
from dataclasses import dataclass

try:
    import cv2
    import numpy as np
    from PIL import Image
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

import pyautogui

from config import config
from logger import get_logger


@dataclass
class DetectionResult:
    """Result of template matching."""
    found: bool
    location: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    width: int = 0
    height: int = 0


class ScreenAwareness:
    """
    Provides screen analysis and template matching capabilities.
    Optional feature - requires opencv-python and numpy.
    """
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialize screen awareness.
        
        Args:
            templates_dir: Directory containing template images
        """
        self.logger = get_logger()
        self.templates_dir = templates_dir
        self.templates: dict = {}
        
        if not OPENCV_AVAILABLE:
            self.logger.warning("OpenCV not available - screen awareness disabled")
            return
        
        # Create templates directory if needed
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        
        # Load existing templates
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load template images from templates directory."""
        if not OPENCV_AVAILABLE or not os.path.exists(self.templates_dir):
            return
        
        for filename in os.listdir(self.templates_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                path = os.path.join(self.templates_dir, filename)
                
                try:
                    template = cv2.imread(path)
                    if template is not None:
                        self.templates[name] = template
                        self.logger.debug(f"Loaded template: {name}")
                except Exception as e:
                    self.logger.error(f"Failed to load template {filename}: {e}")
        
        self.logger.info(f"Loaded {len(self.templates)} templates")
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Capture screenshot of screen or region.
        
        Args:
            region: Optional (x, y, width, height) region to capture
        
        Returns:
            Screenshot as numpy array or None
        """
        if not OPENCV_AVAILABLE:
            return None
        
        try:
            screenshot = pyautogui.screenshot(region=region)
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None
    
    def find_template(
        self,
        template_name: str,
        threshold: Optional[float] = None
    ) -> DetectionResult:
        """
        Find a template on screen.
        
        Args:
            template_name: Name of template to find
            threshold: Matching threshold (default from config)
        
        Returns:
            DetectionResult with location and confidence
        """
        if not OPENCV_AVAILABLE:
            return DetectionResult(found=False)
        
        if template_name not in self.templates:
            self.logger.warning(f"Template not found: {template_name}")
            return DetectionResult(found=False)
        
        template = self.templates[template_name]
        threshold = threshold or config.screen.template_threshold
        
        # Capture screen
        screen = self.capture_screen()
        if screen is None:
            return DetectionResult(found=False)
        
        # Template matching
        try:
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            h, w = template.shape[:2]
            
            if max_val >= threshold:
                # Return center of matched region
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                self.logger.debug(f"Found {template_name} at ({center_x}, {center_y}) with {max_val:.2f} confidence")
                
                return DetectionResult(
                    found=True,
                    location=(center_x, center_y),
                    confidence=max_val,
                    width=w,
                    height=h
                )
            else:
                return DetectionResult(found=False, confidence=max_val)
                
        except Exception as e:
            self.logger.error(f"Template matching failed: {e}")
            return DetectionResult(found=False)
    
    def find_all_templates(
        self,
        template_name: str,
        threshold: Optional[float] = None,
        max_results: int = 10
    ) -> List[DetectionResult]:
        """
        Find all occurrences of a template on screen.
        
        Args:
            template_name: Name of template to find
            threshold: Matching threshold
            max_results: Maximum number of results
        
        Returns:
            List of DetectionResults
        """
        if not OPENCV_AVAILABLE:
            return []
        
        if template_name not in self.templates:
            return []
        
        template = self.templates[template_name]
        threshold = threshold or config.screen.template_threshold
        
        screen = self.capture_screen()
        if screen is None:
            return []
        
        results = []
        
        try:
            match_result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            h, w = template.shape[:2]
            
            # Find all locations above threshold
            locations = np.where(match_result >= threshold)
            
            # Group nearby locations (non-maximum suppression)
            found_locations = []
            for pt in zip(*locations[::-1]):
                # Check if too close to existing location
                too_close = False
                for existing in found_locations:
                    if abs(pt[0] - existing[0]) < w and abs(pt[1] - existing[1]) < h:
                        too_close = True
                        break
                
                if not too_close:
                    found_locations.append(pt)
                    
                    if len(found_locations) >= max_results:
                        break
            
            for loc in found_locations:
                center_x = loc[0] + w // 2
                center_y = loc[1] + h // 2
                confidence = match_result[loc[1], loc[0]]
                
                results.append(DetectionResult(
                    found=True,
                    location=(center_x, center_y),
                    confidence=confidence,
                    width=w,
                    height=h
                ))
                
        except Exception as e:
            self.logger.error(f"Multiple template matching failed: {e}")
        
        return results
    
    def save_template(
        self,
        name: str,
        region: Tuple[int, int, int, int]
    ) -> bool:
        """
        Save a region of the screen as a template.
        
        Args:
            name: Name for the template
            region: (x, y, width, height) region to save
        
        Returns:
            True if saved successfully
        """
        if not OPENCV_AVAILABLE:
            return False
        
        try:
            screenshot = self.capture_screen(region=region)
            if screenshot is None:
                return False
            
            filepath = os.path.join(self.templates_dir, f"{name}.png")
            cv2.imwrite(filepath, screenshot)
            
            self.templates[name] = screenshot
            self.logger.info(f"Saved template: {name}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save template: {e}")
            return False
    
    def get_dominant_colors(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
        num_colors: int = 5
    ) -> List[Tuple[int, int, int]]:
        """
        Get dominant colors in screen region.
        
        Args:
            region: Optional region to analyze
            num_colors: Number of dominant colors to return
        
        Returns:
            List of (R, G, B) tuples
        """
        if not OPENCV_AVAILABLE:
            return []
        
        screen = self.capture_screen(region=region)
        if screen is None:
            return []
        
        try:
            # Reshape to list of pixels
            pixels = screen.reshape(-1, 3).astype(np.float32)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert to RGB
            colors = []
            for center in centers:
                colors.append((int(center[2]), int(center[1]), int(center[0])))
            
            return colors
        except Exception as e:
            self.logger.error(f"Color analysis failed: {e}")
            return []
    
    def is_screen_changed(
        self,
        previous: np.ndarray,
        threshold: float = 0.95
    ) -> bool:
        """
        Check if screen has changed significantly.
        
        Args:
            previous: Previous screenshot
            threshold: Similarity threshold (lower = more sensitive)
        
        Returns:
            True if screen has changed
        """
        if not OPENCV_AVAILABLE:
            return False
        
        current = self.capture_screen()
        if current is None or previous is None:
            return True
        
        # Ensure same size
        if current.shape != previous.shape:
            return True
        
        try:
            # Calculate structural similarity
            gray_current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
            gray_previous = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)
            
            # Simple difference-based comparison
            diff = cv2.absdiff(gray_current, gray_previous)
            non_zero = np.count_nonzero(diff > 30)
            total = diff.size
            
            similarity = 1 - (non_zero / total)
            
            return similarity < threshold
        except Exception as e:
            self.logger.error(f"Screen comparison failed: {e}")
            return True


# Global screen awareness instance
_screen: Optional[ScreenAwareness] = None


def get_screen_awareness() -> ScreenAwareness:
    """Get or create global screen awareness instance."""
    global _screen
    if _screen is None:
        _screen = ScreenAwareness(config.screen.templates_dir)
    return _screen
