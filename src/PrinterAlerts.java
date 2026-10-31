package local.liuying.studio;
final class PrinterAlerts {
 static String describe(String value){
  if(value==null||value.isEmpty()||value.equals("::0"))return "";
  java.util.List<String> messages=new java.util.ArrayList<>();
  for(String code:value.replace("%","").split(":")){String message;
   switch(code){case "":case "0":continue;case "5304":message="相纸与打印尺寸不匹配";break;case "5306":message="请安装相纸盒";break;
    case "5402":message="缺纸或进纸失败，请补充相纸并检查纸盒";break;case "5403":message="打印机卡纸，请检查走纸通道";break;
    case "5414":case "5416":message="相纸尺寸异常，请检查纸盒";break;case "8101":case "8102":message="色带已耗尽，请更换色带";break;
    case "8103":message="未识别到色带，请重新安装";break;case "8104":message="色带类型不匹配";break;case "8199":message="色带异常，请检查或更换";break;
    default:message="打印机告警（"+code.replaceAll("[^0-9A-Za-z_-]","")+")";
   }if(!messages.contains(message))messages.add(message);
  }return String.join("；",messages);
 }
}
