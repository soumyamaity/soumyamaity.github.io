import { useState, useEffect, useRef, useCallback } from "react";

// ── palette & constants ──────────────────────────────────────────────────────
const C = {
  bg:      "#F5EFE6",
  paper:   "#FFFDF9",
  dark:    "#1E1208",
  brown:   "#5C3317",
  mid:     "#8B5E3C",
  gold:    "#D4A853",
  muted:   "#C4B49A",
  todo:    "#2C4A6E",
  prog:    "#7A5C00",
  block:   "#8B1A1A",
  done:    "#1A5C3A",
};

const COLUMNS = [
  { id: "todo",        label: "To Do",        emoji: "📋", accent: C.todo,  light: "#EBF2FA" },
  { id: "inprogress",  label: "In Progress",  emoji: "🔨", accent: C.prog,  light: "#FDF8E1" },
  { id: "blocked",     label: "Blocked",      emoji: "🚧", accent: C.block, light: "#FDECEA" },
  { id: "done",        label: "Done",         emoji: "✅", accent: C.done,  light: "#E8F5EE" },
];

const ROOMS = ["General","Kitchen","Dining Room","Bathroom","Master Bedroom","Guest Room","Couple's Room","Temple Room","Drawing Room","Balcony"];
const ROOM_ICON = { General:"📋", Kitchen:"🍳", "Dining Room":"🍽️", Bathroom:"🚿", "Master Bedroom":"🛏️", "Guest Room":"🛌", "Couple's Room":"💑", "Temple Room":"🪔", "Drawing Room":"🛋️", Balcony:"🌿" };
const PRIO = ["Low","Medium","High","Urgent"];
const PRIO_COLOR = { Low:"#6B9E6B", Medium:"#C4993A", High:"#CC6633", Urgent:"#CC2222" };

