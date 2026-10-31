import Foundation
@preconcurrency import IOBluetooth
import Darwin

final class Transport: NSObject, IOBluetoothRFCOMMChannelDelegate, IOBluetoothDeviceAsyncCallbacks {
 var device: IOBluetoothDevice!
 var channel: IOBluetoothRFCOMMChannel?
 var opened=false
 var phase="baseband"
 func remoteNameRequestComplete(_ device:IOBluetoothDevice,status:IOReturn) {}
 func connectionComplete(_ device:IOBluetoothDevice,status:IOReturn) {
  guard status==0 else { fail("baseband \(status)") };print("INFO baseband connected");query()
 }
 func start() {
  guard let address=ProcessInfo.processInfo.environment["MIJIA_BLUETOOTH_ADDRESS"] else { fail("printer address required") }
  device=IOBluetoothDevice(addressString:address)
  guard device != nil else { fail("device unavailable") }
  print("INFO paired=\(device.isPaired()) connected=\(device.isConnected())")
  if device.isConnected(){query()}else{let result=device.openConnection(self,withPageTimeout:10000,authenticationRequired:true);if result != 0 {fail("baseband start \(result)")}}
  DispatchQueue.main.asyncAfter(deadline:.now()+25){if !self.opened { self.fail("connection timeout at \(self.phase)") }}
 }
 func query(){
  if let value=ProcessInfo.processInfo.environment["MIJIA_RFCOMM_CHANNEL"],let id=UInt8(value),id>0,id<=30 {openChannel(id);return}
  phase="service discovery"
  let result=device.performSDPQuery(self);if result != 0 {fail("SDP start \(result)")}
 }
 func sdpQueryComplete(_ device:IOBluetoothDevice,status:IOReturn) {
  guard status==0 else { fail("SDP \(status)") }
  guard let record=(device.services as? [IOBluetoothSDPServiceRecord])?.first(where: { ($0.getServiceName() ?? "")=="SerialPort" }) ?? device.getServiceRecord(for:IOBluetoothSDPUUID(uuid16:0x1101)) else { fail("printer service absent") }
  var id:BluetoothRFCOMMChannelID=0
  guard record.getRFCOMMChannelID(&id)==0,id>0 else { fail("SPP channel absent") }
  openChannel(id)
 }
 func openChannel(_ id:BluetoothRFCOMMChannelID){
  phase="RFCOMM channel \(id)"
  print("INFO channel=\(id) encryption=\(device.getEncryptionMode())")
  let result=device.openRFCOMMChannelAsync(&channel,withChannelID:id,delegate:self)
  print("INFO async open started=\(result)")
  if result != 0 {fail("RFCOMM start \(result)")}

 }
 func rfcommChannelOpenComplete(_ c:IOBluetoothRFCOMMChannel,status:IOReturn) {
  if opened{return}
  guard status==0 else { fail("RFCOMM open \(status)") }
  channel=c;opened=true;print("READY \(c.getMTU())")
  DispatchQueue.global().async {
   while let line=readLine() {
    if line=="CLOSE" { DispatchQueue.main.async { self.close() }; return }
    guard line.count%2==0 else { self.fail("invalid input") }
    var data=Data();var index=line.startIndex
    while index<line.endIndex {let next=line.index(index,offsetBy:2);guard let b=UInt8(line[index..<next],radix:16) else { self.fail("invalid hex") };data.append(b);index=next}
    var offset=0
    while offset<data.count {
     let n=min(Int(c.getMTU()),data.count-offset)
     var chunk=Data(data[offset..<offset+n])
     let result=chunk.withUnsafeMutableBytes{c.writeSync($0.baseAddress,length:UInt16(n))}
     if result != 0 { self.fail("write \(result)") };offset+=n
    }
    print("SENT")
   }
   DispatchQueue.main.async { self.close() }
  }
 }
 func rfcommChannelData(_ c:IOBluetoothRFCOMMChannel,data pointer:UnsafeMutableRawPointer,length:Int) {
  print("DATA "+Data(bytes:pointer,count:length).map{String(format:"%02x",$0)}.joined())
 }
 func rfcommChannelClosed(_ c:IOBluetoothRFCOMMChannel){fail("disconnected")}
 func close(){channel?.setDelegate(nil);_ = channel?.close();exit(0)}
 func fail(_ message:String)->Never {print("ERROR "+message);exit(2)}
}
setbuf(stdout,nil)
let transport=Transport();transport.start();RunLoop.main.run()
