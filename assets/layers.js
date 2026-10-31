/* Direct manipulation objects. Canvas is the single source of truth for preview and print. */
window.LayerEditor = (() => {
  const FONTS = {sans:['简洁','sans-serif'],happy:['快乐体','StudioHappy'],brush:['毛笔体','StudioBrush'],serif:['衬线','serif']};
  const COLORS = ['#ffffff','#203d33','#111111','#e65a62','#dc954a','#eac859','#589568','#5297ba','#9470b5'];
  const EMOJI=Object.fromEntries(Object.entries(SHARED_EMOJI).map(([k,items])=>[k,items.map(x=>[x.text,x.name])]));
  const emojiImages=new Map(),emojiCodes=new Map();
  const emojiReady=Promise.all(Object.values(SHARED_EMOJI).flat().map(async item=>{const im=new Image();im.src='/emoji/'+item.code+'.svg';await im.decode();emojiImages.set(item.text.replaceAll('\ufe0f',''),im);emojiCodes.set(item.text,item.code);}));
  let editingId=null,selectedId=null,scope='',emojiTab='心情',lastTap=null,resizeState=null,undoTimer;
  const pointers=new Map(); let gestureTarget=null,previous=null,moved=false;
  const measureContext=document.createElement('canvas').getContext('2d');
  const fontReady=Promise.all([document.fonts.load('20px StudioHappy'),document.fonts.load('20px StudioBrush')]).then(()=>{schedule();});
  function list(){
    if(!['label','card'].includes(state.mode)&&!(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))&&active())return active().overlays ||= [];
    state.sceneLayers ||= {};return state.sceneLayers[state.mode] ||= [];
  }
  function scopeKey(){return (['label','card'].includes(state.mode)||(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014)))?'scene:'+state.mode:'photo:'+state.active+':'+(active()?.src||'');}
  function space(){const [w,h]=logicalSize();if(state.media===5014||state.mode==='collage'){const f=photoFrames.find(f=>f.p===active());if(f)return {x:f.x,y:f.y,w:f.w,h:f.h};}return{x:0,y:0,w,h};}
  function layerSize(){const s=space();return[s.w,s.h];}
  function selected(){return list().find(o=>o.id===selectedId)||null;}
  function uid(){return 'layer-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);}
  function select(id){if(document.body.classList.contains('layer-editing')&&editingId&&id!==editingId)closeSheet();selectedId=id;scope=scopeKey();refresh();}
  function characters(value){return typeof Intl.Segmenter==='function'?[...new Intl.Segmenter('zh',{granularity:'grapheme'}).segment(value)].map(s=>s.segment):Array.from(value);}
  function metrics(o,w,h){
    const font=(FONTS[o.font]||FONTS.sans)[1];let size=Math.max(2,Math.min(32,Number(o.sizePct)||9))*w/100;
    let lines=[],width,height,pad;
    if(o.kind==='emoji'){width=size;height=size;pad=0;}
    else{
      measureContext.font=`${size}px ${font}`;
      for(const paragraph of String(o.text||'').split('\n')){
        let line='';for(const char of characters(paragraph)){if(line&&measureContext.measureText(line+char).width>w*.85){lines.push(line);line=char;}else line+=char;}lines.push(line);
      }
      pad=size*.2;width=Math.max(size*.65,...lines.map(line=>measureContext.measureText(line).width))+pad*2;height=lines.length*size*1.28+pad*2;
    }
    const angle=Math.max(-180,Math.min(180,Number(o.angle)||0))*Math.PI/180;
    const c=Math.abs(Math.cos(angle)),s=Math.abs(Math.sin(angle));
    const fit=Math.min(1,(w-24)/(width*c+height*s),(h-24)/(width*s+height*c));
    width*=fit;height*=fit;size*=fit;pad*=fit;
    const rw=width*c+height*s,rh=width*s+height*c;
    const x=Math.max(rw/2+6,Math.min(w-rw/2-6,(Number(o.fx)||.5)*w));
    const y=Math.max(rh/2+6,Math.min(h-rh/2-6,(Number(o.fy)||.5)*h));
    return {x,y,width,height,rw,rh,size,pad,angle,font,lines};
  }
  function paint(ctx,w,h,objects=list(),mode='photo'){
    if(mode==='mask'||mode==='editor'){
      const hidden=objects.filter(o=>o.hidden);
      if(mode==='editor')paint(ctx,w,h,objects,'photo');
      if(!hidden.length)return;
      const mask=document.createElement('canvas');mask.width=w;mask.height=h;
      const mc=mask.getContext('2d');paint(mc,w,h,hidden.map(o=>({...o,hidden:false,color:'#fff',stroke:'',bubble:''})),'photo');
      // Keep dark eyes/mouth as holes instead of flattening every emoji to a disc.
      const pixels=mc.getImageData(0,0,w,h);let bright=0;
      for(let i=0;i<pixels.data.length;i+=4)if(pixels.data[i+3]&&(.299*pixels.data[i]+.587*pixels.data[i+1]+.114*pixels.data[i+2])>=40)bright++;
      for(let i=0;i<pixels.data.length;i+=4){if(bright&&(.299*pixels.data[i]+.587*pixels.data[i+1]+.114*pixels.data[i+2])<40)pixels.data[i+3]=0;pixels.data[i]=mode==='mask'?255:233;pixels.data[i+1]=mode==='mask'?255:196;pixels.data[i+2]=mode==='mask'?255:106;}mc.putImageData(pixels,0,0);
      ctx.save();ctx.globalAlpha=mode==='mask'?1:.65;ctx.drawImage(mask,0,0);ctx.restore();return;
    }
    if(peek)return;
    for(const o of objects){
      if(o.hidden)continue;
      const m=metrics(o,w,h);ctx.save();ctx.translate(m.x,m.y);ctx.rotate(m.angle);
      if(o.kind==='emoji'){
        const im=emojiImages.get(o.text.replaceAll('\ufe0f',''));if(im)ctx.drawImage(im,-m.size/2,-m.size/2,m.size,m.size);else{ctx.font=`${m.size}px sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(o.text,0,0);}
      }else{
        if(o.bubble)rounded(ctx,-m.width/2,-m.height/2,m.width,m.height,m.size*.22,o.bubble);
        ctx.font=`${m.size}px ${m.font}`;ctx.textAlign=o.align||'center';ctx.textBaseline='middle';ctx.lineJoin='round';
        const xx=o.align==='left'?-m.width/2+m.pad:o.align==='right'?m.width/2-m.pad:0;
        m.lines.forEach((line,i)=>{
          const yy=(i-(m.lines.length-1)/2)*m.size*1.28;
          if(o.stroke){ctx.strokeStyle=o.stroke;ctx.lineWidth=Math.max(2,m.size*.055);ctx.strokeText(line,xx,yy);}
          ctx.fillStyle=o.color||'#ffffff';ctx.fillText(line,xx,yy);
        });
      }
      ctx.restore();
    }
  }
  function refresh(){
    const now=scopeKey();if(scope!==now){if(document.body.classList.contains('layer-editing'))closeSheet();selectedId=null;scope=now;pointers.clear();gestureTarget=null;resizeState=null;previous=null;}
    const o=selected(),box=$('layerSelection'),handle=$('layerResize');document.body.classList.toggle('object-selected',!!o);
    if(o&&editingId===o.id&&document.body.classList.contains('layer-editing')){for(const key of ['sizePct','angle']){const input=$('sheetBody').querySelector('[data-layer-range='+key+']');if(input){input.value=o[key];$('out-'+key).value=Math.round(o[key]);}}}
    $('layerTools').hidden=!o;$('layerName').textContent=o?((o.hidden?'覆膜 · ':'')+(o.kind==='emoji'?'已选表情':'已选文字')):'';
    box.hidden=handle.hidden=!o||peek||!readyPhoto();
    if(!o||peek||!readyPhoto())return;
    const [w,h]=layerSize(),m=metrics(o,w,h),rect=$('preview').getBoundingClientRect(),view=window.CropEditor?.geometry()||{tx:0,ty:0},origin=space(),scale=rect.width/$('preview').width;
    Object.assign(box.style,{left:(m.x+origin.x+view.tx)*scale+'px',top:(m.y+origin.y+view.ty)*scale+'px',width:Math.max(44,m.width*scale)+'px',height:Math.max(44,m.height*scale)+'px',transform:`translate(-50%,-50%) rotate(${o.angle||0}deg)`});
    // Keep the resize target outside the minimum 44px movement target, including at edges.
    const cx=(m.x+origin.x+view.tx)*scale,cy=(m.y+origin.y+view.ty)*scale;
    const angle=m.angle,c=Math.abs(Math.cos(angle)),sn=Math.abs(Math.sin(angle));
    const halfW=(Math.max(44,m.width*scale)*c+Math.max(44,m.height*scale)*sn)/2;
    const halfH=(Math.max(44,m.width*scale)*sn+Math.max(44,m.height*scale)*c)/2;
    const hx=cx+(cx+halfW+48<rect.width?1:-1)*(halfW+28),hy=cy+(cy+halfH+48<rect.height?1:-1)*(halfH+28);
    Object.assign(handle.style,{left:Math.max(24,Math.min(rect.width-24,hx))+'px',top:Math.max(24,Math.min(rect.height-24,hy))+'px'});
    $('editLayer').textContent=o.kind==='emoji'?'调整':'编辑';
  }
  function readyPhoto(){return ready()!==false;}
  function create(values){const o={id:uid(),kind:'text',text:'',fx:.5,fy:.5,sizePct:9,angle:0,font:'sans',color:'#ffffff',stroke:'#203d33',bubble:'',align:'center',...values};list().push(o);select(o.id);schedule();return o;}
  function constrain(o){const [w,h]=layerSize(),m=metrics(o,w,h);o.fx=m.x/w;o.fy=m.y/h;}
  function hit(x,y){const [w,h]=layerSize();return [...list()].reverse().find(o=>{const m=metrics(o,w,h),dx=x-m.x,dy=y-m.y;return Math.abs(dx*Math.cos(m.angle)+dy*Math.sin(m.angle))<=Math.max(m.width/2+12,22/($('preview').getBoundingClientRect().width/$('preview').width))&&Math.abs(-dx*Math.sin(m.angle)+dy*Math.cos(m.angle))<=Math.max(m.height/2+12,22/($('preview').getBoundingClientRect().width/$('preview').width));});}
  function drawer(title,html){editingId=null;openSheet('layers',title,html);document.body.classList.add('layer-editing');$('sheet').classList.add('layer-sheet');$('scrim').hidden=true;$('sheet').setAttribute('aria-modal','false');document.body.style.overflow='';}
  function reveal(){if(document.body.classList.contains('landscape')||!selected())return;const r=$('layerSelection').getBoundingClientRect(),top=(document.querySelector('.topbar')?.getBoundingClientRect().height||0)+12,bottom=$('sheet').getBoundingClientRect().top-20;if(r.bottom>bottom)window.scrollBy({top:r.bottom-bottom,behavior:'smooth'});else if(r.top<top)window.scrollBy({top:r.top-top,behavior:'smooth'});}
  function range(key,label,value,min,max){return `<label class="layer-range">${label}<output id="out-${key}">${value}</output><input data-layer-range="${key}" type="range" min="${min}" max="${max}" step="1" value="${value}"></label>`;}
  function openEditor(o){
    if(o)select(o.id);const isText=!o||o.kind==='text';
    drawer(isText?(o?'编辑文字':'添加文字'):'调整表情',`${isText?`<textarea id="layerText" maxlength="160" placeholder="写下想留在照片上的话" aria-label="照片上的文字">${esc(o?.text||'')}</textarea><div class="layer-options" id="fontOptions">${Object.entries(FONTS).map(([k,v])=>`<button data-font="${k}" style="font-family:${v[1]}" class="${(o?.font||'sans')===k?'selected':''}">${v[0]}</button>`).join('')}</div><div class="color-options">${COLORS.map(c=>`<button data-color="${c}" aria-label="文字颜色 ${c}" aria-pressed="${(o?.color||'#ffffff')===c}" style="--swatch:${c}"></button>`).join('')}</div><div class="layer-options"><button id="layerStroke" aria-pressed="${!!(o?.stroke??true)}">描边</button><button id="layerBubble" aria-pressed="${!!o?.bubble}">底色</button><button id="layerAlign">对齐：${o?.align==='left'?'左':o?.align==='right'?'右':'居中'}</button></div>`:`<button class="full-button secondary-button" id="replaceEmoji">更换表情 ${esc(o.text)}</button>`}${list().length>1?'<button class="layer-picker" id="pickCoveredLayer">选择被遮住的文字或表情</button>':''}<label class="coat-switch"><span>隐藏到覆膜<small>仅侧光下可见，不印入照片颜色</small></span><input id="layerHidden" type="checkbox" role="switch" ${o?.hidden?'checked':''}></label>${range('sizePct','大小',o?.sizePct||9,2,32)}${range('angle','旋转',o?.angle||0,-180,180)}<p class="hint">在照片上拖动位置 · 拖动圆形手柄缩放 · 双指缩放、旋转</p>`);
    let draft=o,pending={font:'sans',color:'#ffffff',stroke:'#203d33',bubble:'',align:'center',sizePct:9,angle:0};editingId=o?.id||null;
    const edit=(fn)=>{fn(draft||pending);if(!draft&&$('layerText')?.value.trim()){draft=create({...pending,text:$('layerText').value});editingId=draft.id;}if(draft){constrain(draft);schedule();}};
    $('layerHidden').onchange=e=>edit(l=>l.hidden=e.target.checked);
    if(isText){$('layerText').oninput=e=>edit(l=>l.text=e.target.value);
      $('fontOptions').onclick=e=>{const b=e.target.closest('[data-font]');if(!b)return;edit(l=>l.font=b.dataset.font);$('fontOptions').querySelectorAll('button').forEach(x=>x.classList.toggle('selected',x===b));};
      $('sheetBody').querySelector('.color-options').onclick=e=>{const b=e.target.closest('[data-color]');if(!b)return;edit(l=>l.color=b.dataset.color);b.parentNode.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x===b));};
      $('layerStroke').onclick=e=>edit(l=>{l.stroke=l.stroke?'':'#203d33';e.currentTarget.setAttribute('aria-pressed',!!l.stroke);});
      $('layerBubble').onclick=e=>edit(l=>{l.bubble=l.bubble?'':'#fffaf0';e.currentTarget.setAttribute('aria-pressed',!!l.bubble);});
      $('layerAlign').onclick=e=>edit(l=>{l.align={center:'left',left:'right',right:'center'}[l.align||'center'];e.currentTarget.textContent='对齐：'+({left:'左',right:'右',center:'居中'}[l.align]);});
    }else $('replaceEmoji').onclick=()=>openEmoji(o);
    $('sheetBody').querySelectorAll('[data-layer-range]').forEach(el=>el.oninput=()=>edit(l=>{l[el.dataset.layerRange]=+el.value;$('out-'+el.dataset.layerRange).value=el.value;}));
    if($('pickCoveredLayer'))$('pickCoveredLayer').onclick=()=>openHome('layers');setTimeout(reveal,150);
  }
  function openEmoji(replace){drawer('选择表情',`<label class="coat-switch"><span>隐藏到覆膜<small>表情只出现在覆膜层</small></span><input id="emojiHidden" type="checkbox" role="switch" ${replace?.hidden?'checked':''}></label><div class="emoji-tabs">${Object.keys(EMOJI).map((k,i)=>`<button data-emoji-tab="${i}">${k}</button>`).join('')}</div><p class="hint">上下滑动浏览全部表情 · 点一下添加</p>${Object.entries(EMOJI).map(([category,items],i)=>`<section class="emoji-category" id="emoji-category-${i}"><h3>${category}</h3><div class="emoji-grid">${items.map(([v,label])=>`<button data-emoji="${v}" aria-label="${label}"><img src="/emoji/${emojiCodes.get(v)||Object.values(SHARED_EMOJI).flat().find(x=>x.text===v)?.code}.svg" alt=""></button>`).join('')}</div></section>`).join('')}`);$('sheet').classList.add('emoji-sheet');$('sheetBody').querySelectorAll('[data-emoji-tab]').forEach(b=>b.onclick=()=>{const target=$('emoji-category-'+b.dataset.emojiTab),body=$('sheetBody');body.scrollTo({top:body.scrollTop+target.getBoundingClientRect().top-body.getBoundingClientRect().top-52,behavior:'smooth'});});$('sheetBody').querySelectorAll('[data-emoji]').forEach(b=>b.onclick=()=>{if(replace){replace.text=b.dataset.emoji;replace.hidden=$('emojiHidden').checked;select(replace.id);}else create({kind:'emoji',text:b.dataset.emoji,sizePct:15,stroke:'',hidden:$('emojiHidden').checked});closeSheet();schedule();});}

  function openHome(kind){if(kind==='emoji')return openEmoji();if(kind==='text')return openEditor(selected()?.kind==='text'?selected():null);drawer('文字与表情',`<div class="layer-options"><button id="newLayerText">添加文字</button><button id="newLayerEmoji">添加表情</button></div><div class="layer-list">${[...list()].reverse().map(o=>`<button data-layer-id="${o.id}">${o.kind==='emoji'?'表情':'文字'} · ${esc(o.text||'空文字')}</button>`).join('')||'<p class="hint">还没有添加文字或表情</p>'}</div><button class="full-button secondary-button" id="legacyCaption">${state.mode==='label'?'编辑姓名与副标题':'编辑底部题字'}</button>`);$('newLayerText').onclick=()=>openEditor();$('newLayerEmoji').onclick=()=>openEmoji();$('legacyCaption').onclick=openLegacyText;$('sheetBody').querySelectorAll('[data-layer-id]').forEach(b=>b.onclick=()=>openEditor(list().find(o=>o.id===b.dataset.layerId)));}
  function remove(){const o=selected();if(!o)return;const collection=list(),index=collection.indexOf(o);collection.splice(index,1);select(null);closeSheet();schedule();document.getElementById('layerUndo')?.remove();clearTimeout(undoTimer);const bar=document.createElement('div');bar.id='layerUndo';bar.className='layer-undo';bar.innerHTML='已删除 <button>撤销</button>';document.body.append(bar);bar.querySelector('button').onclick=()=>{collection.splice(index,0,o);bar.remove();schedule();};undoTimer=setTimeout(()=>bar.remove(),6000);}
  const canvas=$('preview');
  function point(e){const p=CropEditor.toPaper(e),s=space();return{x:p.x-s.x,y:p.y-s.y};}
  function geometry(){const p=[...pointers.values()];if(!p.length)return null;return p.length===1?{x:p[0].x,y:p[0].y,d:0,a:0,n:1}:{x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2,d:Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y),a:Math.atan2(p[1].y-p[0].y,p[1].x-p[0].x),n:2};}
  const selection=$('layerSelection');
  selection.onpointerdown=e=>{if(peek)return;e.preventDefault();const p=point(e);if(!pointers.size){const o=selected()||hit(p.x,p.y),had=selected();gestureTarget=o||(!had?'photo':null);select(o?.id||null);moved=false;}pointers.set(e.pointerId,p);selection.setPointerCapture(e.pointerId);previous=geometry();};
  selection.onpointermove=e=>{if(!pointers.has(e.pointerId))return;e.preventDefault();pointers.set(e.pointerId,point(e));const g=geometry(),old=previous;previous=g;if(!old||!gestureTarget)return;const [w,h]=layerSize(),dx=g.x-old.x,dy=g.y-old.y;if(Math.abs(dx)+Math.abs(dy)>2||g.n===2)moved=true;
    if(gestureTarget==='photo'){const p=active();if(!p)return;p.x=Math.max(-1,Math.min(1,(p.x||0)+dx/w*2));p.y=Math.max(-1,Math.min(1,(p.y||0)+dy/h*2));if(g.n===2&&old.n===2&&old.d)p.zoom=Math.max(1,Math.min(4,(p.zoom||1)*g.d/old.d));}
    else {const o=gestureTarget,m=metrics(o,w,h);o.fx=(m.x+dx)/w;o.fy=(m.y+dy)/h;if(g.n===2&&old.n===2&&old.d){o.sizePct=Math.max(2,Math.min(32,o.sizePct*g.d/old.d));o.angle=((o.angle+(g.a-old.a)*180/Math.PI+540)%360)-180;}constrain(o);}schedule();};
  function end(e){if(!pointers.has(e.pointerId))return;pointers.delete(e.pointerId);previous=geometry();if(!pointers.size){if(e.type==='pointerup'&&!moved&&selected()){const now=Date.now();if(lastTap?.id===selectedId&&now-lastTap.time<350){openEditor(selected());lastTap=null;}else lastTap={id:selectedId,time:now};}gestureTarget=null;}}
  selection.onpointerup=end;selection.onpointercancel=end;selection.onlostpointercapture=end;
  let tap=null;
  canvas.onpointerdown=e=>{tap=e.isPrimary?{id:e.pointerId,x:e.clientX,y:e.clientY}:null;};
  canvas.onpointermove=e=>{if(tap&&Math.hypot(e.clientX-tap.x,e.clientY-tap.y)>8)tap=null;};
  canvas.onpointercancel=()=>tap=null;
  canvas.onpointerup=e=>{if(!tap||tap.id!==e.pointerId)return;tap=null;const p=point(e),o=hit(p.x,p.y);select(o?.id||null);};
  const handle=$('layerResize');handle.onpointerdown=e=>{e.preventDefault();e.stopPropagation();const o=selected();if(!o)return;const [w,h]=layerSize(),m=metrics(o,w,h),p=point(e);resizeState={o,d:Math.max(1,Math.hypot(p.x-m.x,p.y-m.y)),size:o.sizePct};handle.setPointerCapture(e.pointerId);};handle.onpointermove=e=>{if(!resizeState)return;e.preventDefault();const {o,d,size}=resizeState,[w,h]=layerSize(),m=metrics(o,w,h),p=point(e);o.sizePct=Math.max(2,Math.min(32,size*Math.hypot(p.x-m.x,p.y-m.y)/d));constrain(o);schedule();};for(const event of ['pointerup','pointercancel','lostpointercapture'])handle.addEventListener(event,()=>resizeState=null);
  document.addEventListener('keydown',e=>{
    if(!['Delete','Backspace'].includes(e.key)||e.isComposing||e.ctrlKey||e.metaKey||e.altKey)return;
    if(e.target.closest?.('input,textarea,select,[contenteditable]')||(!$('sheet').hidden&&!$('sheet').classList.contains('desktop-inspector'))||!selected())return;
    e.preventDefault();remove();
  });
  $('addTextQuick').onclick=()=>openEditor();$('addEmojiQuick').onclick=()=>openEmoji();$('editLayer').onclick=()=>openEditor(selected());$('deselectLayer').onclick=()=>{select(null);closeSheet();};$('deleteLayer').onclick=remove;
  $('copyLayer').onclick=()=>{const o=selected();if(o)create({...o,id:uid(),fx:Math.min(.9,o.fx+.04),fy:Math.min(.9,o.fy+.04)});};$('orderLayer').onclick=()=>{const o=selected();if(!o)return;const items=list(),i=items.indexOf(o),wasTop=i===items.length-1;items.splice(i,1);if(wasTop)items.unshift(o);else items.push(o);schedule();toast(wasTop?'已移到底层':'已移到顶层');};
  $('compare').onkeydown=e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();peek=true;schedule();}};$('compare').onkeyup=$('compare').onblur=()=>{peek=false;schedule();};
  window.addEventListener('resize',()=>{refresh();if(document.body.classList.contains('layer-editing'))setTimeout(reveal,100);});
  window.visualViewport?.addEventListener('resize',()=>{if(document.body.classList.contains('layer-editing'))setTimeout(reveal,100);});
  schedule();return {ready:Promise.all([fontReady,emojiReady]),list,selected,select,metrics,paint,space,refresh,openHome,openEditor,create,hit,remove};
})();
