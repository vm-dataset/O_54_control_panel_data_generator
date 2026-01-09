"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CONTROL PANEL TASK GENERATOR                              ║
║                                                                               ║
║  Generates control panel tasks where video models must operate controls       ║
║  (switches, sliders, buttons, dials) to achieve a target state.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class ControlPanel:
    """Represents a control panel with various controls."""
    
    def __init__(self):
        self.controls: List[Dict] = []
    
    def add_control(self, control_type: str, position: Tuple[int, int], 
                    size: Tuple[int, int], initial_state: any, 
                    target_state: any, label: str = ""):
        """Add a control to the panel."""
        self.controls.append({
            "type": control_type,
            "position": position,
            "size": size,
            "initial_state": initial_state,
            "target_state": target_state,
            "label": label
        })


class TaskGenerator(BaseGenerator):
    """
    Control Panel Task Generator.
    
    Generates tasks where a control panel with various controls (switches,
    sliders, buttons, dials) needs to be operated to reach a target state.
    """
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)
        
        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one control panel task pair."""
        
        # Generate panel configuration
        panel_data = self._generate_panel_data()
        
        # Render images
        first_image = self._render_panel(panel_data, render_target=False)
        final_image = self._render_panel(panel_data, render_target=True)
        
        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, panel_data)
        
        # Select prompt
        prompt = get_prompt(panel_data.get("task_type", "default"))
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    #  PANEL GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_panel_data(self) -> Dict:
        """Generate a control panel configuration."""
        num_controls = self.config.num_controls
        # Ensure valid range
        num_controls = max(2, min(5, num_controls))
        
        panel = ControlPanel()
        width, height = self.config.image_size
        margin = 40
        panel_width = width - 2 * margin
        panel_height = height - 2 * margin
        
        # Available control types
        available_types = self.config.control_types.copy()
        
        # Determine layout (grid or vertical)
        use_grid = num_controls >= 4
        if use_grid:
            cols = 2
            rows = (num_controls + 1) // 2
            cell_width = panel_width // cols
            cell_height = panel_height // rows
        else:
            cols = 1
            rows = num_controls
            cell_width = panel_width
            cell_height = panel_height // rows
        
        control_types_used = []
        for i in range(num_controls):
            # Select control type
            if not available_types:
                available_types = self.config.control_types.copy()
            ctype = random.choice(available_types)
            available_types.remove(ctype)
            control_types_used.append(ctype)
            
            # Calculate position
            if use_grid:
                col = i % cols
                row = i // cols
            else:
                col = 0
                row = i
            
            x = margin + col * cell_width + cell_width // 2
            y = margin + row * cell_height + cell_height // 2
            
            # Control size - ensure reasonable minimums
            control_w = max(80, min(120, cell_width - 40))
            control_h = max(60, min(80, cell_height - 40))
            
            # Generate control states
            initial_state, target_state, label = self._generate_control_states(ctype)
            
            panel.add_control(
                control_type=ctype,
                position=(x, y),
                size=(control_w, control_h),
                initial_state=initial_state,
                target_state=target_state,
                label=label
            )
        
        # Determine task type for prompts
        task_type = "default"
        if all(ct == "switch" for ct in control_types_used):
            task_type = "switches"
        elif "slider" in control_types_used and len(control_types_used) == 1:
            task_type = "slider"
        
        return {
            "panel": panel,
            "task_type": task_type,
            "controls": panel.controls
        }
    
    def _generate_control_states(self, control_type: str) -> Tuple[any, any, str]:
        """Generate initial and target states for a control."""
        if control_type == "switch":
            initial = random.choice([True, False])
            target = not initial
            label = random.choice(["Power", "Mode", "Enable", "State"])
            return initial, target, label
        
        elif control_type == "slider":
            initial = random.randint(0, 100)
            target = random.randint(0, 100)
            # Ensure they're different
            while target == initial:
                target = random.randint(0, 100)
            label = random.choice(["Volume", "Speed", "Level", "Value"])
            return initial, target, label
        
        elif control_type == "button":
            # Button is either pressed or not pressed (but we'll show state change)
            initial = False
            target = True
            label = random.choice(["Start", "Activate", "Run", "Execute"])
            return initial, target, label
        
        elif control_type == "dial":
            initial = random.randint(0, 360)
            target = random.randint(0, 360)
            while abs(target - initial) < 30:  # Ensure meaningful change
                target = random.randint(0, 360)
            label = random.choice(["Rotation", "Angle", "Position"])
            return initial, target, label
        
        else:
            # Default: switch-like
            return False, True, "Control"
    
    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════
    
    def _render_panel(self, panel_data: Dict, render_target: bool = False) -> Image.Image:
        """Render the control panel in initial or target state."""
        panel = panel_data["panel"]
        width, height = self.config.image_size
        
        # Create image with panel background
        img = Image.new('RGB', (width, height), self.config.panel_bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw panel frame/border
        margin = 20
        frame_color = (80, 80, 90)
        draw.rectangle(
            [margin, margin, width - margin, height - margin],
            outline=frame_color,
            width=3
        )
        
        # Draw each control
        for control in panel.controls:
            state = control["target_state"] if render_target else control["initial_state"]
            # Get font for this control (will use internal fallback if None)
            font_size = max(12, min(control["size"][0], control["size"][1]) // 6)
            font = self._get_font(font_size)
            self._draw_control(
                draw, control, state, control["label"], font
            )
        
        return img
    
    def _get_font(self, size: int):
        """Get a font, trying multiple fallbacks."""
        # Try common font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
        
        # Fallback to default font
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def _draw_control(self, draw: ImageDraw.Draw, control: Dict, 
                     state: any, label: str, font=None):
        """Draw a single control."""
        ctype = control["type"]
        x, y = control["position"]
        w, h = control["size"]
        
        # Try to get a font if not provided
        if font is None:
            font_size = max(12, min(w, h) // 6)
            font = self._get_font(font_size)
        
        if ctype == "switch":
            self._draw_switch(draw, x, y, w, h, state, label, font)
        elif ctype == "slider":
            self._draw_slider(draw, x, y, w, h, state, label, font)
        elif ctype == "button":
            self._draw_button(draw, x, y, w, h, state, label, font)
        elif ctype == "dial":
            self._draw_dial(draw, x, y, w, h, state, label, font)
    
    def _draw_switch(self, draw: ImageDraw.Draw, x: int, y: int, 
                    w: int, h: int, is_on: bool, label: str, font):
        """Draw a toggle switch."""
        # Switch background (rail)
        rail_h = h // 3
        rail_y = y - rail_h // 2
        rail_color = (60, 60, 70) if not is_on else (60, 150, 80)
        draw.rounded_rectangle(
            [x - w // 2, rail_y, x + w // 2, rail_y + rail_h],
            radius=rail_h // 2,
            fill=rail_color
        )
        
        # Switch toggle (circle)
        toggle_r = max(5, rail_h * 0.7)  # Ensure minimum radius
        toggle_x = x + int((w // 2 - toggle_r * 1.2)) if is_on else x - int((w // 2 - toggle_r * 1.2))
        toggle_y = y
        toggle_color = (220, 220, 220)
        draw.ellipse(
            [toggle_x - toggle_r, toggle_y - toggle_r,
             toggle_x + toggle_r, toggle_y + toggle_r],
            fill=toggle_color,
            outline=(40, 40, 50),
            width=2
        )
        
        # Label
        if font and label:
            bbox = draw.textbbox((0, 0), label, font=font)
            label_w = bbox[2] - bbox[0]
            draw.text((x - label_w // 2, y - h // 2 + 5), label, 
                     fill=(200, 200, 200), font=font)
    
    def _draw_slider(self, draw: ImageDraw.Draw, x: int, y: int,
                    w: int, h: int, value: int, label: str, font):
        """Draw a slider control."""
        # Slider track
        track_h = h // 8
        track_y = y
        track_color = (60, 60, 70)
        draw.rounded_rectangle(
            [x - w // 2, track_y - track_h // 2,
             x + w // 2, track_y + track_h // 2],
            radius=track_h // 2,
            fill=track_color
        )
        
        # Filled portion (progress)
        fill_w = int((w - track_h) * value / 100)
        fill_color = (70, 130, 200)
        if fill_w > 0:
            draw.rounded_rectangle(
                [x - w // 2, track_y - track_h // 2,
                 x - w // 2 + fill_w, track_y + track_h // 2],
                radius=track_h // 2,
                fill=fill_color
            )
        
        # Slider thumb
        thumb_r = max(5, track_h * 1.2)  # Ensure minimum radius
        # Clamp value to valid range
        value = max(0, min(100, value))
        thumb_x = x - w // 2 + int((w - track_h) * value / 100)
        thumb_y = y
        draw.ellipse(
            [thumb_x - thumb_r, thumb_y - thumb_r,
             thumb_x + thumb_r, thumb_y + thumb_r],
            fill=(220, 220, 220),
            outline=(40, 40, 50),
            width=2
        )
        
        # Label
        if font and label:
            bbox = draw.textbbox((0, 0), label, font=font)
            label_w = bbox[2] - bbox[0]
            draw.text((x - label_w // 2, y - h // 2 + 5), label,
                     fill=(200, 200, 200), font=font)
        
        # Value text
        if font:
            value_text = f"{value}%"
            bbox = draw.textbbox((0, 0), value_text, font=font)
            value_w = bbox[2] - bbox[0]
            draw.text((x - value_w // 2, y + h // 2 - 20), value_text,
                     fill=(180, 180, 180), font=font)
    
    def _draw_button(self, draw: ImageDraw.Draw, x: int, y: int,
                    w: int, h: int, is_pressed: bool, label: str, font):
        """Draw a button control."""
        # Button shape
        button_w = min(w, h * 1.5)
        button_h = h // 2
        
        if is_pressed:
            button_color = (80, 150, 80)
            shadow_offset = 1
        else:
            button_color = (100, 120, 150)
            shadow_offset = 3
        
        # Shadow
        shadow_color = (20, 20, 25)
        draw.rounded_rectangle(
            [x - button_w // 2 + shadow_offset, y + shadow_offset,
             x + button_w // 2 + shadow_offset, y + button_h + shadow_offset],
            radius=button_h // 4,
            fill=shadow_color
        )
        
        # Button
        draw.rounded_rectangle(
            [x - button_w // 2, y,
             x + button_w // 2, y + button_h],
            radius=button_h // 4,
            fill=button_color,
            outline=(60, 60, 70),
            width=2
        )
        
        # Label
        if font and label:
            bbox = draw.textbbox((0, 0), label, font=font)
            label_w = bbox[2] - bbox[0]
            label_h = bbox[3] - bbox[1]
            draw.text(
                (x - label_w // 2, y + (button_h - label_h) // 2),
                label,
                fill=(255, 255, 255),
                font=font
            )
    
    def _draw_dial(self, draw: ImageDraw.Draw, x: int, y: int,
                  w: int, h: int, angle: int, label: str, font):
        """Draw a dial/knob control."""
        # Dial body (circle)
        dial_r = max(15, min(w, h) // 3)  # Ensure minimum radius
        # Normalize angle to [0, 360)
        angle = angle % 360
        dial_color = (80, 80, 90)
        draw.ellipse(
            [x - dial_r, y - dial_r,
             x + dial_r, y + dial_r],
            fill=dial_color,
            outline=(60, 60, 70),
            width=3
        )
        
        # Dial indicator (line/pointer)
        angle_rad = math.radians(angle - 90)  # 0° at top
        indicator_len = dial_r * 0.7
        end_x = x + indicator_len * math.cos(angle_rad)
        end_y = y + indicator_len * math.sin(angle_rad)
        draw.line(
            [(x, y), (end_x, end_y)],
            fill=(255, 200, 50),
            width=4
        )
        
        # Center dot
        center_r = dial_r // 8
        draw.ellipse(
            [x - center_r, y - center_r,
             x + center_r, y + center_r],
            fill=(200, 200, 200)
        )
        
        # Label
        if font and label:
            bbox = draw.textbbox((0, 0), label, font=font)
            label_w = bbox[2] - bbox[0]
            draw.text((x - label_w // 2, y - h // 2 + 5), label,
                     fill=(200, 200, 200), font=font)
    
    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_video(
        self,
        first_image: Image.Image,
        final_image: Image.Image,
        task_id: str,
        panel_data: Dict
    ) -> Optional[str]:
        """Generate ground truth video showing control operations."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames showing controls changing
        frames = self._create_panel_animation_frames(panel_data)
        
        result = self.video_generator.create_video_from_frames(
            frames,
            video_path
        )
        
        return str(result) if result else None
    
    def _create_panel_animation_frames(
        self,
        panel_data: Dict,
        hold_frames: int = 5,
        transition_frames: int = 30
    ) -> List[Image.Image]:
        """Create animation frames showing controls transitioning."""
        panel = panel_data["panel"]
        frames = []
        width, height = self.config.image_size
        
        # Initial state
        initial_img = self._render_panel(panel_data, render_target=False)
        for _ in range(hold_frames):
            frames.append(initial_img.copy())
        
        # Transition frames - interpolate between initial and target states
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            
            # Create interpolated frame
            img = Image.new('RGB', (width, height), self.config.panel_bg_color)
            draw = ImageDraw.Draw(img)
            
            # Draw panel frame
            margin = 20
            frame_color = (80, 80, 90)
            draw.rectangle(
                [margin, margin, width - margin, height - margin],
                outline=frame_color,
                width=3
            )
            
            # Draw each control with interpolated state
            for control in panel.controls:
                initial_state = control["initial_state"]
                target_state = control["target_state"]
                interpolated_state = self._interpolate_control_state(
                    control["type"], initial_state, target_state, progress
                )
                # Get font for this control (will use internal fallback if None)
                font_size = max(12, min(control["size"][0], control["size"][1]) // 6)
                font = self._get_font(font_size)
                self._draw_control(draw, control, interpolated_state, control["label"], font)
            
            frames.append(img)
        
        # Final state
        final_img = self._render_panel(panel_data, render_target=True)
        for _ in range(hold_frames):
            frames.append(final_img.copy())
        
        return frames
    
    def _interpolate_control_state(self, control_type: str, initial: any,
                                  target: any, progress: float) -> any:
        """Interpolate between initial and target states."""
        if control_type == "switch":
            # Switch flips at 50% progress
            return target if progress >= 0.5 else initial
        
        elif control_type == "slider":
            # Linear interpolation for slider
            return int(initial + (target - initial) * progress)
        
        elif control_type == "button":
            # Button activates at 50% progress
            return target if progress >= 0.5 else initial
        
        elif control_type == "dial":
            # Circular interpolation for dial (handle wrap-around)
            diff = target - initial
            # Normalize to [-180, 180] range
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            result = initial + diff * progress
            # Normalize to [0, 360]
            result = result % 360
            return int(result)
        
        else:
            return target if progress >= 0.5 else initial