const SEED = [
  // May 20-30
  { col:"todo", title:"Bathroom & kitchen fittings — decide",          room:"Bathroom",        prio:"Urgent",  note:"Jaquar quote coming tomorrow. Florentine Prime / Ornamix Prime / Cubix Prime shortlisted. ~₹25k per bathroom at 25% discount." },
  { col:"todo", title:"WiFi, electric & CCTV lines layout",            room:"General",         prio:"High",    note:"Electrician contact: Debasish Babu (saved as VCF). Plan conduit routing before walls close." },
  { col:"todo", title:"TDS check & Aquaguard decision",                room:"Kitchen",         prio:"High",    note:"Check water TDS at flat before deciding model." },
  { col:"todo", title:"Bathroom tiles — final slant/slope check",      room:"Bathroom",        prio:"High",    note:"Verify gradient on bathroom floor before tiling begins." },
  { col:"todo", title:"Book community hall & confirm date",            room:"General",         prio:"Medium",  note:"Need hall for move-in day. Check availability with committee." },
  { col:"todo", title:"Kitchen setup — call & escalate",               room:"Kitchen",         prio:"High",    note:"Modular kitchen vendor follow-up overdue." },
  // Fittings / purchases
  { col:"inprogress", title:"Jaquar fittings — get discount quote",    room:"Bathroom",        prio:"Urgent",  note:"Soumyo visiting showroom. Basin faucet ~₹8k, wall mixer ~₹11k, commode shower ~₹2k, rain shower ~₹7k, hand shower ~₹5k." },
  { col:"todo", title:"Order 2nd Atomberg exhaust fan (200mm)",        room:"Bathroom",        prio:"High",    note:"One arrived. Need one more — square cut 175mm cutout. Link: https://amzn.in/d/05fsRWY7" },
  { col:"todo", title:"Sanmaica/laminate choice — couple's wardrobe",  room:"Couple's Room",   prio:"High",    note:"Greenlam samples received. Dona prefers white. Shortlist: Pure Ash, White Oak, Oslo 31114." },
  { col:"inprogress", title:"Basin / vanity cabinet finalise",         room:"Bathroom",        prio:"High",    note:"Options: IKEA IVÖSJÖN (₹?), Kohler Serif oval basin, Plantex wall mount set. Measurement: 39cm above, 31cm from floor." },
  { col:"todo", title:"Kitchen granite slab — confirm tile choice",    room:"Kitchen",         prio:"Medium",  note:"Semone Crema Glossy (option 3) preferred by most. Soumyo likes option 1 (Labur Num Murfin), Shuchi likes option 2." },
  // June 12-20
  { col:"todo", title:"Buy ceiling fans & lights",                     room:"General",         prio:"Medium",  note:"Atomberg Renesa Elite 1200mm shortlisted for main rooms. Dining: small 600mm fan. Shortlist finalised." },
  { col:"todo", title:"Wall colour — finalise & order paint",          room:"General",         prio:"Medium",  note:"Dulux Velvet Touch 'Crisp Linen' suggested for walls." },
  { col:"todo", title:"Measure & order curtains",                      room:"General",         prio:"Medium",  note:"Measure all windows for curtain length before ordering." },
  { col:"todo", title:"Mosquito nets — procure & install",             room:"General",         prio:"Medium",  note:"Sliding mosquito net for all windows. Balcony included." },
  { col:"todo", title:"Clothes drying rod — balcony",                  room:"Balcony",         prio:"Low",     note:"Provision for drying rod in south-facing balcony." },
  // Wardrobe / carpentry
  { col:"inprogress", title:"Wardrobe work — Mrinal Rana carpenter",  room:"Master Bedroom",  prio:"High",    note:"Mrinal Rana: 9836905699. Thakur ghar & guest room in progress. Drawing for attached bath bedroom wardrobe not yet shared." },
  { col:"todo", title:"Grill work — all windows & balcony",           room:"Balcony",         prio:"High",    note:"Contractor: Pintu Kundu 9830729442. Grill person to take measurements once exhaust fan installed." },
  // July
  { col:"todo", title:"Sort & segregate existing furniture",           room:"General",         prio:"Medium",  note:"Decide what goes to New Town vs what stays / sold." },
  { col:"todo", title:"Book packers & movers",                        room:"General",         prio:"Medium",  note:"Book well in advance for July move." },
  { col:"todo", title:"Deep cleaning before move-in",                 room:"General",         prio:"Medium",  note:"Full flat deep clean including commode & bathroom tiles." },
  { col:"todo", title:"Install all electrical appliances",            room:"General",         prio:"Medium",  note:"Fans, lights, exhaust fans, AC units after painting done." },
  // Done
  { col:"done",  title:"Society renovation intimation letter sent",    room:"General",         prio:"Low",     note:"Filed with committee for Flat 8A Tower 8 renovation." },
  { col:"done",  title:"Carpenter rate & plywood grade decided",       room:"General",         prio:"Low",     note:"Sainik 710 (BWP) for general, Club Prime for master bedroom wardrobe only." },
  { col:"done",  title:"Atomberg exhaust fan model finalised",         room:"Bathroom",        prio:"Low",     note:"Atomberg Efficio 150mm 13W square cut — 2 needed." },
  { col:"done",  title:"Window sliding installed",                     room:"General",         prio:"Low",     note:"Janla lagie dieche — dona confirmed 15 May." },
  { col:"done",  title:"Electrician contact saved (Debasish Babu)",   room:"General",         prio:"Low",     note:"VCF shared in group." },
].map((t, i) => ({ ...t, id: `seed_${i}`, ts: Date.now() - i * 60000 }));

const SK = "sankalpa_kanban_v3";

async function load() {
  try { const r = await window.storage.get(SK); return r ? JSON.parse(r.value) : null; } catch { return null; }
}
async function save(data) {
  try { await window.storage.set(SK, JSON.stringify(data)); } catch {}
}

function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2); }
function fmt(ts) { return new Date(ts).toLocaleDateString("en-IN", { day:"numeric", month:"short" }); }

