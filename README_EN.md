> [中文](README.md) | **English**

# DWG AI Field Extraction System

DWG AI Field Extraction System is a Windows desktop and command-line tool that reads CAD native text, block attributes, and title block information from DWG/DXF drawings, then uses an OpenAI-compatible Chat Completions API to extract structured results based on field templates, and exports to Excel.

The current open-source version is intended for source code usage and secondary development, and does not include PyPI packages or desktop installers. The project uses the MIT License.

## Feature Overview

- Batch scan DWG/DXF files or directories.
- Use ODA File Converter to convert DWG to DXF; if only processing DXF, the converter is optional.
- Read CAD text, MTEXT, block attributes, and block definition text.
- Generate prompts based on JSON field templates and call OpenAI-compatible models.
- Export Excel with results table and failure log.
- Provide both desktop GUI and CLI entry points.

## Quick Start

### One-Click Launch (Recommended)

On first run, it automatically creates a virtual environment, installs dependencies, and launches the desktop interface.

```powershell
# Windows (PowerShell)
.\start.ps1
```

```bash
# macOS / Linux
chmod +x start.sh && ./start.sh
```

### Manual Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Set the model API key environment variable. In the interface and configuration, only enter the environment variable name, not the API key value.

```powershell
# Windows
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key", "User")

# macOS / Linux (persist by writing to shell config file)
export OPENAI_API_KEY="your-api-key"
```

Launch the desktop interface:

```powershell
dwg-ai-extractor-gui
```

If the command is not available, use:

```powershell
python -m frontend.desktop.app
```

## Command-Line Entry

```powershell
python -m backend.cli `
  --input D:\drawings `
  --output D:\drawings\extraction_results.xlsx `
  --template configs\default_template.json `
  --llm-config configs\model_config.example.json `
  --converter "C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe" `
  --recursive
```

If only processing DXF, `--converter` can be omitted.

## Configuration Files

- `configs/model_config.example.json`: Model service configuration example, including `base_url`, `api_key_env_var`, `model`, timeout, and JSON object mode options.
- `configs/default_template.json`: Default field template, determining which fields the model extracts and which columns appear in the Excel output.

Field templates support post-processing options such as `strip`, `empty_if_unknown`, `force_empty`, `sequence`, etc. For detailed field configuration, see the [User Guide](docs/user-guide.md).

## Privacy & Security Boundaries

- The program reads DWG/DXF files locally and extracts CAD native text and related metadata.
- By default, only organized text, coordinates, layer names, block names, entity types, and other context are sent to the model.
- The program does not upload DWG/DXF file bodies, images, or screenshots to the model.
- If the drawing text itself contains sensitive information, this text will be sent as context to your configured model service; for fully local processing, please use a local OpenAI-compatible service.
- Do not write real API keys into JSON configurations, README files, issues, logs, commit history, or command-line history.

## Development & Testing

```powershell
python -m json.tool configs\model_config.example.json
python -m json.tool configs\default_template.json
python -m pytest
```

Before open-source submission, ensure that `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, private DWG/DXF drawings, or exported Excel files are not committed.

## Additional Documentation

- [User Guide](docs/user-guide.md): Complete operational guide from installation, model configuration, field templates to batch processing and FAQ.
