# OpenAppFilter (OAF) 官方与 ImmortalWrt 23.05.2 专属适配项目

本项目已完成对源码的安全审计与 ImmortalWrt 23.05.2 (x86_64, Linux 5.15.150) 的深度适配，支持通过 **GitHub Actions 5分钟云端一键全自动编译**，并修复了官方 feeds 旧包混入导致的“加载失败”与协议脱节问题。

---

## 快速实战导航

- 📘 [踩坑与排错完全手册 (TROUBLESHOOTING.md)](./TROUBLESHOOTING.md)：收录“加载失败”、Netlink 端口占用、界面汉化、流卸载加速冲突等全部真实问题与解法。
- 🛠️ [本地编译实战指南 (BUILD_GUIDE.md)](./BUILD_GUIDE.md)：本地 Ubuntu/WSL 结合官方 SDK 编译命令。
- 🚀 [GitHub Actions 云端工作流 (.github/workflows/build-oaf.yml)](./.github/workflows/build-oaf.yml)：直接在网页端点击 Run workflow 即可免费出包。
- 💻 [Windows 一键部署脚本 (deploy_to_router.bat)](./deploy_to_router.bat)：本地自动穿透解压包并一键 SSH 推送安装。

---

## 核心避坑要点（必看）

1. **避免 Feeds 旧包污染**：
   ImmortalWrt 官方 feeds 中自带了 2023 年老版 `appfilter`。编译前必须先卸载 feeds 中的旧版软链接，否则会导致新版 7.0 前端找不到后端的 `fwx` 对象，引发**“加载失败且保存按钮禁用”**。
2. **关闭网络加速 / 流量分流**：
   软路由若开启了 Turbo ACC 中的【软件流量分流 (Flow Offloading)】或【硬件流量分流】，流量会直接绕过 Netfilter 内核钩子，导致应用过滤抓不到包而失效。使用 OAF 前必须将其关闭。
3. **前置依赖安装**：
   ImmortalWrt 23.05 采用现代客户端渲染，必须提前安装 `luci-compat`、`libsqlite3` 与 `libcurl`。

---

## Introduction
OAF is a parental control software based on OpenWrt. It supports popular applications across gaming, video streaming, instant messaging, such as TikTok, YouTube, Facebook. Currently, it supports hundreds of different applications.   
For a detailed introduction, please visit [www.openappfilter.com](http://www.openappfilter.com).

## Features
- DPI-based protocol identification: Supports Layer 7 protocol parsing and HTTPS domain resolution, and operates independently of DNS.
- Industry-standard architecture: Flow-based identification for high efficiency, with extremely low hardware requirements.
- Supports custom protocol signatures: Offers a high degree of flexibility and customization.
- Supports installation as a plugin on OpenWrt systems: Compatible with all OpenWrt-enabled devices.

## How to Compile (SDK or Source)
Detailed step-by-step guides for compiling on modern ImmortalWrt / OpenWrt releases can be found in [BUILD_GUIDE.md](./BUILD_GUIDE.md) and [.github/workflows/build-oaf.yml](./.github/workflows/build-oaf.yml).

## License
- Individuals can use this software completely free of charge, and are also permitted to develop upon and redistribute it.
- Non-commercial and commercial users must retain our copyright information.
- Commercial users are required to display "Powered by OpenAppFilter" on the web management page.
- Modifying the code or directly removing the copyright will be considered a copyright infringement.