// ── main app ─────────────────────────────────────────────────────────────────
export default function App() {
  const [cards, setCards] = useState([]);
  const [ready, setReady] = useState(false);
  const [filterRoom, setFilterRoom] = useState("All");
  const [filterPrio, setFilterPrio] = useState("All");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null);   // { mode: "add"|"edit", col?, card? }
  const [drag, setDrag] = useState(null);     // { cardId }
  const [over, setOver] = useState(null);     // { colId }

  useEffect(() => {
    load().then(d => { setCards(d ?? SEED); setReady(true); });
  }, []);

  const persist = useCallback(next => { setCards(next); save(next); }, []);

  const moveCard = (cardId, toCol) => {
    persist(cards.map(c => c.id === cardId ? { ...c, col: toCol, ts: Date.now() } : c));
  };

  const deleteCard = id => { if (confirm("Delete this task?")) persist(cards.filter(c => c.id !== id)); };

  const upsert = card => {
    if (card.id) persist(cards.map(c => c.id === card.id ? { ...card, ts: Date.now() } : c));
    else persist([{ ...card, id: uid(), ts: Date.now() }, ...cards]);
    setModal(null);
  };

  const visible = cards.filter(c =>
    (filterRoom === "All" || c.room === filterRoom) &&
    (filterPrio === "All" || c.prio === filterPrio) &&
    (!search || c.title.toLowerCase().includes(search.toLowerCase()) || (c.note||"").toLowerCase().includes(search.toLowerCase()))
  );

  const colCards = colId => visible.filter(c => c.col === colId);
  const totalByCol = colId => cards.filter(c => c.col === colId).length;

  // drag handlers
  const onDragStart = (e, cardId) => { setDrag({ cardId }); e.dataTransfer.effectAllowed = "move"; };
  const onDragOver  = (e, colId)  => { e.preventDefault(); setOver({ colId }); };
  const onDrop      = (e, colId)  => { e.preventDefault(); if (drag) moveCard(drag.cardId, colId); setDrag(null); setOver(null); };
  const onDragEnd   = ()          => { setDrag(null); setOver(null); };

  if (!ready) return <div style={{ minHeight:"100vh", background:C.bg, display:"flex", alignItems:"center", justifyContent:"center", fontFamily:"Georgia,serif", color:C.mid }}>Loading…</div>;

  const totalDone = cards.filter(c => c.col === "done").length;
  const pct = cards.length ? Math.round(totalDone / cards.length * 100) : 0;

  return (
    <div style={{ minHeight:"100vh", background:C.bg, fontFamily:"Georgia,serif" }}>
      {/* ── header ── */}
      <div style={{ background:`linear-gradient(135deg, ${C.dark} 0%, ${C.brown} 60%, ${C.mid} 100%)`, color:"#FDF6EC", padding:"0 0 0 0", boxShadow:"0 4px 24px rgba(30,18,8,.5)" }}>
        <div style={{ maxWidth:1400, margin:"0 auto", padding:"18px 24px" }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", flexWrap:"wrap", gap:12 }}>
            <div>
              <div style={{ fontSize:22, fontWeight:"bold", letterSpacing:".06em" }}>🏡 Sankalpa Interiors</div>
              <div style={{ fontSize:11, opacity:.65, letterSpacing:".12em", marginTop:2 }}>FLAT 8A · TOWER 8 · NEW TOWN — RENOVATION TRACKER</div>
            </div>
            {/* progress */}
            <div style={{ flex:"0 0 auto", textAlign:"center" }}>
              <div style={{ position:"relative", width:56, height:56, margin:"0 auto" }}>
                <svg width={56} height={56} style={{ transform:"rotate(-90deg)" }}>
                  <circle cx={28} cy={28} r={22} fill="none" stroke="rgba(255,255,255,.15)" strokeWidth={5}/>
                  <circle cx={28} cy={28} r={22} fill="none" stroke={C.gold} strokeWidth={5}
                    strokeDasharray={`${2*Math.PI*22*pct/100} ${2*Math.PI*22}`} strokeLinecap="round"/>
                </svg>
                <div style={{ position:"absolute", inset:0, display:"flex", alignItems:"center", justifyContent:"center", fontSize:13, fontWeight:"bold" }}>{pct}%</div>
              </div>
              <div style={{ fontSize:10, opacity:.6, marginTop:2 }}>COMPLETE</div>
            </div>
            <button onClick={() => setModal({ mode:"add", col:"todo" })} style={{ background:C.gold, color:C.dark, border:"none", borderRadius:8, padding:"10px 20px", fontWeight:"bold", fontSize:14, cursor:"pointer", fontFamily:"inherit", letterSpacing:".03em" }}>+ Add Task</button>
          </div>

          {/* filters */}
          <div style={{ marginTop:14, display:"flex", gap:8, flexWrap:"wrap", alignItems:"center" }}>
            <input placeholder="🔍 Search tasks…" value={search} onChange={e=>setSearch(e.target.value)}
              style={{ padding:"7px 14px", borderRadius:8, border:"1.5px solid rgba(255,255,255,.2)", background:"rgba(255,255,255,.1)", color:"#FDF6EC", fontSize:13, fontFamily:"inherit", outline:"none", minWidth:180, flex:1 }} />
            <RoomPill active={filterRoom} onChange={setFilterRoom} />
            <PrioPill active={filterPrio} onChange={setFilterPrio} />
          </div>
        </div>
      </div>

      {/* ── board ── */}
      <div style={{ maxWidth:1400, margin:"0 auto", padding:"24px 16px", display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:16, minHeight:"calc(100vh - 180px)" }}>
        {COLUMNS.map(col => (
          <Column key={col.id} col={col} cards={colCards(col.id)} total={totalByCol(col.id)}
            isOver={over?.colId === col.id}
            onDragOver={e => onDragOver(e, col.id)} onDrop={e => onDrop(e, col.id)}
            onAddCard={() => setModal({ mode:"add", col: col.id })}
            onEditCard={card => setModal({ mode:"edit", card })}
            onDeleteCard={deleteCard}
            onMoveCard={moveCard}
            onDragStart={onDragStart} onDragEnd={onDragEnd}
          />
        ))}
      </div>

      {modal && <CardModal modal={modal} onSave={upsert} onClose={() => setModal(null)} />}
    </div>
  );
}

