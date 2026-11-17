package local.liuying.studio;
import java.util.Arrays;
/** Local WebView assets only; private photos keep their separate canonical-path check. */
final class AssetPolicy {
 static boolean allows(String name){
  return name!=null && (Arrays.asList("index.html","apple-touch-icon.png","favicon.png","session.js","pair-restore.js","browser.js","browser.css","paper-preview.js","paper-preview.css","print-process.js","print-process.css","desktop.js","sharing.js","artwork.js","app.js","type-navigation.js","type-navigation.css","printer-errors.js","faces.js","tone.js","emoji-catalog.js","layers.js","crop.js","minimal.css","template-catalog.js","templates.js","template-collection.js","photo-flow.js","photo-works.js","photo-windows.js","original-templates.js","booth-templates.js","playful-templates.js","everyday-templates.js","booth-mascots.webp","kids-templates.js","blended-templates.js", "template-edges.js","effect-browser.js","original-preview.js","editor-chrome.js","effect-browser.css","edit-history.js","edit-history.css","drawer.js","floating-tools.js","extras.js","calendar-data.js","calendar.js","landscape.js","style.css","sample.svg","fonts/MaShanZheng-Regular.ttf","fonts/ZCOOLKuaiLe-Regular.ttf","name-label-catalog.js","name-labels.js","card-catalog.js","card-art.js","cutout.js","photo-strips.js","label-batch.js","project-file.js","qrcodegen.js","qr-sticker.js","capture.js","preview-actions.js","image-export.js","models.js","history-storage.js").contains(name)
   || name.matches("emoji/[A-Za-z0-9_-]+\\.svg"));
 }
}
