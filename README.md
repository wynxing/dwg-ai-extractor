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

## 隐私与安全边界

- 程序会在本机读取 DWG/DXF 文件，并抽取其中的 CAD 原生文字和相关元数据。
- 程序默认只把整理后的文字、坐标、图层、块名、实体类型等上下文发送给模型。
- 程序不会把 DWG/DXF 文件本体、图片或截图上传给模型。
- 如果图纸文字本身包含敏感信息，这些文字会作为上下文发送给你配置的模型服务；如需完全本地处理，请使用本地 OpenAI-compatible 服务。
- 不要把真实 API Key 写入 JSON 配置、README、issue、日志、提交记录或命令行历史。界面和配置中填写的是环境变量名，例如 `OPENAI_API_KEY`。
- 如发现漏洞或敏感信息泄露风险，请先通过私有渠道联系项目维护者，不要公开贴出密钥、图纸内容或客户信息。

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

设置模型密钥环境变量：

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "你的APIKey", "User")
```

启动桌面界面：

```powershell
dwg-ai-extractor-gui
```

或使用命令行：

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

## 开发与测试

```powershell
python -m json.tool configs\model_config.example.json
python -m json.tool configs\default_template.json
python -m pytest
```

开源提交前请确认不会提交 `.venv/`、`__pycache__/`、`.pytest_cache/`、`*.egg-info/`、私有 DWG/DXF 图纸或导出的 Excel 文件。

## 新手操作手册

这份手册面向第一次使用本软件的人。按步骤做，可以完成安装、模型配置、字段模板配置、批量处理 DWG/DXF 图纸，并导出 Excel。

## 1. 软件用途

本软件用于从 DWG/DXF 图纸中批量提取文字信息，并按你定义的字段导出 Excel。

典型用途：

- 从图纸标题栏、技术要求、块属性中提取物料编码、物料名称、材料、颜色、表面处理。
- 按自定义字段模板导出 Excel。
- 批量处理一个文件夹里的 DWG/DXF 图纸。

安全边界：

- 程序会在本机读取 DWG/DXF，并抽取 CAD 原生文字。
- 程序只把整理后的文字、坐标、块名等上下文发给模型。
- 程序不会把 DWG/DXF 文件本体、图片或截图上传给模型。
- API Key 不写入配置文件。界面里填写的是系统环境变量名，例如 `OPENAI_API_KEY`。

## 2. 处理流程图

```text
选择 DWG/DXF 文件或目录
        ↓
DWG 转 DXF（需要 ODA File Converter）
        ↓
读取 CAD 文字、块属性、标题栏块定义
        ↓
按字段模板组织提示词
        ↓
调用 OpenAI-compatible 模型
        ↓
模型返回 JSON 字段结果
        ↓
导出 Excel：结果表 + 失败清单
```

## 3. 安装前准备

你需要准备：

- Windows 电脑。
- Python 3.10 或以上版本。
- ODA File Converter，用于把 DWG 转成 DXF。
- 一个 OpenAI-compatible 模型服务，例如 OpenAI、one-api、DeepSeek、Qwen、LM Studio、vLLM。
- 一个保存 API Key 的系统环境变量，例如 `OPENAI_API_KEY`。

如果只处理 DXF 文件，可以暂时不配置 ODA File Converter。

## 4. 第一次安装

打开 PowerShell，进入项目目录

创建虚拟环境：

```powershell
python -m venv .venv
```

启用虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装软件和开发测试依赖：

```powershell
python -m pip install -e ".[dev]"
```

如果 PowerShell 提示无法执行脚本，可以先执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后重新启用虚拟环境。

## 5. 设置 API Key 环境变量

界面中不要填写 API Key 明文，只填写环境变量名。

例如你想用环境变量 `OPENAI_API_KEY` 保存密钥，可以在 PowerShell 中执行：

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "你的APIKey", "User")
```

设置后，关闭当前 PowerShell 和软件窗口，重新打开 PowerShell 或重新启动软件，让环境变量生效。

检查环境变量是否存在：

```powershell
[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")
```

如果输出 `True`，说明已经设置。不要用会打印密钥值的命令检查。

## 6. 启动桌面软件

确保已经进入项目目录并启用虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

启动桌面端：

```powershell
dwg-ai-extractor-gui
```

如果命令不可用，可以使用：

```powershell
python -m frontend.desktop.app
```

## 7. 填写模型配置

在软件右上角 `模型配置` 区域填写：

- `Base URL`：模型服务地址，例如 `https://api.openai.com/v1`。
- `API Key 环境变量名`：填写环境变量名，例如 `OPENAI_API_KEY`，不是 API Key 明文。
- `Model`：模型名称，例如 `gpt-4.1-mini`，或你的兼容服务提供的模型名。
- `Temperature`：建议填 `0`，让输出更稳定。
- `Timeout 秒`：建议 `60`。
- `Max Retries`：建议 `2`。
- `启用 JSON object 模式`：如果你的模型服务兼容 OpenAI JSON object，可以勾选；如果测试连接报 `response_format` 相关错误，可以取消勾选。

填写完成后，点击 `测试连接`。

测试成功后，再开始批量处理。

## 8. 配置字段模板

字段模板决定 Excel 输出哪些列，也决定模型要提取哪些信息。

默认模板是 7 列：

```text
序号 | 物料编码 | 物料名称 | 图片 | 材料 | 颜色 | 表面处理
```

字段模板表格每列含义：

- `key`：字段的稳定英文标识，例如 `item_code`。不要使用空格。
- `表头`：Excel 中显示的列名，例如 `物料编码`。
- `说明`：告诉模型这个字段怎么提取，越清楚越好。
- `必填`：填 `true` 或 `false`。必填字段为空时，该文件会进入失败清单。
- `示例`：给模型参考的示例值。
- `后处理`：程序对模型结果做的固定处理。

