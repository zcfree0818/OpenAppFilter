# OpenAppFilter 中英文全量特征库与旁路由纯统计模式使用指南

## 一、 中英文特征库同步生效原理

官方 OpenAppFilter 原生设计中，中文特征库与英文特征库相互独立，切换中文则英文丢失，切换英文则中文丢失。主要原因在于官方在两套特征库中复用了部分 `AppID`（例如 `3101` 在中文库为豆瓣电影，在英文库为 YouTube）。

本项目通过逆向官方加密算法（**XTEA-CTR**，密钥：`0x8f4c29a1, 0x73b6d502, 0xc14e87f3, 0x2ad95b60`），实现了特征库的明文提取、冲突消解、智能合并与重新打包：

1. **保留全部中文应用（358 款）**：微信、QQ、抖音、快手、B站、王者荣耀、支付宝等完整保留。
2. **完整接入国际主流应用（48 款）**：YouTube、Netflix、X (Twitter)、Facebook、WhatsApp、Instagram、Roblox、Twitch、Spotify、Google、GitHub、Amazon 等。
3. **冲突重映射机制**：对冲突的 11 款海外视频/网站应用安全重分配至未被占用的 AppID 区间（如 YouTube -> `3201`，NetFlix -> `3203`，Reddit -> `8210` 等），实现 **406 款应用** 完美共存、零冲突、双语全量实时识别。

---

## 二、 旁路由 + sing-box (yacd) 架构下的统计保障

### 1. 两者是否会冲突？
- **结论：完全不冲突，且互为完美补充！**
- **原理分工**：
  - **sing-box + yacd**：工作在用户态（TUN 虚拟网卡或 TPROXY 端口重定向），主要职责是节点选路与代理转发；yacd 统计的是代理连接的域名和出站流量。
  - **OpenAppFilter (OAF)**：工作在 Linux 内核态底层（Netfilter `PREROUTING` 钩子），在数据包刚进入网卡尚未被路由、转发或代理劫持前，直接捕获七层应用特征（DPI 深度包检测），记录应用的流量和时长。
- **纯统计模式建议**：
  - 在 OpenAppFilter Web 后台保持【应用过滤】规则为空（不添加任何拦截阻断规则），只开启主开关和应用记录。
  - 内核处于纯被动监听模式（对网络 0 侵入、0 延迟、0 丢包），仅做数据统计与设备画像。

### 2. 旁路由数据防漏抓关键：MASQUERADE 动态伪装
由于上网终端将网关指向旁路由，回包若经由主路由直接返回给终端，将形成“异步路由（非对称路由）”，可能导致部分长连接或下行流量漏统。

**解决方案**：
在旁路由的防火墙中增加一条局域网转发伪装规则：
```bash
iptables -t nat -I POSTROUTING -o br-lan -j MASQUERADE
```
> **固化方法**：登录 ImmortalWrt 后台 -> 【网络】-> 【防火墙】-> 【自定义规则】最底部追加上述命令，点击【重启防火墙】即可永久生效。

---

## 三、 特征库一键更新与替换方法

### 方法 1：使用自动化脚本一键更新（推荐）
在 Windows 终端中双击运行当前目录下的批处理脚本：
```cmd
update_feature_to_router.bat
```
按提示输入软路由 IP 和 SSH 端口，脚本将自动完成：
1. 将全新 `feature.bin` 安全推送到软路由 `/tmp/` 目录。
2. 自动备份软路由原有 `/etc/fwxd/feature.bin` 为 `/etc/fwxd/feature.bin.bak`。
3. 替换并平滑重启 `appfilter` 服务。

### 方法 2：命令行手动替换
```bash
# 1. 备份原特征库
cp /etc/fwxd/feature.bin /etc/fwxd/feature.bin.bak

# 2. 上传并覆盖新特征库
# (在 Windows 运行: scp feature.bin root@192.168.1.1:/etc/fwxd/feature.bin)

# 3. 重启应用过滤服务使特征库生效
/etc/init.d/appfilter restart
```

---

## 四、 特征库维护与自定义扩展

如果未来想自己增加新的应用识别规则，可使用本项目提供的 Python 工具：
- `feature_merged_plain.txt`：明文规则文件，可在对应分类下自由增加规则行（语法：`AppID~应用名:[proto;sport;dport;host url;request;dict;search str;ignore]`）。
- 运行合并与打包脚本：
```bash
python tools/merge_features.py
```
脚本将自动计算 CRC32、通过 XTEA-CTR 算法加密并输出标准的 `feature.bin`。
