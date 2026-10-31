# 留影工坊

共用编辑器的 Android App 与浏览器打印页面。支持米家桌面照片打印机 2；非官方项目。

## 构建

需要 Python 3、JDK、Android SDK（platforms/android-36、build-tools/37.0.0）。
设置 `JAVA_HOME` 与 `ANDROID_HOME` 后执行：

```sh
python3 fetch_deps.py
python3 build.py
```

输出 `build/liuying-studio.apk`。构建无需 Web 或 AirPrint 项目。依赖下载后可离线构建；App 的网络权限仅用于用户开启的本机与局域网共享服务。

首次构建生成本地调试密钥；密钥与安装包不提交。已安装版本的覆盖更新需要沿用原签名密钥。

## 使用

先在系统蓝牙中配对打印机。App 仅连接名称匹配的已配对设备；检测到多台时拒绝自动选择。
支持六寸、四寸拼接、三寸方形背胶；支持照片、姓名贴、月历、卡片、ID 卡贴与证件照。
证件照提供离线抠图和白、蓝、红底，保留原图。复杂边缘需检查预览。
打印结果不明确时不自动重印。蓝牙实现仅适用于经过授权的设备。

## 浏览器共享

App 的「更多 → 共享打印」可开启本机访问或同一 Wi-Fi 共享。
本机浏览器访问 `http://127.0.0.1:8634`；其他设备使用 App 显示的局域网地址，输入配对码。
照片、草稿和任务按浏览器会话隔离。打印共用串行队列；结果未知时暂停，不自动重印。
停止共享会撤销配对、取消尚未开始的远程任务；已开始的批次继续由通知中的服务管理。
需在解锁后的 App 前台开启，后台运行保留通知；系统强制停止或省电限制可能中断服务。

`assets/` 是两端唯一编辑器源文件；Android 原生能力在 `src/`。接口与迁移边界见 `web/CONTRACT.md`。
电脑服务入口为 `web/serve.py`，独立蓝牙后端与 Android 共用网页代码、素材和打印数据格式。旧 Web、AirPrint/AirDrop 源码与数据保留，可作为回退。

## 电脑服务

需要 Python 3.12+，真实蓝牙打印需要 macOS 与 Xcode Command Line Tools。

```sh
python3 -m venv build/venv
build/venv/bin/pip install -r web/requirements.txt
python3 web/build_bluetooth.py
build/venv/bin/python web/serve.py --simulate
```

默认地址 `http://127.0.0.1:8635`，配对码显示在终端。`--simulate` 只模拟任务，不会连接打印机。
真实打印先在系统配对打印机，再设置 `MIJIA_BLUETOOTH_ADDRESS`，去掉 `--simulate` 启动。
加 `--lan` 可提供局域网访问；数据默认保存在用户目录的 `Library/Application Support/LiuyingStudio`，不在仓库中。
照片合成在浏览器完成，电脑后端负责导入、抠图与蓝牙传输。HEIC 导入调用 macOS 系统图片转换工具。
抠图使用同一份 U2NetP 模型；模型未准备时执行 `python3 fetch_deps.py`，其余编辑功能不依赖模型。

打印结果未知时保留任务记录并暂停队列，不能直接重试；电脑端的异常记录仍需在服务端核对处理。
旧电脑 Web 源码与数据继续保留。新入口采用共用编辑器，可接管原 Web 和 AirPrint 端口；旧任务不会迁移或重放。

## 测试

`tests/` 包含浏览器、原生辅助类和设备验证脚本。浏览器测试需要 Playwright 与 Pillow；打印接口被拦截。
`tests/cdp.mjs` 用于通过 ADB 转发的 App 调试页面操作。设备测试前保存草稿，完成后恢复；不自动执行实物打印。

浏览器与模拟服务回归：`tests/check_browser_transport.py`、`tests/check_desktop_web.py`。
Android 队列测试：先安装当前 App 并停止共享，运行 `python3 tests/run_android_queue_test.py`，测试只在临时目录操作，不调用蓝牙。

## 发布仓库

这是独立的发布候选仓库，不继承开发仓库历史。原创内容采用 MIT，第三方许可见 `THIRD_PARTY.md`。
照片模板、姓名贴和卡片均由代码绘制；表情采用有明确授权的 Twemoji SVG。
公开包名 `local.liuying.studio` 与开发版隔离，安装后不会覆盖开发版数据。

运行 `python3 tests/check_release_assets.py` 检查素材来源和清单，浏览器回归见 `tests/check_release_artwork.py`。
此仓库尚未推送，未承诺所有适用法域下均无风险；兼容性与发布边界见 `RELEASE_REVIEW.md`。

## Mac AirPrint

`desktop/serve.py` 可单独开启 Web、单独开启 AirPrint，或同时开启两者。
两者只依赖 `printing/` 的公共队列，不互相导入入口。只有公共核心连接蓝牙；
同一数据目录或同一打印机的第二个服务会拒绝启动。两入口默认端口分别为 8635、8636。

