# 共用编辑器与服务接口

`assets/` 是 App 与浏览器共用的编辑器、合成逻辑和原创素材。
Android WebView 使用 `Studio` 原生桥；普通浏览器由 `browser.js` 适配 HTTP。
浏览器和原生桥共用照片编辑参数和 `preparePrintPages()`，不维护第二份渲染器。

## HTTP

Android App 内主动开启共享，默认仅监听本机；同一 Wi-Fi 共享需单独选择。
端口 8634。浏览器先输入手机显示的配对码，服务设置 HttpOnly、SameSite=Strict 会话 Cookie。
所有 POST 必须携带与 Host 一致的 Origin；服务器仅接受自身监听地址作为 Host。
这是局域网 HTTP，照片传输未加密，只适用于可信家庭网络；不做公网映射。

- `POST /api/pair`：表单 `code`，成功后转到编辑器。
- `GET /api/state`：当前会话任务、历史和设备状态，不暴露其他浏览器照片。
- `POST /api/upload`：原始图片二进制，最多 25 MB；返回 `{src,width,height}`。Android 转为 JPEG 并限制长边 2400。
- `POST /api/cutout`：`{source}`，返回 `{images:{white,blue,red}}`。
- `POST /api/print`：`{requestId,pages}`，最多六张相纸；同会话同 requestId 同内容不重复入队，不同内容拒绝。
- `POST /api/connect`、`/api/reconcile`、`/api/cancel`：连接状态、查询自己的任务、取消自己的任务。
- `GET /private/...`：只能读取此会话导入或生成的图片。

`pages` 与原生 `printBatch` 一致：JPEG base64、media（5009/5012/5014）、copies、orientation、title、sharpen，可选 ocMask 与 threshold。
不允许用户传入服务器文件路径代替打印内容。预览和实际提交使用同一份合成输出。

## 任务与生命周期

共享服务使用 Android connectedDevice 前台服务，通知中可以停止。
打印与状态检查共用蓝牙互斥锁；远程请求进入串行队列，失败或结果未知时暂停，不自动重印。
停止共享会撤销配对并取消尚未开始的队列；已开始的批次继续由前台服务管理。
进程被杀后不自动恢复打印；再次开启共享时取消旧等待任务，未知的已提交任务需在手机上检查。
会话结束后浏览器草稿不能跨新会话读取旧私有照片，需重新选择照片。

## 电脑后端

`serve.py` 实现同一 HTTP 接口与会话隔离，默认端口 8635，照片合成仍在共用编辑器完成。
`bluetooth_client.py`、`bluetooth_printer.py`、`native/` 为独立 Mac 蓝牙后端；不导入其他项目、不调用旧 Web/AirPrint 服务。
跨进程设备锁仅用于避免两套程序同时占用同一台打印机，配置、数据和任务队列各自独立。
模拟模式不构建 BluetoothPrinter，也不启动蓝牙助手。
电脑端已提交任务支持请求取消；异常结果保留打印意图记录，暂停队列，不自动重印。电脑端支持查询已取得编号的原任务；没有任务编号或服务重启后的未知记录仍需在服务端核对。

## 迁移边界

共用编辑器、Android 承载 Web、电脑独立 Web 与蓝牙后端已进入同一仓库。
原电脑 Web、AirPrint/AirDrop 未移动、未改动，也未切换运行入口。新入口仍需用户确认使用体验后替换原服务。
手机 App 与浏览器使用相同的编辑数据、模板和合成实现；平台相关的文件导入、抠图与蓝牙能力保留独立适配。
