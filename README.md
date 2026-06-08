# LayoutPrompter-Harness

An AI-powered harness that uses Claude (via AWS Bedrock) to beautify and optimize **Weintek EBX** HMI screen layouts through natural language prompts.

## Overview

LayoutPrompter-Harness lets you describe UI improvements in plain English. Claude reads your EBX project file, understands the current screen layout, and generates an improved design — which can be written back to your project with a single confirmation.

**Typical workflow:**
1. Run the harness and describe what you want ("make the buttons more consistent", "add a blue background to the header area")
2. Claude reads the current screen layout, reasons about the design, and produces updated JSON
3. Optionally apply the changes back to your project file (auto-backup is created first)

## Supported Widget Types

| Widget | Description |
|---|---|
| Lamp | Visual indicator light |
| Switch | Two-state toggle control |
| Button | Clickable button |
| OptionList | Dropdown / list selection |
| Slider | Range input control |
| NumericInput | Number entry field |
| TextInput | Text entry field |
| DrawingRectangle | Geometric shape for layout decoration |
| DrawingLine | Line / Arrow |
| DrawingLinkLine | Multi Link Line |
| DrawingEllipse | Ellipse / Circle |
| DrawingArc | Arc shape |
| DrawingPolygon | Polygon shape |
| Text | Static text label |
| Picture | External / System Picture |
| DrawingScale | Circular gauge / Linear Scale  |
| EmbeddedWindow | Embedded / Pop-up Window  |
| 2DBarcode | Matrix Barcode  |
| CompositeWidget | Complex grouped widget |

## Project Structure

```
LayoutPrompter-Harness/
├── agent_harness.py        # Main entry point — interactive chat loop
├── Config.ini              # AWS Bedrock credentials and model config
├── Project.json            # Your EBX project file (screen design)
├── prompts/
│   └── SystemPrompt.md     # System prompt with full EBX schema documentation
├── scripts/
│   ├── ClaudeFunc.py       # Bedrock client setup and streaming
│   ├── ToolCalling.py      # Tool definitions and execution
│   ├── StreamFilter.py     # Filters tool call details from terminal output
│   ├── EBXImportExport.py  # Socket tool for user to operate EBX Server
│   └── EBXJsonProcess.py   # Core JSON transformation engine (EBX ↔ view format)
├── EBXDefaultJSON/         # Default JSON templates for each widget type
├── backup/                 # Auto-backups of Project.json before any modification
└── temp/                   # LLM-generated JSON output files (timestamped)
```

## Prerequisites

- Python 3.8+
- AWS account with Bedrock access (Claude Sonnet model enabled)
- AWS credentials with `bedrock-runtime` permissions

**Install dependencies:**
```bash
pip install boto3 botocore
```

## Configuration

Edit `Config.ini` before running:

```ini
[BEDROCK_EU]
service_name = bedrock-runtime
anthropic_version = bedrock-2023-05-31
chat_model_id = global.anthropic.claude-sonnet-4-6
region = us-east-1
aws_access_key_id = <YOUR_KEY_ID>
aws_secret_access_key = <YOUR_SECRET_KEY>

[PROMPT]
system_prompt_file = ./prompts/SystemPrompt.md
```

## Usage

```bash
python agent_harness.py
```

The harness opens an interactive terminal loop. Type your request in natural language:

```
You: Read image <IMAGE_PATH> which is a HMI design pattern, then optimize and redesign it on screen `<YOUR_SCREEN_NAME>` from project `<YOUR_PROJECT_PATH>`.
You: Read the current screen `<YOUR_SCREEN_NAME>` from project `<YOUR_PROJECT_PATH>` and relayout objects uniformly.
You: Create 4 buttons closer to the bottom of screen `<YOUR_SCREEN_NAME>` from project `<YOUR_PROJECT_PATH>`. Their texts are "Home", "Page1", "Page2", "Page3" respectively.
```

**Available commands:**

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/clear` | Clear terminal output |
| `/reset` | Reset conversation history |
| `/exit` or `/quit` | Exit the harness |

## How It Works

```
User prompt (natural language)
	↓
Claude + SystemPrompt
	↓
[Tool Calls]
├── GetScreenLayout      →  EBXJsonProcess decodes Project (.json | .ebxprj ext) → view format
└── ReadImageByteData    →  Load reference images for analysis
	↓
Beautified JSON saved to ./temp/llm-output-<timestamp>.json
	↓
[Tool Calls]
├── UpsertWidgets        →  EBXJsonProcess insert or update a portion widgets on a screen
└── OverrideRes2Proj     →  EBXJsonProcess encodes a complete view format → Project (.json | .ebxprj)
	↓
Project updated  (original backed up to ./backup/)
	↓
[Tool Calls]
└── ReadScreenShot       →  LLM verifies results visually
```

The core engine (`EBXJsonProcess.py`) handles bidirectional transformation between the native EBX JSON format and a simplified "view" format that Claude can reason about effectively.

### Agent Tools

| Tool | Description |
|---|---|
| `GetScreenLayout` | Extracts and simplifies the current screen from `Project.json` |
| `ReadImageByteData` | Reads an image file and passes it to Claude for visual analysis |
| `OverrideRes2Proj` | Writes Claude's improved layout back to `Project.json` (creates backup first, extension of `.ebxprj` is allowed) |
| `UpsertWidgets` | Inserts or updates individual widgets without replacing the whole screen |
| `ReadScreenShot` | Read and Pass a screenshot image to Claude to verify result |

## Output

- Generated JSON views are saved to `./temp/llm-output-<timestamp>.json` automatically
- Before any write to `Project.json`, the original is backed up to `./backup/`
- The agent runs up to 3-5 tool-call steps per request before stopping
