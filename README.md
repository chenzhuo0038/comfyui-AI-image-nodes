# ComfyUI AI Image Nodes

从 Photoshop UXP 插件改造而来的 ComfyUI 自定义节点，通过 OpenAI 兼容 API 调用远程图像生成模型。

## 节点列表

| 节点 | 中文名 | 功能 |
|------|--------|------|
| `AIImageSettings` | AI 图像 - API 设置 | 配置并保存 baseUrl / model / apiKey |
| `AIImageGenerate` | AI 图像 - 文生图 | 文字描述生成图像 |
| `AIImageEdit` | AI 图像 - 图像编辑 | 传入图像 + 描述，编辑图像 |
| `AIImageVariation` | AI 图像 - 多图合成 | 多张参考图 + 提示词合成新图 |

## 安装

```bash
cd ComfyUI/custom_nodes/
# 将 comfyui-AI-image-nodes 文件夹复制到此目录
pip install -r comfyui-AI-image-nodes/requirements.txt
```

Windows 便携版 ComfyUI：
```bash
cd ComfyUI_windows_portable
python_embeded\python.exe -m pip install -r custom_nodes\comfyui-AI-image-nodes\requirements.txt
```

## 使用方法

### 1. 配置 API

**方式一（推荐）：使用 AIImageSettings 节点**

1. 在 ComfyUI 中，右键 → `Add Node` → `AI Image` → `AI 图像 - API 设置`
2. 填入：
   - `baseUrl`：API 服务地址（默认 `https://checct.site`）
   - `model`：选择模型（如 `gpt-image-2-all`）
   - `apiKey`：你的 API 密钥
3. 按 `Ctrl+Enter` 执行，看到日志输出 `✓ 设置已保存` 即成功

**方式二：手动编辑配置文件**

在 `comfyui-AI-image-nodes/settings.json` 写入：

```json
{
  "baseUrl": "https://checct.site",
  "model": "gpt-image-2-all",
  "apiKey": "sk-你的密钥"
}
```

### 2. 生成图像

1. 添加文生图/编辑/合成节点
2. （可选）将 `AIImageSettings` 节点的 `settings_json` 输出连接到目标节点的 `settings_json` 输入，以使用连线传入的配置
3. 不连线时，节点自动从 `settings.json` 读取配置
4. 填入 prompt，连接到 `Save Image` 或 `Preview Image` 节点
5. 执行队列

### 3. 添加新模型

编辑 `config.py`：

```python
DEFAULT_MODELS = [
    {"value": "gpt-image-2-all", "label": "gpt-image-2-all"},
    {"value": "新模型ID", "label": "新模型名称"},
]

SIZE_MAP = {
    "gpt-image-2-all": ["1024x1024", "1536x1024", "1024x1536"],
    "新模型ID": ["1024x1024", "2048x2048"],
}
```

## 参数说明

| 参数 | 节点 | 说明 |
|------|------|------|
| prompt | 全部 | 图像描述/提示词 |
| size | 全部 | 1024×1024 / 1536×1024 / 1024×1536 |
| n | 全部 | 生成数量 (1-10) |
| quality | 全部 | auto / low / medium / high |
| output_format | 全部 | png / jpeg / webp |
| background | 全部 | auto / transparent / opaque |
| input_fidelity | 编辑 | 输入保真度：low / high |
| model | 全部(可选) | 覆盖 settings 中的模型 |
| settings_json | 全部(可选) | 连线传入配置 |
