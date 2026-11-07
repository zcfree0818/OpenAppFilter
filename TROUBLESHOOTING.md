# ImmortalWrt 23.05.2 部署 OpenAppFilter 踩坑与常见问题排查全手册

本手册收录了在 **ImmortalWrt 23.05.2 (x86_64, Linux 5.15)** 软路由上编译、部署与运行 OpenAppFilter 过程中遇到的所有真实问题、底层机理与终极解决方案。

---

## 目录
1. [【必看踩坑】设置页面提示“加载失败”，保存按钮为半透明不可点击](#1-必看踩坑设置页面提示加载失败保存按钮为半透明不可点击)
2. [终端运行 oafd 报 `Bind failed Address in use` 或 `Failed to publish object`](#2-终端运行-oafd-报-bind-failed-address-in-use-或-failed-to-publish-object)
3. [安装第 4 个包时提示 `can't open '/etc/uci-defaults/luci-i18n-oaf-zh-cn'`](#3-安装第-4-个包时提示-cant-open-etcuci-defaultsluci-i18n-oaf-zh-cn)
4. [安装第 2 个包时提示 `rm: can't remove '/tmp/feature.cfg': No such file...`](#4-安装第-2-个包时提示-rm-cant-remove-tmpfeaturecfg-no-such-file)
5. [配置了拦截规则，但手机依然能正常刷视频 / 仪表盘没有流量数据](#5-配置了拦截规则但手机依然能正常刷视频--仪表盘没有流量数据)
6. [安装内核驱动时提示 `kernel vermagic mismatch`](#6-安装内核驱动时提示-kernel-vermagic-mismatch)

---

### 1. 【必看踩坑】设置页面提示“加载失败”，保存按钮为半透明不可点击

#### 现象：
登录管理后台进入【设置】页面，底部【保存】按钮呈现禁用状态，并带有小红字提示“加载失败”。同时在【仪表盘】中右侧的“OAF状态”（工作模式、服务版本、引擎版本）全为空白。

#### 根本原因：
**编译时误混入了 ImmortalWrt 官方 feeds 中自带的 2023 年老版本后台包！**
- **老版后台 (`appfilter 2023-05-25`)**：在系统中暴露的 ubus 对象名称为 `appfilter`。
- **新版前端 (`luci-app-oaf 7.0`)**：调用接口时请求的是 `fwx` 对象（`ubus call fwx common`）。
- **结果**：新前端找不到老后端的接口，前后端协议脱节，所有配置数据无法加载，触发前端自我保护并禁用了保存按钮。

#### 彻底解决方案：
在编译前彻底清除 feeds 中自带的旧版包软链接，强制编译当前仓库原生的 7.0 模块：
```bash
./scripts/feeds uninstall appfilter luci-app-oaf kmod-oaf 2>/dev/null || true
rm -rf feeds/packages/net/appfilter feeds/luci/applications/luci-app-oaf 2>/dev/null || true
rm -rf package/feeds/packages/appfilter package/feeds/luci/luci-app-oaf 2>/dev/null || true
```
重新编译并安装 `appfilter_7.0.2-1_x86_64.ipk` 即可瞬间秒解！

---

### 2. 终端运行 oafd 报 `Bind failed Address in use` 或 `Failed to publish object`

#### 现象：
在软路由命令行手动执行 `/usr/bin/oafd`，终端回显：
```text
Failed to publish object 'appfilter': Invalid argument
Bind failed Address in use
```

#### 原因：
1. 后台已有进程占用了 Netlink 端口（`DEFAULT_FWX_NL_PID`）以及 ubus 对象。
2. 或者是旧版守护进程已在后台自启运行。

#### 解决办法：
强制杀掉旧进程并重启服务：
```bash
killall -9 oafd rule_manager 2>/dev/null
/etc/init.d/appfilter restart
```

---

### 3. 安装第 4 个包时提示 `can't open '/etc/uci-defaults/luci-i18n-oaf-zh-cn'`

#### 现象：
上传安装 `luci-i18n-oaf-zh-cn` 简体中文语言包时，控制台报错：
`can't open '/etc/uci-defaults/luci-i18n-oaf-zh-cn': No such file or directory`。

#### 原因与结论：
**属于完全正常的无害提示，语言包实际上已经成功安装！**
- 核心汉化二进制字典（`/usr/lib/lua/luci/i18n/oaf.zh-cn.lmo`）早已成功写入系统。
- 报错只是因为该包自带的初始化脚本用于在配置文件中声明中文支持，执行完毕后系统自动删除了它，包管理器二次探测时报了找不到临时文件的警告。
- 刷新后台页面后，界面已完全汉化。

---

### 4. 安装第 2 个包时提示 `rm: can't remove '/tmp/feature.cfg': No such file...`

#### 现象：
安装 `appfilter` 包后系统弹出：
`rm: can't remove '/tmp/feature.cfg': No such file or directory`。

#### 原因与结论：
**正常无害提示！**
首次安装时，程序在初始化启动阶段会尝试清理旧特征缓存，因为是第一次安装，`/tmp` 下本来就没有旧缓存，所以打印了该系统提示。随后程序就会自动生成全新特征库并正常工作。

---

### 5. 配置了拦截规则，但手机依然能正常刷视频 / 仪表盘没有流量数据

#### 根本原因：
软路由开启了 **Turbo ACC 网络加速 / 软件流量分流 (Flow Offloading)**！
流卸载功能将数据包在网卡底层直接短路转发，**绕过了 Netfilter 内核钩子**，导致应用过滤的 DPI 引擎抓不到流量包。

#### 解决方案：
1. 进入软路由后台 **【网络】->【Turbo ACC 网络加速】**。
2. 将 **【软件流量分流 (Flow Offloading)】** 和 **【硬件流量分流】** 全部设为 **关闭** 并保存应用。
3. 检查 LAN 接口名称：进入【应用过滤】->【设置】，确认监控网口为实际的局域网口（如 `br-lan` 或 `eth0`）。

---

### 6. 安装内核驱动时提示 `kernel vermagic mismatch`

#### 现象：
安装 `kmod-oaf` 时提示内核版本校验码不匹配。

#### 解决方案：
只要固件内核大版本一致（如 Linux 5.15.x），可以加上 `--nodeps` 强制忽略签名验证安装：
```bash
opkg install --nodeps /tmp/kmod-oaf_*.ipk
modprobe oaf
lsmod | grep oaf
```
只要 `lsmod` 显示包含 `oaf` 模块，即代表驱动完全正常挂载运行！
