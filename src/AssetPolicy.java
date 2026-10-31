package local.liuying.studio;
import java.util.Arrays;
/** Local WebView assets only; private photos keep their separate canonical-path check. */
final class AssetPolicy {
 static boolean allows(String name){
  return name!=null && (Arrays.asList("index.html","session.js","browser.js","browser.css","sharing.js","artwork.js","app.js","tone.js","emoji-catalog.js","layers.js","crop.js","minimal.css","template-catalog.js","templates.js","original-templates.js","drawer.js","floating-tools.js","extras.js","calendar-data.js","landscape.js","style.css","sample.svg","fonts/MaShanZheng-Regular.ttf","fonts/ZCOOLKuaiLe-Regular.ttf","name-label-catalog.js","name-labels.js","card-catalog.js","card-art.js","cutout.js").contains(name)
   || name.matches("emoji/[A-Za-z0-9_-]+\\.svg"));
 }
}
