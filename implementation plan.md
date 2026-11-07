# ImmortalWrt 23.05.2 编译与部署 OpenAppFilter 实施计划

## 1. 目标与环境参数
- **目标设备系统**：ImmortalWrt 23.05.2 (版本号: `r27625-416c8c5c91`)
- **硬件架构**：软路由（默认为 `x86/64`，若为 ARM64 替换对应 Target 即可）
- **内核驱动关键要求**：`kmod-oaf` 必须与固件内核符号及 vermagic 精准匹配。

## 2. 实施方案
### 方案 A：GitHub Actions 云端一键编译（零门槛、最推荐）
- 创建针对 ImmortalWrt 23.05.2 x86/64 的官方 SDK Actions 工作流。
- 自动拉取 SDK、注入 OpenAppFilter 代码、编译并自动打包下载 3 个核心 ipk：
  1. `kmod-oaf_*.ipk`
  2. `appfilter_*.ipk`
  3. `luci-app-oaf_*.ipk`

### 方案 B：本地 Linux / WSL 终端编译
- 搭建 Ubuntu/Debian 编译环境及依赖包。
- 下载 ImmortalWrt 23.05.2 对应官方 SDK。
- 配置 feeds 与 package，执行独立包编译。

### 软路由安装与配置
- 将编译生成的 ipk 文件通过 SCP 上传到路由器 `/tmp`。
- 安装 `luci-compat` 等必要依赖。
- 检查后台服务与网络加速冲突设置。
