# Uma Musume Auto-Train Bot - New GUI

A completely redesigned, modern GUI application for the Uma Musume Auto-Train Bot with a dark theme and the exact layout you requested.

## 🎨 **Design Features**

### **Dark Theme**
- **Professional dark color scheme** with gray tones
- **High contrast** for better readability
- **Modern styling** with rounded corners and clean lines

### **Exact Layout Match**
- **Config Panel** (Top Left): Organized configuration with tabbed sections
- **Status Panel** (Bottom Left): Real-time bot status display
- **Log Panel** (Right Side): Comprehensive logging with controls

## 🏗️ **Architecture**

### **Modular Design**
```
gui/
├── __init__.py              # Package initialization
├── main_window.py           # Main application window
├── config_panel.py          # Configuration management
├── status_panel.py          # Real-time status display
├── log_panel.py             # Logging and bot control
├── bot_controller.py        # Bot integration and control
├── launch_gui.py            # Application launcher
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### **Component Structure**
- **MainWindow**: Orchestrates all components and manages the overall application
- **ConfigPanel**: Handles all configuration with organized tabs
- **StatusPanel**: Displays real-time bot status and statistics
- **LogPanel**: Manages logging and bot control buttons
- **BotController**: Integrates with actual bot scripts and provides status updates

## 🚀 **Features**

### **Configuration Management**
- **Main Tab**: ADB configuration (device address, paths, timeouts)
- **Training Tab**: Stats priority, mood settings, failure rates, energy thresholds
- **Racing Tab**: G1 race prioritization, strategy selection, retry settings
- **Event Tab**: Good/bad choice management
- **Skill Tab**: Skill point management and auto-purchase settings
- **Others Tab**: Debug mode and additional settings

### **Real-time Status Display**
- **Year**: Current game year
- **Energy**: Current energy percentage
- **Turn**: Current turn number
- **Mood**: Current character mood
- **Goal**: Visual indicator (✅/❌) for goal completion
- **Stats**: Current SPD, STA, PWR, GUTS, WIT values

### **Advanced Logging**
- **Color-coded logs** by message type (info, warning, error, success, debug)
- **Real-time updates** from bot operations
- **Auto-scroll toggle** for log management
- **Log export** functionality

### **Bot Control**
- **START/STOP button** with visual feedback
- **Status monitoring** with live updates
- **Integration** with existing bot scripts
- **Safe shutdown** with confirmation dialogs

## 🛠️ **Installation & Usage**

### **Quick Start**
1. Navigate to your bot directory
2. Run the launcher:
   ```bash
   python gui/launch_gui.py
   ```

### **Requirements**
- **Python 3.7+** with tkinter support
- **No additional packages** required (uses only standard library)
- **Existing bot files** in the same directory

## 📋 **Configuration Sections**

### **Main Configuration**
- Device Address: `127.0.0.1:7555`
- ADB Path: `adb`
- Screenshot Timeout: 5 seconds
- Input Delay: 0.5 seconds
- Connection Timeout: 10 seconds

### **Training Configuration**
- **Stats Priority**: Drag-and-drop reordering of SPD, STA, WIT, PWR, GUTS
- **Minimum Mood**: GREAT, GOOD, NORMAL, BAD, AWFUL
- **Maximum Failure Rate**: 0-100%
- **Minimum Energy**: 0-100%
- **Race Fallback**: Enable/disable racing when training is poor
- **Training Scores**: Configurable scoring for different support card types
- **Stat Caps**: Individual caps for each stat type

### **Racing Configuration**
- **G1 Race Prioritization**: Enable for fan farming
- **Strategy Selection**: FRONT, PACE, LATE, END
- **Race Retry**: Enable clock-based retry system

### **Event Configuration**
- **Good Choices**: Manage positive event choices
- **Bad Choices**: Manage negative event choices
- **Drag-and-drop** reordering for priority

### **Skill Configuration**
- **Skill Point Check**: Enable automatic skill management
- **Skill Point Cap**: Maximum skill points before auto-purchase
- **Purchase Mode**: Auto or Manual
- **Skill Templates**: Configurable skill priority lists
- **Gold Skill Relationships**: Base skill to gold skill mappings

## 🔧 **Technical Details**

### **Theme System**
- **Dark color palette** with professional appearance
- **Consistent styling** across all components
- **High contrast** for accessibility
- **Modern widgets** with rounded corners

### **Status Integration**
- **Real-time updates** from bot scripts
- **Fallback simulation** when bot modules unavailable
- **Thread-safe** status updates
- **Error handling** for robust operation

### **Configuration Persistence**
- **JSON-based** configuration storage
- **Automatic saving** of all changes
- **Validation** of configuration values
- **Default values** for missing settings

## 🎯 **Usage Workflow**

1. **Launch GUI**: Run `python gui/launch_gui.py`
2. **Configure Settings**: Use the tabbed configuration panel
3. **Start Bot**: Click START button in log panel
4. **Monitor Progress**: Watch real-time status updates
5. **View Logs**: Monitor bot operations in the log panel
6. **Stop Bot**: Click STOP button when finished

## 🚨 **Troubleshooting**

### **Common Issues**
- **GUI won't start**: Check Python version and tkinter availability
- **Configuration errors**: Verify JSON syntax and file permissions
- **Bot connection issues**: Ensure ADB is properly configured
- **Status not updating**: Check if bot modules are accessible

### **Getting Help**
1. Check the log panel for error messages
2. Verify configuration settings
3. Ensure all dependencies are available
4. Check ADB connection status

## 🔮 **Future Enhancements**

- **Drag-and-drop** for stat priority reordering
- **Advanced skill editor** with visual interface
- **Event choice editor** with drag-and-drop
- **Configuration import/export** functionality
- **Plugin system** for extensibility
- **Multi-language** support
- **Theme customization** options

## 🤝 **Contributing**

The modular design makes it easy to:
- Add new configuration sections
- Enhance status display features
- Improve logging capabilities
- Add new bot integration features
- Customize themes and styling

## 📄 **License**

This GUI application is part of the Uma Musume Auto-Train Bot project.
Please refer to the main project license for terms and conditions.

---

**Happy Training! 🏇**

*This redesigned GUI provides a modern, professional interface for managing your Uma Musume bot automation.*
