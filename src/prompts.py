"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CONTROL PANEL TASK PROMPTS                                  ║
║                                                                               ║
║  Prompts for control panel tasks - instructions for video models to          ║
║  operate controls to achieve the target state.                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Operate the control panel to match the target configuration. Adjust each control (switches, sliders, buttons, dials) to the correct state shown in the final image.",
        "Show how to configure the control panel to reach the target state. Animate the operation of each control that needs to be changed.",
        "Demonstrate the sequence of control operations needed to transform the panel from its current state to the target state. Move each control smoothly to its final position.",
        "Animate the control panel being configured to match the target state. Show each control being adjusted to the correct setting.",
    ],
    
    "switches": [
        "Flip the switches on the control panel to match the target configuration. Show each switch being toggled to its correct on/off state.",
        "Operate the toggle switches to achieve the target panel state. Animate each switch flipping to the correct position.",
        "Configure the switches to match the target state. Show the sequence of switch operations needed.",
    ],
    
    "slider": [
        "Adjust the slider to the target value shown in the final image. Show the slider moving smoothly from its current position to the target position.",
        "Move the slider control to match the target configuration. Animate the slider smoothly transitioning to the correct value.",
    ],
    
    "mixed": [
        "Operate all the controls on the panel to reach the target state. Show switches being flipped, sliders being adjusted, buttons being pressed, and dials being rotated as needed.",
        "Configure the control panel by operating all necessary controls. Demonstrate the sequence of operations: toggling switches, moving sliders, pressing buttons, and rotating dials to match the target state.",
    ],
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.
    
    Args:
        task_type: Type of task (key in PROMPTS dict)
        
    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
