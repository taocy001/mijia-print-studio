window.CardArt=(()=>{
 const ready=Promise.resolve();
 const spec=()=>CARD_CATALOG.find(s=>s.id==='card_'+state.cardStyle)||CARD_CATALOG[0];
 function draw(c,x,y,w,h,s=spec()){
  const key=`${s.id}-${w}x${h}`;c.save();c.translate(x,y);StudioArtwork.card(c,w,h,s.id);
  for(const slot of CARD_SLOTS[key]||[]){const value=(slot.field==='title'?state.cardTitle:state.cardSubtitle)?.trim()||s[slot.field];NameLabels.center(c,slot.box,value,slot.size,slot.color,slot.font==='heiti'?'sans-serif':'NameLabelFont');}c.restore();
 }
 function options(){const [w,h]=logicalSize();return '<div class="filter-grid">'+CARD_CATALOG.map(s=>{const c=document.createElement('canvas');c.width=w;c.height=state.media===5014?h/2:h;draw(c.getContext('2d'),0,0,c.width,c.height,s);return `<button class="filter-card ${s.id===spec().id?'active':''}" data-setting="cardStyle" data-value="${s.id.slice(5)}"><img style="width:100%;display:block" src="${c.toDataURL('image/jpeg',.75)}" alt=""><small>${s.name}</small></button>`;}).join('')+'</div>';}
 return{ready,draw,options,spec};
})();
