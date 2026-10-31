# 第三方来源

原创代码、模板、姓名贴、卡片及图标采用根目录 MIT；第三方内容沿用各自许可。

| 内容 | 来源与版本 | 许可文件 |
| --- | --- | --- |
| 蓝牙协议参考 | [xiaomi-photo-printer](https://github.com/tuat-yate/xiaomi-photo-printer) | `licenses/Bluetooth-MIT.txt` |
| 表情，未修改上游 SVG | [Twemoji 14.0.2](https://github.com/twitter/twemoji/tree/v14.0.2/assets/svg)，Twitter, Inc. and other contributors | `licenses/Twemoji-CC-BY-4.0.txt` |
| 字体 | ZCOOL KuaiLe、Ma Shan Zheng | `assets/fonts/*-OFL.txt` |
| 日历数据 | lunar_python 1.4.8、chinesecalendar 1.11.0；休息日截至2026年 | `licenses/Calendar-*.txt` |
| 抠图模型与转换参考 | U2NetP（Apache-2.0）、rembg（MIT） | `assets/models/` |
| 人脸检测 | OpenCV Zoo YuNet 2023mar（MIT） | `assets/models/YuNet-MIT.txt` |
| Android推理运行时 | ONNX Runtime 1.23.2（MIT及捆绑组件许可） | `assets/models/ONNXRuntime-LICENSE.txt`、`ONNXRuntime-ThirdPartyNotices.txt` |

素材下载地址与校验值见 `assets/provenance.json`；模型固定版本、来源和校验值见 `assets/models/SOURCES.txt`。模型及运行时按需下载，不纳入Git。APK随包保留 `assets/licenses/`、字体和模型目录中的许可全文；第三方作者署名不可删除。

电脑依赖通过 `web/requirements.txt` 安装，不随仓库打包：

| 依赖 | 许可与来源 |
| --- | --- |
| aiohttp | [Apache-2.0](https://github.com/aio-libs/aiohttp) |
| Pillow | [MIT-CMU](https://github.com/python-pillow/Pillow) |
| PyCryptodome | [BSD/Public Domain](https://www.pycryptodome.org/src/license) |
| NumPy | [BSD-3-Clause及附带声明](https://numpy.org/doc/stable/license.html) |
| ONNX Runtime | [MIT及附带声明](https://github.com/microsoft/onnxruntime) |
| pypdf | [BSD-3-Clause](https://github.com/py-pdf/pypdf) |

系统 IOBluetooth、CoreGraphics/CUPS 不随仓库分发。测试人像是NASA公共领域图片，来源见 `tests/fixtures/faces/SOURCES.txt`，不作为App素材打包；其他打印测试夹具由代码生成。
