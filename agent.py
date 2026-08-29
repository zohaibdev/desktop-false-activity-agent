"""
Agent Core - Enhanced Human-Like Automation Agent
Integrates vision, tasks, brain, and actions into cohesive behavior
Features F10 pause/resume, F8 stop, F9 emergency stop
"""
import threading
import time
import random
import keyboard
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, Dict, List
from datetime import datetime, timedelta
from collections import deque

from config import get_config
from logger import get_logger
from brain import get_brain, AgentState, ActionType
from actions import get_actions
from vision import get_vision
from tasks import get_task_manager, TaskType
from utils import get_active_window_title


class AgentStatus(Enum):
    """Agent operational status"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    EMERGENCY_STOP = "emergency_stop"


class ActivityLevel(Enum):
    """Overall activity intensity levels"""
    IDLE = "idle"              # Minimal activity, long pauses
    LOW = "low"                # Occasional actions
    NORMAL = "normal"          # Regular human-like activity
    BUSY = "busy"              # Active work simulation
    INTENSE = "intense"        # High activity period


@dataclass
class AgentSession:
    """Tracks current agent session"""
    start_time: datetime
    total_actions: int = 0
    total_pauses: int = 0
    pause_duration: float = 0.0
    activity_level: ActivityLevel = ActivityLevel.NORMAL
    current_task_type: Optional[TaskType] = None
    errors_count: int = 0
    
    @property
    def elapsed_time(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def actions_per_minute(self) -> float:
        elapsed = self.elapsed_time / 60.0
        return self.total_actions / elapsed if elapsed > 0 else 0


class HotkeyManager:
    """Manages keyboard hotkeys for agent control"""
    
    def __init__(self, agent: 'Agent'):
        self.agent = agent
        self.logger = get_logger()
        self.registered = False
    
    def register_hotkeys(self):
        """Register all control hotkeys"""
        if self.registered:
            return
        
        try:
            keyboard.on_press_key('f8', self._on_stop)
            keyboard.on_press_key('f9', self._on_emergency_stop)
            keyboard.on_press_key('f10', self._on_toggle_pause)
            self.registered = True
            self.logger.info("Hotkeys registered: F8=Stop, F9=Emergency, F10=Pause/Resume")
        except Exception as e:
            self.logger.error(f"Failed to register hotkeys: {e}")
    
    def unregister_hotkeys(self):
        """Unregister all hotkeys"""
        if not self.registered:
            return
        
        try:
            keyboard.unhook_all()
            self.registered = False
            self.logger.info("Hotkeys unregistered")
        except Exception as e:
            self.logger.error(f"Failed to unregister hotkeys: {e}")
    
    def _on_stop(self, event):
        """F8 - Graceful stop"""
        self.logger.info("F8 pressed - Stopping agent")
        self.agent.stop()
    
    def _on_emergency_stop(self, event):
        """F9 - Emergency stop"""
        self.logger.warning("F9 pressed - EMERGENCY STOP")
        self.agent.emergency_stop()
    
    def _on_toggle_pause(self, event):
        """F10 - Toggle pause/resume"""
        if self.agent.status == AgentStatus.PAUSED:
            self.logger.info("F10 pressed - Resuming agent")
            self.agent.resume()
        elif self.agent.status == AgentStatus.RUNNING:
            self.logger.info("F10 pressed - Pausing agent")
            self.agent.pause()


class ActivityManager:
    """Manages activity levels and pacing"""
    
    def __init__(self):
        self.logger = get_logger()
        self.config = get_config()
        
        # Activity level parameters: (min_delay, max_delay, action_probability) - FAST
        self.level_params = {
            ActivityLevel.IDLE: (1.0, 3.0, 0.5),
            ActivityLevel.LOW: (0.5, 1.5, 0.7),
            ActivityLevel.NORMAL: (0.2, 0.8, 0.85),
            ActivityLevel.BUSY: (0.1, 0.4, 0.95),
            ActivityLevel.INTENSE: (0.05, 0.2, 0.98),
        }
        
        self.current_level = ActivityLevel.BUSY
        self.level_start_time = datetime.now()
        self.level_duration = self._random_level_duration()
    
    def _random_level_duration(self) -> float:
        """Random duration for current activity level"""
        return random.uniform(30.0, 120.0)  # 30s-2 minutes
    
    def get_action_delay(self) -> float:
        """Get delay before next action based on activity level"""
        min_delay, max_delay, _ = self.level_params[self.current_level]
        base_delay = random.uniform(min_delay, max_delay)
        
        # Add human-like variation
        if random.random() < 0.1:
            # Occasional longer pause (thinking)
            base_delay *= random.uniform(2.0, 4.0)
        elif random.random() < 0.05:
            # Rare very quick action
            base_delay *= random.uniform(0.3, 0.6)
        
        return base_delay
    
    def should_take_action(self) -> bool:
        """Decide if action should be taken based on activity level"""
        _, _, probability = self.level_params[self.current_level]
        return random.random() < probability
    
    def update_activity_level(self):
        """Potentially change activity level over time"""
        elapsed = (datetime.now() - self.level_start_time).total_seconds()
        
        if elapsed > self.level_duration:
            self._transition_level()
    
    def _transition_level(self):
        """Transition to new activity level"""
        # Activity level transition probabilities
        transitions = {
            ActivityLevel.IDLE: [
                (ActivityLevel.IDLE, 0.2),
                (ActivityLevel.LOW, 0.5),
                (ActivityLevel.NORMAL, 0.3),
            ],
            ActivityLevel.LOW: [
                (ActivityLevel.IDLE, 0.2),
                (ActivityLevel.LOW, 0.3),
                (ActivityLevel.NORMAL, 0.4),
                (ActivityLevel.BUSY, 0.1),
            ],
            ActivityLevel.NORMAL: [
                (ActivityLevel.LOW, 0.15),
                (ActivityLevel.NORMAL, 0.5),
                (ActivityLevel.BUSY, 0.3),
                (ActivityLevel.INTENSE, 0.05),
            ],
            ActivityLevel.BUSY: [
                (ActivityLevel.NORMAL, 0.3),
                (ActivityLevel.BUSY, 0.4),
                (ActivityLevel.INTENSE, 0.2),
                (ActivityLevel.LOW, 0.1),
            ],
            ActivityLevel.INTENSE: [
                (ActivityLevel.BUSY, 0.4),
                (ActivityLevel.NORMAL, 0.3),
                (ActivityLevel.INTENSE, 0.2),
                (ActivityLevel.LOW, 0.1),
            ],
        }
        
        choices = transitions.get(self.current_level, [(ActivityLevel.NORMAL, 1.0)])
        levels, weights = zip(*choices)
        
        new_level = random.choices(levels, weights=weights)[0]
        
        if new_level != self.current_level:
            self.logger.debug(f"Activity level: {self.current_level.value} -> {new_level.value}")
            self.current_level = new_level
        
        self.level_start_time = datetime.now()
        self.level_duration = self._random_level_duration()
    
    def set_level(self, level: ActivityLevel):
        """Manually set activity level"""
        self.current_level = level
        self.level_start_time = datetime.now()
        self.level_duration = self._random_level_duration()
        self.logger.info(f"Activity level set to: {level.value}")


class Agent:
    """
    Main agent class - coordinates all components
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.logger = get_logger()
        self.config = get_config()
        
        # Core components
        self.brain = get_brain()
        self.actions = get_actions()
        self.vision = get_vision()
        self.task_manager = get_task_manager()
        
        # Control components
        self.hotkey_manager = HotkeyManager(self)
        self.activity_manager = ActivityManager()
        
        # State
        self.status = AgentStatus.STOPPED
        self.session: Optional[AgentSession] = None
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        self._stop_event = threading.Event()
        self._main_thread: Optional[threading.Thread] = None
        
        # Action history for anti-repetition
        self.recent_actions: deque = deque(maxlen=20)
        self.last_screen_context = None
        
        self._initialized = True
        self.logger.info("Agent initialized")
    
    def start(self, initial_delay: float = 3.0):
        """Start the agent"""
        if self.status == AgentStatus.RUNNING:
            self.logger.warning("Agent already running")
            return
        
        self.logger.info(f"Starting agent in {initial_delay} seconds...")
        time.sleep(initial_delay)
        
        # Initialize session
        self.session = AgentSession(start_time=datetime.now())
        self.status = AgentStatus.RUNNING
        self._stop_event.clear()
        self._pause_event.set()
        
        # Register hotkeys
        self.hotkey_manager.register_hotkeys()
        
        # Start main loop in thread
        self._main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self._main_thread.start()
        
        self.logger.info("Agent started")
    
    def stop(self):
        """Gracefully stop the agent"""
        if self.status == AgentStatus.STOPPED:
            return
        
        self.logger.info("Stopping agent...")
        self.status = AgentStatus.STOPPED
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        
        if self._main_thread and self._main_thread.is_alive():
            self._main_thread.join(timeout=5.0)
        
        self.hotkey_manager.unregister_hotkeys()
        self._log_session_stats()
        self.logger.info("Agent stopped")
    
    def emergency_stop(self):
        """Emergency stop - immediate halt"""
        self.logger.warning("EMERGENCY STOP INITIATED")
        self.status = AgentStatus.EMERGENCY_STOP
        self._stop_event.set()
        self._pause_event.set()
        
        self.hotkey_manager.unregister_hotkeys()
        self.logger.warning("Agent emergency stopped")
    
    def pause(self):
        """Pause agent execution"""
        if self.status != AgentStatus.RUNNING:
            return
        
        self.status = AgentStatus.PAUSED
        self._pause_event.clear()
        self.session.total_pauses += 1
        self._pause_start = datetime.now()
        self.logger.info("Agent paused")
    
    def resume(self):
        """Resume agent execution"""
        if self.status != AgentStatus.PAUSED:
            return
        
        pause_duration = (datetime.now() - self._pause_start).total_seconds()
        self.session.pause_duration += pause_duration
        
        self.status = AgentStatus.RUNNING
        self._pause_event.set()
        self.logger.info(f"Agent resumed (paused for {pause_duration:.1f}s)")
    
    def _main_loop(self):
        """Main agent loop"""
        self.logger.info("Main loop started")
        
        while not self._stop_event.is_set():
            try:
                # Check for pause
                self._pause_event.wait()
                
                if self._stop_event.is_set():
                    break
                
                # Update activity level
                self.activity_manager.update_activity_level()
                
                # Decide if we should act
                if not self.activity_manager.should_take_action():
                    self._idle_behavior()
                    continue
                
                # Gather screen context
                self._update_screen_context()
                
                # Execute behavior cycle
                self._execute_behavior_cycle()
                
                # Action delay based on activity level
                delay = self.activity_manager.get_action_delay()
                self._interruptible_sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.session.errors_count += 1
                time.sleep(1.0)  # Brief pause on error
        
        self.logger.info("Main loop ended")
    
    def _update_screen_context(self):
        """Update screen context using vision system"""
        try:
            context = self.vision.get_screen_context()
            self.last_screen_context = context
            
            # Update brain with screen context
            state = self.brain.get_current_state()
            state.screen_context = {
                "active_app": context.active_app,
                "visible_elements": [e.element_type for e in context.visible_elements],
                "screen_changed": context.screen_changed,
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to update screen context: {e}")
    
    def _execute_behavior_cycle(self):
        """Execute one behavior cycle"""
        # Check if we have an active task
        current_task = self.task_manager.current_task
        
        if current_task and not current_task.is_complete:
            # Continue with current task
            self._execute_task_step()
        else:
            # No task or task complete - decide next action
            self._decide_and_execute_action()
    
    def _execute_task_step(self):
        """Execute one step of current task"""
        task = self.task_manager.current_task
        
        if task is None:
            return
        
        try:
            # Execute task step
            result = self.task_manager.execute_current_step()
            
            if result:
                self.session.total_actions += 1
                self.recent_actions.append(f"task:{task.task_type.value}")
                self.logger.debug(f"Task step executed: {task.task_type.value}")
            
            # Check if task completed
            if task.is_complete:
                self.session.current_task_type = None
                self.logger.info(f"Task completed: {task.task_type.value}")
                
        except Exception as e:
            self.logger.error(f"Task step failed: {e}")
    
    def _decide_and_execute_action(self):
        """Use brain to decide and execute action"""
        # Get decision from brain
        action_type = self.brain.decide_action()
        
        # Check for repetition
        action_key = f"action:{action_type.value}"
        if self._is_too_repetitive(action_key):
            # Force diversity
            action_type = self._get_diverse_action(action_type)
        
        # Maybe start a task instead of single action
        if random.random() < 0.3 and self.last_screen_context:
            self._maybe_start_task(action_type)
            return
        
        # Execute single action
        self._execute_action(action_type)
    
    def _execute_action(self, action_type: ActionType):
        """Execute a single action based on type"""
        try:
            if action_type == ActionType.MOUSE_MOVE:
                self.actions.mouse.random_move()
                
            elif action_type == ActionType.MOUSE_CLICK:
                self.actions.mouse.click_random_area()
                
            elif action_type == ActionType.SCROLL:
                self.actions.scroll.random_scroll()
                
            elif action_type == ActionType.TYPE:
                self._do_typing_action()
                
            elif action_type == ActionType.SWITCH_TAB:
                self.actions.application.switch_tab()
                
            elif action_type == ActionType.SWITCH_WINDOW:
                self.actions.application.switch_window()
                
            elif action_type == ActionType.IDLE:
                self._idle_behavior()
                return  # Don't count as action
            
            elif action_type == ActionType.MICRO_PAUSE:
                self.actions.idle.micro_break()
                return  # Don't count as action
            
            # Record action
            self.session.total_actions += 1
            self.recent_actions.append(f"action:{action_type.value}")
            
            # Update brain with action taken
            self.brain.record_action(action_type)
            
            self.logger.debug(f"Action executed: {action_type.value}")
            
        except Exception as e:
            self.logger.error(f"Action failed: {action_type.value} - {e}")
    
    def _do_typing_action(self):
        """Execute a typing action with context awareness - WordPress/browsing content"""
        title = get_active_window_title().lower()

        # Never type in generic Chrome context to avoid URL bar/search typing.
        if ("chrome" in title or "edge" in title or "firefox" in title) and not any(
            k in title for k in ["wordpress", "wp-admin", "elementor"]
        ):
            self._idle_behavior()
            return

        # Context-aware phrases for WordPress and browsing
        phrases = [
            "update elementor section spacing",
            "fix wordpress mobile layout",
            "adjust heading typography",
            "review inspect css rule",
            "update call to action style",
            "check plugin conflict",
            "optimize hero image size",
            "align container and columns",
            "improve page speed settings",
            "verify responsive breakpoint",
            "update footer widget style",
            "review form validation",
            "publish page update",
            "preview template changes",
        ]
        
        text = random.choice(phrases)
        self.actions.keyboard.type_text(text)
    
    def _maybe_start_task(self, suggested_action: ActionType):
        """Maybe start a high-level task based on context"""
        if self.last_screen_context is None:
            return
        
        # Select task based on screen context and suggested action
        task = self.task_manager.select_task_for_context(self.last_screen_context)
        
        if task:
            self.session.current_task_type = task.task_type
            self.logger.info(f"Starting task: {task.task_type.value}")
    
    def _idle_behavior(self):
        """Execute idle/waiting behavior - quick and then continue"""
        behavior = random.choice([
            lambda: self.actions.idle.micro_break(),
            lambda: self.actions.mouse.random_move(),
            lambda: time.sleep(random.uniform(0.1, 0.5)),
        ])
        behavior()
    
    def _is_too_repetitive(self, action_key: str) -> bool:
        """Check if action would be too repetitive"""
        if len(self.recent_actions) < 3:
            return False
        
        recent = list(self.recent_actions)[-5:]
        count = sum(1 for a in recent if a == action_key)
        return count >= 3
    
    def _get_diverse_action(self, avoid: ActionType) -> ActionType:
        """Get a different action type for diversity"""
        alternatives = [
            ActionType.MOUSE_MOVE,
            ActionType.SCROLL,
            ActionType.IDLE,
            ActionType.MICRO_PAUSE,
        ]
        alternatives = [a for a in alternatives if a != avoid]
        return random.choice(alternatives)
    
    def _interruptible_sleep(self, duration: float):
        """Sleep that can be interrupted by stop/pause"""
        end_time = time.time() + duration
        while time.time() < end_time:
            if self._stop_event.is_set():
                break
            self._pause_event.wait(timeout=0.1)
    
    def _log_session_stats(self):
        """Log session statistics"""
        if self.session is None:
            return
        
        self.logger.info("=" * 50)
        self.logger.info("SESSION STATISTICS")
        self.logger.info(f"Duration: {self.session.elapsed_time:.1f} seconds")
        self.logger.info(f"Total actions: {self.session.total_actions}")
        self.logger.info(f"Actions/minute: {self.session.actions_per_minute:.2f}")
        self.logger.info(f"Pauses: {self.session.total_pauses}")
        self.logger.info(f"Total pause duration: {self.session.pause_duration:.1f}s")
        self.logger.info(f"Errors: {self.session.errors_count}")
        self.logger.info("=" * 50)
    
    def get_status_info(self) -> dict:
        """Get current status information"""
        return {
            "status": self.status.value,
            "session_duration": self.session.elapsed_time if self.session else 0,
            "total_actions": self.session.total_actions if self.session else 0,
            "activity_level": self.activity_manager.current_level.value,
            "current_task": self.session.current_task_type.value if self.session and self.session.current_task_type else None,
        }


# Global instance
_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """Get the global agent instance"""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


def run_agent(duration: Optional[float] = None):
    """
    Run the agent for specified duration or indefinitely
    
    Args:
        duration: Run duration in seconds, or None for indefinite
    """
    agent = get_agent()
    agent.start(initial_delay=3.0)
    
    try:
        if duration:
            time.sleep(duration)
            agent.stop()
        else:
            # Run until stopped by hotkey
            while agent.status not in [AgentStatus.STOPPED, AgentStatus.EMERGENCY_STOP]:
                time.sleep(0.5)
    except KeyboardInterrupt:
        agent.stop()


if __name__ == "__main__":
    print("=" * 50)
    print("AI Desktop Automation Agent")
    print("=" * 50)
    print("\nControls:")
    print("  F8  - Graceful stop")
    print("  F9  - Emergency stop")
    print("  F10 - Pause/Resume")
    print("\nStarting in 3 seconds...")
    print("=" * 50)
    
    run_agent()
