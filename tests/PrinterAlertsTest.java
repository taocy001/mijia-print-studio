package local.liuying.studio;
public final class PrinterAlertsTest {
 public static void main(String[] args){
  if(!PrinterAlerts.describe("::0").isEmpty())throw new AssertionError("Ready");
  if(!PrinterAlerts.describe("::5402%").contains("缺纸"))throw new AssertionError("Paper");
  if(!PrinterAlerts.describe("::8101").contains("耗尽"))throw new AssertionError("Ribbon");
  if(!PrinterAlerts.describe("::8103").contains("未识别"))throw new AssertionError("Ribbon detection");
  if(!PrinterAlerts.describe("::9999").contains("9999"))throw new AssertionError("Unknown");
  System.out.println("PASS: paper, ribbon and unknown alerts");
 }
}
