window.NameLabels=(()=>{
 const font=new FontFace('NameLabelFont','url(fonts/ZCOOLKuaiLe-Regular.ttf)');
 const ready=font.load().then(f=>document.fonts.add(f));
 function geometry(w,h){const rows=w===h?2:w>h?1:3,margin=Math.max(8,Math.floor(Math.min(w,h)/65)),gap=state.nameGap==null?margin:Math.round(Math.max(0,Math.min(5,+state.nameGap||0))*300/25.4);return{rows,margin,gap,cw:Math.floor((w-margin*2-gap)/2),ch:Math.floor((h-margin*2-gap*(rows-1))/rows)};}
 function spec(){return NAME_LABEL_CATALOG.find(s=>s.id==='name_'+state.labelTheme)||NAME_LABEL_CATALOG[0];}
 function center(c,box,value,size,color,font='NameLabelFont'){let n=Math.floor(size);c.textAlign='left';c.textBaseline='alphabetic';do{c.font=`${n}px ${font}`;if(c.measureText(value).width<=(box[2]-box[0])||n<=10)break;n-=2;}while(true);
 const m=c.measureText(value),left=m.actualBoundingBoxLeft||0,right=m.actualBoundingBoxRight||m.width,asc=m.actualBoundingBoxAscent||0,desc=m.actualBoundingBoxDescent||0;
 c.fillStyle=color;c.fillText(value,(box[0]+box[2]-left-right)/2+left,(box[1]+box[3]+asc-desc)/2);
 }
 function draw(c,x,y,w,h,theme=spec()){
 const {rows,margin,gap,cw,ch}=geometry(w,h),title=(state.labelTitle||'').trim()||theme.title,sub=(state.labelSubtitle||'').trim()||theme.subtitle;
 const ink={rainbow:'#6B3E26',space:'#FFFFFF',panda:'#14532D',flower:'#9D174D',minimal:'#111111',unicorn:'#6B21A8'}[theme.id.slice(5)],top=theme.id==='name_minimal'?.30:.35;
 c.save();c.fillStyle='#E5E7EB';c.fillRect(x,y,w,h);
 for(let r=0;r<rows;r++)for(let col=0;col<2;col++){c.save();c.translate(x+margin+col*(cw+gap),y+margin+r*(ch+gap));StudioArtwork.label(c,cw,ch,theme.id);center(c,[cw*.08,ch*top,cw*.92,ch*(top+.34)],title,ch*.28,ink);center(c,[cw*.12,ch*.73,cw*.88,ch*.91],sub,ch*.12,theme.id==='name_space'?'#FDE68A':ink);c.restore();}c.restore();
 }
 function count(){const [w,h]=logicalSize();return geometry(w,state.media===5014?h/2:h).rows*2*(state.media===5014?2:1);}
 function options(){const [w,h]=logicalSize();return '<div class="filter-grid">'+NAME_LABEL_CATALOG.map(s=>{const c=document.createElement('canvas');c.width=w;c.height=state.media===5014?h/2:h;draw(c.getContext('2d'),0,0,c.width,c.height,s);return `<button class="filter-card ${s.id===spec().id?'active':''}" data-setting="labelTheme" data-value="${s.id.slice(5)}"><img style="width:100%;display:block" src="${c.toDataURL('image/jpeg',.75)}" alt=""><small>${s.name}</small></button>`;}).join('')+'</div>';}
 return{ready,draw,count,options,spec,geometry,center};
})();
