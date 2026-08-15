# NSSM 常用命令

把任意程序（含 [[Python]] 脚本）注册成 Windows 服务：开机自启、崩溃重启、日志写文件。命令要在**管理员** PowerShell / cmd 里跑。

官网下载：[nssm.cc](https://nssm.cc/download)。把 `nssm.exe` 放到 PATH，或直接用完整路径调用。

## 安装 / 删除服务

```powershell
nssm install MyApp                   # 弹 GUI，填可执行文件、参数、目录
nssm install MyApp "C:\Python\python.exe" "C:\app\server.py"
nssm remove MyApp confirm            # 删除服务（confirm 跳过二次确认）
```

服务名自己定，后面所有命令都用这个名字。

## 启停

```powershell
nssm start MyApp
nssm stop MyApp
nssm restart MyApp
nssm status MyApp
nssm edit MyApp                      # 再打开 GUI 改配置
```

系统自带的也能用：`sc start MyApp` / `sc stop MyApp` / `sc query MyApp`。

## 命令行改配置

GUI 填过一遍之后，也可以用 `set` 改单项。路径一律用绝对路径。

```powershell
nssm set MyApp Application "C:\Python\python.exe"
nssm set MyApp AppDirectory "C:\app"
nssm set MyApp AppParameters "server.py --host 0.0.0.0 --port 8080"
nssm set MyApp DisplayName "My App"
nssm set MyApp Description "本地服务"
nssm set MyApp Start SERVICE_AUTO_START
```

`Start` 常用值：`SERVICE_AUTO_START`（开机）、`SERVICE_DEMAND_START`（手动）。

## 日志与崩溃重启

```powershell
nssm set MyApp AppStdout "C:\app\logs\out.log"
nssm set MyApp AppStderr "C:\app\logs\err.log"
nssm set MyApp AppRotateFiles 1
nssm set MyApp AppRotateBytes 10485760    # 约 10MB 切文件
nssm set MyApp AppExit Default Restart  
nssm set MyApp AppRestartDelay 5000       # 崩了等 5 秒再拉起
```

日志目录要先建好，NSSM 不会自动创建文件夹。

## 查看当前配置

```powershell
nssm dump MyApp                      # 打印等价的 nssm set 命令
nssm get MyApp Application
nssm get MyApp AppParameters
nssm get MyApp AppDirectory
```

## 最短流程

把 Python 脚本挂成开机服务：

```powershell
mkdir C:\app\logs
nssm install MyApp "C:\Python\python.exe" "C:\app\server.py"
nssm set MyApp AppDirectory "C:\app"
nssm set MyApp AppStdout "C:\app\logs\out.log"
nssm set MyApp AppStderr "C:\app\logs\err.log"
nssm set MyApp AppExit Default Restart
nssm start MyApp
nssm status MyApp
```

`python.exe` 换成你实际环境里的路径：`where.exe python`，或 conda 环境里的 `...\envs\myenv\python.exe`。用 uv 项目时，`Application` 填 `uv.exe`，`AppParameters` 填 `run server.py`，`AppDirectory` 填项目根目录。
