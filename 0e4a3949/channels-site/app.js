const $=s=>document.querySelector(s);
const KEY="tv_channels_v1", SES="tv_admin";
let channels=JSON.parse(localStorage.getItem(KEY)||"null")||CONFIG.defaultChannels.slice();
let cat="الكل", hls=null;
const save=()=>localStorage.setItem(KEY,JSON.stringify(channels));
const isAdmin=()=>sessionStorage.getItem(SES)==="1";
$("#siteName").textContent="📺 "+CONFIG.siteName;
const esc=t=>String(t).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

function render(){
  const cats=["الكل",...new Set(channels.map(c=>c.category||"عام"))];
  $("#tabs").innerHTML=cats.map(c=>`<button class="${c===cat?"on":""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");
  const q=$("#search").value.trim().toLowerCase();
  const list=channels.map((c,i)=>({...c,i})).filter(c=>(cat==="الكل"||(c.category||"عام")===cat)&&c.name.toLowerCase().includes(q));
  $("#grid").innerHTML=list.map(c=>`<div class="ch" data-i="${c.i}">
   ${c.logo?`<img src="${esc(c.logo)}" alt="" onerror="this.outerHTML='<div class=ph>📺</div>'">`:`<div class="ph">📺</div>`}
   <b>${esc(c.name)}</b><br><small>${esc(c.category||"عام")}</small></div>`).join("")||"<p>لا توجد قنوات.</p>";
  $("#adminList").innerHTML=channels.map((c,i)=>`<div><span>${esc(c.name)}</span><button class="del" data-del="${i}">حذف</button></div>`).join("");
}
function play(i){
  const c=channels[i]; $("#now").textContent="▶ "+c.name;
  const p=$("#player"); if(hls){hls.destroy();hls=null}
  if(/\.m3u8(\?|$)/i.test(c.url)){
    p.innerHTML='<video controls autoplay playsinline></video>'; const v=p.firstChild;
    if(window.Hls&&Hls.isSupported()){hls=new Hls();hls.loadSource(c.url);hls.attachMedia(v)}
    else v.src=c.url;
  } else if(/\.(mp4|webm)(\?|$)/i.test(c.url)){
    p.innerHTML=`<video controls autoplay playsinline src="${esc(c.url)}"></video>`;
  } else p.innerHTML=`<iframe src="${esc(c.url)}" allowfullscreen allow="autoplay; fullscreen"></iframe>`;
  scrollTo({top:0,behavior:"smooth"});
}
document.addEventListener("click",e=>{
  const t=e.target;
  if(t.closest("[data-cat]")){cat=t.closest("[data-cat]").dataset.cat;render()}
  if(t.closest(".ch")) play(t.closest(".ch").dataset.i);
  if(t.dataset.close!==undefined) t.closest(".modal").classList.remove("show");
  if(t.dataset.del!==undefined&&isAdmin()&&confirm("حذف القناة؟")){channels.splice(t.dataset.del,1);save();render()}
  if(t.classList.contains("modal")) t.classList.remove("show");
});
$("#search").oninput=render;
$("#devBtn").onclick=()=>$((isAdmin()?"#adminModal":"#loginModal")).classList.add("show");
$("#loginGo").onclick=()=>{
  if($("#u").value.trim()===CONFIG.admin.username&&$("#p").value===CONFIG.admin.password){
    sessionStorage.setItem(SES,"1");$("#err").textContent="";$("#p").value="";
    $("#loginModal").classList.remove("show");$("#adminModal").classList.add("show");
  } else $("#err").textContent="بيانات الدخول غير صحيحة";
};
$("#logout").onclick=()=>{sessionStorage.removeItem(SES);$("#adminModal").classList.remove("show")};
$("#add").onclick=()=>{
  if(!isAdmin())return;
  const name=$("#cn").value.trim(),url=$("#cu").value.trim();
  if(!name||!url)return alert("اكتب اسم القناة والرابط");
  channels.push({name,url,logo:$("#cl").value.trim(),category:$("#cc").value.trim()||"عام"});
  save();["#cn","#cu","#cl","#cc"].forEach(s=>$(s).value="");render();
};
render();

// ===== خلفية متحركة =====
const cv=$("#bg"),cx=cv.getContext("2d");let W,H,pts=[];
function size(){W=cv.width=innerWidth;H=cv.height=innerHeight;pts=Array.from({length:Math.min(90,W/12|0)},()=>({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.6,vy:(Math.random()-.5)*.6}))}
addEventListener("resize",size);size();
(function loop(){
  const g=cx.createLinearGradient(0,0,W,H);g.addColorStop(0,"#070b16");g.addColorStop(1,"#1a0b33");
  cx.fillStyle=g;cx.fillRect(0,0,W,H);
  for(const a of pts){
    a.x+=a.vx;a.y+=a.vy;if(a.x<0||a.x>W)a.vx*=-1;if(a.y<0||a.y>H)a.vy*=-1;
    cx.fillStyle="#00e5ff";cx.beginPath();cx.arc(a.x,a.y,2,0,7);cx.fill();
    for(const b of pts){const d=Math.hypot(a.x-b.x,a.y-b.y);
      if(d<110){cx.strokeStyle=`rgba(168,85,247,${1-d/110})`;cx.beginPath();cx.moveTo(a.x,a.y);cx.lineTo(b.x,b.y);cx.stroke()}}
  }
  requestAnimationFrame(loop);
})();