// ── column ────────────────────────────────────────────────────────────────────
function Column({ col, cards, total, isOver, onDragOver, onDrop, onAddCard, onEditCard, onDeleteCard, onMoveCard, onDragStart, onDragEnd }) {
  return (
    <div onDragOver={onDragOver} onDrop={onDrop}
      style={{ background: isOver ? col.light : "rgba(255,253,249,.6)", borderRadius:14,
        border:`2px solid ${isOver ? col.accent : "rgba(196,180,154,.35)"}`,
        transition:"border .15s, background .15s", display:"flex", flexDirection:"column", minHeight:400 }}>
      {/* col header */}
      <div style={{ padding:"14px 16px 10px", borderBottom:`2px solid ${col.light}` }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ fontSize:18 }}>{col.emoji}</span>
            <span style={{ fontWeight:"bold", fontSize:14, color: col.accent, letterSpacing:".04em" }}>{col.label}</span>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ background:col.accent, color:"#fff", fontSize:11, fontWeight:"bold", padding:"2px 8px", borderRadius:10 }}>{total}</span>
            <button onClick={onAddCard} title="Add task" style={{ background:"none", border:`1.5px solid ${col.accent}`, color:col.accent, borderRadius:6, width:24, height:24, cursor:"pointer", fontSize:16, lineHeight:"22px", padding:0, fontWeight:"bold" }}>+</button>
          </div>
        </div>
      </div>

      {/* cards */}
      <div style={{ padding:"10px 10px", flex:1, display:"flex", flexDirection:"column", gap:8, overflowY:"auto" }}>
        {cards.length === 0 && (
          <div style={{ textAlign:"center", padding:"32px 0", color:C.muted, fontSize:13, userSelect:"none" }}>Drop tasks here</div>
        )}
        {cards.map(card => (
          <Card key={card.id} card={card} colAccent={col.accent}
            onEdit={() => onEditCard(card)} onDelete={() => onDeleteCard(card.id)}
            onMove={toCol => onMoveCard(card.id, toCol)}
            onDragStart={e => onDragStart(e, card.id)} onDragEnd={onDragEnd}
          />
        ))}
      </div>
    </div>
  );
}

