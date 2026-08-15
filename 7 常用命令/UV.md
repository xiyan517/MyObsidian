# UV 常用命令

Astral 的 Python 包管理器，比 pip 快。项目日常用 `uv add` / `uv run`，不必先 `activate`。和 [[Python]]、[[Conda]] 并列，一个项目里选一种即可。

## 安装 / 更新

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

装完**重启终端**，否则常提示找不到 `uv`。也可以：`pip install uv`。

```bash
uv --version
uv self update                       # 更新 uv 自己
```

## Python 版本

```bash
uv python list                       # 本机已有 / 可安装的版本
uv python install 3.12               # 装一份给 uv 用
uv python pin 3.12                   # 当前项目钉死版本（写 .python-version）
```

## 项目

```bash
uv init                              # 当前目录建成项目（生成 pyproject.toml）
uv init myproj                       # 新建目录并初始化
cd myproj
uv add numpy                         # 加依赖，同时写进 pyproject.toml
uv add numpy==1.26.4                 # 指定版本
uv add --dev pytest                  # 开发依赖
uv remove numpy                      # 移除
uv sync                              # 按锁文件装齐环境
uv lock                              # 只更新锁文件
uv run python script.py              # 用项目环境跑脚本
uv run pytest                        # 跑测试
```

`[]` 这种 extras 在 PowerShell 里要加引号：`uv add "mcp[cli]"`。

## 虚拟环境 / pip 兼容

没有 `pyproject.toml`、只想像 pip 那样用时：

```bash
uv venv                              # 建 .venv
.\.venv\Scripts\Activate.ps1         # 可选：激活后再手动跑 python
uv pip install numpy
uv pip install -r requirements.txt
uv pip list
uv pip freeze
uv pip uninstall numpy
```

从 uv 项目导出给别人用 pip：

```bash
uv export --no-hashes -o requirements.txt
```

## 一次性工具

```bash
uvx ruff check .                     # 临时跑，不装进项目
uv tool install ruff                 # 装到用户级工具目录
uv tool list
uv tool uninstall ruff
```

MCP 里常见 `uvx blender-mcp`，就是这条路。Python 版本不匹配时先 `uv python install 3.12`。

## 清理

```bash
uv cache dir                         # 缓存位置
uv cache clean                       # 清缓存
```

## 最短流程

```bash
uv init myproj
cd myproj
uv add numpy pandas
uv run python script.py
```
