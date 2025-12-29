# WPF PowerShell Template

A reusable template for building Windows Presentation Foundation (WPF) applications using PowerShell. This template provides a foundation for creating professional desktop utilities with modern graphical interfaces, tabbed navigation, and JSON-based configuration.

## Overview

This template serves as a starting point for developing WPF-based PowerShell utilities. It demonstrates best practices for structuring WPF applications, managing XAML layouts, organizing PowerShell functions, and implementing JSON-driven data management. The template is designed to be easily customizable and extended for various utility applications.

## Template Structure

### Core Components

- **Main.ps1**: Entry point script that initializes the WPF application, loads assemblies, and manages the application lifecycle
- **MainWindow.xaml**: Primary application window with TabControl container for organizing multiple functional areas
- **Tab XAML Files**: Individual tab definitions (WelcomeTab, Example1Tab, Example2Tab, Example3Tab) demonstrating different UI patterns
- **Function Scripts**: PowerShell modules containing business logic and event handlers
- **JSON Configuration**: Data-driven configuration files for templates and executions

### Directory Organization

```
WPF_Powershell_Template/
├── Scripts/
│   ├── Main.ps1                    # Application entry point
│   ├── MainWindow.xaml             # Main window definition
│   ├── WelcomeTab.xaml             # Welcome/home tab
│   ├── Example1Tab.xaml            # Example tab with DataGrids
│   ├── Example2Tab.xaml            # Additional example tab
│   ├── Example3Tab.xaml            # Additional example tab
│   ├── Example1Functions.ps1       # PowerShell functions for Example1
│   └── xCreate-EXE-and-Shortcut.bat # Utility for creating executables
├── JSON/
│   ├── Example1_Templates.json     # Template definitions
│   └── Example1_Executions.json    # Execution history/data
└── Welcome_Notes.txt               # Release notes and updates
```

## Key Features

### WPF Application Framework

- **Single-Threaded Apartment (STA)**: Automatic STA mode detection and initialization for WPF compatibility
- **Assembly Loading**: Automatic loading of required WPF assemblies (PresentationCore, PresentationFramework, WindowsBase, System.Xaml)
- **Path Resolution**: Robust base directory resolution supporting multiple execution contexts (script, compiled EXE, shortcut)
- **Modular XAML Loading**: Dynamic XAML loading with error handling and validation

### User Interface Patterns

- **Tabbed Navigation**: TabControl-based interface for organizing multiple functional areas
- **DataGrid Integration**: Examples of binding PowerShell data to WPF DataGrids
- **Button Actions**: Event handler patterns for button clicks and user interactions
- **Image Assets**: Support for icons and images in the UI
- **Responsive Layout**: Grid-based layouts with proper row/column definitions

### Data Management

- **JSON Configuration**: External JSON files for storing templates, configurations, and data
- **Dynamic Data Binding**: PowerShell objects bound to WPF controls
- **CRUD Operations**: Examples of Create, Read, Update, Delete operations on JSON data
- **File System Integration**: Opening folders, launching external applications

### Code Organization

- **Separation of Concerns**: XAML for UI, PowerShell for logic, JSON for data
- **Function Modules**: Reusable PowerShell functions organized in separate files
- **Event Handlers**: Centralized event handling for UI controls
- **Error Handling**: Try-catch blocks and error logging throughout

## Example Implementations

### Example 1: Template Management

Demonstrates a dual-DataGrid interface for managing templates and executions:
- **Templates Grid**: Displays available templates with ID, name, description, and file path
- **Executions Grid**: Shows execution history with status, timestamps, and results
- **Button Actions**: Open folders, refresh data, add/edit/delete items
- **JSON Integration**: Load and save data from JSON configuration files

### Example 2 & 3: Additional Patterns

Placeholder tabs for implementing additional functionality:
- Custom UI layouts
- Different data binding scenarios
- Alternative control patterns

## Customization Guide

### Creating a New Utility

1. **Clone the Template**: Copy the entire directory structure
2. **Update MainWindow.xaml**: Modify window title, size, and icon
3. **Create Custom Tabs**: Design new XAML tab files for your functionality
4. **Implement Functions**: Write PowerShell functions for business logic
5. **Configure JSON**: Define data structures in JSON files
6. **Update Main.ps1**: Register new tabs and function files
7. **Test and Deploy**: Run Main.ps1 to test, use batch file to create EXE

### Adding a New Tab

1. Create a new XAML file in the `Scripts/` directory (e.g., `MyNewTab.xaml`)
2. Define the TabItem with appropriate controls and layout
3. Add the filename to the `$tabFiles` array in `Main.ps1`
4. Create corresponding PowerShell functions if needed
5. Wire up event handlers in `Main.ps1`

### Working with JSON Data

The template demonstrates JSON-based data management:
- Load JSON files using `Get-Content | ConvertFrom-Json`
- Bind PowerShell objects to DataGrid ItemsSource
- Modify objects and save back using `ConvertTo-Json | Set-Content`
- Implement validation and error handling

## Executable Creation

The template includes a batch file (`xCreate-EXE-and-Shortcut.bat`) for converting the PowerShell application into a standalone executable:
- Packages the PowerShell script as an EXE
- Creates desktop shortcuts
- Simplifies distribution and deployment

## Use Cases

This template is ideal for creating:
- **Database Administration Tools**: SQL Server management utilities with tabbed interfaces
- **Deployment Utilities**: Application deployment and configuration tools
- **System Monitoring Dashboards**: Real-time monitoring with data grids and charts
- **Configuration Managers**: Tools for managing JSON/XML configuration files
- **Automation Utilities**: Scheduled task managers, script executors
- **Data Analysis Tools**: CSV/Excel data viewers and processors

## Requirements

- **Windows PowerShell 5.1+** or **PowerShell 7+**
- **.NET Framework 4.5+** (for WPF assemblies)
- **Windows OS** (WPF is Windows-specific)

## Best Practices

- Keep XAML files focused on UI structure, not logic
- Use PowerShell functions for all business logic
- Store configuration and data in JSON files, not hardcoded
- Implement proper error handling and user feedback
- Test in both PowerShell console and as compiled EXE
- Use meaningful names for controls (x:Name attribute)
- Comment complex XAML layouts and PowerShell functions
- Validate user input before processing

## Limitations

- WPF is Windows-only (not cross-platform)
- PowerShell execution policy must allow script execution
- Large datasets in DataGrids may impact performance
- Compiled EXEs may trigger antivirus false positives

---

**Note**: This is a template, not a functional utility. Customize and extend it to build your own WPF PowerShell applications.
