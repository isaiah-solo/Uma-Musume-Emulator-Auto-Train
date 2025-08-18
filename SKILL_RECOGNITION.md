# Skill Recognition System

This document describes the skill recognition functionality that can detect and count `skill_up.png` icons on screen using ADB screen capture.

## Overview

The skill recognition system provides the following features:

- **🔍 Template Matching**: Uses OpenCV template matching to find skill_up.png icons
- **📱 ADB Integration**: Works with Android devices connected via ADB
- **🎯 De-duplication**: Removes overlapping detections automatically
- **🌟 Smart Filtering**: Distinguishes between available (bright) and unavailable (dark) skill buttons
- **🖼️ Debug Output**: Generates annotated images showing detected locations with availability status
- **⚡ Performance**: Fast detection with configurable confidence and brightness thresholds

## Files

- `utils/skill_recognizer.py` - Main recognition functions
- `test_skill_recognition.py` - Comprehensive test suite
- `demo_skill_recognition.py` - Interactive demo and examples

## Quick Start

### 1. Prerequisites

Make sure you have:
- Android device connected via ADB with USB debugging enabled
- Required dependencies installed: `pip install opencv-python pillow numpy`
- The `skill_up.png` template file in `assets/buttons/`

### 2. Basic Usage

```python
from utils.skill_recognizer import recognize_skill_up_locations

# Simple detection (filters dark buttons by default)
result = recognize_skill_up_locations()
print(f"Found {result['count']} available skill_up icons")

# With custom settings
result = recognize_skill_up_locations(
    confidence=0.8,              # Template matching confidence
    debug_output=True,           # Generate debug image
    overlap_threshold=0.5,       # De-duplication threshold
    filter_dark_buttons=True,    # Filter out dark/unavailable buttons
    brightness_threshold=100     # Minimum brightness for available buttons
)

# Disable dark button filtering (detect all buttons)
result = recognize_skill_up_locations(
    filter_dark_buttons=False
)
```

### 3. Run Demo

```bash
python demo_skill_recognition.py
```

### 4. Run Tests

```bash
# Unit tests only
python test_skill_recognition.py

# With integration tests (requires ADB)
python test_skill_recognition.py --integration

# Manual test with real device
python test_skill_recognition.py --manual
```

## API Reference

### `recognize_skill_up_locations(confidence=0.8, debug_output=True, overlap_threshold=0.5, filter_dark_buttons=True, brightness_threshold=100)`

Main function to detect skill_up icons on screen with smart filtering.

**Parameters:**
- `confidence` (float): Minimum confidence threshold (0.0-1.0)
- `debug_output` (bool): Generate debug image with bounding boxes
- `overlap_threshold` (float): Minimum overlap ratio to consider duplicates
- `filter_dark_buttons` (bool): Filter out dark/unavailable skill buttons
- `brightness_threshold` (int): Minimum average brightness for available buttons (0-255)

**Returns:**
```python
{
    'count': int,                        # Number of available detections
    'locations': [(x,y,w,h), ...],      # List of available button rectangles
    'debug_image_path': str,             # Path to debug image (if generated)
    'raw_matches': int,                  # Matches before de-duplication
    'deduplicated_matches': int,         # Matches after de-duplication
    'dark_buttons_filtered': int,        # Number of dark buttons filtered out
    'brightness_info': [{}],             # Detailed brightness analysis
    'confidence_used': float,            # Confidence threshold used
    'overlap_threshold_used': float,     # Overlap threshold used
    'brightness_threshold_used': int,    # Brightness threshold used
    'filter_dark_buttons_used': bool     # Whether filtering was applied
}
```

### `remove_overlapping_rectangles(rectangles, overlap_threshold=0.5)`

Utility function to remove overlapping detections.

**Parameters:**
- `rectangles`: List of (x, y, width, height) tuples
- `overlap_threshold`: Minimum overlap ratio to consider duplicates

**Returns:**
- List of non-overlapping rectangles

### `generate_debug_image(screenshot, locations, confidence)`

Generate debug image with bounding boxes around detections.

**Parameters:**
- `screenshot`: PIL Image of the screen
- `locations`: List of detection rectangles
- `confidence`: Confidence threshold used

