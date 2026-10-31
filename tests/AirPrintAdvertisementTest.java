package local.liuying.studio;
public class AirPrintAdvertisementTest {
 static void check(boolean condition,String why){if(!condition)throw new AssertionError(why);}
 static void action(AirPrintAdvertisement.Action actual,AirPrintAdvertisement.Action expected){check(actual==expected,"Expected "+expected+", got "+actual);}
 public static void main(String[] args){
  AirPrintAdvertisement state=new AirPrintAdvertisement();
  action(state.update(false,"all"),AirPrintAdvertisement.Action.NONE);check(!state.visible(),"Unavailable stays hidden");
  action(state.update(true,"all"),AirPrintAdvertisement.Action.REGISTER);int first=state.token();check(!state.visible(),"Pending registration not visible");
  action(state.update(false,"all"),AirPrintAdvertisement.Action.NONE);action(state.registered(first,true),AirPrintAdvertisement.Action.UNREGISTER);check(state.visible(),"Pending withdrawal remains actually registered");
  action(state.update(true,"jpeg,pdf"),AirPrintAdvertisement.Action.NONE);action(state.unregistered(first,true),AirPrintAdvertisement.Action.REGISTER);int second=state.token();check(second!=first&&state.key().equals("jpeg,pdf"),"Newest format after withdrawal");
  action(state.registered(first,true),AirPrintAdvertisement.Action.NONE);check(!state.visible(),"Stale registration cannot resurrect service");action(state.registered(second,true),AirPrintAdvertisement.Action.NONE);check(state.visible(),"Available advertised");
  for(int i=0;i<10;i++)action(state.update(true,"jpeg,pdf"),AirPrintAdvertisement.Action.NONE);
  action(state.update(true,"all"),AirPrintAdvertisement.Action.UNREGISTER);action(state.unregistered(second,false),AirPrintAdvertisement.Action.NONE);action(state.update(false,"all",false),AirPrintAdvertisement.Action.NONE);check(state.visible(),"Failed withdrawal remains visible for retry");action(state.update(false,"all"),AirPrintAdvertisement.Action.UNREGISTER);action(state.unregistered(second,true),AirPrintAdvertisement.Action.NONE);check(!state.visible(),"Release hidden after callback");
  action(state.update(true,"all"),AirPrintAdvertisement.Action.REGISTER);int third=state.token();action(state.registered(third,false),AirPrintAdvertisement.Action.NONE);check(!state.visible(),"Failed registration hidden");action(state.update(true,"all",false),AirPrintAdvertisement.Action.NONE);action(state.update(true,"all"),AirPrintAdvertisement.Action.REGISTER);action(state.registered(state.token(),true),AirPrintAdvertisement.Action.NONE);check(state.visible(),"Probe/registration recovery visible");
  AirPrintAdvertisement paper=new AirPrintAdvertisement();action(paper.update(true,"5009|all"),AirPrintAdvertisement.Action.REGISTER);action(paper.registered(paper.token(),true),AirPrintAdvertisement.Action.NONE);action(paper.update(true,"5012|all"),AirPrintAdvertisement.Action.UNREGISTER);action(paper.unregistered(paper.token(),true),AirPrintAdvertisement.Action.REGISTER);check(paper.key().equals("5012|all"),"Paper change forces clients to refresh attributes");
  System.out.println("PASS availability broadcast lifecycle: unavailable, pending release, rapid restart, stale callback, format changes and retry backoff");
 }
}