// ── card ──────────────────────────────────────────────────────────────────────
function Card({ card, colAccent, onEdit, onDelete, onMove, onDragStart, onDragEnd }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const pc = PRIO_COLOR[card.prio];
  const otherCols = COLUMNS.filter(c => c.id !== card.col);

  return (
    <div draggable onDragStart={onDragStart} onDragEnd={onDragEnd}
      style={{ background:C.paper, borderRadius:10, padding:"12px 13px", border:`1.5px solid #E8DFD2`,
        boxShadow:"0 2px 6px rgba(30,18,8,.07)", cursor:"grab", position:"relative",
        borderLeft:`4px solid ${colAccent}`, transition:"box-shadow .15s" }}
      onMouseEnter={e => e.currentTarget.style.boxShadow="0 6px 18px rgba(30,18,8,.14)"}
      onMouseLeave={e => e.currentTarget.style.boxShadow="0 2px 6px rgba(30,18,8,.07)"}
    >
      {/* top row */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:8, marginBottom:6 }}>
        <div style={{ flex:1 }}>
          <div style={{ fontSize:13.5, fontWeight:"bold", color:C.dark, lineHeight:1.35 }}>{card.title}</div>
        </div>
        <div style={{ position:"relative", flexShrink:0 }}>
          <button onClick={() => setMenuOpen(m => !m)} style={{ background:"none", border:"none", color:C.muted, cursor:"pointer", fontSize:18, padding:"0 2px", lineHeight:1 }}>⋯</button>
          {menuOpen && (
            <div style={{ position:"absolute", right:0, top:22, background:"#fff", borderRadius:8, boxShadow:"0 8px 24px rgba(0,0,0,.15)", zIndex:99, minWidth:140, border:"1px solid #E8DFD2" }} onMouseLeave={() => setMenuOpen(false)}>
              <div onClick={() => { onEdit(); setMenuOpen(false); }} style={mItem}>✎ Edit</div>
              <div style={{ padding:"4px 12px", fontSize:11, color:C.muted, fontWeight:"bold", letterSpacing:".06em" }}>MOVE TO</div>
              {otherCols.map(c => <div key={c.id} onClick={() => { onMove(c.id); setMenuOpen(false); }} style={mItem}>{c.emoji} {c.label}</div>)}
              <div style={{ borderTop:"1px solid #F0E8DE" }}/>
              <div onClick={() => { onDelete(); setMenuOpen(false); }} style={{ ...mItem, color:"#CC2222" }}>✕ Delete</div>
            </div>
          )}
        </div>
      </div>

      {/* room + priority badges */}
      <div style={{ display:"flex", gap:5, flexWrap:"wrap", marginBottom: card.note ? 6 : 0 }}>
        <span style={{ fontSize:10, background:"#F5EFE6", color:C.brown, padding:"2px 7px", borderRadius:10 }}>{ROOM_ICON[card.room]} {card.room}</span>
        <span style={{ fontSize:10, background: pc+"22", color:pc, border:`1px solid ${pc}55`, padding:"2px 7px", borderRadius:10, fontWeight:"bold" }}>{card.prio}</span>
      </div>

      {/* note */}
      {card.note && (
        <div>
          <div style={{ fontSize:11.5, color:"#777", lineHeight:1.55, marginTop:5,
            display: expanded ? "block" : "-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical", overflow: expanded ? "visible" : "hidden" }}>
            {card.note}
          </div>
          {card.note.length > 80 && (
            <button onClick={() => setExpanded(x => !x)} style={{ fontSize:10, color:colAccent, background:"none", border:"none", cursor:"pointer", padding:0, marginTop:2 }}>
              {expanded ? "show less ▲" : "show more ▼"}
            </button>
          )}
        </div>
      )}

      <div style={{ fontSize:10, color:"#C4B49A", marginTop:8, textAlign:"right" }}>{fmt(card.ts)}</div>
    </div>
  );
}

