/* Curated chooser only. Historical template IDs and painters stay intact for saved works. */
window.TemplateCollection=(()=>{
 const groups=[['food','美食茶歇'],['imagination','宇宙奇想'],['kids','童趣校园'],['life','生活日常'],['nature','自然旅行'],['party','萌趣派对'],['art','拼贴艺术']];
 const byGroup={
  food:[...['pork','feast','burger','toast','ramen','pudding','rice','melon'].map(x=>'booth-fun-'+x),...['tea','teatime','dragonfruit','fruitduo'].map(x=>'booth-life-'+x)],
  imagination:[...['volcano','ufo','rocket','monster','ghost','potion'].map(x=>'booth-fun-'+x),...['ufopilot','ufoduo'].map(x=>'booth-life-'+x),...['space','moon'].map(x=>'studio-kids-'+x)],
  kids:[...['dino','ocean','bakery','unicorn','picnic','train','ducks','art'].map(x=>'studio-kids-'+x),...['schoolbag','schoolbus'].map(x=>'booth-life-'+x)],
  life:[...['plate','roadtrip','clipboard','briefcase','computer','windows','watch','watchduo'].map(x=>'booth-life-'+x),...['tv','game'].map(x=>'booth-fun-'+x)],
  nature:[...['tide','botanical','sunset','petal','constellation','ripple','orchard','alpine'].map(x=>'studio-'+x),...['botanical','watercolor'].map(x=>'studio-blend-'+x)],
  party:['purikura-1','purikura-2','purikura-4','together-1','together-2','studio-1','studio-2','season-2','y2k-1','y2k-2'].map(x=>'booth-v2-'+x),
  art:[...['journal-2','journal-3','comic-1','comic-3','comic-4','magazine-1'].map(x=>'booth-v2-'+x),'booth-puzzle-1',...['splash','paper','ink'].map(x=>'studio-blend-'+x)]
 };
 const membership=new Map(Object.entries(byGroup).flatMap(([g,ids])=>ids.map(id=>[id,g])));
 return{groups,byGroup,includes:id=>membership.has(id),group:id=>membership.get(id)};
})();
