---
title: VLC ActiveX 插件（IE 浏览器）
aliases:
  - VLC IE 插件
  - VLC ActiveX
  - IE 播 RTSP
created: 2026-08-07
updated: 2026-08-07
tags:
  - type/project
  - topic/vlc
  - topic/activex
  - topic/ie
  - topic/rtsp
  - status/draft
---

# VLC ActiveX 插件（IE 浏览器）

> [!summary]
> 在 **IE / IE 内核** 页面里用 **VLC ActiveX** 播本地文件或 RTSP 流：装 **32 位 VLC** 并勾选 ActiveX → 用固定 `classid` 嵌入 `<object>` → 用 `playlist` API 清列表、加地址、播放。

> [!warning]
> ActiveX 只适用于旧版 IE / 兼容模式环境。现代 Chrome / Edge / Firefox 不支持。生产环境勿把账号密码写死在页面里。

## 1. 安装

1. 安装 **32 位** VLC（IE 多为 32 位进程，64 位控件常加载失败）。
2. 安装时勾选 **ActiveX plugin**（ActiveX 插件）。
3. 用 IE 打开页面；若提示拦截 ActiveX，允许该控件运行。

## 2. 最小可用 HTML

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>VLC 播放</title>
</head>
<body>
  <input id="url" type="text" style="width:500px"
    value="rtsp://user:password@192.168.1.100:554/Streaming/Channels/101" />
  <button onclick="play()">播放</button>
  <br /><br />

  <object id="vlc"
    classid="clsid:9BE31822-FDAD-461B-AD51-BE1D1C159921"
    width="960" height="540">
    <param name="AutoPlay" value="False" />

              <param name="Control" value="false" />

              <param name="ShowControls" value="false" />

              <param name="ShowStatusBar" value="false" />

              <param name="ShowToolbar" value="false" />

              <param name="ShowCursor" value="false" />

              <param name="ShowFullScreenButton" value="false" />

              <param name="ShowZoomBar" value="false" />

              <param name="ShowNavigation" value="false" />
  </object>

  <script>
    function play() {
      var vlc = document.getElementById("vlc");
      vlc.playlist.items.clear();
      vlc.playlist.add(document.getElementById("url").value);
      vlc.playlist.play();
    }
  </script>
</body>
</html>
```

流程：`clear()` 清空列表 → `add(url)` 加入媒体 → `play()` 开始播放。

## 3. 关键代码说明

### 3.1 `<object>`：挂载 VLC 控件

```html
<object id="vlc"
  classid="clsid:9BE31822-FDAD-461B-AD51-BE1D1C159921"
  width="960" height="540">
```

| 属性                           | 作用                                                                        |
| ---------------------------- | ------------------------------------------------------------------------- |
| `id="vlc"`                   | JS 取控件实例的句柄                                                               |
| `classid="clsid:9BE31822-…"` | VLC ActiveX 的 CLSID；IE 靠它在注册表里找控件（9BE31822-FDAD-461B-AD51-BE1D1C159921）固定 |
| `width` / `height`           | 播放区域尺寸                                                                    |

### 3.2 `<param>`：初始化参数

```html
<param name="AutoPlay" value="False" />
```

`AutoPlay=False`：页面加载后不自动播，等用户点「播放」。

### 3.3 `playlist` API

| 调用 | 作用 |
| --- | --- |
| `playlist.items.clear()` | 清空播放列表 |
| `playlist.add(url)` | 追加媒体地址（文件路径或 RTSP 等 URL） |
| `playlist.play()` | 从当前项开始播放 |

## 4. 常用初始化参数

在 `<object>` 内用 `<param>` 设置：

| 参数名 | 取值 | 说明 |
| --- | --- | --- |
| `Src` | 路径 / URL | 初始媒体源（也可用 JS `playlist.add` 动态指定） |
| `AutoPlay` | `true` / `false` | 加载后是否自动播放 |
| `AutoLoop` | `true` / `false` | 播完是否循环 |
| `Volume` | `0`–`200` | 初始音量；`100` 为常态，`0` 静音 |
| `ShowDisplay` | `true` / `false` | 是否显示画面；`false` 时近似纯音频 |
| `Fullscreen` | `true` / `false` | 启动时是否全屏 |
| `Controls` | `true` / `false` | 是否显示控制栏 |
| `AllowFullScreen` | `true` / `false` | 是否允许用户切全屏 |

## 5. 常见问题

| 现象 | 优先排查 |
| --- | --- |
| 页面空白 / 控件不出现 | 是否装了 **32 位** VLC；安装时是否勾了 ActiveX；IE 是否拦截控件 |
| `playlist` 报错 | `id` 是否与 `getElementById` 一致；控件是否已成功加载 |
| RTSP 连不上 | 地址、账号、端口、通道号；本机防火墙；摄像机侧是否允许该客户端 |

