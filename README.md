# DWG AI 字段抽取系统

DWG AI 字段抽取系统是一个 Windows 桌面和命令行工具，用于从 DWG/DXF 图纸中读取 CAD 原生文字、块属性和标题栏信息，再通过 OpenAI-compatible Chat Completions 接口按字段模板抽取结构化结果，并导出 Excel。

当前开源版本面向源码使用和二次开发，不包含 PyPI 发布包或桌面安装包。项目采用 MIT License。

## 功能概览

- 批量扫描 DWG/DXF 文件或目录。
- 使用 ODA File Converter 将 DWG 转换为 DXF；如果只处理 DXF，可以不配置转换器。
- 读取 CAD 文本、MTEXT、块属性和块定义文字。
- 按 JSON 字段模板生成提示词并调用 OpenAI-compatible 模型。
- 导出 Excel，包含结果表和失败清单。
- 提供桌面 GUI 和 CLI 两种入口。

## 快速开始

### 一键启动（推荐）

首次运行会自动创建虚拟环境、安装依赖并启动桌面界面。

```powershell
# Windows (PowerShell)
.\start.ps1
```

```bash
# macOS / Linux
chmod +x start.sh && ./start.sh
```

### 手动初始化

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

设置模型密钥环境变量。界面和配置里只填写环境变量名，不要填写 API Key 明文。

```powershell
# Windows
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "你的APIKey", "User")

# macOS / Linux（写入 shell 配置文件持久化）
export OPENAI_API_KEY="你的APIKey"
```

启动桌面界面：

```powershell
dwg-ai-extractor-gui
```

如果命令不可用，可以使用：

```powershell
python -m frontend.desktop.app
```

## 命令行入口

```powershell
python -m backend.cli `
  --input D:\drawings `
  --output D:\drawings\字段抽取结果.xlsx `
  --template configs\default_template.json `
  --llm-config configs\model_config.example.json `
  --converter "C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe" `
  --recursive
```

如果只处理 DXF，可以省略 `--converter`。

## 配置文件

- `configs/model_config.example.json`：模型服务配置示例，包含 `base_url`、`api_key_env_var`、`model`、超时和 JSON object 模式等选项。
- `configs/default_template.json`：默认字段模板，决定模型抽取哪些字段以及 Excel 输出哪些列。

字段模板支持 `strip`、`empty_if_unknown`、`force_empty`、`sequence` 等后处理方式。详细字段配置方式见 [新手操作手册](docs/user-guide.md)。

## 隐私与安全边界

- 程序会在本机读取 DWG/DXF 文件，并抽取其中的 CAD 原生文字和相关元数据。
- 程序默认只把整理后的文字、坐标、图层、块名、实体类型等上下文发送给模型。
- 程序不会把 DWG/DXF 文件本体、图片或截图上传给模型。
- 如果图纸文字本身包含敏感信息，这些文字会作为上下文发送给你配置的模型服务；如需完全本地处理，请使用本地 OpenAI-compatible 服务。
- 不要把真实 API Key 写入 JSON 配置、README、issue、日志、提交记录或命令行历史。

## 开发与测试

```powershell
python -m json.tool configs\model_config.example.json
python -m json.tool configs\default_template.json
python -m pytest
```

开源提交前请确认不会提交 `.venv/`、`__pycache__/`、`.pytest_cache/`、`*.egg-info/`、私有 DWG/DXF 图纸或导出的 Excel 文件。

## 更多文档

- [新手操作手册](docs/user-guide.md)：从安装、模型配置、字段模板到批量处理和常见问题的完整操作引导。