支持的后处理：

- `strip`：去掉前后空格，常用默认值。
- `empty_if_unknown`：如果模型输出 `未知`、`N/A` 等，改为空。
- `force_empty`：强制为空，适合首版的 `图片` 字段。
- `sequence`：由程序生成序号，适合 `序号` 字段。

新增字段示例：申请数量

| key | 表头 | 说明 | 必填 | 示例 | 后处理 |
| --- | --- | --- | --- | --- | --- |
| request_qty | 申请数量 | 申请采购或生产数量；如果图纸文字中没有数量，返回空字符串。 | false | 10 | strip |

新增字段示例：备注

| key | 表头 | 说明 | 必填 | 示例 | 后处理 |
| --- | --- | --- | --- | --- | --- |
| remark | 备注 | 其他需要补充的信息；没有则返回空字符串。 | false | 需喷油绝缘 | strip |

删除 `图片` 字段：

1. 在字段模板表格中选中 `image / 图片` 这一行。
2. 点击 `删除选中`。
3. 点击 `保存模板`，保存为新的 JSON 文件。

建议第一次使用时先不要改模板，先用默认模板跑通 1 个文件。

## 9. 选择图纸并开始处理

在 `批处理` 区域操作：

1. 点击 `添加文件`，选择一个或多个 DWG/DXF。
2. 或点击 `添加目录`，选择一个包含图纸的文件夹。
3. 如果要处理子文件夹，勾选 `递归扫描目录`。
4. 在 `输出 Excel` 中选择结果文件路径。
5. 如果处理 DWG，在 `ODA 转换器` 中选择 `ODAFileConverter.exe`。
6. 点击 `开始处理`。
7. 在日志区域查看每个文件成功或失败的原因。

第一次测试建议：

- 先只选 1 个 DWG 或 DXF。
- 确认 `测试连接` 成功。
- 确认 Excel 结果符合预期。
- 再选择整个目录批量处理。

## 10. 查看 Excel 结果

导出的 Excel 包含两个 Sheet：

- `物料明细表` 或模板中设置的输出表名：成功提取的结果。
- `失败清单`：失败文件、文件路径、错误信息、耗时秒。

如果某个文件没有出现在结果表中，先看 `失败清单`。

常见失败原因：

- API Key 环境变量没有设置。
- 模型服务连接失败。
- 模型没有返回合法 JSON。
- 必填字段为空。
- DWG 转 DXF 失败。
- ODA File Converter 路径不正确。

## 11. 命令行用法

桌面端适合新手。命令行适合批处理或自动化。

查看帮助：

```powershell
python -m backend.cli --help
```

使用默认模板和模型配置文件：

```powershell
python -m backend.cli `
  --input D:\drawings `
  --output D:\drawings\字段抽取结果.xlsx `
  --template \configs\default_template.json `
  --llm-config \configs\model_config.example.json `
  --converter "C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe" `
  --recursive
```

如果只处理 DXF，可以不填 `--converter`。

## 12. 常见问题与解决办法

### 12.1 提示环境变量未设置或为空

原因：`API Key 环境变量名` 填了 `OPENAI_API_KEY`，但系统里没有这个环境变量。

解决：

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "你的APIKey", "User")
```

然后重启软件。

### 12.2 模型连接测试失败

检查：

- `Base URL` 是否正确，通常以 `/v1` 结尾。
- `Model` 是否是服务支持的模型名。
- 环境变量名是否填对。
- 当前网络是否能访问模型服务。
- 如果报 `response_format`，取消勾选 `启用 JSON object 模式` 再试。

### 12.3 DWG 转换失败

检查：

- 是否安装 ODA File Converter。
- `ODA 转换器` 是否选择了正确的 `ODAFileConverter.exe`。
- DWG 文件是否损坏或被其他程序占用。
- 如果只处理 DXF，不需要 ODA。

### 12.4 Excel 里没有某个文件

查看 `失败清单`，里面会写具体错误。

如果是必填字段缺失：

- 可以把字段模板中该字段的 `必填` 改成 `false`。
- 或在字段说明里写得更清楚，让模型更容易提取。

### 12.5 模型结果不准确

优先修改字段模板的 `说明` 和 `示例`。

例如 `表面处理` 可以写得更具体：

```text
表面处理工艺。若标题栏写“见技术要求”或“详见技术要求”，必须从技术要求正文中总结喷油、NCVM、抛光等工艺，并包含厚度、绝缘、耐压等关键描述。
```

### 12.6 输出列不符合需要

在字段模板中新增、删除或调整字段行，然后保存模板。

字段顺序就是 Excel 输出列顺序。

## 13. 安全说明

- 不要把 API Key 明文写进模板 JSON、模型配置 JSON 或 README。
- 界面只填写环境变量名，例如 `OPENAI_API_KEY`。
- 程序日志不会输出 API Key。
- 发给模型的是 CAD 文字上下文，不是 DWG/DXF 文件。
- 如果图纸文字本身包含敏感信息，它会作为文本上下文发给模型服务；如需完全本地处理，请使用本地 OpenAI-compatible 服务。

## 14. 后续自定义字段建议

建议先从少量字段开始：

- 物料编码
- 物料名称
- 材料
- 颜色
- 表面处理

跑通后再增加：

- 申请数量
- 备注
- 产品型号
- 版本
- 单位
- 图纸页数
- 检验规范

每新增一个字段，都要写清楚字段说明和示例。字段说明越明确，模型输出越稳定。
