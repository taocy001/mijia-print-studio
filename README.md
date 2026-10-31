# 留影工坊 Android

独立的本地照片编辑与蓝牙打印 App。支持米家桌面照片打印机 2；非官方项目。

## 构建

需要 Python 3、JDK、Android SDK（platforms/android-36、build-tools/37.0.0）。
设置 `JAVA_HOME` 与 `ANDROID_HOME` 后执行：

```sh
python3 fetch_deps.py
python3 build.py
```

输出 `build/liuying-studio.apk`。构建无需 Web 或 AirPrint 项目。依赖下载后可离线构建；App 不请求联网权限。

首次构建生成本地调试密钥；密钥与安装包不提交。已安装版本的覆盖更新需要沿用原签名密钥。

## 使用

先在系统蓝牙中配对打印机。App 仅连接名称匹配的已配对设备；检测到多台时拒绝自动选择。
支持六寸、四寸拼接、三寸方形背胶；支持照片、姓名贴、月历、卡片、ID 卡贴与证件照。
证件照提供离线抠图和白、蓝、红底，保留原图。复杂边缘需检查预览。
打印结果不明确时不自动重印。蓝牙实现仅适用于经过授权的设备。

## 测试

`tests/` 包含浏览器、原生辅助类和设备验证脚本。浏览器测试需要 Playwright 与 Pillow；打印接口被拦截。
`tests/cdp.mjs` 用于通过 ADB 转发的 App 调试页面操作。设备测试前保存草稿，完成后恢复；不自动执行实物打印。

## 发布仓库

这是独立的发布候选仓库，不继承开发仓库历史。原创内容采用 MIT，第三方许可见 `THIRD_PARTY.md`。
照片模板、姓名贴和卡片均由代码绘制；表情采用有明确授权的 Twemoji SVG。
公开包名 `local.liuying.studio` 与开发版隔离，安装后不会覆盖开发版数据。

运行 `python3 tests/check_release_assets.py` 检查素材来源和清单，浏览器回归见 `tests/check_release_artwork.py`。
此仓库尚未推送，未承诺所有适用法域下均无风险；兼容性与发布边界见 `RELEASE_REVIEW.md`。
