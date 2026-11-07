@echo off
chcp 936 >nul
title ImmortalWrt 23.05.2 - OpenAppFilter 一键上传与安装部署脚本

echo =====================================================================
echo           ImmortalWrt 23.05.2 - OpenAppFilter 一键部署脚本
echo =====================================================================
echo.

:: 自动防呆检索：如果在子文件夹解压，自动将 ipk 复制到当前目录
for /d %%d in (*) do (
    if exist "%%d\*oaf*.ipk" (
        echo 正在从子文件夹 [%%d] 自动提取 IPK 安装包...
        copy /y "%%d\*oaf*.ipk" . >nul 2>&1
        copy /y "%%d\*appfilter*.ipk" . >nul 2>&1
    )
)

echo 正在检查本地 IPK 安装包...
dir /b *oaf*.ipk *appfilter*.ipk 2>nul | findstr /i "ipk" >nul
if %errorlevel% neq 0 (
    echo [提示] 未发现 ipk 安装包！
    echo 请先将从 GitHub Actions 下载的 zip 压缩包解压，把里面的 .ipk 文件
    echo 放置在当前脚本同级目录下，然后再运行本脚本。
    echo.
    pause
    exit /b
)

echo [检测到以下待安装的 IPK 包]:
dir /b *oaf*.ipk *appfilter*.ipk
echo.

set /p ROUTER_IP=请输入您的软路由 IP 地址 (默认: 192.168.1.1): 
if "%ROUTER_IP%"=="" set ROUTER_IP=192.168.1.1

set /p ROUTER_USER=请输入软路由登录用户名 (默认: root): 
if "%ROUTER_USER%"=="" set ROUTER_USER=root

echo.
echo [1/3] 正在上传 IPK 安装包到软路由 /tmp 目录...
scp *oaf*.ipk *appfilter*.ipk %ROUTER_USER%@%ROUTER_IP%:/tmp/
if %errorlevel% neq 0 (
    echo.
    echo [错误] 文件上传失败，请检查软路由 IP 与密码是否正确！
    pause
    exit /b
)

echo.
echo [2/3] 正在远程连接软路由执行强制升级覆盖安装...
ssh %ROUTER_USER%@%ROUTER_IP% "killall -9 oafd rule_manager 2>/dev/null; opkg update && opkg install luci-compat libsqlite3 libcurl && cd /tmp && opkg install --nodeps --force-reinstall --force-downgrade kmod-oaf_*.ipk appfilter_*.ipk luci-app-oaf_*.ipk luci-i18n-oaf-zh-cn_*.ipk"

echo.
echo [3/3] 正在重启后台服务并刷新界面缓存...
ssh %ROUTER_USER%@%ROUTER_IP% "/etc/init.d/appfilter enable && /etc/init.d/appfilter restart && rm -rf /tmp/luci-*cache && /etc/init.d/rpcd restart && /etc/init.d/uhttpd restart"

echo.
echo =====================================================================
echo   [完成] OpenAppFilter v7.0 已成功覆盖部署到您的软路由！
echo   请在浏览器打开 http://%ROUTER_IP% 登录后台查看【应用过滤】。
echo   现在设置页面不会再出现“加载失败”，保存按钮已恢复正常！
echo =====================================================================
echo.
pause