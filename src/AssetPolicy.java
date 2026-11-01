package local.liuying.studio;
import java.util.Arrays;
/** Local WebView assets only; private photos keep their separate canonical-path check. */
final class AssetPolicy {
 static boolean allows(String name){
  return name!=null && (Arrays.asList("index.html","apple-touch-icon.png","favicon.png","session.js","browser.js","browser.css","paper-preview.js","paper-preview.css","print-process.js","print-process.css","desktop.js","sharing.js","artwork.js","app.js","faces.js","tone.js","emoji-catalog.js","layers.js","crop.js","minimal.css","template-catalog.js","templates.js","original-templates.js","kids-templates.js","blended-templates.js", "template-edges.js","effect-browser.js","effect-browser.css","drawer.js","floating-tools.js","extras.js","calendar-data.js","landscape.js","style.css","sample.svg","fonts/MaShanZheng-Regular.ttf","fonts/ZCOOLKuaiLe-Regular.ttf","name-label-catalog.js","name-labels.js","card-catalog.js","card-art.js","cutout.js","photo-strips.js","label-batch.js","project-file.js","qrcodegen.js","qr-sticker.js","capture.js","image-export.js","models.js","history-storage.js").contains(name)
   || name.matches("emoji/[A-Za-z0-9_-]+\\.svg"));
 }
}
