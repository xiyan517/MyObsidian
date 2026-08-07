---
title: Hunyuan3D v2 + Blender MCP
aliases:
  - Blender MCP
  - Hunyuan3D-2
  - 混元 3D
  - BlearnMCP
created: 2026-08-05
updated: 2026-08-05
series: 本地 RAG
part: 17
source: https://kgptalkie.com/tutorials/generative-ai/hunyuan3d-blender-mcp-setup-guide · 配套演示视频
author: Laxmi Kant Tiwari
published: 2026-03-30
article_updated: 2026-07-12
tags:
  - type/literature-note
  - topic/blender
  - topic/mcp
  - topic/hunyuan3d
  - topic/claude-desktop
  - topic/wsl2
  - status/draft
---

# Hunyuan3D v2 + Blender MCP

> [!summary]
> 把 **Hunyuan3D-2** 接到 **Blender MCP**，让 **Claude Desktop** 用自然语言在 Blender 里**生成 / 贴图 / 放置** 3D 资产。两条能力：① **纯 MCP** 用 Blender Python 画示意（地球剖面、玻尔模型、DNA）；② **混元 API** 生成游戏角色（钢铁侠、绿巨人）。Windows 上 Blender + Claude 本机跑；吃 GPU 的混元服务放 **WSL2:8081**。

