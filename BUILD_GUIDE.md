# ImmortalWrt 23.05.2 编译与部署 OpenAppFilter 完全实战指南

本文档提供在 **本地 Ubuntu / Debian / WSL 环境** 下编译并部署 OpenAppFilter 7.0 到 **ImmortalWrt 23.05.2 (r27625-416c8c5c91, x86_64)** 软路由的完整实操流程。

---

## 一、环境准备（Ubuntu 20.04/22.04 或 WSL2）

在您的 Linux 终端中安装基础编译工具链：
```bash
sudo apt-get update
sudo apt-get install -y build-essential libncurses5-dev libncursesw5-dev \
    zlib1g-dev gawk git gettext libssl-dev xsltproc rsync wget unzip python3 \
    tar xz-utils file
```

---

## 二、下载与解压 ImmortalWrt 23.05.2 官方 SDK

如果您的软路由是常见的 **x86_64** 架构（绝大多数软路由如工控机、J4125、N5105、N100 等）：

```bash
# 1. 创建工作目录
mkdir -p ~/immortalwrt-sdk && cd ~/immortalwrt-sdk

# 2. 下载 ImmortalWrt 23.05.2 官方 x86/64 SDK (约 368MB，注意后缀是 .tar.xz)
wget https://downloads.immortalwrt.org/releases/23.05.2/targets/x86/64/immortalwrt-sdk-23.05.2-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz

# 3. 解压 SDK 并进入目录
tar -xf immortalwrt-sdk-23.05.2-*.tar.xz
cd immortalwrt-sdk-23.05.2-*
```

---

## 三、导入 OpenAppFilter 7.0 源码与剔除旧版 Feeds（极关键！）

```bash
# 1. 更新并安装 SDK 基础依赖 Feeds
./scripts/feeds update -a
./scripts/feeds install -a

# 2. 【核心避坑】彻底清理 feeds 中自带的 2023 老旧包 (防止官方源旧版本覆盖当前 7.0 源码)
./scripts/feeds uninstall appfilter luci-app-oaf kmod-oaf 2>/dev/null || true
rm -rf feeds/packages/net/appfilter feeds/luci/applications/luci-app-oaf 2>/dev/null || true
rm -rf package/feeds/packages/appfilter package/feeds/luci/luci-app-oaf 2>/dev/null || true

# 3. 将当前仓库的真实 7.0 模块引入 package 目录
rm -rf package/luci-app-oaf package/oaf package/open-app-filter
cp -r ../OpenAppFilter/luci-app-oaf package/
cp -r ../OpenAppFilter/oaf package/
cp -r ../OpenAppFilter/open-app-filter package/

# 4. 显式开启 OAF 7.0 模块编译配置
echo "CONFIG_PACKAGE_kmod-oaf=m" >> .config
echo "CONFIG_PACKAGE_appfilter=m" >> .config
echo "CONFIG_PACKAGE_luci-app-oaf=m" >> .config
make defconfig
```

---

## 四、执行独立编译

单独并发编译 OAF 相关的三个子软件包（耗时约 2~3 分钟）：

```bash
make package/oaf/compile V=s -j$(nproc)
make package/open-app-filter/compile V=s -j$(nproc)
make package/luci-app-oaf/compile V=s -j$(nproc)
```

编译完成后，在 `bin/` 目录下即可提取出 4 个文件：
1. **`kmod-oaf_5.15.150..._x86_64.ipk`**（内核驱动模块）
2. **`appfilter_7.0.2-1_x86_64.ipk`**（新版 7.0 后台守护程序，原生提供 `fwx` 接口）
3. **`luci-app-oaf_7.0_all.ipk`**（现代化管理界面）
4. **`luci-i18n-oaf-zh-cn_unknown_all.ipk`**（简体中文汉化包）

---

## 五、软路由部署与避坑

### 1. 安装命令
上传到路由器 `/tmp` 目录后执行：
```bash
opkg update
opkg install luci-compat libsqlite3 libcurl
cd /tmp
opkg install --nodeps --force-reinstall --force-downgrade kmod-oaf_*.ipk appfilter_*.ipk luci-app-oaf_*.ipk luci-i18n-oaf-zh-cn_*.ipk
/etc/init.d/appfilter enable
/etc/init.d/appfilter restart
```

### 2. 关闭网络加速（防止过滤失效）
前往软路由后台 **【网络】->【Turbo ACC 网络加速】**，关闭 **【软件流量分流 (Flow Offloading)】** 与 **【硬件流量分流】**。
