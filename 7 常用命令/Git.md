# Git 常用命令

本库已在用 Git。日常几乎只需要：改文件 → `add` → `commit` → `push`。

## 配置（一般只做一次）

```bash
git config --global user.name "你的名字"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --list                    # 查看当前配置
```

只改当前仓库，去掉 `--global`。

## 新建 / 克隆

```bash
git init                             # 当前目录建成仓库
git clone <url>                      # 克隆远程仓库
git clone <url> my-folder            # 克隆到指定目录
```

## 日常提交

```bash
git status                           # 看改了什么
git diff                             # 未暂存的改动
git diff --staged                    # 已暂存、待提交的改动
git add .                            # 暂存全部
git add 文件.md                      # 只暂存某个文件
git add IeVedio                      # 只暂存某个文件夹
git commit -m "说明这次改了什么"
git log --oneline -10                # 最近 10 条提交
```

`.gitignore` 里写不需要进仓库的路径，例如 `.obsidian/workspace.json`、`__pycache__/`。

## 分支

```bash
git branch                           # 本地分支
git branch -a                        # 含远程
git switch -c feat/xxx               # 新建并切过去
git switch main                      # 切回
git merge feat/xxx                   # 把某分支合进当前分支
git branch -d feat/xxx               # 删已合并的本地分支
```

旧写法 `git checkout -b` 也能建分支，新仓库优先 `switch`。

## 远程

```bash
git remote -v                        # 看远程地址
git remote add origin <url>          # 第一次关联
git push -u origin main              # 首次推送并设上游
git push                             # 之后直接 push
git pull                             # 拉远程并合并
git fetch                            # 只拉，不合并
```

当前分支跟踪哪个远程：`git status` 第一行会写。

## 撤销（按危险程度）

还没 commit：

```bash
git restore 文件.md                  # 丢弃工作区改动
git restore --staged 文件.md         # 取消暂存，文件内容还在
```

刚 commit、还没 push：

```bash
git commit --amend -m "改提交说明"   # 改上一条说明（或把漏掉的文件补进去再 amend）
```

已经 push 的提交不要 amend，也不要用 `reset --hard` 去改公共历史。

只想丢掉本地未提交改动、回到上次提交：

```bash
git restore .
```

## 临时搁置

切分支前有未完成的改动，又还不想 commit：

```bash
git stash -u                         # 搁置（含未跟踪文件）
git stash list
git stash pop                        # 取回并删掉这条 stash
git stash drop                       # 只删、不取回
```

## 最短流程

新仓库推上去：

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin <url>
git push -u origin main
```

已有仓库的日常：

```bash
git pull
git add .
git commit -m "说明"
git push
```

```
git pull          # 拉取最新代码，避免冲突
git status        # 确认要提交的文件
git diff          # 确认修改内容



git add .
git commit -m "[feat] 今日工作内容"
git push
```