```sh
build/venv/bin/python airprint/build_renderer.py
build/venv/bin/python desktop/serve.py --simulate
```

`--entry web` / `--entry airprint` 可只启用一个入口。模拟模式不允许 Bonjour 广播。
真实使用前先停止占用打印机的旧服务，再设置蓝牙地址，去掉 `--simulate`。
局域网 AirPrint 还需 `--lan --hostname 主机名.local --allow-network 可信网段 --announce`；
主机名须使用本机实际 Bonjour 名称，网段由用户指定。未传 `--announce` 不广播。
AirPrint 仅允许列出的可信网段，无账号认证；Web 仍需配对码。两入口均不用于公网。

默认 `--paper auto` 读取实际托盘，支持六寸、三寸方形背胶；
检测到六寸纸盒时，可在 Web 的打印机面板设置 AirPrint 整张六寸或两张四寸拼接；
也可使用 `--paper splice` 设置启动默认值。三寸纸盒始终输出三寸，不再提供强制纸型参数。
相纸状态定期刷新，发送前再次校验；不需要因换纸重启服务。
JPEG、PDF、URF、PWG 离线转换后进入相同队列；PDF 最多六页，拼接按每两页一张纸，
最后单页重复拼接。URF/PWG 只接受单页，拼接仅接受 JPEG/PDF，不会静默丢页。
AirPrint 每个任务一份；Web 的多份设置保持原有行为。

文档转换在有超时的独立子进程执行。重复请求返回原任务，重启不自动重发。
服务退出先停止接单、取消未开始任务，等待正在执行的蓝牙操作结束。
异常任务保留在服务数据目录，确认结果前暂停；原服务的任务记录不会迁移或重放。

AirPrint 在手机上的发现及最终输出仍需人工验收；离线测试不执行实物打印。

离线回归：`python -m unittest discover -s tests -p 'test_airprint*.py'`。
需要先构建渲染器并安装 `web/requirements.txt`；测试只使用合成图片和临时数据。

## 手机 AirPrint

App「更多 → 共享打印」可独立开启 AirPrint（8637 端口）。
同一 Wi-Fi 的 iPhone、Mac 可发现「留影工坊 · 手机」，通过系统打印菜单提交。
Web 与 AirPrint 共用手机队列，可同时开启、分别关闭；关闭一个入口只取消该入口尚未开始的任务。
AirPrint 不使用 Web 配对码，仅在可信局域网开启。后台运行保留通知。

手机独立解析 IPP，转换 JPEG、PDF、单页 URF/PWG，不依赖 Mac。
PDF 最多六页；四寸拼接仅支持 JPEG/PDF，每两页一张纸，奇数页重复最后一张。
仅接受单份、单面、8 位灰度或 sRGB 栅格；不支持的参数明确拒绝。
未连接、纸型未知、状态过期或蓝牙已释放时不接单。最终发送仍重新读取纸盒。
协议参考 [IPP 指南](https://www.pwg.org/ipp/ippguide.html) 和
[CUPS 栅格格式](https://openprinting.github.io/cups/libcups/spec-raster.html)。

`tests/AirPrintProtocolTest.java` 覆盖 IPP 和栅格；
`python3 tests/run_android_airprint_test.py` 使用手机隔离目录验证转换与队列，不启动蓝牙。
实机已验证 Mac 发现、HTTP/IPP 查询、后台与独立开关；iPhone 系统打印操作及纸面输出仍需人工验收。

## 编辑功能对齐

原创照片模板现支持六寸横竖版、三寸方形及四寸拼接的单幅比例。
拼接中每张照片独立选择模板，可与无模板照片混排；切换纸型保留选择。
模板缩略图、编辑画布和打印输出使用相同的几何参数。
选中文字或表情后支持 Delete/Backspace 删除，输入框内仍正常编辑文字。
竖屏的照片选择区紧贴底部五个工具；照片区域独立滚动，空页和选图后位置一致。

回归脚本：`tests/check_template_papers.py`、`tests/check_ui_parity.py`。
对齐记录和保留的平台差异见 `PARITY.txt`。测试不会实际打印。

## 连接恢复

服务启动不等待打印机上线。后台每分钟读取状态，失败后按退避间隔重试；
每次握手最多尝试两次，打印请求和上传不会自动重放。
状态读取与打印共用设备锁，忙时跳过后台探测。连接未确认时 AirPrint 暂不接单，
不公告未经确认的已装纸型；恢复后自动更新。`--printer-name` 可保留原 Bonjour 名称。

公共服务复用蓝牙连接，状态查询、打印和结果核对串行使用同一连接；断线后清理并重连，关停时释放设备锁。

打印机面板提供「释放蓝牙给其他设备」。释放后暂停该设备的自动探测，重新点「连接并刷新状态」才恢复。
从 Mac 切换到手机时先在 Mac Web 释放，再在手机连接；切回时顺序相反。不会强行断开另一台设备。
手机连接成功后在 App 前台或共享服务运行期间定期读取状态；超过 150 秒未确认的纸型不允许提交打印。
