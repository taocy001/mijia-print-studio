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
电脑服务入口为 `web/serve.py`，独立蓝牙后端与 Android 共用网页代码、素材和打印数据格式。原有 Web、AirPrint/AirDrop 服务未改动。

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
现有电脑 Web 服务继续保留。新入口不复制旧布局代码，采用共用编辑器，尚未替换原服务。

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
四寸拼接需显式 `--paper splice`。也可固定 `--paper six` 或 `--paper square`，
发送前仍校验实际相纸，纸型不匹配拒绝打印。切换纸张后重启服务以刷新公告。
JPEG、PDF、URF、PWG 离线转换后进入相同队列；PDF 最多六页，拼接按每两页一张纸，
最后单页重复拼接。URF/PWG 只接受单页，拼接仅接受 JPEG/PDF，不会静默丢页。
AirPrint 每个任务一份；Web 的多份设置保持原有行为。

文档转换在有超时的独立子进程执行。重复请求返回原任务，重启不自动重发。
服务退出先停止接单、取消未开始任务，等待正在执行的蓝牙操作结束。
异常任务保留在服务数据目录，确认结果前暂停；原服务的任务记录不会迁移或重放。

本次仅集成代码并进行模拟测试，未替换旧服务、未广播新打印机、未实物打印。
AirPrint 在手机上的发现、纸型展示及最终输出仍需人工验收。

离线回归：`python -m unittest discover -s tests -p 'test_airprint*.py'`。
需要先构建渲染器并安装 `web/requirements.txt`；测试只使用合成图片和临时数据。
