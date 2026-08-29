"""
Configuration settings for the AI Desktop Automation Agent.
Modify these values to tune the agent's behavior.
"""

import os
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class MouseConfig:
    """Mouse movement and click configuration."""
    # Movement speed range (seconds) - Human-like speed
    move_duration_min: float = 0.25
    move_duration_max: float = 0.8
    
    # Bezier curve control points randomness
    curve_variation: float = 80.0
    
    # Click probability (0.0 to 1.0)
    click_probability: float = 0.20
    
    # Double-click probability when clicking
    double_click_probability: float = 0.1
    
    # Safe zones to avoid (corners for failsafe)
    margin: int = 50


@dataclass
class KeyboardConfig:
    """Keyboard typing and shortcuts configuration."""
    # Typing speed range (seconds between keystrokes)
    typing_delay_min: float = 0.04
    typing_delay_max: float = 0.12
    
    # Probability of typo and correction
    typo_probability: float = 0.02
    
    # Common words/phrases for realistic typing - contextual content
    typing_samples: List[str] = field(default_factory=lambda: [
        "edit wordpress header section",
        "adjust elementor container spacing",
        "update hero typography",
        "refactor css for mobile breakpoint",
        "check console warning",
        "inspect section padding",
        "optimize image alt text",
        "fix responsive layout",
        "update button hover style",
        "review plugin compatibility",
        "customize elementor widget",
        "improve page performance",
        "update page template",
        "test contact form validation",
        "review seo meta settings",
        "publish updated landing page",
        "check wordpress comments",
        "adjust global colors",
        "refine section alignment",
        "verify mobile navigation",
    ])


@dataclass
class ScrollConfig:
    """Scrolling behavior configuration."""
    # Scroll amount range (pixels or clicks)
    scroll_min: int = 1
    scroll_max: int = 5
    
    # Scroll direction weights (0.5 = equal up/down)
    scroll_down_weight: float = 0.5
    
    # Smooth scroll steps
    smooth_scroll_steps: int = 3


@dataclass
class TimingConfig:
    """Timing and delay configuration."""
    # Delay between actions (seconds) - FAST
    action_delay_min: float = 0.1
    action_delay_max: float = 0.8
    
    # Idle behavior settings
    idle_probability: float = 0.05
    idle_duration_min: float = 0.5
    idle_duration_max: float = 2.0
    
    # Long pause probability (simulates thinking/reading)
    long_pause_probability: float = 0.02
    long_pause_min: float = 1.0
    long_pause_max: float = 3.0


@dataclass
class ApplicationConfig:
    """Application-specific configuration."""
    # Chrome settings
    chrome_process_name: str = "chrome.exe"
    chrome_window_title: str = "Chrome"
    
    # VS Code settings
    vscode_process_name: str = "Code.exe"
    vscode_window_title: str = "Visual Studio Code"
    
    # Target applications for interaction
    target_apps: List[str] = field(default_factory=lambda: [
        "Chrome",
        "Visual Studio Code",
        "Notepad",
        "Explorer"
    ])


@dataclass
class VirtualBoxConfig:
    """VirtualBox compatibility settings."""
    # Enable VirtualBox mode (uses different mouse input method)
    virtualbox_mode: bool = True
    
    # Use relative mouse movements (better for VMs)
    use_relative_movement: bool = True
    
    # Mouse movement steps (smaller = smoother but slower)
    movement_steps: int = 20
    
    # Additional delay between mouse steps in VM
    vm_mouse_delay: float = 0.01


@dataclass
class SafetyConfig:
    """Safety and failsafe configuration."""
    # Failsafe corners (move mouse here to stop)
    failsafe_enabled: bool = True
    failsafe_corners: List[Tuple[int, int]] = field(default_factory=lambda: [
        (0, 0),  # Top-left
    ])
    failsafe_threshold: int = 5  # Pixels from corner
    
    # Maximum runtime (seconds, 0 = unlimited)
    max_runtime: int = 0
    
    # Emergency stop key
    stop_key: str = "f9"
    start_key: str = "f8"


