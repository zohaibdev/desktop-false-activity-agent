"""
Brain Module for AI Desktop Automation Agent (Enhanced Version)
================================================================

Advanced decision-making engine with:
- Markov-style state transitions
- Behavior memory with anti-repetition
- Context-aware decision making
- LLM-ready architecture
- Dynamic probability adjustment

This is the "intelligence" of the agent.
"""

import random
import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Tuple
from enum import Enum
from collections import deque, Counter

from config import config
from logger import get_logger
from utils import weighted_random_choice, get_active_window_title


class ActionType(Enum):
    """Available action types."""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    SCROLL = "scroll"
    TYPE = "type"
    TYPE_TEXT = "type_text"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    SWITCH_WINDOW = "switch_window"
    SWITCH_TAB = "switch_tab"
    IDLE = "idle"
    MICRO_PAUSE = "micro_pause"
    MICRO_MOVEMENT = "micro_movement"
    HESITATE = "hesitate"
    MISTAKE_CORRECTION = "mistake_correction"
    TASK = "task"  # Execute high-level task


class ActivityLevel(Enum):
    """Activity intensity levels."""
    VERY_LOW = 0.3
    LOW = 0.6
    MEDIUM = 1.0
    HIGH = 1.5
    VERY_HIGH = 2.0


class AppContext(Enum):
    """Application context types."""
    CHROME = "chrome"
    VSCODE = "vscode"
    EXPLORER = "explorer"
    TERMINAL = "terminal"
    UNKNOWN = "unknown"
    IDLE = "idle"


@dataclass
class AgentState:
    """
    Comprehensive state representation for the agent.
    Tracks everything needed for intelligent decision-making.
    """
    # Session info
    session_start_time: float = 0.0
    total_actions: int = 0
    total_tasks: int = 0
    
    # Current context
    current_app: AppContext = AppContext.UNKNOWN
    active_window: str = ""
    last_action: str = ""
    last_action_time: float = 0.0
    
    # Activity tracking
    activity_level: ActivityLevel = ActivityLevel.MEDIUM
    consecutive_same_actions: int = 0
    
    # Behavioral flags
    is_idle: bool = False
    is_typing: bool = False
    is_in_task: bool = False
    current_task: str = ""
    current_focus: str = "general"  # For backward compatibility
    
    # History (using deque for efficient memory)
    action_history: deque = field(default_factory=lambda: deque(maxlen=50))
    task_history: deque = field(default_factory=lambda: deque(maxlen=20))
    
    # Screen context (from vision system)
    screen_brightness: float = 0.5
    has_dark_theme: bool = False
    screen_changed: bool = False
    
    # Timing
    time_in_current_app: float = 0.0
    app_switch_time: float = 0.0
    
    def add_action(self, action: str) -> None:
        """Record an executed action."""
        # Track consecutive same actions
        if action == self.last_action:
            self.consecutive_same_actions += 1
        else:
            self.consecutive_same_actions = 0
        
        self.action_history.append({
            "action": action,
            "time": time.time(),
            "app": self.current_app.value
        })
        
        self.last_action = action
        self.last_action_time = time.time()
        self.total_actions += 1
    
    def add_task(self, task: str) -> None:
        """Record an executed task."""
        self.task_history.append({
            "task": task,
            "time": time.time(),
            "app": self.current_app.value
        })
        self.total_tasks += 1
    
    def get_recent_actions(self, count: int = 10) -> List[str]:
        """Get recent action names."""
        recent = list(self.action_history)[-count:]
        return [a["action"] for a in recent]
    
    def get_action_frequency(self, action: str, window: int = 20) -> float:
        """Get frequency of action in recent history."""
        recent = list(self.action_history)[-window:]
        if not recent:
            return 0.0
        count = sum(1 for a in recent if a["action"] == action)
        return count / len(recent)
    
    def get_last_n_unique_actions(self, n: int = 5) -> List[str]:
        """Get last N unique actions."""
        seen = []
        for item in reversed(list(self.action_history)):
            if item["action"] not in seen:
                seen.append(item["action"])
                if len(seen) >= n:
                    break
        return seen
    
    def time_since_last_action(self) -> float:
        """Seconds since last action."""
        if self.last_action_time == 0:
            return 0.0
        return time.time() - self.last_action_time
    
    def time_since_session_start(self) -> float:
        """Seconds since session started."""
        return time.time() - self.session_start_time
    
    def update_context(self, window_title: str = None) -> None:
        """Update context from active window."""
        if window_title is None:
            window_title = get_active_window_title()
        
        self.active_window = window_title
        window_lower = window_title.lower()
        
        old_app = self.current_app
        
        # Detect application
        if 'chrome' in window_lower or 'edge' in window_lower or 'firefox' in window_lower:
            self.current_app = AppContext.CHROME
            self.current_focus = "browser"
        elif 'visual studio code' in window_lower or ' code' in window_lower:
            self.current_app = AppContext.VSCODE
            self.current_focus = "editor"
        elif 'explorer' in window_lower or 'file' in window_lower:
            self.current_app = AppContext.EXPLORER
            self.current_focus = "explorer"
        elif 'terminal' in window_lower or 'cmd' in window_lower or 'powershell' in window_lower:
            self.current_app = AppContext.TERMINAL
            self.current_focus = "terminal"
        elif window_title.strip() == '':
            self.current_app = AppContext.IDLE
            self.current_focus = "general"
        else:
            self.current_app = AppContext.UNKNOWN
            self.current_focus = "general"
        
        # Track time in app
        if old_app != self.current_app:
            self.app_switch_time = time.time()
            self.time_in_current_app = 0.0
        else:
            self.time_in_current_app = time.time() - self.app_switch_time
    
    def to_context_dict(self) -> Dict[str, Any]:
        """Export state for LLM context."""
        return {
            "current_app": self.current_app.value,
            "window_title": self.active_window,
            "last_action": self.last_action,
            "activity_level": self.activity_level.name,
            "recent_actions": self.get_recent_actions(5),
            "time_in_app": self.time_in_current_app,
            "consecutive_same": self.consecutive_same_actions,
            "is_idle": self.is_idle,
            "is_typing": self.is_typing,
            "total_actions": self.total_actions,
            "session_duration": self.time_since_session_start(),
            "current_focus": self.current_focus,
        }


