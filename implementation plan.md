# OpenAppFilter 针对 sing-box 场景定制与中英文特征库合并实施方案

## 一、 中英文特征库合并实现计划

### 1. 数据来源分析
- **英文基础库**：当前项目中的 `open-app-filter/files/feature.bin` 解密后为纯正的海外热门应用（YouTube, Netflix, Facebook, X, Roblox, WhatsApp 等）。
- **中文基础库**：包含国内热门应用（微信、抖音、快手、王者荣耀、原神、B站等，在旧版 `feature_cn.cfg` 或在线 Lite 中文版中）。
- **合并规则**：
  1. 解析两套特征库中的 `#class` 类别（Chat, Game, Video, Shopping 等）。
  2. 合并各分类下的应用规则，保持各应用 AppID 不冲突（例如中文应用使用 `1001~`，英文应用使用 `1101~`）。
  3. 保留应用图标索引与七层协议正则/特征码。
  4. 使用相同的 XTEA-CTR 加密密钥（`0x8f4c29a1, 0x73b6d502, 0xc14e87f3, 0x2ad95b60`）和标准头部格式生成统一的 `/etc/fwxd/feature.bin`。

### 2. 成果产出
- 生成中英文双语全量 `feature.bin`，直接替换软路由上的文件，执行 `/etc/init.d/appfilter restart` 即可同时生效。

---

## 二、 sing-box + yacd 架构改造与融合评估

### 1. 业务流程对比
- **流量路径**：局域网客户端流量 -> Netfilter PREROUTING（OAF 先行捕获并识别真实客户端 MAC/应用）-> sing-box 透明代理转发（根据分流规则直连或走代理节点）。
- **交互整合方式**：
  - 调研 yacd 控制面板的扩展能力，探讨是在 yacd 中增加 OAF 控制卡片，还是提供轻量级联动方案。
