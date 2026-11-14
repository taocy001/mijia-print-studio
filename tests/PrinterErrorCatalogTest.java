package local.liuying.studio;
public class PrinterErrorCatalogTest {
 public static void main(String[]args){
  if(PrinterAlerts.MESSAGES.size()!=28)throw new AssertionError("Coverage");
  if(!PrinterAlerts.describe("::9008").contains("Type-C 供电不足"))throw new AssertionError("Power");
  if(!PrinterAlerts.describe("::0").isEmpty())throw new AssertionError("Zero");
  String both=PrinterAlerts.describe("::5402%9008:5402");
  if(!both.equals(PrinterAlerts.code("5402")+"；"+PrinterAlerts.code("9008")))throw new AssertionError("Combined/deduplicated");
  if(!PrinterAlerts.code("9999").contains("未识别")||PrinterAlerts.code("<script>").contains("<"))throw new AssertionError("Unknown");
  for(String key:PrinterAlerts.MESSAGES.keySet())System.out.println(key+"\t"+PrinterAlerts.code(key));
 }
}
