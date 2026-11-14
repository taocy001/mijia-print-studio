package local.liuying.studio;
public class JobRecoveryTest {
 public static void main(String[] args){
  for(String phase:new String[]{"held","blocked","uncertain"})if(!JobRecovery.recoverable(phase))throw new AssertionError(phase);
  for(String phase:new String[]{"done","printing","uploading","prepared","cancelled",""})if(JobRecovery.recoverable(phase))throw new AssertionError(phase);
  if(!JobRecovery.canResolve("20","")||!JobRecovery.canResolve("30",""))throw new AssertionError("idle empty");
  for(Object queue:new Object[]{null,"158"," ",0})if(JobRecovery.canResolve("30",queue))throw new AssertionError("unknown or active queue");
  if(JobRecovery.canResolve("40",""))throw new AssertionError("not idle");
  if(!JobRecovery.error(8011).contains("正忙"))throw new AssertionError("busy");
  System.out.println("PASS: recovery eligibility, active/unknown queue protection and error mapping");
 }
}