原文：[Hunyuan3D v2 and Blender MCP Setup Guide](https://kgptalkie.com/tutorials/generative-ai/hunyuan3d-blender-mcp-setup-guide)（KGP Talkie）

## 本章目录

| 章节 | 学什么 |
| --- | --- |
| §1 目标与架构 | Claude → MCP → Blender；WSL2 跑混元 |
| §2 Blender MCP | 插件、`uv`、Claude 配置、启动顺序 |
| §3 Hunyuan3D-2 | WSL2 安装、权重、`api_server`、面板参数 |
| §4 贴图生成（可选） | Paint/Delight 权重、CUDA rasterizer、`--enable_tex` |
| §5 参考表 | 模型档位、生成参数、API 端点 |
| §6 演示：纯 MCP 示意 | 地球剖面 / 玻尔 / DNA、导出 |
| §7 演示：混元角色 | 钢铁侠 / 绿巨人、强制用混元工具 |
| §8 踩坑与操作习惯 | 审批、断连重连、显式 prompt |

---

## 1. 目标与架构

| 组件 | 跑在哪 | 作用 |
| --- | --- | --- |
| Blender + BlenderMCP 插件 | Windows | 实时场景；本机 RPC（默认端口 **9876**） |
| Claude Desktop + MCP bridge | Windows | 自然语言 → 调 MCP 工具（如 `execute_blender_code`） |
| Hunyuan3D-2 `api_server` | **WSL2** + CUDA GPU | 文生 3D / 贴图；默认 **8081** |

> [!note]
> WSL2 会把端口转发到 Windows，故 Blender 侧可直接用 `http://localhost:8081`，一般不必再配端口映射。

学完应能：装好插件 → Claude 控 Blender → 在 WSL2 起混元服务 → 面板勾选腾讯混元 → 用自然语言直接往场景里塞模型。

---

## 2. Blender MCP 配置

Blender MCP 让 MCP 客户端（如 Claude Desktop）在**正在运行的** Blender 里执行命令、查物体、跑 Python。

### 2.1 安装插件

从官方 blender-mcp GitHub 仓库下载 `addon.py`。

1. 打开 Blender
2. **Edit → Preferences → Add-ons**
3. 点 **Install...**（或 Install from Disk，视版本 UI）
4. 选中下载的 `addon.py` → Install Add-on
5. 列表里找到 **System: BlenderMCP**，勾选启用

启用后：

1. 打开 3D Viewport
2. 按 **`N`** 打开侧栏
3. 点 **BlenderMCP** 标签
4. **Start MCP Server**（本地 RPC，默认端口 **9876**）

### 2.2 Python 环境（MCP bridge）

专用 **Python 3.12**。在更新的 Python（如 3.14）上跑 `uvx blender-mcp` 可能因 `pyiceberg` 等依赖编译失败。

```bash
conda create -n py312 python=3.12 -y
conda activate py312
pip install uv
```

### 2.3 配置 Claude Desktop

配置文件：`%APPDATA%\Claude\claude_desktop_config.json`

注册 `blender` 服务器（**路径改成你本机 Anaconda**）：

```json
{
  "mcpServers": {
    "blender": {
      "command": "C:/Users/laxmi/anaconda3/envs/py312/Scripts/uvx.exe",
      "args": [
        "--python",
        "C:/Users/laxmi/anaconda3/envs/py312/python.exe",
        "blender-mcp"
      ]
    }
  }
}
```

改完后：**完全退出再打开** Claude Desktop，新开对话才能加载工具。

### 2.4 启动顺序（重要）

1. 启动 **Blender**，并在 N 面板确认 MCP Server 已跑
2. 启动 **Claude Desktop**
3. **新开一条对话**（旧窗口可能不刷新 MCP 工具列表）

> [!warning]
> 持续开着的会话未必会装载新注册的 MCP 工具。要用不了 `execute_blender_code` 时，先新开 thread。

---

## 3. Hunyuan3D-2（WSL2）

需要较快的 **NVIDIA GPU + CUDA**。Windows 建议在 **WSL2（Ubuntu）** 里跑。

### 3.1 安装

```bash
conda create -n hunyuan3d_312 python=3.12 -y
conda activate hunyuan3d_312

# PyTorch + CUDA（索引以原文/官网当前推荐为准；示例为 cu130）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130

cd ~
git clone https://github.com/Tencent/Hunyuan3D-2
cd Hunyuan3D-2

pip install -r requirements.txt
pip install -e .

pip install sentencepiece tiktoken pybind11 ninja "pybind11[global]" huggingface_hub

cd hy3dgen/texgen/differentiable_renderer
	pip install -e .
cd ~/Hunyuan3D-2
```

### 3.2 下载权重（轻量 mini）

```bash
huggingface-cli download tencent/Hunyuan3D-2mini --local-dir ~/Hunyuan3D-2/weights
hf download tencent/Hunyuan3D-2mini --local-dir ~/Hunyuan3D-2/weights
```

### 3.3 启动 API Server


先获取其他需要的模型 在 Windows 上用下载工具获取

如果 WSL 里网络不稳定，你可以在 **Windows 宿主机**上直接用浏览器或迅雷等工具下载：

1. **下载地址**：`https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx`
    
2. **保存位置**：下载完成后，通过 `\\wsl$` 路径（比如 `\\wsl$\Ubuntu\root\.u2net\`），把文件复制到 WSL 的 `/root/.u2net/` 目录下。
	``` shell
	sudo mkdir -p /root/.u2net
	cp /mnt/c/Users/Administrator/Downloads/u2net.onnx ~/.u2net/
	```


```bash
conda activate hunyuan3d_312
cd ~/Hunyuan3D-2
python api_server.py --host 0.0.0.0 --port 8081 --model_path ~/Hunyuan3D-2/weights --device cuda
```

Blender MCP 集成时须保持 **8081** 上的 `api_server.py` 在跑。

### 3.4 BlenderMCP 面板

| 设置 | 值 | 说明 |
| --- | --- | --- |
| Use Tencent Hunyuan | 勾选 | 走 API 直接生成资产 |
| Hunyuan API URL | `http://localhost:8081` | WSL2 上的模型服务 |
| Octree Resolution | 256（可调） | 网格细节与显存 |

**分辨率 vs 显存 / 耗时：**

| Resolution | 约需显存 | 约耗时 |
| --- | --- | --- |
| 128 | ~8 GB | ~30 s |
| 256 | ~16 GB | ~90 s |
| 512 | ~24 GB | ~3 min |

### 3.5 Gradio Web UI（可选，测生成）

无贴图：

```bash
cd ~/Hunyuan3D-2
python gradio_app.py --model_path ~/Hunyuan3D-2/weights --device cuda --disable_tex --port 8080 --enable_t23d
```

带贴图（需贴图权重）：

```bash
cd ~/Hunyuan3D-2
LD_LIBRARY_PATH=$CONDA_PREFIX/lib/python3.12/site-packages/torch/lib:$CONDA_PREFIX/lib \
python gradio_app.py --model_path ~/Hunyuan3D-2/weights --texgen_model_path ~/Hunyuan3D-2/weights --device cuda --port 8080 --enable_t23d
```

浏览器打开 `http://localhost:8080`。**Blender MCP 仍依赖 8081 的 api_server**，与 Gradio 8080 分开。

---

## 4. 启用贴图生成（可选）

要更真实贴图：额外权重 + 编译自定义 rasterizer。

### 4.1 系统库

```bash
sudo apt-get update
sudo apt-get install -y libopengl0
```

### 4.2 下载 Paint / Delight 权重

```bash
huggingface-cli download tencent/Hunyuan3D-2 --include "hunyuan3d-paint-v2-0-turbo/*" --local-dir ~/Hunyuan3D-2/weights

huggingface-cli download tencent/Hunyuan3D-2 --include "hunyuan3d-delight-v2-0/*" --local-dir ~/Hunyuan3D-2/weights
```

### 4.3 编译 CUDA Custom Rasterizer

```bash
conda install -c nvidia/label/cuda-13.0.0 cuda-toolkit -y

cd ~/Hunyuan3D-2/hy3dgen/texgen/custom_rasterizer
CUDA_HOME=$CONDA_PREFIX pip install . --no-build-isolation
cd ~/Hunyuan3D-2
```

> [!tip]
> `CUDA_HOME=$CONDA_PREFIX` 强制用 Conda 里的编译头文件，避免落到系统路径。

### 4.4 `trust_remote_code` 补丁

编辑 `hy3dgen/texgen/utils/multiview_utils.py`（约第 34 行），加载 pipeline 时加上 `trust_remote_code=True`：

```python
# After patch
pipeline = DiffusionPipeline.from_pretrained(
    multiview_ckpt_path,
    custom_pipeline=custom_pipeline_path,
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
```

### 4.5 带贴图启动 API

```bash
cd ~/Hunyuan3D-2
LD_LIBRARY_PATH=$CONDA_PREFIX/lib/python3.12/site-packages/torch/lib:$CONDA_PREFIX/lib \
python api_server.py \
  --host 0.0.0.0 --port 8081 \
  --model_path ~/Hunyuan3D-2/weights \
  --tex_model_path ~/Hunyuan3D-2/weights/hunyuan3d-paint-v2-0-turbo \
  --device cuda --enable_tex
```

8081 起来后，Claude Desktop 可用自然语言直接在 Blender 场景里生成并贴图。

---

## 5. 参考

### 5.1 模型档位

| Model                       | Type                            | Speed | Quality |
| --------------------------- | ------------------------------- | ----- | ------- |
| hunyuan3d-dit-v2-mini       | Standard DIT                    | 最慢    | 最好      |
| hunyuan3d-dit-v2-mini-fast  | Fast DIT（Guidance distillation） | ~2×   | 略降      |
| hunyuan3d-dit-v2-mini-turbo | Turbo DIT（Step distillation）    | 最快    | 够用      |

### 5.2 生成参数

| Parameter | Default | 说明 |
| --- | --- | --- |
| seed | 1234 | 可复现 |
| octree_resolution | 128 | 细节：64 / 128 / 256 |
| num_inference_steps | 5 | 步数↑ → 质量↑、更慢 |
| guidance_scale | 5.0 | 对 prompt 的遵循强度 |
| texture | false | 仅当服务以 `--enable_tex` 启动时再开 |

### 5.3 API 端点

| Method | Endpoint | 说明 |
| --- | --- | --- |
| POST | `/generate` | 同步；直接返回 GLB 流 |
| POST | `/send` | 异步；返回 `{"uid": "..."}` |
| GET | `/status/{uid}` | 查状态，队列完成后取资产 |

---

## 速查清单

```text
1. conda py312 + uv  → Claude 配 blender-mcp
2. Blender 装 addon → N 面板 Start MCP Server (9876)
3. 先 Blender MCP，再开 Claude，再新对话
4. 冒烟：问「Blender MCP 有多少 tools？」（课上约 22 个）
5. WSL2：hunyuan3d_312 + Hunyuan3D-2 + 权重
6. api_server.py → 8081（贴图则 --enable_tex）
7. Blender 面板：Use Tencent Hunyuan + localhost:8081 → 断连再重连 MCP
8. Claude 生成角色时写明：use Hunyuan 3D MCP tools
```

---

## 6. 演示：纯 MCP 示意（不用混元）

配置好 §2 后，Claude 侧分屏对着 Blender，即可用 **`execute_blender_code` 等工具**在场景里搭几何体，适合课本示意。

### 6.1 冒烟测试

问：*How many tools do I have in my blender mcp?*  
课上回复约 **22** 个（execute blender code、scene info、object info …）。执行代码时 Claude / MCP 可能弹 **批准请求**，需手动允许；也可给 Claude Desktop **完整控制**。

### 6.2 地球剖面（地理 / 物理）

示例 prompt：

> Create a cross section of earth showing four layers. Inner core bright yellow, outer core orange, mantle dark red, and crust. Each as a hemisphere so the layers are visible from the front.

生成后可进 Modeling / Render 视图旋转查看。若标签文字反了、难看，明确说：

> Remove text data from blender object.

### 6.3 玻尔模型（化学）

> Build a Bohr model of carbon atom. Nucleus in the center with proton red spheres and neutron gray spheres. 2 electrons on the inner ring, 4 on the outer ring using glowing blue spheres.

新物体前通常会 **删掉现有物体**。想保留：先 **File → Export**，或另存再开新文件。课上导出地球为 `earth`，可用系统 3D Viewer / Babylon.js Sandbox 预览。

### 6.4 DNA（生物）

> Build a DNA double helix with two twisted strands.

同样会先清空场景；重要结果先导出再覆盖。

| 示意 | 领域 | 主要靠 |
| --- | --- | --- |
| 地球四层剖面 | 地理 / 物理 | Blender Python via MCP |
| 碳原子玻尔模型 | 化学 | 同上 |
| DNA 双螺旋 | 生物 | 同上 |
| 钢铁侠 / 绿巨人 | 游戏角色 | **混元**（§7） |

---

## 7. 演示：混元生成游戏角色

### 7.1 接上混元后再控 Blender

1. WSL2 起 `api_server`（§3.3），浏览器访 `http://localhost:8081`——出现类似 *details not found* 也说明服务在跑  
2. Blender N 面板：勾选 **Use Tencent Hunyuan**，Local API → `http://localhost:8081`  
3. **Disconnect** MCP → 再 **Connect**（改面板后必须重连）  
4. Claude 新对话问：*Can you connect with your 3D MCP tool?* 确认有权限  

生成时 GPU 常拉满（课上约 100%），属正常。

### 7.2 钢铁侠

> Create a full body 3D model of Iron Man standing upright facing forward. Build a red and gold metallic armored suit with smooth curved surfaces …

后台走混元 → 网格进 Blender → 再上色。可多视角查看；改色可能不稳定，课上曾想刷全红出问题。

### 7.3 绿巨人 +「必须用混元」

> Create a full body 3D model of Hulk with extremely large muscular proportion.

> [!warning] Claude 可能偷懒
> 课上第一次它只用 **Blender Python** 拼了一个滑稽绿巨人，**没调混元**。应停掉并明确：
>
> `Use Hunyuan 3D MCP tools`
>
> 之后才正确生成角色。换角色会覆盖场景——重要模型先 Export。

渲染可用 **F12**（课上口误说过 F2）。旋转 / 缩放检查网格与材质。

---

## 8. 踩坑与操作习惯

| 问题 | 处理 |
| --- | --- |
| Python 3.13 / 3.14 | MCP bridge 用 **3.12**（§2.2） |
| 工具列表为空 | 先起 Blender MCP，再开 Claude，**新开对话** |
| 改了混元面板仍旧行为 | Disconnect → Connect 重连 MCP |
| 生成角色像「几何体拼凑」 | Prompt 写明 **use Hunyuan 3D MCP tools** |
| 文字标注反了 | *remove text data from blender object* |
| 场景被清空 | 先 Export；或另存 `.blend` |
| 本机验证 API | curl / 浏览器开 `localhost:8081` |
| 显存不够 | 降低 Octree Resolution（§3.4） |

---

## 相关笔记

- [[16_杂项]] — Conda / PyTorch / CUDA 环境
- [[11_Tool Calling]] — 工具调用思路（MCP 同类扩展面）


命令
```
# 将wsl 的文件拷贝到主机  # 将 /root/my_folder 文件夹完整复制到 Windows 桌面
cp -r /root/my_folder /mnt/c/Users/Administrator/Desktop/
```
