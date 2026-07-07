# PNG to ICO Converter

Centralized utility for converting PNG images to ICO format for the Advanced SQL Server Toolkit.

## Purpose

This tool provides a single, centralized location for converting PNG images to ICO format across all utilities in the toolkit. This eliminates code duplication and makes it easier to maintain.

## Files

- **Convert-PngToIco.ps1** - Main PowerShell script
- **convert-config.json** - Configuration file defining all PNG to ICO conversions

## Usage

### Convert All Files from Configuration

```powershell
.\Convert-PngToIco.ps1 -ConvertAll
```

This will convert all PNG files defined in `convert-config.json`.

### Convert a Single File

```powershell
.\Convert-PngToIco.ps1 -PngPath "C:\path\to\image.png" -IcoPath "C:\path\to\output.ico"
```

### Custom Configuration File

```powershell
.\Convert-PngToIco.ps1 -ConvertAll -ConfigPath "C:\path\to\custom-config.json"
```

## Configuration File Format

The `convert-config.json` file contains an array of conversion definitions:

```json
{
  "conversions": [
    {
      "name": "Descriptive Name",
      "png_path": "C:/path/to/source.png",
      "ico_path": "C:/path/to/output.ico"
    }
  ]
}
```

### Adding New Conversions

To add a new PNG to ICO conversion:

1. Open `convert-config.json`
2. Add a new entry to the `conversions` array
3. Specify the `name`, `png_path`, and `ico_path`
4. Run `.\Convert-PngToIco.ps1 -ConvertAll`

## Features

- ✅ Batch conversion of multiple files
- ✅ Single file conversion
- ✅ Automatic output directory creation
- ✅ Input file validation
- ✅ Detailed error reporting
- ✅ Conversion summary with success/failure counts
- ✅ Color-coded console output

## Error Handling

The script includes comprehensive error handling:

- Validates input PNG file exists
- Creates output directory if needed
- Reports file lock errors (file in use)
- Provides detailed error messages
- Returns appropriate exit codes

## Exit Codes

- **0** - All conversions successful
- **1** - One or more conversions failed

## Notes

- The script uses `System.Drawing` assembly for image conversion
- Output ICO files are created with the same dimensions as the source PNG
- If an ICO file is locked (in use), the conversion will fail for that file
- Use forward slashes (/) or escaped backslashes (\\\\) in JSON paths

