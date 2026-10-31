# 第三方来源

本项目原创代码、照片边框、姓名贴、卡片、示例图与图标按根目录 MIT 许可证发布。第三方内容保持各自许可，不适用根目录许可替代。

- 协议参考：xiaomi-photo-printer，MIT。https://github.com/tuat-yate/xiaomi-photo-printer ，见 `licenses/Bluetooth-MIT.txt`。
- 表情：Twemoji 14.0.2，Copyright Twitter, Inc. and other contributors，图形 CC BY 4.0。直接使用上游 SVG，未修改图形。https://github.com/twitter/twemoji/tree/v14.0.2/assets/svg ，见 `licenses/Twemoji-CC-BY-4.0.txt`。
- 字体：ZCOOL KuaiLe、Ma Shan Zheng，SIL OFL 1.1；版权声明和许可见 `assets/fonts/*-OFL.txt`。
- 日历数据：由 lunar_python 1.4.8（MIT）及 chinesecalendar 1.11.0（MIT）生成；见 `licenses/Calendar-*`。休息日安排数据截至 2026 年。
- 离线模型 U2NetP（Apache-2.0）、转换参考 rembg（MIT）、ONNX Runtime（MIT）：见 `assets/models/SOURCES.txt` 及同目录许可证。模型和运行时按校验值下载，不纳入 Git。

下载素材的 URL 和 SHA-256 见 `assets/provenance.json`。源码中的素材由本项目独立绘制，未使用官方模板、官方横版衍生图或旧姓名贴、卡片位图。保留第三方版权声明及许可证。

电脑服务通过 `web/requirements.txt` 安装依赖，不将其二进制或源码打包进 Git：
- aiohttp：Apache-2.0，https://github.com/aio-libs/aiohttp 。
- Pillow：MIT-CMU，https://github.com/python-pillow/Pillow 。
- PyCryptodome：BSD/Public Domain，https://www.pycryptodome.org/src/license 。
- NumPy：BSD-3-Clause 及其附带组件许可，https://numpy.org/doc/stable/license.html 。
- ONNX Runtime Python：MIT，来源同前述 ONNX Runtime。
Mac 蓝牙兼容实现沿用同一 MIT 协议参考；系统 IOBluetooth 框架不随仓库分发。