@dataclass
class AIConfig:
    """AI decision engine configuration."""
    # Decision mode: "rule_based", "weighted_random", "llm"
    decision_mode: str = "weighted_random"
    
    # Action weights for weighted random mode - mouse-heavy workflow
    action_weights: dict = field(default_factory=lambda: {
        "mouse_move": 40,
        "mouse_click": 25,
        "scroll": 20,
        "type_text": 3,
        "keyboard_shortcut": 4,
        "switch_window": 6,
        "idle": 2,
    })
    
    # LLM settings (for future integration)
    llm_enabled: bool = False
    llm_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_endpoint: str = "https://api.openai.com/v1/chat/completions"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    # Log level: DEBUG, INFO, WARNING, ERROR
    log_level: str = "INFO"
    
    # Log to file
    log_to_file: bool = True
    log_file_path: str = "agent_log.txt"
    
    # Log to console
    log_to_console: bool = True
    
    # Maximum log file size (bytes)
    max_log_size: int = 10 * 1024 * 1024  # 10 MB


@dataclass
class ScreenConfig:
    """Screen awareness configuration."""
    # Enable screenshot-based awareness
    screen_awareness_enabled: bool = False
    
    # Screenshot interval (seconds)
    screenshot_interval: float = 5.0
    
    # Template matching threshold (0.0 to 1.0)
    template_threshold: float = 0.8
    
    # Templates directory
    templates_dir: str = "templates"


@dataclass
class VisionConfig:
    """Enhanced vision system configuration."""
    # Enable vision system
    enabled: bool = True
    
    # Application detection
    detect_applications: bool = True
    supported_apps: List[str] = field(default_factory=lambda: [
        "chrome", "vscode", "explorer", "notepad", "firefox", "edge"
    ])
    
    # UI element detection
    detect_ui_elements: bool = True
    element_confidence_threshold: float = 0.7
    
    # Screen change detection
    detect_changes: bool = True
    change_threshold: float = 0.05  # 5% change triggers detection
    
    # Performance settings
    cache_screenshots: bool = True
    cache_duration: float = 0.5  # seconds


@dataclass
class TaskConfig:
    """Task system configuration."""
    # Enable task-based behavior
    enabled: bool = True
    
    # Task selection weights
    task_weights: dict = field(default_factory=lambda: {
        "browsing": 25,
        "wordpress_developer": 20,
        "coding": 20,
        "reading": 15,
        "file_exploration": 10,
        "window_management": 10,
        "search": 10,
        "idle": 10,
    })

    # WordPress developer mode
    wordpress_developer_enabled: bool = True
    wordpress_developer_intensity: str = "high"  # low, medium, high
    
    # Task completion settings
    min_task_steps: int = 3
    max_task_steps: int = 15
    task_timeout: float = 120.0  # seconds
    
    # Allow task interruption
    allow_interruption: bool = True
    interruption_probability: float = 0.1


@dataclass
class HumanBehaviorConfig:
    """Human-like behavior simulation settings."""
    # Micro-movements and jitter
    enable_micro_jitter: bool = True
    jitter_amount_min: int = 1
    jitter_amount_max: int = 2
    jitter_probability: float = 0.2
    
    # Hesitation and thinking pauses - REDUCED
    enable_hesitation: bool = True
    hesitation_probability: float = 0.08
    hesitation_min: float = 0.1
    hesitation_max: float = 0.4
    
    # Typing mistakes
    enable_typos: bool = True
    typo_probability: float = 0.02
    correction_delay_min: float = 0.1
    correction_delay_max: float = 0.3
    
    # Variable action speeds
    enable_variable_speed: bool = True
    speed_variation: float = 0.2  # +/- 20%
    
    # Mouse overshoot and correction
    enable_overshoot: bool = True
    overshoot_probability: float = 0.05
    overshoot_distance_min: int = 3
    overshoot_distance_max: int = 10


@dataclass
class MarkovConfig:
    """Markov transition matrix configuration."""
    # Enable Markov-based decisions
    enabled: bool = True
    
    # Anti-repetition settings
    enable_anti_repetition: bool = True
    repetition_penalty: float = 0.5
    recent_history_size: int = 10
    
    # Diversity enforcement
    enforce_diversity: bool = True
    diversity_threshold: float = 0.6
    
    # Learning from behavior
    enable_learning: bool = False  # Future: LLM-based
    learning_rate: float = 0.1