const mItem = { padding:"8px 14px", fontSize:13, cursor:"pointer", color:C.dark, fontFamily:"Georgia,serif",
  transition:"background .1s", onMouseEnter:()=>{}, "&:hover":{ background:"#F5EFE6" } };

// ── filter pills ──────────────────────────────────────────────────────────────
function RoomPill({ active, onChange }) {
  const rooms = ["All", ...ROOMS];
  return (
    <div style={{ display:"flex", gap:5, flexWrap:"wrap" }}>
      {rooms.map(r => (
        <button key={r} onClick={() => onChange(r)} style={{
          padding:"4px 11px", borderRadius:20, fontSize:11, cursor:"pointer", fontFamily:"inherit", fontWeight: active===r?"bold":"normal",
          border: active===r ? "2px solid #FDF6EC" : "1.5px solid rgba(255,255,255,.25)",
          background: active===r ? "rgba(255,253,249,.25)" : "transparent", color:"#FDF6EC"
        }}>{r==="All"?"🏠 All":ROOM_ICON[r]+" "+r}</button>
      ))}
    </div>
  );
}
function PrioPill({ active, onChange }) {
  const opts = ["All",...PRIO];
  return (
    <div style={{ display:"flex", gap:5 }}>
      {opts.map(p => (
        <button key={p} onClick={() => onChange(p)} style={{
          padding:"4px 10px", borderRadius:20, fontSize:11, cursor:"pointer", fontFamily:"inherit",
          border: active===p ? `2px solid ${PRIO_COLOR[p]||"#FDF6EC"}` : "1.5px solid rgba(255,255,255,.25)",
          background: active===p ? (PRIO_COLOR[p]||"rgba(255,253,249,.25)")+"44" : "transparent",
          color:"#FDF6EC", fontWeight: active===p?"bold":"normal"
        }}>{p}</button>
      ))}
    </div>
  );
}

