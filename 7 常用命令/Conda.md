# Conda 常用命令

## 环境

```bash
conda create -n myenv python=3.11   # 创建环境
conda env list                      # 查看环境
conda activate myenv                # 激活
conda deactivate                    # 退出
conda remove -n myenv --all         # 删除环境
```

## 包

```bash
conda install numpy                 # 安装
conda install numpy=1.26            # 指定版本
conda update numpy                  # 更新
conda remove numpy                  # 卸载
conda list                          # 查看已安装
conda search pytorch                # 搜索
```

conda 没有的包，激活环境后用：`pip install 包名`

## 导出 / 复现

```bash
conda env export --from-history > environment.yml   # 导出
conda env create -f environment.yml                 # 按文件创建
```

## 频道

```bash
conda config --add channels conda-forge             # 添加频道
conda install -c conda-forge jupyterlab             # 临时用某频道安装
```

## 清理

```bash
conda clean -a                      # 清缓存
conda update conda                  # 更新 conda
```

## 最短流程

```bash
conda create -n myenv python=3.11 -y
conda activate myenv
conda install numpy pandas -y
conda deactivate
```
