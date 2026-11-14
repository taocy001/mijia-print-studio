package local.liuying.studio;
final class JobRecovery {
 static boolean recoverable(String phase){return "uncertain".equals(phase)||"blocked".equals(phase)||"held".equals(phase);}
 static boolean canResolve(String state,Object queue){return ("20".equals(state)||"30".equals(state))&&queue instanceof String&&((String)queue).isEmpty();}
 static String error(int code){return PrinterAlerts.code(String.valueOf(code));}
}
