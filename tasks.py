"""
Tasks Module for AI Desktop Automation Agent
=============================================

High-level behavioral tasks that simulate real user activities.
Each task is a sequence of actions that together form natural workflows.

Tasks are context-aware and adapt based on screen state.
This provides more realistic behavior than raw random actions.
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod

from logger import get_logger
from config import config


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskType(Enum):
    """Types of tasks available."""
    BROWSING = "browsing"
    CODING = "coding"
    IDLE = "idle"
    WINDOW_MANAGEMENT = "window_management"
    FILE_EXPLORATION = "file_exploration"
    READING = "reading"
    SEARCH = "search"
    WORDPRESS_DEVELOPER = "wordpress_developer"


@dataclass
class TaskStep:
    """A single step within a task."""
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    delay_after: float = 0.15  # Fast default delay
    optional: bool = False
    condition: Optional[Callable[[], bool]] = None
    
    def should_execute(self) -> bool:
        """Check if step should be executed."""
        if self.condition is not None:
            return self.condition()
        return True


@dataclass
class TaskResult:
    """Result of task execution."""
    status: TaskStatus
    steps_completed: int
    total_steps: int
    duration: float
    error_message: str = ""
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_steps == 0:
            return 0.0
        return self.steps_completed / self.total_steps


class Task(ABC):
    """
    Abstract base class for all tasks.
    Tasks represent high-level user behaviors.
    """
    
    # Default task type - subclasses should override
    task_type: TaskType = TaskType.IDLE
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = get_logger()
        self.status = TaskStatus.PENDING
        self.priority = TaskPriority.MEDIUM
        
        # Execution tracking
        self._start_time: Optional[float] = None
        self._steps_completed = 0
        
        # Interruption flag
        self._interrupted = False
    
    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.INTERRUPTED]
    
    @abstractmethod
    def get_steps(self) -> List[TaskStep]:
        """Get the sequence of steps for this task."""
        pass
    
    def execute(self, action_executor: Callable[[str, Dict], bool]) -> TaskResult:
        """
        Execute the task.
        
        Args:
            action_executor: Function to execute actions (action_name, params) -> success
        
        Returns:
            TaskResult with execution details
        """
        self.status = TaskStatus.RUNNING
        self._start_time = time.time()
        self._steps_completed = 0
        self._interrupted = False
        
        steps = self.get_steps()
        self.logger.info(f"Starting task: {self.name} ({len(steps)} steps)")
        
        for i, step in enumerate(steps):
            # Check for interruption
            if self._interrupted:
                self.status = TaskStatus.INTERRUPTED
                break
            
            # Check if step should execute
            if not step.should_execute():
                self.logger.debug(f"Skipping optional step: {step.action}")
                continue
            
            try:
                # Execute the step
                success = action_executor(step.action, step.params)
                
                if success:
                    self._steps_completed += 1
                elif not step.optional:
                    self.logger.warning(f"Required step failed: {step.action}")
                
                # Delay after step
                if step.delay_after > 0 and i < len(steps) - 1:
                    delay = step.delay_after * random.uniform(0.8, 1.3)
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Step error: {step.action} - {e}")
                if not step.optional:
                    self.status = TaskStatus.FAILED
                    return TaskResult(
                        status=TaskStatus.FAILED,
                        steps_completed=self._steps_completed,
                        total_steps=len(steps),
                        duration=time.time() - self._start_time,
                        error_message=str(e)
                    )
        
        # Determine final status
        if self.status != TaskStatus.INTERRUPTED:
            self.status = TaskStatus.COMPLETED
        
        duration = time.time() - self._start_time
        self.logger.info(f"Task {self.name} {self.status.value}: {self._steps_completed}/{len(steps)} steps in {duration:.1f}s")
        
        return TaskResult(
            status=self.status,
            steps_completed=self._steps_completed,
            total_steps=len(steps),
            duration=duration
        )
    
    def interrupt(self) -> None:
        """Interrupt the running task."""
        self._interrupted = True


class BrowsingTask(Task):
    """
    Simulates a browsing session in Chrome/browser.
    Includes scrolling, tab switching, and occasional clicks.
    """
    
    task_type = TaskType.BROWSING
    
    def __init__(self, intensity: str = "medium"):
        super().__init__(
            name="browsing_session",
            description="Simulate natural web browsing behavior"
        )
        self.intensity = intensity
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Number of scroll-pause cycles based on intensity
        cycles = {"low": 2, "medium": 4, "high": 7}.get(self.intensity, 4)
        
        # Initial pause (looking at page)
        steps.append(TaskStep(
            action="idle",
            params={"duration": random.uniform(1.5, 3.0)},
            delay_after=0.3
        ))
        
        for i in range(cycles):
            # Frequent pointer movement to look more human in browser sessions
            if random.random() < 0.7:
                steps.append(TaskStep(
                    action="mouse_move",
                    params={"random": True},
                    delay_after=random.uniform(0.15, 0.4),
                    optional=True
                ))

            # Scroll down
            steps.append(TaskStep(
                action="scroll",
                params={"direction": "down", "amount": random.randint(2, 5)},
                delay_after=random.uniform(0.5, 1.5)
            ))
            
            # Pause to "read"
            steps.append(TaskStep(
                action="idle",
                params={"duration": random.uniform(1.0, 4.0)},
                delay_after=0.2
            ))
            
            # Occasional mouse movement
            if random.random() < 0.4:
                steps.append(TaskStep(
                    action="mouse_move",
                    params={"random": True},
                    delay_after=random.uniform(0.3, 0.8),
                    optional=True
                ))
            
            # Occasional tab switch
            if random.random() < 0.2 and i > 0:
                steps.append(TaskStep(
                    action="switch_tab",
                    params={},
                    delay_after=random.uniform(0.5, 1.0),
                    optional=True
                ))

            # Occasionally open inspect element in browser developer flow
            if random.random() < 0.25:
                steps.append(TaskStep(
                    action="keyboard_shortcut",
                    params={"shortcut": random.choice(["f12", "ctrl+shift+i"])},
                    delay_after=random.uniform(0.2, 0.5),
                    optional=True
                ))
        
        # Sometimes scroll back up
        if random.random() < 0.3:
            steps.append(TaskStep(
                action="scroll",
                params={"direction": "up", "amount": random.randint(3, 8)},
                delay_after=0.5
            ))
        
        return steps


class CodingTask(Task):
    """
    Simulates a coding session in VS Code/IDE.
    Includes typing, navigation, and occasional saves.
    """
    
    task_type = TaskType.CODING
    
    def __init__(self, intensity: str = "medium"):
        super().__init__(
            name="coding_session",
            description="Simulate natural coding behavior"
        )
        self.intensity = intensity
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Number of type-pause cycles
        cycles = {"low": 2, "medium": 4, "high": 6}.get(self.intensity, 4)
        
        # Initial positioning
        steps.append(TaskStep(
            action="mouse_move",
            params={"random": True},
            delay_after=0.3
        ))
        
        steps.append(TaskStep(
            action="mouse_click",
            params={},
            delay_after=0.5
        ))
        
        for i in range(cycles):
            # Think/read code
            steps.append(TaskStep(
                action="idle",
                params={"duration": random.uniform(1.0, 3.0)},
                delay_after=0.2
            ))
            
            # Type some code
            steps.append(TaskStep(
                action="type_text",
                params={"realistic": True},
                delay_after=random.uniform(0.3, 0.8)
            ))
            
            # Occasional navigation
            if random.random() < 0.3:
                steps.append(TaskStep(
                    action="keyboard_shortcut",
                    params={"shortcut": random.choice(["ctrl+g", "ctrl+p", "ctrl+f"])},
                    delay_after=0.5,
                    optional=True
                ))
                steps.append(TaskStep(
                    action="press_escape",
                    params={},
                    delay_after=0.3,
                    optional=True
                ))
            
            # Scroll occasionally
            if random.random() < 0.4:
                direction = random.choice(["up", "down"])
                steps.append(TaskStep(
                    action="scroll",
                    params={"direction": direction, "amount": random.randint(1, 3)},
                    delay_after=0.3
                ))
        
        # Navigation shortcut instead of save (no ctrl+s to avoid Chrome save dialogs)
        if random.random() < 0.5:
            steps.append(TaskStep(
                action="keyboard_shortcut",
                params={"shortcut": "ctrl+tab"},
                delay_after=0.3
            ))
        
        return steps


class IdleTask(Task):
    """
    Simulates idle/AFK behavior with small movements.
    Appears as if user stepped away briefly.
    """
    
    task_type = TaskType.IDLE
    
    def __init__(self, duration: float = 5.0):
        super().__init__(
            name="idle_session",
            description="Simulate brief idle/away behavior"
        )
        self.duration = duration
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Calculate number of micro-movements
        num_movements = int(self.duration / 2)
        
        for _ in range(max(1, num_movements)):
            # Micro mouse movement (jitter)
            steps.append(TaskStep(
                action="micro_movement",
                params={"range": 10},
                delay_after=random.uniform(1.0, 3.0)
            ))
            
            # Occasionally nothing at all
            if random.random() < 0.3:
                steps.append(TaskStep(
                    action="idle",
                    params={"duration": random.uniform(1.0, 2.0)},
                    delay_after=0.1
                ))
        
        return steps


class WindowManagementTask(Task):
    """
    Simulates window management activities.
    Switching between apps, arranging windows.
    """
    
    task_type = TaskType.WINDOW_MANAGEMENT
    
    def __init__(self):
        super().__init__(
            name="window_management",
            description="Simulate window switching and management"
        )
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Alt+Tab sequence
        num_switches = random.randint(1, 3)
        
        for i in range(num_switches):
            steps.append(TaskStep(
                action="switch_window",
                params={},
                delay_after=random.uniform(0.5, 1.5)
            ))
            
            # Pause in new window
            steps.append(TaskStep(
                action="idle",
                params={"duration": random.uniform(1.0, 3.0)},
                delay_after=0.2
            ))
            
            # Maybe do something quick
            if random.random() < 0.5:
                action = random.choice(["scroll", "mouse_move", "mouse_click"])
                steps.append(TaskStep(
                    action=action,
                    params={},
                    delay_after=0.3,
                    optional=True
                ))
        
        return steps


class FileExplorationTask(Task):
    """
    Simulates file browsing in Explorer.
    Navigating folders, scrolling file lists.
    """
    
    task_type = TaskType.FILE_EXPLORATION
    
    def __init__(self):
        super().__init__(
            name="file_exploration",
            description="Simulate file browsing behavior"
        )
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Open file dialog or use existing explorer
        steps.append(TaskStep(
            action="idle",
            params={"duration": random.uniform(0.5, 1.0)},
            delay_after=0.2
        ))
        
        # Scroll through files
        for _ in range(random.randint(2, 4)):
            steps.append(TaskStep(
                action="scroll",
                params={"direction": random.choice(["up", "down"]), "amount": 2},
                delay_after=random.uniform(0.3, 0.8)
            ))
        
        # Click on something
        steps.append(TaskStep(
            action="mouse_move",
            params={"random": True},
            delay_after=0.3
        ))
        
        if random.random() < 0.3:
            steps.append(TaskStep(
                action="mouse_click",
                params={"double": random.random() < 0.3},
                delay_after=0.5,
                optional=True
            ))
        
        return steps


class ReadingTask(Task):
    """
    Simulates reading a document or webpage.
    Slow scrolling with long pauses.
    """
    
    task_type = TaskType.READING
    
    def __init__(self, duration: float = 30.0):
        super().__init__(
            name="reading_session",
            description="Simulate document reading behavior"
        )
        self.duration = duration
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Calculate reading segments
        num_segments = max(3, int(self.duration / 8))
        
        for i in range(num_segments):
            # Read (long pause)
            read_time = random.uniform(3.0, 8.0)
            steps.append(TaskStep(
                action="idle",
                params={"duration": read_time},
                delay_after=0.1
            ))
            
            # Slow scroll
            steps.append(TaskStep(
                action="scroll",
                params={"direction": "down", "amount": 1, "smooth": True},
                delay_after=random.uniform(0.3, 0.6)
            ))
            
            # Occasional highlight attempt
            if random.random() < 0.15:
                steps.append(TaskStep(
                    action="drag_select",
                    params={},
                    delay_after=0.5,
                    optional=True
                ))
                # Copy
                steps.append(TaskStep(
                    action="keyboard_shortcut",
                    params={"shortcut": "ctrl+c"},
                    delay_after=0.3,
                    optional=True
                ))
        
        return steps


class SearchTask(Task):
    """
    Simulates using search functionality.
    Opening search, typing query, reviewing results.
    """
    
    task_type = TaskType.SEARCH
    
    def __init__(self, app_context: str = "browser"):
        super().__init__(
            name="search_session",
            description="Simulate search behavior"
        )
        self.app_context = app_context
    
    def get_steps(self) -> List[TaskStep]:
        steps = []
        
        # Open search (never use browser address bar)
        if self.app_context == "browser":
            steps.append(TaskStep(
                action="keyboard_shortcut",
                params={"shortcut": "ctrl+f"},
                delay_after=0.3
            ))
        else:
            steps.append(TaskStep(
                action="keyboard_shortcut",
                params={"shortcut": "ctrl+f"},
                delay_after=0.3
            ))
        
        # Think about what to search
        steps.append(TaskStep(
            action="idle",
            params={"duration": random.uniform(0.5, 1.5)},
            delay_after=0.1
        ))
        
        # Type search query
        steps.append(TaskStep(
            action="type_text",
            params={"realistic": True, "short": True},
            delay_after=0.3
        ))
        
        # Submit search
        steps.append(TaskStep(
            action="press_key",
            params={"key": "enter"},
            delay_after=random.uniform(0.5, 1.0)
        ))
        
        # Wait for and review results
        steps.append(TaskStep(
            action="idle",
            params={"duration": random.uniform(1.0, 2.0)},
            delay_after=0.2
        ))
        
        # Scroll through results
        for _ in range(random.randint(1, 3)):
            steps.append(TaskStep(
                action="scroll",
                params={"direction": "down", "amount": 2},
                delay_after=random.uniform(0.5, 1.0)
            ))
        
        # Maybe close search
        if random.random() < 0.5:
            steps.append(TaskStep(
                action="press_escape",
                params={},
                delay_after=0.3
            ))
        
        return steps


class WordPressDeveloperTask(Task):
    """
    Simulates WordPress + Elementor editing like a developer.
    Focuses on mouse-driven editing and inspect usage.
    """

    task_type = TaskType.WORDPRESS_DEVELOPER

    def __init__(self, intensity: str = "medium"):
        super().__init__(
            name="wordpress_developer_session",
            description="Simulate WordPress Elementor editing and inspection"
        )
        self.intensity = intensity

    def get_steps(self) -> List[TaskStep]:
        steps = []
        cycles = {"low": 3, "medium": 5, "high": 8}.get(self.intensity, 5)

        # Open inspect tools early in the flow.
        steps.append(TaskStep(
            action="keyboard_shortcut",
            params={"shortcut": random.choice(["f12", "ctrl+shift+i"])},
            delay_after=0.35
        ))

        for _ in range(cycles):
            steps.append(TaskStep(
                action="mouse_move",
                params={"random": True},
                delay_after=random.uniform(0.12, 0.35)
            ))
            steps.append(TaskStep(
                action="mouse_click",
                params={},
                delay_after=random.uniform(0.15, 0.4)
            ))
            steps.append(TaskStep(
                action="scroll",
                params={"direction": random.choice(["up", "down"]), "amount": random.randint(1, 3)},
                delay_after=random.uniform(0.2, 0.6)
            ))

            # Find UI labels without using URL bar search.
            if random.random() < 0.35:
                steps.append(TaskStep(
                    action="keyboard_shortcut",
                    params={"shortcut": "ctrl+f"},
                    delay_after=0.2,
                    optional=True
                ))
                steps.append(TaskStep(
                    action="type_text",
                    params={"text": random.choice(["elementor", "section", "container", "style", "padding"])},
                    delay_after=0.2,
                    optional=True
                ))
                steps.append(TaskStep(
                    action="press_escape",
                    params={},
                    delay_after=0.2,
                    optional=True
                ))

            # WordPress developer style text edits inside editor fields.
            if random.random() < 0.5:
                steps.append(TaskStep(
                    action="type_text",
                    params={
                        "text": random.choice([
                            "update elementor section spacing",
                            "fix mobile hero overlap",
                            "adjust heading typography",
                            "optimize wordpress template",
                            "review console style issue",
                        ]),
                        "realistic": True,
                    },
                    delay_after=random.uniform(0.25, 0.7),
                    optional=True
                ))

        return steps


class TaskManager:
    """
    Manages task selection and execution.
    Provides intelligent task selection based on context.
    """
    
    def __init__(self):
        self.logger = get_logger()

        wp_intensity = str(getattr(config.tasks, "wordpress_developer_intensity", "medium")).lower()
        if wp_intensity not in ["low", "medium", "high"]:
            wp_intensity = "medium"
        wp_enabled = bool(getattr(config.tasks, "wordpress_developer_enabled", True))
        
        # Current running task
        self.current_task: Optional[Task] = None
        self._current_step_index: int = 0
        self._current_steps: List[TaskStep] = []
        
        # Available task factories
        self.task_types: Dict[str, Callable[[], Task]] = {
            "browsing": lambda: BrowsingTask(random.choice(["low", "medium", "high"])),
            "coding": lambda: CodingTask(random.choice(["low", "medium", "high"])),
            "wordpress_developer": (lambda: WordPressDeveloperTask(wp_intensity)) if wp_enabled else (lambda: BrowsingTask("medium")),
            "idle": lambda: IdleTask(random.uniform(3.0, 10.0)),
            "window_management": WindowManagementTask,
            "file_exploration": FileExplorationTask,
            "reading": lambda: ReadingTask(random.uniform(15.0, 45.0)),
            "search": lambda: SearchTask(random.choice(["browser", "editor"])),
        }
        
        # Task history
        self._history: List[str] = []
        self._max_history = 10
        
        # Context-based weights
        self.context_weights: Dict[str, Dict[str, float]] = {
            "chrome": {
                "browsing": 45,
                "reading": 25,
                "search": 3,
                "idle": 10,
                "window_management": 10,
                "file_exploration": 7,
            },
            "wordpress": {
                "wordpress_developer": 55,
                "browsing": 20,
                "reading": 10,
                "search": 3,
                "idle": 5,
                "window_management": 5,
                "file_exploration": 2,
            },
            "vscode": {
                "coding": 40,
                "search": 15,
                "reading": 10,
                "idle": 15,
                "window_management": 15,
                "file_exploration": 5,
            },
            "unknown": {
                "idle": 25,
                "window_management": 25,
                "browsing": 15,
                "coding": 10,
                "file_exploration": 15,
                "reading": 10,
            },
        }
    
    def select_task(self, context: str = "unknown") -> Task:
        """
        Select appropriate task based on context.
        
        Args:
            context: Application context (chrome, vscode, unknown)
        
        Returns:
            Selected Task instance
        """
        weights = self.context_weights.get(context, self.context_weights["unknown"]).copy()
        
        # Reduce weight of recently used tasks
        for task_name in self._history[-3:]:
            if task_name in weights:
                weights[task_name] *= 0.5
        
        # Weighted random selection
        total = sum(weights.values())
        r = random.uniform(0, total)
        
        cumulative = 0
        for task_name, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                self._add_to_history(task_name)
                return self.task_types[task_name]()
        
        # Fallback
        return IdleTask()
    
    def _add_to_history(self, task_name: str) -> None:
        """Add task to history."""
        self._history.append(task_name)
        if len(self._history) > self._max_history:
            self._history.pop(0)
    
    def get_task_by_name(self, name: str) -> Optional[Task]:
        """Get specific task by name."""
        if name in self.task_types:
            return self.task_types[name]()
        return None
    
    def register_task(self, name: str, factory: Callable[[], Task]) -> None:
        """Register a new task type."""
        self.task_types[name] = factory
        self.logger.info(f"Registered task: {name}")
    
    def select_task_for_context(self, screen_context) -> Optional[Task]:
        """
        Select and start a task based on screen context.
        
        Args:
            screen_context: ScreenContext from vision system
        
        Returns:
            Selected Task or None
        """
        # Map detected app to context string
        context = "unknown"
        if screen_context and hasattr(screen_context, 'active_app'):
            app = screen_context.active_app
            if app and 'chrome' in app.lower():
                context = "chrome"
            elif app and ('code' in app.lower() or 'vscode' in app.lower()):
                context = "vscode"

        # Prefer WordPress developer workflow when title indicates WP/Elementor.
        title = ""
        if screen_context and hasattr(screen_context, 'window_title') and screen_context.window_title:
            title = screen_context.window_title.lower()
        if any(k in title for k in ["wordpress", "wp-admin", "elementor"]):
            context = "wordpress"
        
        task = self.select_task(context)
        self.current_task = task
        self._current_steps = task.get_steps()
        self._current_step_index = 0
        return task
    
    def execute_current_step(self) -> bool:
        """
        Execute the current step of the active task.
        
        Returns:
            True if step was executed, False if no task or task complete
        """
        if self.current_task is None:
            return False
        
        if self._current_step_index >= len(self._current_steps):
            # Task complete
            self.current_task.status = TaskStatus.COMPLETED
            self.current_task = None
            return False
        
        step = self._current_steps[self._current_step_index]
        
        # Check if step should be executed
        if not step.should_execute():
            self._current_step_index += 1
            return self.execute_current_step()
        
        # Execute the step
        try:
            from actions import perform_action
            success = perform_action(step.action, step.params)
            
            if success:
                self._current_step_index += 1
                
                # Add delay after step
                if step.delay_after > 0:
                    time.sleep(step.delay_after)
                
                return True
        except Exception as e:
            self.logger.error(f"Task step failed: {e}")
        
        return False


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create global task manager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
