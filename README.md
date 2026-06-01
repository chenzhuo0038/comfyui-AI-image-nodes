# ComfyUI AI Image Nodes

ComfyUI 自定义节点，通过 OpenAI 兼容图像 API 调用远程模型，支持文生图、图像编辑和多图参考合成。

模型服务商：`https://checct.site`

当前默认服务地址固定为 `https://checct.site`，默认模型为 `gpt-image-2-all`。

## 节点列表

| 节点类名 | ComfyUI 显示名 | 功能 |
|---|---|---|
| `AIImageSettings` | AI 图像 - API 设置 | 保存模型和 API 密钥，输出可连线的配置 |
| `AIImageGenerate` | AI 图像 - 文生图 | 根据提示词生成图像 |
| `AIImageEdit` | AI 图像 - 图像编辑 | 输入一张图像并按描述编辑 |
| `AIImageVariation` | AI 图像 - 多图合成 | 输入 2-5 张参考图并按提示词合成新图 |

## 安装

进入 ComfyUI 的 `custom_nodes` 目录后克隆本仓库：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/chenzhuo0038/comfyui-AI-image-nodes.git
pip install -r comfyui-AI-image-nodes/requirements.txt
```

Windows 便携版 ComfyUI：

```bash
cd ComfyUI_windows_portable
git clone https://github.com/chenzhuo0038/comfyui-AI-image-nodes.git custom_nodes/comfyui-AI-image-nodes
python_embeded\python.exe -m pip install -r custom_nodes\comfyui-AI-image-nodes\requirements.txt
```

安装完成后重启 ComfyUI。

## 使用方法

### 1. 配置 API

模型服务商：`https://checct.site`

在 ComfyUI 中添加：

`Add Node` -> `AI 图像` -> `AI 图像 - API 设置`

填写：

| 参数 | 说明 |
|---|---|
| 模型 | 当前默认 `gpt-image-2-all` |
| API 密钥 | 你的 API Key |

执行该节点后，插件会在本目录生成 `settings.json` 保存配置。该文件已加入 `.gitignore`，不会被提交到仓库。

`AIImageSettings` 会输出 `配置`，可以连接到其他 AI 图像节点的 `配置` 输入；如果不连接，其他节点会自动读取本地 `settings.json`。

### 2. 文生图

添加 `AI 图像 - 文生图` 节点，填写 `提示词`，选择图像尺寸、生成数量、质量、输出格式和背景处理，然后连接到 `Preview Image` 或 `Save Image`。

### 3. 图像编辑

添加 `AI 图像 - 图像编辑` 节点，连接 `输入图像`，填写 `编辑描述`，可选设置 `输入保真度`、图像尺寸、质量、输出格式和背景处理。

### 4. 多图合成

添加 `AI 图像 - 多图合成` 节点，至少连接 `参考图 1` 和 `参考图 2`，最多可连接 5 张参考图，然后填写 `提示词` 生成新图。

## 参数说明

| 参数 | 节点 | 说明 |
|---|---|---|
| 提示词 | 文生图、多图合成 | 图像生成描述 |
| 编辑描述 | 图像编辑 | 对输入图像的修改描述 |
| 图像尺寸 | 全部生成节点 | `1024x1024` / `1536x1024` / `1024x1536` |
| 生成数量 | 全部生成节点 | 1-10 |
| 图像质量 | 全部生成节点 | 空 / `auto` / `low` / `medium` / `high` |
| 输出格式 | 全部生成节点 | `png` / `jpeg` / `webp` |
| 背景处理 | 全部生成节点 | `auto` / `transparent` / `opaque` |
| 输入保真度 | 图像编辑 | 空 / `low` / `high` |
| 模型 | 全部生成节点，可选 | 覆盖配置里的默认模型 |
| 配置 | 全部生成节点，可选 | 从 `AIImageSettings` 节点连线传入配置 |

## 添加模型

编辑 `config.py` 中的模型和尺寸配置：

```python
MODEL_OPTIONS = ["gpt-image-2-all", "新模型ID"]

SIZE_MAP = {
    "gpt-image-2-all": ["1024x1024", "1536x1024", "1024x1536"],
    "新模型ID": ["1024x1024"],
}
```

如果需要修改默认服务地址，可以修改 `config.py` 中的 `DEFAULT_BASE_URL`。

## API 路径

插件当前调用以下 OpenAI 兼容接口：

| 功能 | 接口 |
|---|---|
| 文生图 | `POST /v1/images/generations` |
| 多图合成 | `POST /v1/images/generations` |
| 图像编辑 | `POST /v1/images/edits` |
