import Foundation
import Vision
let request = VNDetectBarcodesRequest()
request.symbologies = [.qr]
try VNImageRequestHandler(url: URL(fileURLWithPath: CommandLine.arguments[1])).perform([request])
let values = (request.results ?? []).compactMap { $0.payloadStringValue }
let data = try JSONSerialization.data(withJSONObject: values)
print(String(data: data, encoding: .utf8)!)