class MarkovTransitionMatrix:
    """
    Markov-style transition probabilities between actions.
    Provides natural action sequencing.
    """
    
    def __init__(self):
        # Base transition probabilities: current_action -> {next_action: probability}
        self.transitions: Dict[str, Dict[str, float]] = {
            "mouse_move": {
                "mouse_click": 0.25,
                "scroll": 0.15,
                "mouse_move": 0.10,
                "idle": 0.15,
                "type_text": 0.10,
                "keyboard_shortcut": 0.10,
                "micro_movement": 0.10,
                "hesitate": 0.05,
            },
            "mouse_click": {
                "idle": 0.25,
                "scroll": 0.15,
                "type_text": 0.20,
                "mouse_move": 0.15,
                "keyboard_shortcut": 0.10,
                "mouse_click": 0.05,
                "hesitate": 0.10,
            },
            "scroll": {
                "scroll": 0.25,
                "idle": 0.20,
                "mouse_move": 0.15,
                "mouse_click": 0.10,
                "keyboard_shortcut": 0.10,
                "switch_tab": 0.10,
                "hesitate": 0.10,
            },
            "type_text": {
                "type_text": 0.20,
                "idle": 0.20,
                "keyboard_shortcut": 0.20,
                "scroll": 0.10,
                "mouse_move": 0.10,
                "hesitate": 0.15,
                "mistake_correction": 0.05,
            },
            "keyboard_shortcut": {
                "idle": 0.25,
                "type_text": 0.20,
                "mouse_move": 0.15,
                "scroll": 0.15,
                "keyboard_shortcut": 0.10,
                "mouse_click": 0.15,
            },
            "switch_window": {
                "idle": 0.30,
                "mouse_move": 0.20,
                "scroll": 0.15,
                "mouse_click": 0.15,
                "type_text": 0.10,
                "switch_tab": 0.10,
            },
            "switch_tab": {
                "scroll": 0.25,
                "idle": 0.20,
                "mouse_move": 0.15,
                "mouse_click": 0.15,
                "switch_tab": 0.15,
                "type_text": 0.10,
            },
            "idle": {
                "mouse_move": 0.25,
                "scroll": 0.20,
                "type_text": 0.15,
                "keyboard_shortcut": 0.10,
                "micro_movement": 0.15,
                "switch_window": 0.10,
                "idle": 0.05,
            },
            "micro_movement": {
                "idle": 0.30,
                "mouse_move": 0.25,
                "micro_movement": 0.20,
                "scroll": 0.10,
                "mouse_click": 0.15,
            },
            "hesitate": {
                "type_text": 0.25,
                "mouse_click": 0.25,
                "mouse_move": 0.20,
                "idle": 0.20,
                "scroll": 0.10,
            },
            "mistake_correction": {
                "type_text": 0.60,
                "idle": 0.20,
                "hesitate": 0.20,
            },
            "task": {
                "idle": 0.30,
                "task": 0.25,
                "mouse_move": 0.20,
                "scroll": 0.15,
                "switch_window": 0.10,
            },
        }
        
        # Default transition for unknown actions
        self.default_transition = {
            "mouse_move": 0.20,
            "scroll": 0.15,
            "idle": 0.20,
            "type_text": 0.15,
            "keyboard_shortcut": 0.15,
            "mouse_click": 0.15,
        }
    
    def get_next_action_probabilities(
        self, 
        current_action: str,
        context_modifier: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Get probability distribution for next action.
        
        Args:
            current_action: Current/last action
            context_modifier: Optional multipliers per action
        
        Returns:
            Dictionary of action -> probability
        """
        probs = self.transitions.get(current_action, self.default_transition).copy()
        
        # Apply context modifiers
        if context_modifier:
            for action, modifier in context_modifier.items():
                if action in probs:
                    probs[action] *= modifier
        
        # Normalize
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}
        
        return probs
    
    def sample_next_action(
        self, 
        current_action: str,
        context_modifier: Dict[str, float] = None,
        forbidden: List[str] = None
    ) -> str:
        """Sample next action based on probabilities."""
        probs = self.get_next_action_probabilities(current_action, context_modifier)
        
        # Remove forbidden actions
        if forbidden:
            probs = {k: v for k, v in probs.items() if k not in forbidden}
            total = sum(probs.values())
            if total > 0:
                probs = {k: v / total for k, v in probs.items()}
        
        if not probs:
            return "idle"
        
        return weighted_random_choice(probs)


class BehaviorMemory:
    """
    Memory system to prevent repetitive patterns.
    Tracks action patterns and adjusts probabilities.
    """
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.pattern_cache: Dict[str, int] = {}
        self._last_pattern_check = 0
    
    def record(self, action: str) -> None:
        """Record an action."""
        self.history.append(action)
    
    def detect_repetition(self, action: str, threshold: int = 3) -> bool:
        """Check if action would be too repetitive."""
        if len(self.history) < threshold:
            return False
        
        recent = list(self.history)[-threshold:]
        return all(a == action for a in recent)
    
    def get_penalty_multiplier(self, action: str) -> float:
        """
        Get penalty multiplier for an action based on recent frequency.
        Returns value < 1.0 if action should be discouraged.
        """
        if len(self.history) < 5:
            return 1.0
        
        recent = list(self.history)[-10:]
        frequency = recent.count(action) / len(recent)
        
        # Penalize high frequency
        if frequency > 0.4:
            return 0.3
        elif frequency > 0.3:
            return 0.5
        elif frequency > 0.2:
            return 0.7
        return 1.0
    
    def detect_pattern(self, pattern_length: int = 3) -> Optional[List[str]]:
        """Detect if a repeating pattern exists."""
        if len(self.history) < pattern_length * 2:
            return None
        
        recent = list(self.history)[-pattern_length * 2:]
        candidate = recent[-pattern_length:]
        previous = recent[:pattern_length]
        
        if candidate == previous:
            return candidate
        return None
    
    def get_diversity_score(self, window: int = 15) -> float:
        """
        Calculate action diversity score (0-1).
        Higher = more diverse, lower = repetitive.
        """
        if len(self.history) < window:
            return 1.0
        
        recent = list(self.history)[-window:]
        unique = len(set(recent))
        return unique / len(recent)
    
    def get_adjustment_weights(self) -> Dict[str, float]:
        """Get weight adjustments based on memory."""
        weights = {}
        
        for action in set(self.history):
            weights[action] = self.get_penalty_multiplier(action)
        
        return weights


class ContextAnalyzer:
    """
    Analyzes context to provide action weight modifiers.
    Makes decisions context-aware.
    """
    
    # App-specific action preferences
    APP_PREFERENCES: Dict[AppContext, Dict[str, float]] = {
        AppContext.CHROME: {
            "scroll": 1.4,
            "switch_tab": 1.2,
            "mouse_move": 1.4,
            "mouse_click": 1.5,
            "type_text": 0.15,
            "keyboard_shortcut": 1.1,
        },
        AppContext.VSCODE: {
            "type_text": 1.5,
            "keyboard_shortcut": 1.4,
            "scroll": 1.0,
            "mouse_click": 0.8,
            "switch_tab": 0.7,
        },
        AppContext.EXPLORER: {
            "mouse_click": 1.4,
            "scroll": 1.3,
            "mouse_move": 1.2,
            "type_text": 0.5,
        },
        AppContext.TERMINAL: {
            "type_text": 1.6,
            "keyboard_shortcut": 1.4,
            "scroll": 0.8,
            "mouse_click": 0.5,
        },
        AppContext.IDLE: {
            "idle": 2.0,
            "micro_movement": 1.5,
            "mouse_move": 0.5,
        },
    }
    
    def __init__(self):
        self.logger = get_logger()
    
    def get_context_weights(
        self, 
        state: AgentState,
        screen_context: Dict = None
    ) -> Dict[str, float]:
        """
        Get action weight modifiers based on current context.
        
        Args:
            state: Current agent state
            screen_context: Optional screen analysis data
        
        Returns:
            Dictionary of action -> weight_multiplier
        """
        weights = {}
        
        # Base app preferences
        app_prefs = self.APP_PREFERENCES.get(state.current_app, {})
        weights.update(app_prefs)
        
        # Time-based adjustments
        time_in_app = state.time_in_current_app
        
        # If in app for long time, increase switch probability
        if time_in_app > 120:  # 2 minutes
            weights["switch_window"] = weights.get("switch_window", 1.0) * 1.5
            weights["switch_tab"] = weights.get("switch_tab", 1.0) * 1.3
        
        # If just switched, decrease switch probability
        if time_in_app < 5:
            weights["switch_window"] = weights.get("switch_window", 1.0) * 0.3
            weights["switch_tab"] = weights.get("switch_tab", 1.0) * 0.5
        
        # Activity level adjustments
        if state.activity_level == ActivityLevel.LOW:
            weights["idle"] = weights.get("idle", 1.0) * 1.5
            weights["micro_movement"] = weights.get("micro_movement", 1.0) * 1.3
        elif state.activity_level == ActivityLevel.HIGH:
            weights["idle"] = weights.get("idle", 1.0) * 0.5
            weights["type_text"] = weights.get("type_text", 1.0) * 1.3
        
        # Consecutive action penalty
        if state.consecutive_same_actions >= 2:
            weights[state.last_action] = weights.get(state.last_action, 1.0) * 0.3
        
        # Typing mode
        if state.is_typing:
            weights["type_text"] = weights.get("type_text", 1.0) * 1.5
            weights["keyboard_shortcut"] = weights.get("keyboard_shortcut", 1.0) * 1.2
        
        # Screen-based adjustments
        if screen_context:
            if screen_context.get("screen_changed", False):
                weights["scroll"] = weights.get("scroll", 1.0) * 1.2
                weights["idle"] = weights.get("idle", 1.0) * 1.3
        
        return weights


class LLMInterface:
    """
    Interface for LLM-based decision making.
    Provides prompt building and response parsing.
    Ready for integration with OpenAI or local models.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.enabled = config.ai.llm_enabled
        self.api_key = config.ai.llm_api_key
        self.model = config.ai.llm_model
        self.endpoint = config.ai.llm_endpoint
    
    def build_prompt(
        self, 
        state: AgentState,
        available_actions: List[str],
        screen_context: Dict = None
    ) -> str:
        """
        Build prompt for LLM decision making.
        """
        context = state.to_context_dict()
        
        prompt = f"""You are an AI controlling a desktop automation agent that simulates human-like behavior.

CURRENT STATE:
- Application: {context['current_app']}
- Window: {context['window_title'][:50] if context['window_title'] else 'Unknown'}
- Last action: {context['last_action']}
- Recent actions: {', '.join(context['recent_actions'][-5:])}
- Time in current app: {context['time_in_app']:.0f}s
- Activity level: {context['activity_level']}
- Is typing: {context['is_typing']}

AVAILABLE ACTIONS:
{', '.join(available_actions)}

RULES:
1. Choose actions that appear natural and human-like
2. Avoid repeating the same action more than twice in a row
3. Match actions to the current application context
4. Include occasional pauses and micro-movements
5. Typing is more likely in VS Code, scrolling in Chrome

Choose the single best next action. Respond with ONLY the action name, nothing else."""

        if screen_context:
            prompt += f"\n\nSCREEN INFO: brightness={screen_context.get('brightness', 0.5):.2f}, changed={screen_context.get('screen_changed', False)}"
        
        return prompt
    
    def call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM API and get response."""
        if not self.enabled or not self.api_key:
            return None
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a desktop automation decision engine. Respond with only action names."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 30,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                action = result['choices'][0]['message']['content'].strip().lower()
                action = action.replace('"', '').replace("'", '')
                return action
                
        except Exception as e:
            self.logger.debug(f"LLM call failed: {e}")
        
        return None
    
    def get_decision(
        self, 
        state: AgentState,
        available_actions: List[str],
        screen_context: Dict = None
    ) -> Optional[str]:
        """Get action decision from LLM."""
        prompt = self.build_prompt(state, available_actions, screen_context)
        action = self.call_llm(prompt)
        
        # Validate action
        if action and action in available_actions:
            self.logger.decision(action, "LLM decision")
            return action
        
        return None


class Brain:
    """
    Main intelligent decision engine.
    Combines all subsystems for smart action selection.
    """
    
    # Available action types
    ALL_ACTIONS = [
        "mouse_move", "mouse_click", "scroll", "type_text",
        "keyboard_shortcut", "switch_window", "switch_tab",
        "idle", "micro_movement", "hesitate", "mistake_correction", "task"
    ]
    
    def __init__(self, use_tasks: bool = True):
        self.logger = get_logger()
        
        # Initialize state
        self.state = AgentState()
        self.state.session_start_time = time.time()
        
        # Initialize subsystems
        self.markov = MarkovTransitionMatrix()
        self.memory = BehaviorMemory()
        self.context_analyzer = ContextAnalyzer()
        self.llm = LLMInterface()
        
        # Task system
        self.use_tasks = use_tasks
        self._task_probability = 0.15  # Probability to execute task vs raw action
        
        # Decision mode
        self.decision_mode = config.ai.decision_mode
        
        # Screen context (set by vision system)
        self._screen_context: Optional[Dict] = None
        
        self.logger.info(f"Brain initialized: mode={self.decision_mode}, tasks={use_tasks}")
    
    def set_screen_context(self, context: Dict) -> None:
        """Update screen context from vision system."""
        self._screen_context = context
        
        # Update state from screen context
        if context:
            if 'brightness' in context:
                self.state.screen_brightness = context['brightness']
            if 'has_dark_theme' in context:
                self.state.has_dark_theme = context['has_dark_theme']
            if 'screen_changed' in context:
                self.state.screen_changed = context['screen_changed']
    
    def think(self) -> Tuple[str, Dict[str, Any]]:
        """
        Main decision method.
        
        Returns:
            Tuple of (action_name, action_params)
        """
        # Update context
        self.state.update_context()
        
        # Check if should execute task instead of raw action
        if self.use_tasks and random.random() < self._task_probability:
            return self._decide_task()
        
        # Get action decision based on mode
        if self.decision_mode == "llm" and self.llm.enabled:
            action = self._decide_with_llm()
        elif self.decision_mode == "markov":
            action = self._decide_with_markov()
        elif self.decision_mode == "rule_based":
            action = self._decide_with_rules()
        else:  # weighted_random (default)
            action = self._decide_with_weighted_random()
        
        # Generate parameters
        params = self._generate_action_params(action)
        
        self.logger.decision(action, f"mode={self.decision_mode}, app={self.state.current_app.value}")
        
        return action, params
    
    def _decide_with_llm(self) -> str:
        """Make decision using LLM."""
        action = self.llm.get_decision(
            self.state,
            self.ALL_ACTIONS,
            self._screen_context
        )
        
        if action:
            return action
        
        # Fallback to weighted random
        return self._decide_with_weighted_random()
    
    def _decide_with_markov(self) -> str:
        """Make decision using Markov transitions."""
        # Get context-based weight modifiers
        context_weights = self.context_analyzer.get_context_weights(
            self.state, self._screen_context
        )
        
        # Get memory-based adjustments
        memory_weights = self.memory.get_adjustment_weights()
        
        # Combine weights
        combined = {}
        for action in self.ALL_ACTIONS:
            w = context_weights.get(action, 1.0) * memory_weights.get(action, 1.0)
            combined[action] = w
        
        # Sample from Markov matrix
        action = self.markov.sample_next_action(
            self.state.last_action or "idle",
            context_modifier=combined,
            forbidden=self._get_forbidden_actions()
        )
        
        return action
    
    def _decide_with_rules(self) -> str:
        """Make decision using rule-based logic."""
        # Rule: Long idle triggers movement
        if self.state.time_since_last_action() > 5:
            if random.random() < 0.7:
                return random.choice(["mouse_move", "micro_movement", "scroll"])
        
        # Rule: In browser, prefer scrolling
        if self.state.current_app == AppContext.CHROME:
            if random.random() < 0.3:
                return "scroll"
            if random.random() < 0.2:
                return "switch_tab"
        
        # Rule: In editor, prefer typing
        if self.state.current_app == AppContext.VSCODE:
            if random.random() < 0.25:
                return "type_text"
            if random.random() < 0.15:
                return "keyboard_shortcut"
        
        # Rule: After many actions, take a break
        if self.state.total_actions % 20 == 19:
            return "idle"
        
        # Rule: Avoid repetition
        if self.memory.detect_repetition(self.state.last_action, threshold=2):
            forbidden = [self.state.last_action]
            return random.choice([a for a in self.ALL_ACTIONS[:8] if a not in forbidden])
        
        # Default: weighted random
        return self._decide_with_weighted_random()
    
    def _decide_with_weighted_random(self) -> str:
        """Make decision using weighted random with adjustments."""
        # Start with base weights from config
        weights = dict(config.ai.action_weights)
        
        # Get context adjustments
        context_weights = self.context_analyzer.get_context_weights(
            self.state, self._screen_context
        )
        
        # Get memory adjustments
        memory_weights = self.memory.get_adjustment_weights()
        
        # Apply adjustments
        for action in weights:
            weights[action] *= context_weights.get(action, 1.0)
            weights[action] *= memory_weights.get(action, 1.0)
        
        # Remove forbidden actions
        forbidden = self._get_forbidden_actions()
        weights = {k: v for k, v in weights.items() if k not in forbidden}
        
        # Normalize and select
        if not weights:
            return "idle"
        
        return weighted_random_choice(weights)
    
    def _decide_task(self) -> Tuple[str, Dict[str, Any]]:
        """Decide which high-level task to execute."""
        # Map app context to task context
        context_map = {
            AppContext.CHROME: "chrome",
            AppContext.VSCODE: "vscode",
            AppContext.EXPLORER: "unknown",
            AppContext.TERMINAL: "vscode",
            AppContext.UNKNOWN: "unknown",
            AppContext.IDLE: "unknown",
        }
        
        task_context = context_map.get(self.state.current_app, "unknown")
        
        return "task", {"context": task_context}
    
    def _get_forbidden_actions(self) -> List[str]:
        """Get list of actions that should not be selected."""
        forbidden = []
        
        # Don't repeat too many times
        if self.state.consecutive_same_actions >= 3:
            forbidden.append(self.state.last_action)
        
        # Pattern breaking
        pattern = self.memory.detect_pattern(3)
        if pattern:
            forbidden.extend(pattern)

        # Do not type in browser unless WordPress/Elementor editing context is active.
        if self.state.current_app == AppContext.CHROME:
            title = (self.state.active_window or "").lower()
            wp_context = any(k in title for k in ["wordpress", "wp-admin", "elementor"])
            if not wp_context:
                forbidden.append("type_text")
        
        return list(set(forbidden))
    
    def _generate_action_params(self, action: str) -> Dict[str, Any]:
        """Generate parameters for an action."""
        params = {}
        
        if action == "scroll":
            params["direction"] = random.choice(["up", "down"])
            params["amount"] = random.randint(1, 5)
            params["smooth"] = random.random() < 0.5
            
        elif action == "type_text":
            params["realistic"] = True
            params["include_typos"] = random.random() < 0.1
            
        elif action == "idle":
            params["duration"] = random.uniform(1.0, 5.0)
            
        elif action == "micro_movement":
            params["range"] = random.randint(5, 15)
            
        elif action == "hesitate":
            params["duration"] = random.uniform(0.3, 1.5)
            
        elif action == "mouse_click":
            params["double"] = random.random() < 0.1
            
        elif action == "keyboard_shortcut":
            # No ctrl+s anywhere - avoid triggering save dialogs
            shortcuts = ["ctrl+z", "ctrl+c", "ctrl+f"]
            if self.state.current_app == AppContext.CHROME:
                shortcuts.extend(["ctrl+tab", "ctrl+shift+tab", "f5", "f12", "ctrl+shift+i"])
            elif self.state.current_app == AppContext.VSCODE:
                shortcuts.extend(["ctrl+p", "ctrl+shift+p", "ctrl+`"])
            params["shortcut"] = random.choice(shortcuts)
        
        return params
    
    def record_action(self, action: str) -> None:
        """Record that an action was executed."""
        self.state.add_action(action)
        self.memory.record(action)
    
    def record_task(self, task_name: str) -> None:
        """Record that a task was executed."""
        self.state.add_task(task_name)
    
    def get_action_delay(self) -> float:
        """Get delay before next action."""
        base = random.uniform(
            config.timing.action_delay_min,
            config.timing.action_delay_max
        )
        
        # Adjust by activity level
        multiplier = 1.0 / self.state.activity_level.value
        
        return base * multiplier
    
    def set_activity_level(self, level: str) -> None:
        """Set activity level."""
        level_map = {
            "very_low": ActivityLevel.VERY_LOW,
            "low": ActivityLevel.LOW,
            "medium": ActivityLevel.MEDIUM,
            "high": ActivityLevel.HIGH,
            "very_high": ActivityLevel.VERY_HIGH,
        }
        self.state.activity_level = level_map.get(level.lower(), ActivityLevel.MEDIUM)
        self.logger.info(f"Activity level set to: {self.state.activity_level.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get brain statistics."""
        return {
            "total_actions": self.state.total_actions,
            "total_tasks": self.state.total_tasks,
            "session_duration": self.state.time_since_session_start(),
            "current_app": self.state.current_app.value,
            "activity_level": self.state.activity_level.name,
            "diversity_score": self.memory.get_diversity_score(),
            "recent_actions": self.state.get_recent_actions(10),
            "decision_mode": self.decision_mode,
        }
    
    def export_state(self) -> str:
        """Export state as JSON for debugging/logging."""
        return json.dumps(self.state.to_context_dict(), indent=2)
    
    def decide_action(self) -> ActionType:
        """
        Decide next action and return as ActionType enum.
        This is the main interface used by agent.py.
        """
        action_name, _ = self.think()
        
        # Map action string to ActionType enum
        action_map = {
            "mouse_move": ActionType.MOUSE_MOVE,
            "mouse_click": ActionType.MOUSE_CLICK,
            "scroll": ActionType.SCROLL,
            "type_text": ActionType.TYPE_TEXT,
            "type": ActionType.TYPE_TEXT,
            "keyboard_shortcut": ActionType.KEYBOARD_SHORTCUT,
            "switch_window": ActionType.SWITCH_WINDOW,
            "switch_tab": ActionType.SWITCH_TAB,
            "idle": ActionType.IDLE,
            "micro_movement": ActionType.MICRO_MOVEMENT,
            "hesitate": ActionType.HESITATE,
            "mistake_correction": ActionType.MISTAKE_CORRECTION,
            "task": ActionType.TASK,
            "micro_pause": ActionType.IDLE,
        }
        
        return action_map.get(action_name, ActionType.IDLE)
    
    def get_current_state(self) -> AgentState:
        """Get the current agent state."""
        return self.state


# Global brain instance (singleton)
_brain: Optional[Brain] = None


def get_brain() -> Brain:
    """Get the global Brain instance."""
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain
