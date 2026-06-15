(function(){
  // Chapter order, titles and numbers are read from the DOM, so adding or
  // reordering chapters requires no change here — just add a chapter file.
  var SECTIONS = [].slice.call(document.querySelectorAll('.chapter'));
  var order = SECTIONS.map(function(c){ return c.id; });
  var TITLES = {}, NUMS = {};
  SECTIONS.forEach(function(c){
    TITLES[c.id] = c.getAttribute('data-title') || 'Cover';
    NUMS[c.id]  = c.getAttribute('data-num') || '';
  });
  function num(id){ return NUMS[id] || ''; }

  // ----- remember progress: auto last-position + an explicit line bookmark -----
  var STORE = 'fbtb:last';   // auto: last chapter + scroll position
  var MARK  = 'fbtb:mark';   // explicit: a chapter + paragraph the reader marked
  function readSaved(){ try{ return JSON.parse(localStorage.getItem(STORE) || 'null'); }catch(e){ return null; } }
  function readMark(){ try{ return JSON.parse(localStorage.getItem(MARK) || 'null'); }catch(e){ return null; } }
  function markSaved(){
    var s = readMark() || readSaved();   // the sidebar dot prefers your explicit bookmark
    toc.forEach(function(l){ l.classList.toggle('marked', !!s && l.getAttribute('data-go') === s.id); });
  }
  function save(id, y){
    if(id && id !== 'cover'){ try{ localStorage.setItem(STORE, JSON.stringify({ id:id, y:Math.round(y || 0) })); }catch(e){} }
    markSaved();
  }
  function paras(id){ var sec=document.getElementById(id); return sec ? Array.prototype.slice.call(sec.querySelectorAll('.page > p')) : []; }
  function renderMark(){
    document.querySelectorAll('p.bookmarked').forEach(function(e){ e.classList.remove('bookmarked'); });
    var m = readMark(); if(!m) return;
    var ps = paras(m.id); if(ps[m.p]) ps[m.p].classList.add('bookmarked');
  }

  var bar = document.getElementById('progress');
  var toc = Array.prototype.slice.call(document.querySelectorAll('.book-toc a'));
  var nav = document.getElementById('bookNav');
  var menuBtn = document.getElementById('menuBtn');
  var scrim = document.getElementById('navScrim');
  var pgPrev = document.getElementById('pgPrev'), pgNext = document.getElementById('pgNext');
  var pgPrevT = document.getElementById('pgPrevT'), pgNextT = document.getElementById('pgNextT');
  var bmToast = document.getElementById('bmToast');
  var ttsAdvancing = false;   // true only while read-aloud auto-advances to the next chapter

  function indexOfActive(){
    var a = document.querySelector('.chapter.active');
    return a ? order.indexOf(a.id) : 0;
  }
  function closeNav(){ nav.classList.remove('open'); if(scrim) scrim.style.display='none'; if(menuBtn) menuBtn.style.display=''; }
  function openNav(){ nav.classList.add('open'); if(scrim) scrim.style.display='block'; if(menuBtn) menuBtn.style.display='none'; }

  function setPager(i){
    var p = i > 0 ? order[i-1] : null;
    var n = i < order.length-1 ? order[i+1] : null;
    if(p){ pgPrev.hidden=false; pgPrevT.textContent=(num(p)?num(p)+'  ':'')+TITLES[p]; pgPrev.setAttribute('aria-label','Previous: '+TITLES[p]); }
    else pgPrev.hidden=true;
    if(n){ pgNext.hidden=false; pgNextT.textContent=(num(n)?num(n)+'  ':'')+TITLES[n]; pgNext.setAttribute('aria-label','Next: '+TITLES[n]); }
    else pgNext.hidden=true;
  }

  function show(id, push, y){
    if(order.indexOf(id) === -1) id = 'cover';
    document.querySelectorAll('.chapter').forEach(function(c){ c.classList.toggle('active', c.id === id); });
    document.body.classList.toggle('on-cover', id === 'cover');   // hide the pager on the cover
    if(!ttsAdvancing) stopReadAloud();   // stop narration when the reader navigates manually
    toc.forEach(function(l){ var on = l.getAttribute('data-go') === id; l.classList.toggle('current', on); if(on){ l.setAttribute('aria-current','true'); } else { l.removeAttribute('aria-current'); } });
    setPager(order.indexOf(id));
    window.scrollTo(0, 0);
    if(y){ var _y = y; requestAnimationFrame(function(){ requestAnimationFrame(function(){ window.scrollTo(0, _y); }); }); }
    if(push !== false){ try{ history.pushState({id:id}, '', '#' + id); }catch(e){} }
    closeNav();
    updateBar();
    save(id, y || 0);
    renderMark();
    if(id !== 'cover') maybeHint();
  }
  function go(delta){
    var i = indexOfActive() + delta;
    if(i >= 0 && i < order.length) show(order[i]);
  }
  function updateBar(){
    var h = document.documentElement;
    var denom = h.scrollHeight - h.clientHeight;
    var p = denom > 0 ? h.scrollTop / denom : 0;
    bar.style.width = Math.max(0, Math.min(1, p)) * 100 + '%';
  }

  // ----- explicit line bookmark: click / select a line to mark it -----
  function toast(msg){
    if(!bmToast) return;
    bmToast.textContent = msg; bmToast.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(function(){ bmToast.classList.remove('show'); }, 1800);
  }
  function chapterOf(p){ var s = p.closest('.chapter'); return s ? s.id : null; }
  function setMark(p){
    var id = chapterOf(p); if(!id || id === 'cover') return;
    var ps = paras(id), idx = ps.indexOf(p); if(idx < 0) return;
    try{ localStorage.setItem(MARK, JSON.stringify({ id:id, p:idx })); }catch(e){}
    renderMark(); markSaved(); setupReturn(); toast('Bookmarked this line');
  }
  function toggleMark(p){
    var id = chapterOf(p), ps = paras(id || ''), idx = ps.indexOf(p), m = readMark();
    if(m && m.id === id && m.p === idx){
      try{ localStorage.removeItem(MARK); }catch(e){}
      renderMark(); markSaved(); setupReturn(); toast('Bookmark removed');
    } else { setMark(p); }
  }
  function gotoMark(){
    var m = readMark(); if(!m || order.indexOf(m.id) === -1) return;
    show(m.id, true);
    requestAnimationFrame(function(){ requestAnimationFrame(function(){
      var ps = paras(m.id), el = ps[m.p];
      if(el){ el.scrollIntoView({ block:'center' }); el.classList.add('bm-flash'); setTimeout(function(){ el.classList.remove('bm-flash'); }, 1600); }
    });});
  }
  function maybeHint(){
    try{ if(localStorage.getItem('fbtb:hint') || readMark()){ localStorage.setItem('fbtb:hint','1'); return; } }catch(e){ return; }
    toast('Tip: click or select any line to bookmark it');
    try{ localStorage.setItem('fbtb:hint','1'); }catch(e){}
  }

  // sidebar menu
  toc.forEach(function(l){ l.addEventListener('click', function(e){ e.preventDefault(); show(l.getAttribute('data-go')); }); });
  // bottom pager
  if(pgPrev) pgPrev.addEventListener('click', function(){ go(-1); });
  if(pgNext) pgNext.addEventListener('click', function(){ go(1); });
  // cover CTA
  var cta = document.getElementById('startReading');
  if(cta) cta.addEventListener('click', function(e){ e.preventDefault(); show('ch1'); });
  // "next chapter" teasers are clickable
  document.querySelectorAll('.next').forEach(function(n){ n.style.cursor='pointer'; n.addEventListener('click', function(){ go(1); }); });

  // keyboard: left / right turn pages; space toggles narration while it's active
  addEventListener('keydown', function(e){
    if(e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if(e.key === 'ArrowRight'){ go(1); }
    else if(e.key === 'ArrowLeft'){ go(-1); }
    else if((e.key === ' ' || e.code === 'Space') && typeof synth !== 'undefined' && synth && ttsState !== 'idle'){
      e.preventDefault(); ttsTogglePlay();   // only hijack space while reading aloud, so it still scrolls otherwise
    }
  });

  // progress bar follows scroll; also remember scroll position (throttled)
  var saveTimer = null;
  addEventListener('scroll', function(){
    updateBar();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function(){
      var a = document.querySelector('.chapter.active');
      if(a) save(a.id, window.scrollY || document.documentElement.scrollTop || 0);
    }, 300);
  }, {passive:true});

  // scroll past the edges to turn the page — ONE turn per gesture (no skipping)
  var acc = 0, gestureUsed = false, wt = null;
  function atBottom(){ var h=document.documentElement; return (h.scrollTop + h.clientHeight) >= (h.scrollHeight - 2); }
  function atTop(){ return (document.documentElement.scrollTop || 0) <= 0; }
  addEventListener('wheel', function(e){
    clearTimeout(wt); wt = setTimeout(function(){ gestureUsed = false; acc = 0; }, 200); // re-arm only after the scroll stops
    if(gestureUsed) return;
    if(e.deltaY > 0 && atBottom()){ acc += e.deltaY; if(acc > 140){ gestureUsed = true; acc = 0; go(1); } }
    else if(e.deltaY < 0 && atTop()){ acc += e.deltaY; if(acc < -140){ gestureUsed = true; acc = 0; go(-1); } }
    else { acc = 0; }
  }, {passive:true});

  // touch: ONE turn per swipe
  var ty = null, swiped = false;
  addEventListener('touchstart', function(e){ ty = e.touches[0].clientY; swiped = false; }, {passive:true});
  addEventListener('touchmove', function(e){
    if(ty === null || swiped) return;
    var dy = ty - e.touches[0].clientY; // positive = scrolling down
    if(dy > 90 && atBottom()){ swiped = true; go(1); }
    else if(dy < -90 && atTop()){ swiped = true; go(-1); }
  }, {passive:true});
  addEventListener('touchend', function(){ ty = null; }, {passive:true});

  // mobile drawer
  if(menuBtn) menuBtn.addEventListener('click', openNav);
  if(scrim) scrim.addEventListener('click', closeNav);
  var navClose = document.getElementById('navClose');
  if(navClose) navClose.addEventListener('click', closeNav);

  // browser back/forward between chapters
  addEventListener('popstate', function(){ show((location.hash || '#cover').slice(1), false); });

  // bookmark a line: click a body paragraph (or select text in it) to mark it
  var readerEl = document.getElementById('reader');
  if(readerEl) readerEl.addEventListener('click', function(e){
    var p = e.target.closest('p');
    if(!p || !p.parentElement || !p.parentElement.classList.contains('page')) return;
    // while reading aloud, tapping a line jumps narration there (instead of bookmarking)
    if(typeof synth !== 'undefined' && synth && ttsState !== 'idle'){ if(ttsSeekTo(p)) return; }
    var sel = (window.getSelection && window.getSelection().toString().trim()) || '';
    if(sel) setMark(p);      // selecting text → mark that line
    else toggleMark(p);      // a plain click toggles the bookmark on that line
  });

  // cover return button — prefer the explicit bookmark, else the last auto position
  var resumeBtn = document.getElementById('resumeBtn');
  var rLead = resumeBtn ? resumeBtn.querySelector('.r-lead') : null;
  var rTtl  = resumeBtn ? resumeBtn.querySelector('.r-ttl')  : null;
  function setupReturn(){
    if(!resumeBtn) return;
    var m = readMark(), s = readSaved();
    if(m && order.indexOf(m.id) !== -1){
      resumeBtn._mode = 'mark';
      if(rLead) rLead.textContent = '🔖 Your bookmark';
      if(rTtl)  rTtl.textContent = (num(m.id) ? num(m.id) + '  ' : '') + TITLES[m.id];
      resumeBtn.hidden = false;
    } else if(s && order.indexOf(s.id) !== -1){
      resumeBtn._mode = 'last';
      if(rLead) rLead.textContent = 'Continue';
      if(rTtl)  rTtl.textContent = (num(s.id) ? num(s.id) + '  ' : '') + TITLES[s.id];
      resumeBtn.hidden = false;
    } else {
      resumeBtn.hidden = true;
    }
  }
  if(resumeBtn) resumeBtn.addEventListener('click', function(e){
    e.preventDefault();
    if(resumeBtn._mode === 'mark'){ gotoMark(); }
    else { var s = readSaved(); if(s && order.indexOf(s.id) !== -1) show(s.id, true, s.y); }
  });

  // ===== read aloud (Web Speech API) =====
  var synth = window.speechSynthesis || null;
  var ttsEl = document.getElementById('tts');
  var ttsPlay = document.getElementById('ttsPlay');
  var ttsStop = document.getElementById('ttsStop');
  var ttsRateBtn = document.getElementById('ttsRate');
  var ttsVoiceSel = document.getElementById('ttsVoice');
  var ttsItems = [], ttsIdx = -1, ttsState = 'idle';   // idle | playing | paused
  var TTS_RATES = [1, 1.25, 1.5, 0.85], ttsRateI = 0;
  var ttsVoices = [], ttsVoice = null, ttsAutoAdvance = true, ttsChapterStart = 0, ttsSelEl = null;

  function ttsClearHL(){ for(var i = 0; i < ttsItems.length; i++) ttsItems[i].classList.remove('tts-speaking'); }
  function stopReadAloud(){ if(synth){ try{ synth.cancel(); }catch(e){} } ttsClearHL(); ttsState = 'idle'; ttsIdx = -1; ttsSelEl = null; ttsUI(); }
  function ttsCollect(){
    var a = document.querySelector('.chapter.active'); if(!a) return [];
    var sel = '.cb-title, .cb-sub, .page > p, .page .big-quote, .note, .bcap, .suite .case p, .next h3, .next p';
    return [].slice.call(a.querySelectorAll(sel)).filter(function(el){ return el.textContent.trim().length > 1; });
  }
  // say acronyms, symbols and amounts the way a person would (spoken text only)
  function ttsNormalize(t){
    return t
      .replace(/£\s?([\d,]+(?:\.\d+)?)/g, function(_, n){ return n.replace(/,/g, '') + ' pounds'; })
      .replace(/\bCI\/CD\b/g, 'C I, C D')
      .replace(/\bAPIs\b/g, 'A P Eyes')
      .replace(/\bAPI\b/g, 'A P I')
      .replace(/\bUI\b/g, 'U I')
      .replace(/\bAI\b/g, 'A.I.')
      .replace(/\bJSON\b/g, 'Jason')
      .replace(/\bSDET\b/g, 'S D E T')
      .replace(/\bQA\b/g, 'Q A')
      .replace(/\bCI\b/g, 'C I')
      .replace(/\bSEV-?1\b/gi, 'severity one')
      .replace(/\bP1\b/g, 'P one')
      .replace(/\bSAST\b/g, 'S A S T')
      .replace(/\bDAST\b/g, 'D A S T')
      .replace(/\bK6\b/g, 'K six')
      .replace(/\s+/g, ' ').trim();
  }
  // start from the line nearest the top of the viewport (so "Listen" resumes where you're reading)
  function ttsTopIndex(){
    for(var i = 0; i < ttsItems.length; i++){ if(ttsItems[i].getBoundingClientRect().bottom > 110) return i; }
    return 0;
  }
  // if the reader selected text in a line, start narration from that line
  function ttsSelectedIndex(){
    var el = null, sel = window.getSelection && window.getSelection();
    if(sel && sel.rangeCount && !sel.isCollapsed && sel.anchorNode){
      el = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentNode;
    } else if(ttsSelEl){ el = ttsSelEl; }
    if(!el) return -1;
    for(var i = 0; i < ttsItems.length; i++){ if(ttsItems[i].contains(el)) return i; }
    return -1;
  }
  function ttsSpeak(i){
    if(!synth) return;
    if(i >= ttsItems.length){ ttsFinish(); return; }
    ttsIdx = i; ttsClearHL();
    var el = ttsItems[i]; el.classList.add('tts-speaking'); el.scrollIntoView({ block:'center' });
    var u = new SpeechSynthesisUtterance(ttsNormalize(el.textContent));
    if(ttsVoice){ u.voice = ttsVoice; u.lang = ttsVoice.lang; }
    u.rate = TTS_RATES[ttsRateI];
    u.onend = function(){ if(ttsState === 'playing') ttsSpeak(ttsIdx + 1); };
    synth.speak(u);
  }
  function startReadAloud(startIdx){
    ttsItems = ttsCollect(); if(!ttsItems.length) return;
    var i;
    if(typeof startIdx === 'number' && startIdx >= 0){ i = startIdx; }
    else { var s = ttsSelectedIndex(); i = s >= 0 ? s : ttsTopIndex(); }   // selected line, else where you're reading
    ttsSelEl = null;
    try{ synth.cancel(); }catch(e){}
    ttsState = 'playing'; ttsChapterStart = Date.now(); ttsUI(); ttsSpeak(i);
  }
  function ttsTogglePlay(){
    if(ttsState === 'idle'){
      var hadSel = !!ttsSelEl || (window.getSelection && (window.getSelection().toString() || '').trim().length > 0);
      startReadAloud();
      toast(hadSel ? '🔊 Reading from your selected line' : '🔊 Reading aloud — select or tap a line to start there');
    }
    else if(ttsState === 'playing'){ try{ synth.pause(); }catch(e){} ttsState = 'paused'; ttsUI(); toast('⏸ Paused'); }
    else { try{ synth.resume(); }catch(e){} ttsState = 'playing'; ttsUI(); }
  }
  // jump narration to a tapped paragraph (used while reading aloud)
  function ttsSeekTo(p){
    var k = ttsItems.indexOf(p);
    if(k < 0) return false;
    try{ synth.cancel(); }catch(e){}
    ttsState = 'playing'; ttsUI(); ttsSpeak(k);
    return true;
  }
  function ttsFinish(){
    ttsClearHL();
    var i = order.indexOf((document.querySelector('.chapter.active') || {}).id);
    var realPlayback = (Date.now() - ttsChapterStart) > 3000;   // guard: don't blaze through if speech is silent/instant
    if(ttsAutoAdvance && realPlayback && i >= 0 && i < order.length - 1){
      ttsAdvancing = true; show(order[i + 1]); ttsAdvancing = false;
      startReadAloud(0);
    } else { ttsState = 'idle'; ttsIdx = -1; ttsUI(); }
  }
  function ttsUI(){
    if(!ttsEl) return;
    var playing = ttsState === 'playing', active = playing || ttsState === 'paused';
    ttsPlay.textContent = playing ? '⏸ Pause' : (ttsState === 'paused' ? '▶ Resume' : '🔊 Listen');
    ttsPlay.setAttribute('aria-label', playing ? 'Pause reading' : (ttsState === 'paused' ? 'Resume reading' : 'Listen to this chapter'));
    ttsStop.hidden = !active; ttsRateBtn.hidden = !active; ttsVoiceSel.hidden = !active;
    ttsRateBtn.textContent = TTS_RATES[ttsRateI] + '×';
    ttsEl.classList.toggle('on', active);
  }
  function ttsLoadVoices(){
    if(!synth || !ttsVoiceSel) return;
    var all = synth.getVoices();
    var en = all.filter(function(v){ return /^en([-_]|$)/i.test(v.lang); });
    if(!en.length) en = all;
    var nice = /natural|neural|premium|enhanced|siri|samantha|daniel|karen|moira|aria|jenny|guy|google (us|uk)/i;
    en.sort(function(a, b){ return (nice.test(b.name) ? 1 : 0) - (nice.test(a.name) ? 1 : 0); });
    ttsVoices = en;
    if(!ttsVoices.length) return;
    ttsVoiceSel.innerHTML = '';
    en.forEach(function(v){ var o = document.createElement('option'); o.value = v.name; o.textContent = (nice.test(v.name) ? '★ ' : '') + v.name.replace(/\s*\(.*?\)\s*/, '').slice(0, 20); ttsVoiceSel.appendChild(o); });
    var saved = null; try{ saved = localStorage.getItem('fbtb:voice'); }catch(e){}
    var pick = (saved && en.filter(function(v){ return v.name === saved; })[0]) || en[0];
    ttsVoice = pick; if(pick) ttsVoiceSel.value = pick.name;
  }
  if(synth && ttsEl){
    try{ var sr = parseInt(localStorage.getItem('fbtb:rate'), 10); if(!isNaN(sr) && sr >= 0 && sr < TTS_RATES.length) ttsRateI = sr; }catch(e){}
    ttsLoadVoices();
    if('onvoiceschanged' in synth) synth.addEventListener('voiceschanged', ttsLoadVoices);
    ttsPlay.addEventListener('click', ttsTogglePlay);
    ttsStop.addEventListener('click', stopReadAloud);
    ttsRateBtn.addEventListener('click', function(){ ttsRateI = (ttsRateI + 1) % TTS_RATES.length; try{ localStorage.setItem('fbtb:rate', ttsRateI); }catch(e){} ttsUI(); if(ttsState === 'playing'){ try{ synth.cancel(); }catch(e){} ttsSpeak(ttsIdx); } });
    ttsVoiceSel.addEventListener('change', function(){ for(var k = 0; k < ttsVoices.length; k++){ if(ttsVoices[k].name === ttsVoiceSel.value){ ttsVoice = ttsVoices[k]; break; } } try{ localStorage.setItem('fbtb:voice', ttsVoiceSel.value); }catch(e){} if(ttsState === 'playing'){ try{ synth.cancel(); }catch(e){} ttsSpeak(ttsIdx); } });
    // remember the last text selection inside the open chapter (survives clicking the Listen button)
    document.addEventListener('selectionchange', function(){
      var sel = window.getSelection();
      if(sel && sel.rangeCount && !sel.isCollapsed && sel.anchorNode){
        var el = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentNode;
        if(el && el.closest && el.closest('.chapter.active')) ttsSelEl = el;
      }
    });
    addEventListener('beforeunload', function(){ try{ synth.cancel(); }catch(e){} });
    ttsUI();
  } else if(ttsEl){
    ttsEl.style.display = 'none';   // browser has no speech synthesis
  }

  // start: a deep link (#chN) wins; otherwise the cover, offering a return button if we have history
  var saved = readSaved();
  var hash = (location.hash || '').slice(1);
  if(order.indexOf(hash) !== -1){
    show(hash, false, (saved && saved.id === hash) ? saved.y : 0);
  } else {
    show('cover', false);
    setupReturn();
  }
  renderMark();
  markSaved();
})();