@dataclass
class ActivityConfig:
    """Activity level configuration."""
    # Default activity level: idle, low, normal, busy, intense
    default_level: str = "busy"
    
    # Activity level transition probabilities
    enable_transitions: bool = True
    transition_interval_min: float = 30.0   # seconds
    transition_interval_max: float = 120.0  # seconds
    
    # Level-specific settings (min_delay, max_delay, action_probability) - FASTER
    level_idle: Tuple[float, float, float] = (1.0, 3.0, 0.5)
    level_low: Tuple[float, float, float] = (0.5, 1.5, 0.7)
    level_normal: Tuple[float, float, float] = (0.2, 0.8, 0.85)
    level_busy: Tuple[float, float, float] = (0.1, 0.4, 0.95)
    level_intense: Tuple[float, float, float] = (0.05, 0.2, 0.98)


@dataclass
class LLMConfig:
    """Extended LLM integration settings."""
    # Enable LLM decision making
    enabled: bool = False
    
    # API settings
    provider: str = "openai"  # openai, anthropic, local
    api_key: str = ""
    model: str = "gpt-4"
    endpoint: str = "https://api.openai.com/v1/chat/completions"
    
    # Request settings
    timeout: float = 30.0
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 150
    
    # Context settings
    include_screen_context: bool = True
    include_action_history: bool = True
    history_length: int = 20


class Config:
    """Main configuration class combining all settings."""
    
    def __init__(self):
        self.mouse = MouseConfig()
        self.keyboard = KeyboardConfig()
        self.scroll = ScrollConfig()
        self.timing = TimingConfig()
        self.application = ApplicationConfig()
        self.safety = SafetyConfig()
        self.ai = AIConfig()
        self.logging = LoggingConfig()
        self.screen = ScreenConfig()
        self.vision = VisionConfig()
        self.tasks = TaskConfig()
        self.human_behavior = HumanBehaviorConfig()
        self.markov = MarkovConfig()
        self.activity = ActivityConfig()
        self.llm = LLMConfig()
        self.virtualbox = VirtualBoxConfig()
    
    def load_from_file(self, filepath: str) -> None:
        """Load configuration from a JSON file."""
        import json
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                self._update_from_dict(data)
    
    def save_to_file(self, filepath: str) -> None:
        """Save current configuration to a JSON file."""
        import json
        data = {
            'mouse': self.mouse.__dict__,
            'keyboard': {k: v for k, v in self.keyboard.__dict__.items() 
                        if k != 'typing_samples'},
            'scroll': self.scroll.__dict__,
            'timing': self.timing.__dict__,
            'application': {k: v for k, v in self.application.__dict__.items()
                           if k != 'target_apps'},
            'safety': {k: v for k, v in self.safety.__dict__.items()
                      if k != 'failsafe_corners'},
            'ai': self.ai.__dict__,
            'logging': self.logging.__dict__,
            'screen': self.screen.__dict__,
            'vision': {k: v for k, v in self.vision.__dict__.items()
                      if k != 'supported_apps'},
            'tasks': {k: v for k, v in self.tasks.__dict__.items()
                     if k != 'task_weights'},
            'human_behavior': self.human_behavior.__dict__,
            'markov': self.markov.__dict__,
            'activity': {k: v for k, v in self.activity.__dict__.items()
                        if not k.startswith('level_')},
            'llm': {k: v for k, v in self.llm.__dict__.items()
                   if k != 'api_key'},  # Don't save API key
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    
    def _update_from_dict(self, data: dict) -> None:
        """Update configuration from dictionary."""
        for section, values in data.items():
            if hasattr(self, section):
                config_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def __repr__(self) -> str:
        """String representation of config."""
        return f"Config(vision={self.vision.enabled}, tasks={self.tasks.enabled}, markov={self.markov.enabled})"


# Global configuration instance
_config: Config = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        # Try to load from config.json if it exists
        config_file = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_file):
            _config.load_from_file(config_file)
    return _config


def save_config(filepath: str = None) -> None:
    """Save current configuration to file."""
    config = get_config()
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), "config.json")
    config.save_to_file(filepath)


# Backward compatibility
config = get_config()
