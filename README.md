# Control Panel Task Data Generator 🎛️

A data generator for creating control panel reasoning tasks. Generates tasks where video models must operate control panels with switches, sliders, buttons, and dials to achieve target configurations.

Repository: [O_54_control_panel_data_generator](https://github.com/vm-dataset/O_54_control_panel_data_generator)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/vm-dataset/O_54_control_panel_data_generator.git
cd O_54_control_panel_data_generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate tasks
python examples/generate.py --num-samples 50
```

---

## 📁 Structure

```
control_panel_task-data-generator/
├── core/                    # ✅ KEEP: Standard utilities
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # ⚠️ CUSTOMIZE: Your task logic
│   ├── generator.py        # Your task generator
│   ├── prompts.py          # Your prompt templates
│   └── config.py           # Your configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
```

---

## 📦 Output Format

Every generator produces:

```
data/questions/{domain}_task/{task_id}/
├── first_frame.png          # Initial state (REQUIRED)
├── final_frame.png          # Goal state (or goal.txt)
├── prompt.txt               # Instructions (REQUIRED)
└── ground_truth.mp4         # Solution video (OPTIONAL)
```

---

## 🎨 Customization (3 Files to Modify)

### Control Panel Task

This generator creates control panel tasks with various control types:

- **Switches**: Toggle switches that can be on/off
- **Sliders**: Linear sliders with values from 0-100
- **Buttons**: Press buttons that activate when pressed
- **Dials**: Rotating dials with 0-360 degree angles

Each task shows:
1. **Initial state**: Control panel with controls in starting positions
2. **Target state**: The desired configuration to achieve
3. **Video**: Animation showing the operations needed to reach the target

### Configuration

Key parameters in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    domain: str = Field(default="control_panel")
    image_size: tuple[int, int] = Field(default=(512, 512))
    
    # Task-specific settings
    num_controls: int = Field(default=3, description="Number of controls (2-5)")
    control_types: list[str] = Field(
        default=["switch", "slider", "button"],
        description="Available control types"
    )
    panel_bg_color: tuple[int, int, int] = Field(
        default=(45, 45, 55),
        description="Panel background color"
    )
```

**Single entry point:** `python examples/generate.py --num-samples 50`