// ── modal ─────────────────────────────────────────────────────────────────────
function CardModal({ modal, onSave, onClose }) {
  const isEdit = modal.mode === "edit";
  const init = isEdit ? modal.card : { col: modal.col, title:"", room:"General", prio:"Medium", note:"" };
  const [form, setForm] = useState(init);
  const set = (k,v) => setForm(f => ({ ...f, [k]:v }));

  return (
    <div style={{ position:"fixed", inset:0, background:"rgba(30,18,8,.65)", zIndex:300, display:"flex", alignItems:"center", justifyContent:"center", padding:16 }}>
      <div style={{ background:"#FFFDF9", borderRadius:16, width:"100%", maxWidth:500, boxShadow:"0 24px 64px rgba(0,0,0,.35)", overflow:"hidden" }}>
        <div style={{ background:`linear-gradient(135deg, ${C.dark}, ${C.brown})`, padding:"18px 22px", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <span style={{ color:"#FDF6EC", fontWeight:"bold", fontSize:16 }}>{isEdit ? "✎ Edit Task" : "＋ New Task"}</span>
          <button onClick={onClose} style={{ background:"none", border:"none", color:"#FDF6EC", fontSize:20, cursor:"pointer" }}>✕</button>
        </div>

        <div style={{ padding:22, display:"flex", flexDirection:"column", gap:14 }}>
          {/* title */}
          <div>
            <label style={lbl}>Task Title *</label>
            <input value={form.title} onChange={e=>set("title",e.target.value)} placeholder="e.g. Confirm Jaquar fittings"
              style={inp} />
          </div>

          {/* note */}
          <div>
            <label style={lbl}>Notes / Details</label>
            <textarea value={form.note||""} onChange={e=>set("note",e.target.value)} rows={3} placeholder="Measurements, vendor, links, amounts…" style={{ ...inp, resize:"vertical" }} />
          </div>

          {/* column */}
          <div>
            <label style={lbl}>Column</label>
            <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
              {COLUMNS.map(c => (
                <button key={c.id} onClick={()=>set("col",c.id)} type="button" style={{ padding:"5px 12px", borderRadius:20, fontSize:12, cursor:"pointer", fontFamily:"inherit",
                  border: form.col===c.id ? `2px solid ${c.accent}` : "1.5px solid #D5C9B8",
                  background: form.col===c.id ? c.accent : "#FAF7F3",
                  color: form.col===c.id ? "#fff" : C.brown }}>
                  {c.emoji} {c.label}
                </button>
              ))}
            </div>
          </div>

          {/* room */}
          <div>
            <label style={lbl}>Room</label>
            <div style={{ display:"flex", gap:5, flexWrap:"wrap" }}>
              {ROOMS.map(r => (
                <button key={r} onClick={()=>set("room",r)} type="button" style={{ padding:"4px 10px", borderRadius:20, fontSize:11, cursor:"pointer", fontFamily:"inherit",
                  border: form.room===r ? `2px solid ${C.brown}` : "1.5px solid #D5C9B8",
                  background: form.room===r ? C.brown : "#FAF7F3",
                  color: form.room===r ? "#FDF6EC" : C.brown }}>
                  {ROOM_ICON[r]} {r}
                </button>
              ))}
            </div>
          </div>

          {/* priority */}
          <div>
            <label style={lbl}>Priority</label>
            <div style={{ display:"flex", gap:6 }}>
              {PRIO.map(p => (
                <button key={p} onClick={()=>set("prio",p)} type="button" style={{ flex:1, padding:"6px 0", borderRadius:8, fontSize:12, cursor:"pointer", fontFamily:"inherit", fontWeight:"bold",
                  border: form.prio===p ? `2px solid ${PRIO_COLOR[p]}` : "1.5px solid #D5C9B8",
                  background: form.prio===p ? PRIO_COLOR[p]+"22" : "#FAF7F3",
                  color: form.prio===p ? PRIO_COLOR[p] : "#999" }}>
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display:"flex", gap:10, justifyContent:"flex-end", borderTop:"1px solid #EDE5D8", paddingTop:14 }}>
            <button onClick={onClose} style={{ padding:"9px 18px", borderRadius:8, border:"1.5px solid #D5C9B8", background:"#FAF7F3", cursor:"pointer", fontFamily:"inherit", color:"#666" }}>Cancel</button>
            <button onClick={() => { if(!form.title.trim()){alert("Title required");return;} onSave(form); }}
              style={{ padding:"9px 22px", borderRadius:8, border:"none", background:C.brown, color:"#FDF6EC", cursor:"pointer", fontFamily:"inherit", fontWeight:"bold" }}>
              {isEdit ? "Save Changes" : "Add Task"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const lbl = { display:"block", fontSize:11, fontWeight:"bold", color:C.brown, marginBottom:5, letterSpacing:".06em", textTransform:"uppercase" };
const inp = { width:"100%", padding:"9px 13px", border:"1.5px solid #D5C9B8", borderRadius:8, fontSize:13.5, fontFamily:"Georgia,serif", outline:"none", background:"#fff", color:C.dark, boxSizing:"border-box" };
