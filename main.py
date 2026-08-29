#!/usr/bin/env python3
"""
AI Desktop Automation Agent - Main Entry Point
A human-like automation agent that simulates natural user activity on Windows.

Features:
- Intelligent decision engine with Markov-style transitions
- Screen awareness and context understanding
- Human-like behavior simulation (micro-movements, hesitation, typos)
- Task-based activity sequences
- LLM-ready architecture for future AI integration

Controls:
    F8  - Stop agent gracefully
    F9  - Emergency stop (immediate halt)
    F10 - Pause/Resume agent

Usage:
    python main.py                    # Run indefinitely
    python main.py --duration 300     # Run for 5 minutes
    python main.py --activity busy    # Start with busy activity level
    python main.py --help             # Show all options
"""

import argparse
import sys
import time
from datetime import datetime

# Ensure proper import path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, save_config
from logger import get_logger
from agent import get_agent, run_agent, AgentStatus


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║           AI Desktop Automation Agent v2.0                   ║
║                                                              ║
║   Intelligent | Human-Like | Context-Aware                   ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_controls():
    """Print control instructions"""
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  CONTROLS                                                   │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│    F8   Stop gracefully                                     │")
    print("│    F9   Emergency stop (immediate)                          │")
    print("│    F10  Pause / Resume                                      │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()


def print_status(agent):
    """Print current agent status"""
    info = agent.get_status_info()
    print(f"\n[STATUS] {info['status'].upper()}")
    print(f"         Activity: {info['activity_level']}")
    print(f"         Actions: {info['total_actions']}")
    if info['current_task']:
        print(f"         Task: {info['current_task']}")
    print()


def setup_logging(verbose: bool):
    """Configure logging based on verbosity"""
    config = get_config()
    if verbose:
        config.logging.log_level = "DEBUG"
        config.logging.log_to_console = True
    else:
        config.logging.log_level = "INFO"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Desktop Automation Agent - Human-like activity simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                     Run indefinitely with default settings
    python main.py --duration 600      Run for 10 minutes
    python main.py --activity busy     Start in busy mode
    python main.py --no-vision         Disable screen awareness
    python main.py -v                  Enable verbose logging
        """
    )
    
    # Duration options
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=None,
        help="Run duration in seconds (default: indefinite)"
    )
    
    # Activity level
    parser.add_argument(
        "-a", "--activity",
        choices=["idle", "low", "normal", "busy", "intense"],
        default="normal",
        help="Initial activity level (default: normal)"
    )
    
    # Feature toggles
    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="Disable screen awareness/vision system"
    )
    
    parser.add_argument(
        "--no-tasks",
        action="store_true",
        help="Disable task-based behaviors"
    )
    
    parser.add_argument(
        "--no-markov",
        action="store_true",
        help="Use simple random decisions instead of Markov transitions"
    )
    
    # Behavior options
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Initial delay before starting (seconds, default: 3)"
    )
    
    # Logging options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress banner and status output"
    )
    
    # Config options
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save current configuration to config.json"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Load configuration from specified file"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = get_config()
    if args.config:
        config.load_from_file(args.config)
    
    # Apply command line overrides
    if args.no_vision:
        config.vision.enabled = False
    if args.no_tasks:
        config.tasks.enabled = False
    if args.no_markov:
        config.markov.enabled = False
    
    config.activity.default_level = args.activity
    
    # Setup logging
    setup_logging(args.verbose)
    logger = get_logger()
    
    # Save config if requested
    if args.save_config:
        save_config()
        print("Configuration saved to config.json")
        if not args.duration and not args.quiet:
            return
    
    # Print banner and controls
    if not args.quiet:
        print_banner()
        print_controls()
        
        print(f"[INFO] Starting in {args.delay:.1f} seconds...")
        print(f"[INFO] Activity level: {args.activity}")
        print(f"[INFO] Vision: {'enabled' if config.vision.enabled else 'disabled'}")
        print(f"[INFO] Tasks: {'enabled' if config.tasks.enabled else 'disabled'}")
        print(f"[INFO] Markov: {'enabled' if config.markov.enabled else 'disabled'}")
        
        if args.duration:
            print(f"[INFO] Duration: {args.duration} seconds")
        else:
            print(f"[INFO] Duration: Indefinite (use F8 to stop)")
        print()
    
    # Get agent
    agent = get_agent()
    
    # Set initial activity level
    from agent import ActivityLevel
    level_map = {
        "idle": ActivityLevel.IDLE,
        "low": ActivityLevel.LOW,
        "normal": ActivityLevel.NORMAL,
        "busy": ActivityLevel.BUSY,
        "intense": ActivityLevel.INTENSE,
    }
    agent.activity_manager.set_level(level_map[args.activity])
    
    # Start agent
    try:
        logger.info("=" * 50)
        logger.info(f"Agent starting at {datetime.now().isoformat()}")
        logger.info(f"Duration: {args.duration or 'indefinite'} seconds")
        logger.info("=" * 50)
        
        agent.start(initial_delay=args.delay)
        
        if args.duration:
            # Run for specified duration
            start_time = time.time()
            while (time.time() - start_time) < args.duration:
                if agent.status in [AgentStatus.STOPPED, AgentStatus.EMERGENCY_STOP]:
                    break
                time.sleep(1.0)
                
                # Periodic status update
                elapsed = time.time() - start_time
                if not args.quiet and int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    info = agent.get_status_info()
                    print(f"[{int(elapsed)}s] Actions: {info['total_actions']}, Level: {info['activity_level']}")
            
            agent.stop()
        else:
            # Run indefinitely until stopped
            while agent.status not in [AgentStatus.STOPPED, AgentStatus.EMERGENCY_STOP]:
                time.sleep(1.0)
        
        if not args.quiet:
            print("\n[INFO] Agent stopped")
            print_status(agent)
        
    except KeyboardInterrupt:
        print("\n[INFO] Keyboard interrupt received")
        agent.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        agent.emergency_stop()
        raise
    finally:
        logger.info("Agent shutdown complete")


if __name__ == "__main__":
    main()
