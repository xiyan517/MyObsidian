# Python 常用命令

环境管理优先看 [[Conda]]。包管理也可以用 [[UV]]。下面是系统 Python / `venv` / `pip` 的日常命令。

Windows 上优先用启动器 `py`，避免点到错误的 `python`。

## 版本与运行

```bash
py --list                            # Windows：本机已装的 Python
py -3.11                             # 指定版本进 REPL
python --version
python script.py                     # 跑脚本
python -m http.server 8000           # 当前目录起静态服务
```

REPL 里退出：`exit()` 或 `Ctrl+Z` 再回车（Windows）。

## 虚拟环境（venv）

```bash
py -3.11 -m venv .venv               # 在项目里建环境
.\.venv\Scripts\Activate.ps1         # PowerShell 激活
# Windows cmd: .venv\Scripts\activate.bat
deactivate                           # 退出
```

PowerShell 提示无法执行脚本时：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

激活成功后，提示符前面会出现 `(.venv)`，之后的 `python` / `pip` 都走这个环境。

## pip

一定要在已激活的环境里装包。

```bash
python -m pip install -U pip         # 先升级 pip 自己
pip install numpy                    # 安装
pip install numpy==1.26.4            # 指定版本
pip install -r requirements.txt      # 按清单安装
pip uninstall numpy                  # 卸载
pip list                             # 已装包
pip show numpy                       # 某个包的信息
pip freeze > requirements.txt        # 导出当前环境
```

装 PyTorch 不要盲抄版本，到 [PyTorch 官网](https://pytorch.org/get-started/locally/) 按本机 CUDA 生成命令。示例：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

`cu128` 只是示例，以本机驱动为准。

## 常用检查

```bash
python -c "import sys; print(sys.executable)"   # 当前到底用的哪份 Python
python -c "import numpy; print(numpy.__version__)"
where.exe python                                 # Windows：python 在 PATH 里的位置
```

Jupyter / VS Code 要认这个环境：

```bash
pip install ipykernel
python -m ipykernel install --user --name myenv
```

然后在 notebook 里选名为 `myenv` 的 kernel。

## 模块方式运行

项目是包、或脚本依赖相对导入时，用 `-m`，不要直接 `python 子目录/文件.py`。

```bash
python -m pip install -e .           # 以可编辑模式安装当前项目
python -m pytest                     # 跑测试
python -m venv .venv                 # 建环境也是同一套路
```

## 最短流程

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install numpy pandas
python script.py
deactivate
```
