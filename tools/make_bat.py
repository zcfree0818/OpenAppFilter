# -*- coding: utf-8 -*-
bat_text = """@echo off
chcp 936 >nul
title OpenAppFilter 中英文全量特征库一键更新工具
color 0b

echo ======================================================================
echo          OpenAppFilter 中英文双语全量特征库一键更新部署工具
echo ======================================================================
echo.
echo 特征库详情:
echo   - 状态: 中英文双语特征库合并无冲突版 (v26.11.08)
echo   - 应用总数: 406 款 (国内 358 款 + 国际 48 款海外主流应用)
echo   - 覆盖应用: 微信/抖音/B站/王者荣耀 + YouTube/Netflix/X/Roblox/Google 等
echo.

set ROUTER_IP=192.168.1.1
set ROUTER_PORT=22
set ROUTER_USER=root

set /p INPUT_IP=请输入旁路由/软路由 IP 地址 (直接回车默认 192.168.1.1): 
if not "%INPUT_IP%"=="" set ROUTER_IP=%INPUT_IP%

set /p INPUT_PORT=请输入 SSH 端口号 (直接回车默认 22): 
if not "%INPUT_PORT%"=="" set ROUTER_PORT=%INPUT_PORT%

echo.
echo [*] 目标软路由: %ROUTER_USER%@%ROUTER_IP%:%ROUTER_PORT%
echo [*] 正在将全新中英文特征库 feature.bin 推送到软路由 /tmp/ ...

scp -P %ROUTER_PORT% feature.bin %ROUTER_USER%@%ROUTER_IP%:/tmp/feature.bin
if errorlevel 1 (
    echo.
    echo [错误] 文件传输失败，请检查 IP、端口或 SSH 密钥/密码是否正确。
    pause
    exit /b 1
)

echo.
echo [*] 文件传输成功！正在软路由上应用并重启 OAF 服务...

ssh -p %ROUTER_PORT% %ROUTER_USER%@%ROUTER_IP% "mkdir -p /etc/fwxd && cp -f /etc/fwxd/feature.bin /etc/fwxd/feature.bin.bak 2>/dev/null; mv -f /tmp/feature.bin /etc/fwxd/feature.bin && /etc/init.d/appfilter restart"

echo.
echo ======================================================================
echo [√] 中英文双语特征库已成功部署生效！
echo ======================================================================
echo.
echo [旁路由模式关键提示]:
echo 1. 请刷新 OpenWrt/ImmortalWrt 后台【应用过滤】->【特征库】页面。
echo    此时特征库版本将显示为最新版本，应用总数达 400+ 款。
echo 2. 在【仪表板】或【应用记录】中，国内和海外主流应用都将被实时识别并统计。
echo 3. 若旁路由未开启 MASQUERADE 导致回包绕过旁路由从而漏抓数据，可在软路由运行:
echo    iptables -t nat -I POSTROUTING -o br-lan -j MASQUERADE
echo.
pause
"""

crlf_content = bat_text.replace('\r\n', '\n').replace('\n', '\r\n')
with open('update_feature_to_router.bat', 'wb') as f:
    f.write(crlf_content.encode('gbk'))
print("Successfully generated update_feature_to_router.bat with GBK and CRLF.")
