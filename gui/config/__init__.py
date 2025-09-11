"""
Config tabs for Uma Musume Auto-Train Bot GUI

This package contains modular configuration tabs that can be imported
and used by the main ConfigPanel class.
"""

try:
    from .main_tab import MainTab
    from .training_tab import TrainingTab
    from .racing_tab import RacingTab
    from .event_tab import EventTab
    from .skill_tab import SkillTab
    from .restart_tab import RestartTab
    from .others_tab import OthersTab
    
    __all__ = [
        'MainTab',
        'TrainingTab', 
        'RacingTab',
        'EventTab',
        'SkillTab',
        'RestartTab',
        'OthersTab'
    ]
    
except ImportError as e:
    # If import fails, the main config panel will fall back to inline methods
    print(f"Warning: Could not import config tabs: {e}")
    __all__ = []