**Returns:**
- Path to saved debug image

## Configuration

### Confidence Threshold

- **0.6-0.7**: More sensitive, may catch partial matches
- **0.8**: Recommended default, good balance
- **0.9+**: Very strict, only exact matches

### Overlap Threshold

- **0.3-0.4**: Aggressive de-duplication
- **0.5**: Recommended default
- **0.7+**: Conservative, keeps more detections

### Brightness Threshold

- **60-80**: Very permissive, includes dimmer buttons
- **100**: Recommended default, good balance
- **120-140**: Strict, only very bright buttons
- **Note**: Dark/grayed out buttons typically have brightness < 80

## Debug Output

When `debug_output=True`, the function generates an annotated image showing:

- 🟢 Green bounding boxes around available skill_up icons
- 🔴 Red bounding boxes around dark/unavailable skill_up icons (if detected)
- 🔢 Numbered labels with brightness values for each detection
- 📊 Summary information (count, confidence, filtering stats)
- 🏷️ Legend showing availability status (✓=Available, ✗=Dark)

Debug images are saved to `debug_images/debug_skill_up_<timestamp>.png`

## Example Output

```
Found 12 raw matches, 5 after de-duplication, 3 available (bright) buttons

Results:
  • Available buttons found: 3
  • Total detected (before filtering): 5
  • Dark buttons filtered out: 2
  • Raw matches (before de-duplication): 12
  • Confidence threshold used: 0.8
  • Brightness threshold used: 100
  • Available button locations:
    1. Position: (245, 120) Size: 50x30
    2. Position: (645, 120) Size: 50x30
    3. Position: (245, 320) Size: 50x30
  • Brightness analysis:
    (245, 120): 145.2 - ✓ Available
    (645, 120): 142.8 - ✓ Available
    (445, 120): 78.3 - ✗ Dark
    (245, 320): 138.1 - ✓ Available
    (645, 320): 65.7 - ✗ Dark

🖼️ Debug image saved: debug_images/debug_skill_up_1703123456.png
```

## Testing

The test suite includes:

### Unit Tests
- Rectangle overlap removal logic
- Parameter validation
- Error handling

### Integration Tests
- Real ADB screenshot testing
- Template matching accuracy
- Performance benchmarks

### Manual Tests
- Interactive testing with real device
- Visual verification of results
- Confidence level comparison

Run specific test categories:

```bash
# All tests
python test_skill_recognition.py --verbose

# Integration tests only
python test_skill_recognition.py --integration

# Manual interactive test
python test_skill_recognition.py --manual
```

## Troubleshooting

### Common Issues

**"Template not found" Error**
- Ensure `assets/buttons/skill_up.png` exists
- Check file permissions

**"No ADB devices connected" Error**
- Connect Android device via USB
- Enable USB debugging in Developer Options
- Run `adb devices` to verify connection

**Poor Detection Accuracy**
- Try different confidence levels (0.6-0.9)
- Ensure template image matches actual game graphics
- Check screen resolution and scaling

**Performance Issues**
- Disable debug output for faster detection
- Use smaller screen regions if possible
- Consider template image size optimization

### Debug Tips

1. **Use debug images** to visually verify detections
2. **Try different confidence levels** to find optimal threshold
3. **Check overlap threshold** if getting too many/few detections
4. **Monitor raw vs final counts** to understand de-duplication

## Integration with Main Project

To integrate with the main Uma Musume automation:

```python
# Add to your automation logic
from utils.skill_recognizer import recognize_skill_up_locations

def check_skill_opportunities():
    result = recognize_skill_up_locations(confidence=0.8)
    
    if result['count'] > 0:
        print(f"Found {result['count']} skill learning opportunities!")
        # Add your skill selection logic here
        return True
    
    return False
```

## Performance

Typical performance on 1080x1920 screenshots:
- **Detection time**: 0.1-0.5 seconds
- **Memory usage**: ~50MB peak
- **Template matching**: OpenCV optimized
- **De-duplication**: O(n²) where n = raw matches

## Future Enhancements

Potential improvements:
- Multi-template support for different skill types
- Region-based detection for better performance
- Machine learning-based detection
- Real-time monitoring capabilities
- ROI (Region of Interest) optimization