# Menu System Architecture

## Composite Pattern Structure

```mermaid
classDiagram
    class Menu {
        <<abstract>>
        +String name
        +SubMenu parent
        +execute()* Menu
        +get_display_text()* String
        +get_parent() SubMenu
        +set_parent(parent)
    }
    
    class MenuItem {
        +Callable action
        +execute() Menu
        +get_display_text() String
    }
    
    class SubMenu {
        +List~Menu~ children
        +int current_index
        +add(menu) SubMenu
        +remove(menu) SubMenu
        +get_child(index) Menu
        +get_current_child() Menu
        +next()
        +previous()
        +execute() Menu
        +get_display_text() String
    }
    
    class BackMenuItem {
        +execute() Menu
    }
    
    Menu <|-- MenuItem : implements
    Menu <|-- SubMenu : implements
    MenuItem <|-- BackMenuItem : extends
    SubMenu o-- Menu : contains
```

## Component Relationships

```mermaid
graph TD
    A[Menu - Component] --> B[MenuItem - Leaf]
    A --> C[SubMenu - Composite]
    B --> D[BackMenuItem - Special Leaf]
    C --> E[Contains Menu objects]
    E --> B
    E --> C
```

## Chess Menu Hierarchy

```mermaid
graph TD
    Root[Main Menu]
    
    Root --> PvR[Player vs Robot]
    Root --> RvR[Robot vs Robot]
    
    PvR --> PC[Player Colour]
    PvR --> RL[Robot Level]
    PvR --> SG1[Start Game]
    PvR --> B1[Back]
    
    PC --> White[White]
    PC --> Black[Black]
    PC --> B2[Back]
    
    RL --> L1[Level 1]
    RL --> L2[Level 2]
    RL --> Ldots[...]
    RL --> L20[Level 20]
    RL --> B3[Back]
    
    RvR --> R1L[Robot 1 Level]
    RvR --> R2L[Robot 2 Level]
    RvR --> SG2[Start Game]
    RvR --> B4[Back]
    
    R1L --> R1L1[Level 1]
    R1L --> R1Ldots[...]
    R1L --> R1L20[Level 20]
    R1L --> B5[Back]
    
    R2L --> R2L1[Level 1]
    R2L --> R2Ldots[...]
    R2L --> R2L20[Level 20]
    R2L --> B6[Back]
    
    style Root fill:#e1f5ff
    style PvR fill:#fff4e1
    style RvR fill:#fff4e1
    style PC fill:#e8f5e9
    style RL fill:#e8f5e9
    style R1L fill:#e8f5e9
    style R2L fill:#e8f5e9
    style SG1 fill:#ffebee
    style SG2 fill:#ffebee
```

## System Integration

```mermaid
graph LR
    A[Rotary Encoder] -->|Rotation Events| B[MenuNavigator]
    C[Switch Button] -->|Press Events| B
    B -->|Updates| D[LCD Display]
    B -->|Navigates| E[Menu Tree]
    E -->|Executes| F[Game Logic]
    
    style A fill:#e3f2fd
    style C fill:#e3f2fd
    style D fill:#f3e5f5
    style B fill:#fff9c4
    style E fill:#e8f5e9
    style F fill:#ffebee
```

## Navigation Flow

```mermaid
stateDiagram-v2
    [*] --> MainMenu
    
    MainMenu --> PlayerVsRobot: Select & Press
    MainMenu --> RobotVsRobot: Select & Press
    
    PlayerVsRobot --> PlayerColour: Select & Press
    PlayerVsRobot --> RobotLevel: Select & Press
    PlayerVsRobot --> StartGame1: Select & Press
    PlayerVsRobot --> MainMenu: Back
    
    PlayerColour --> PlayerVsRobot: Back
    RobotLevel --> PlayerVsRobot: Back
    
    RobotVsRobot --> Robot1Level: Select & Press
    RobotVsRobot --> Robot2Level: Select & Press
    RobotVsRobot --> StartGame2: Select & Press
    RobotVsRobot --> MainMenu: Back
    
    Robot1Level --> RobotVsRobot: Back
    Robot2Level --> RobotVsRobot: Back
    
    StartGame1 --> [*]: Game Starts
    StartGame2 --> [*]: Game Starts
    
    note right of MainMenu
        Rotate: Cycle options
        Press: Select option
    end note
```

