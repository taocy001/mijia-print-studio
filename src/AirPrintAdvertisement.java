package local.liuying.studio;
final class AirPrintAdvertisement {
 enum Action {NONE,REGISTER,UNREGISTER}
 private enum Phase {OFF,REGISTERING,ON,UNREGISTERING}
 private volatile Phase phase=Phase.OFF;
 private boolean wanted;
 private String desired="",published="";
 private int token;
 int token(){return token;}
 String key(){return published;}
 boolean visible(){return phase==Phase.ON||phase==Phase.UNREGISTERING;}
 Action update(boolean value,String key){return update(value,key,true);}
 Action update(boolean value,String key,boolean attempt){wanted=value;desired=key;return attempt?next():Action.NONE;}
 private Action next(){
  if(phase==Phase.OFF&&wanted){phase=Phase.REGISTERING;published=desired;token++;return Action.REGISTER;}
  if(phase==Phase.ON&&(!wanted||!published.equals(desired))){phase=Phase.UNREGISTERING;return Action.UNREGISTER;}
  return Action.NONE;
 }
 Action registered(int id,boolean success){if(id!=token||phase!=Phase.REGISTERING)return Action.NONE;phase=success?Phase.ON:Phase.OFF;return success?next():Action.NONE;}
 Action unregistered(int id,boolean success){if(id!=token||phase!=Phase.UNREGISTERING)return Action.NONE;phase=success?Phase.OFF:Phase.ON;return success?next():Action.NONE;}
}