## LCD Display Format

```
┌────────────────┐
│ Main Menu      │  ← Line 1: Current menu title
│ > Option 1 1/3 │  ← Line 2: > Current selection + position
└────────────────┘
     16 chars
```

### Display Components:
- **Line 1**: Current menu/submenu name (max 16 chars)
- **Line 2**: 
  - `>` : Selection indicator (1 char)
  - ` ` : Space (1 char)
  - Item name (variable, truncated if needed)
  - ` ` : Space (1 char)
  - `X/Y` : Position indicator (variable length)

## Event Flow

```mermaid
sequenceDiagram
    participant User
    participant Encoder
    participant Navigator
    participant Menu
    participant LCD
    
    User->>Encoder: Rotate clockwise
    Encoder->>Navigator: when_rotated()
    Navigator->>Menu: next()
    Menu->>Menu: current_index++
    Navigator->>LCD: update_display()
    LCD-->>User: Shows next item
    
    User->>Encoder: Press button
    Encoder->>Navigator: when_pressed()
    Navigator->>Menu: execute()
    Menu->>Menu: Get current child
    Menu->>Menu: Execute child
    Menu-->>Navigator: Return next menu
    Navigator->>Navigator: current_menu = next_menu
    Navigator->>LCD: update_display()
    LCD-->>User: Shows new menu
```

## Code Organization

```
display_and_input/
│
├── Core Pattern Implementation
│   └── menu.py
│       ├── Menu (Component)
│       ├── MenuItem (Leaf)
│       ├── SubMenu (Composite)
│       └── BackMenuItem (Special Leaf)
│
├── Hardware Integration
│   ├── LCD.py (Display driver)
│   └── menu_navigator.py (Integration layer)
│
├── Application Layer
│   └── chess_menu.py (Chess-specific menu builder)
│
└── Testing & Documentation
    ├── menu_example.py (Test file)
    ├── README.md (User documentation)
    └── ARCHITECTURE.md (This file)
```

## Key Design Decisions

### 1. Composite Pattern
- **Why**: Natural fit for hierarchical menu structure
- **Benefit**: Uniform treatment of items and submenus
- **Trade-off**: Slightly more complex than simple list-based menu

### 2. Insertion Order Preservation
- **Implementation**: Python list maintains insertion order
- **Benefit**: Predictable menu item ordering
- **Alternative**: Could use explicit ordering numbers

### 3. Parent References
- **Why**: Enable "Back" navigation
- **Benefit**: Easy to navigate up the tree
- **Trade-off**: Bidirectional references require careful management

### 4. Callback-based Actions
- **Why**: Flexible action execution
- **Benefit**: Decouple menu structure from game logic
- **Alternative**: Could use command pattern for undo/redo

### 5. Two-line LCD Display
- **Line 1**: Context (current menu)
- **Line 2**: Selection (current item + position)
- **Benefit**: User always knows where they are
- **Limitation**: Long item names must be truncated

## Extension Points

### Adding New Menu Item Types

```python
class ToggleMenuItem(MenuItem):
    """Example: Menu item with on/off state"""
    def __init__(self, name, toggle_action):
        super().__init__(name, toggle_action)
        self.state = False
    
    def execute(self):
        self.state = not self.state
        if self.action:
            self.action(self.state)
        return None
    
    def get_display_text(self):
        return f"{self.name} [{'ON' if self.state else 'OFF'}]"
```

### Custom Display Formatting

```python
class IconMenuItem(MenuItem):
    """Example: Menu item with custom icon"""
    def __init__(self, name, action, icon="•"):
        super().__init__(name, action)
        self.icon = icon
    
    def get_display_text(self):
        return f"{self.icon} {self.name}"
```

### Validation/Conditional Items

```python
class ConditionalMenuItem(MenuItem):
    """Example: Menu item that can be disabled"""
    def __init__(self, name, action, enabled_func):
        super().__init__(name, action)
        self.enabled_func = enabled_func
    
    def execute(self):
        if self.enabled_func():
            return super().execute()
        return None
    
    def get_display_text(self):
        if self.enabled_func():
            return self.name
        return f"{self.name} (disabled)"
```
