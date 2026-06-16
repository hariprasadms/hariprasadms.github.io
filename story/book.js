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
  var firstReadable = order.filter(function(id){ return id !== 'cover'; })[0] || 'ch1';
  if(cta) cta.addEventListener('click', function(e){ e.preventDefault(); show(firstReadable); });
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
    if(ttsState !== 'idle'){ if(ttsSeekTo(p)) return; }
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
  var ttsNow = document.getElementById('ttsNow');
  var ttsBackBtn = document.getElementById('ttsBack');
  var ttsFwdBtn = document.getElementById('ttsFwd');
  var ttsBar = document.getElementById('ttsBar');
  var ttsTrack = document.getElementById('ttsTrack');
  var ttsFill = document.getElementById('ttsFill');
  var ttsCurEl = document.getElementById('ttsCur');
  var ttsDurEl = document.getElementById('ttsDur');
  function fmt(s){ s = Math.max(0, Math.floor(s || 0)); var m = Math.floor(s/60), x = s%60; return m + ':' + (x<10?'0':'') + x; }
  function esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
  var ttsItems = [], ttsIdx = -1, ttsState = 'idle';   // idle | playing | paused
  var ttsWantPlay = false;   // true while the reader intends playback (used to resume after a system pause, e.g. screen lock)
  var TTS_RATES = [1, 1.25, 1.5, 0.85], ttsRateI = 0;
  var ttsVoices = [], ttsVoice = null, ttsAutoAdvance = true, ttsChapterStart = 0, ttsSelEl = null;
  var audioEl = document.getElementById('bookAudio'), ttsMode = 'speech';   // 'speech' = device TTS, 'audio' = recorded MP3
  var ttsCues = null, ttsCueCache = {}, ttsPendingSeek = null;   // recorded-narration highlight cues (start seconds per line)
  function activeAudioSrc(){ var a = document.querySelector('.chapter.active'); return (a && a.getAttribute('data-audio')) || ''; }
  function cuesUrl(src){ return src ? src.replace(/\.[^.]+$/, '') + '.cues.json' : ''; }
  // fetch the highlight cues for a recorded chapter (cached); then start syncing
  function loadCues(src, done){
    var url = cuesUrl(src);
    if(ttsCueCache[url]){ ttsCues = ttsCueCache[url]; done && done(); return; }
    try{
      fetch(url).then(function(r){ return r.ok ? r.json() : null; })
        .then(function(j){ ttsCueCache[url] = j || []; ttsCues = ttsCueCache[url]; done && done(); })
        .catch(function(){ ttsCues = []; done && done(); });
    }catch(e){ ttsCues = []; done && done(); }
  }
  // update the seek bar + clock (recorded audio only)
  function ttsProgress(){
    if(ttsMode !== 'audio') return;
    var t = audioEl.currentTime || 0, d = audioEl.duration || 0;
    var pct = d ? Math.max(0, Math.min(1, t/d)) * 100 : 0;
    if(ttsFill) ttsFill.style.width = pct + '%';
    if(ttsTrack){ ttsTrack.style.setProperty('--p', pct + '%'); ttsTrack.setAttribute('aria-valuetext', fmt(t) + ' of ' + fmt(d)); }
    if(ttsCurEl) ttsCurEl.textContent = fmt(t);
    if(ttsDurEl) ttsDurEl.textContent = fmt(d);
    msPos();
  }
  // highlight the line matching the current audio time
  function ttsAudioSync(){
    if(ttsMode !== 'audio') return;
    ttsProgress();
    if(!ttsCues || !ttsCues.length || !ttsItems.length) return;
    var t = audioEl.currentTime, k = -1;
    for(var i = 0; i < ttsCues.length && i < ttsItems.length; i++){ if(ttsCues[i] <= t + 0.05) k = i; else break; }
    if(k >= 0 && k !== ttsIdx){
      ttsIdx = k; ttsClearHL();
      var el = ttsItems[k]; if(el){ el.classList.add('tts-speaking'); el.scrollIntoView({ block:'center' }); }
    }
  }
  // back / forward: ±15s in recorded audio, ±1 line in device-voice mode
  function ttsSkip(sec){
    if(ttsState === 'idle') return;
    if(ttsMode === 'audio'){
      try{ audioEl.currentTime = Math.max(0, Math.min((audioEl.duration||0) - 0.3, (audioEl.currentTime||0) + sec)); }catch(e){}
      ttsAudioSync();
    } else {
      var n = (ttsIdx < 0 ? 0 : ttsIdx) + (sec > 0 ? 1 : -1);
      n = Math.max(0, Math.min(ttsItems.length - 1, n));
      try{ synth.cancel(); }catch(e){} ttsState = 'playing'; ttsUI(); ttsSpeak(n);
    }
  }
  // click / drag the track to seek (recorded audio)
  function ttsSeekFromEvent(e){
    if(ttsMode !== 'audio' || !audioEl.duration || !ttsTrack) return;
    var r = ttsTrack.getBoundingClientRect();
    var cx = (e.touches && e.touches[0]) ? e.touches[0].clientX : e.clientX;
    var ratio = Math.max(0, Math.min(1, (cx - r.left) / r.width));
    try{ audioEl.currentTime = ratio * audioEl.duration; }catch(e2){}
    ttsAudioSync();
  }

  // ----- Media Session: keep playing when the screen locks + lock-screen controls -----
  var hasMS = ('mediaSession' in navigator) && (typeof window.MediaMetadata === 'function');
  function msMeta(){
    if(!hasMS) return;
    var id = (document.querySelector('.chapter.active') || {}).id, n = num(id);
    try{
      navigator.mediaSession.metadata = new MediaMetadata({
        title: (n ? n + ' · ' : '') + (TITLES[id] || 'From Bugs to Brilliance'),
        artist: 'From Bugs to Brilliance',
        album: 'A Story of Software Testing',
        artwork: [{ src: '/story/cover.jpg', sizes: '1024x1536', type: 'image/jpeg' }]
      });
    }catch(e){}
  }
  function msState(s){ if(hasMS){ try{ navigator.mediaSession.playbackState = s; }catch(e){} } }
  function msPos(){
    if(!hasMS || ttsMode !== 'audio' || !audioEl.duration) return;
    try{ navigator.mediaSession.setPositionState({ duration: audioEl.duration, playbackRate: audioEl.playbackRate || 1, position: Math.min(audioEl.currentTime || 0, audioEl.duration) }); }catch(e){}
  }
  function msAdvance(delta){
    var i = indexOfActive() + delta;
    if(i < 0 || i >= order.length) return;
    ttsAdvancing = true; show(order[i]); ttsAdvancing = false; startReadAloud(0);
  }
  function msSetup(){
    if(!hasMS) return;
    var set = function(a, fn){ try{ navigator.mediaSession.setActionHandler(a, fn); }catch(e){} };
    set('play', function(){ if(ttsState !== 'playing') ttsTogglePlay(); });
    set('pause', function(){ if(ttsState === 'playing') ttsTogglePlay(); });
    set('seekbackward', function(){ ttsSkip(-15); });
    set('seekforward', function(){ ttsSkip(15); });
    set('previoustrack', function(){ msAdvance(-1); });
    set('nexttrack', function(){ msAdvance(1); });
    set('seekto', function(d){ if(d && d.seekTime != null && ttsMode === 'audio'){ try{ audioEl.currentTime = d.seekTime; }catch(e){} ttsAudioSync(); } });
  }

  function ttsClearHL(){ for(var i = 0; i < ttsItems.length; i++) ttsItems[i].classList.remove('tts-speaking'); }
  function stopReadAloud(){ ttsWantPlay = false; if(synth){ try{ synth.cancel(); }catch(e){} } if(audioEl){ try{ audioEl.pause(); audioEl.currentTime = 0; }catch(e){} } ttsClearHL(); ttsState = 'idle'; ttsIdx = -1; ttsSelEl = null; ttsMode = 'speech'; ttsUI(); }
  // Stop button: bookmark the line we stopped on, then stop
  function ttsStopAndBookmark(){
    var el = (ttsIdx >= 0 && ttsItems[ttsIdx]) ? ttsItems[ttsIdx] : null;
    var marked = false;
    if(el && el.tagName === 'P' && el.parentElement && el.parentElement.classList.contains('page')){
      var id = chapterOf(el), idx = paras(id).indexOf(el);
      if(idx >= 0){ try{ localStorage.setItem(MARK, JSON.stringify({ id:id, p:idx })); }catch(e){} markSaved(); setupReturn(); marked = true; }
    }
    stopReadAloud();
    if(marked) renderMark();
    toast(marked ? '🔖 Bookmarked where you stopped' : 'Stopped');
  }
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
  function startReadAloud(startIdx, forceSpeech){
    ttsWantPlay = true;   // the reader wants to listen (used to auto-resume after a lock-screen pause)
    // recorded narration if this chapter has an MP3 (falls back to device voice on error)
    var src = activeAudioSrc();
    if(!forceSpeech && src && audioEl){
      ttsMode = 'audio'; ttsClearHL(); ttsIdx = -1;
      ttsItems = ttsCollect();   // same elements the cues line up with, for highlighting
      // start line: explicit arg, else a selected/tapped line (so "Listen" begins where you are)
      var aStart = (typeof startIdx === 'number' && startIdx >= 0) ? startIdx : ttsSelectedIndex();
      ttsSelEl = null;
      if(audioEl.getAttribute('src') !== src){ audioEl.setAttribute('src', src); }
      audioEl.playbackRate = TTS_RATES[ttsRateI];
      ttsState = 'playing'; ttsChapterStart = Date.now(); ttsUI();
      msMeta(); msState('playing');
      loadCues(src, function(){
        if(aStart > 0 && ttsCues && ttsCues[aStart] != null){
          var to = ttsCues[aStart];
          if(audioEl.readyState >= 1){ try{ audioEl.currentTime = to; }catch(e){} }
          else { ttsPendingSeek = to; }
        }
      });
      var pr = audioEl.play(); if(pr && pr.catch){ pr.catch(function(){}); }
      return;
    }
    ttsMode = 'speech';
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
      toast(ttsMode === 'audio' ? '🔊 Playing recorded narration' : (hadSel ? '🔊 Reading from your selected line' : '🔊 Reading aloud — select or tap a line to start there'));
    }
    else if(ttsState === 'playing'){ ttsWantPlay = false; if(ttsMode === 'audio'){ try{ audioEl.pause(); }catch(e){} } else { try{ synth.pause(); }catch(e){} } ttsState = 'paused'; ttsUI(); toast('⏸ Paused'); }
    else { ttsWantPlay = true; if(ttsMode === 'audio'){ var p = audioEl.play(); if(p && p.catch) p.catch(function(){}); } else { try{ synth.resume(); }catch(e){} } ttsState = 'playing'; ttsUI(); }
  }
  // jump narration to a tapped paragraph (used while reading aloud)
  function ttsSeekTo(p){
    var k = ttsItems.indexOf(p);
    if(k < 0) return false;
    if(ttsMode === 'audio'){
      if(ttsCues && ttsCues[k] != null){ try{ audioEl.currentTime = ttsCues[k]; }catch(e){} }
      if(ttsState !== 'playing'){ var pr = audioEl.play(); if(pr && pr.catch) pr.catch(function(){}); ttsState = 'playing'; ttsUI(); }
      ttsAudioSync();
      return true;
    }
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
    var audioMode = ttsMode === 'audio';
    ttsPlay.textContent = playing ? '⏸ Pause' : (ttsState === 'paused' ? '▶ Resume' : '🔊 Listen');
    ttsPlay.setAttribute('aria-label', playing ? 'Pause' : (ttsState === 'paused' ? 'Resume' : 'Listen to this chapter'));
    ttsStop.hidden = !active; ttsRateBtn.hidden = !active;
    ttsBackBtn.hidden = !active; ttsFwdBtn.hidden = !active;
    ttsVoiceSel.hidden = !active || audioMode;
    if(ttsBar) ttsBar.hidden = !active || !audioMode;     // seek bar only where we have a duration
    if(ttsNow){
      ttsNow.hidden = !active;
      if(active){
        var id = (document.querySelector('.chapter.active') || {}).id, n = num(id);
        ttsNow.innerHTML = 'Now playing &middot; <b>' + (n ? esc(n) + ' &middot; ' : '') + esc(TITLES[id] || '') + '</b>';
      }
    }
    ttsRateBtn.textContent = TTS_RATES[ttsRateI] + '×';
    ttsEl.classList.toggle('on', active);
    document.body.classList.toggle('tts-active', active);
    msState(active ? (playing ? 'playing' : 'paused') : 'none');
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
    ttsStop.addEventListener('click', ttsStopAndBookmark);
    if(ttsBackBtn) ttsBackBtn.addEventListener('click', function(){ ttsSkip(-15); });
    if(ttsFwdBtn)  ttsFwdBtn.addEventListener('click', function(){ ttsSkip(15); });
    if(ttsTrack){
      var seeking = false;
      ttsTrack.addEventListener('pointerdown', function(e){ seeking = true; try{ ttsTrack.setPointerCapture(e.pointerId); }catch(_){} ttsSeekFromEvent(e); });
      ttsTrack.addEventListener('pointermove', function(e){ if(seeking) ttsSeekFromEvent(e); });
      ttsTrack.addEventListener('pointerup', function(){ seeking = false; });
      ttsTrack.addEventListener('click', ttsSeekFromEvent);
      ttsTrack.addEventListener('keydown', function(e){ if(e.key === 'ArrowLeft'){ e.preventDefault(); ttsSkip(-5); } else if(e.key === 'ArrowRight'){ e.preventDefault(); ttsSkip(5); } });
    }
    ttsRateBtn.addEventListener('click', function(){ ttsRateI = (ttsRateI + 1) % TTS_RATES.length; try{ localStorage.setItem('fbtb:rate', ttsRateI); }catch(e){} ttsUI(); if(ttsState === 'playing'){ if(ttsMode === 'audio'){ audioEl.playbackRate = TTS_RATES[ttsRateI]; } else { try{ synth.cancel(); }catch(e){} ttsSpeak(ttsIdx); } } });
    ttsVoiceSel.addEventListener('change', function(){ for(var k = 0; k < ttsVoices.length; k++){ if(ttsVoices[k].name === ttsVoiceSel.value){ ttsVoice = ttsVoices[k]; break; } } try{ localStorage.setItem('fbtb:voice', ttsVoiceSel.value); }catch(e){} if(ttsState === 'playing'){ try{ synth.cancel(); }catch(e){} ttsSpeak(ttsIdx); } });
    // remember the last text selection inside the open chapter (survives clicking the Listen button)
    document.addEventListener('selectionchange', function(){
      var sel = window.getSelection();
      if(sel && sel.rangeCount && !sel.isCollapsed && sel.anchorNode){
        var el = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentNode;
        if(el && el.closest && el.closest('.chapter.active')) ttsSelEl = el;
      }
    });
    if(audioEl){
      msSetup();   // lock-screen / OS media controls (also keeps audio alive when the screen locks)
      audioEl.addEventListener('play', function(){ if(ttsState !== 'idle'){ ttsState = 'playing'; ttsUI(); } msState('playing'); });
      // a pause we didn't ask for (e.g. iOS locks the screen): reflect it as paused, keep the place + intent to resume
      audioEl.addEventListener('pause', function(){
        if(ttsWantPlay && ttsState === 'playing' && !audioEl.ended){ ttsState = 'paused'; ttsUI(); toast('⏸ Paused — tap ▶ to continue'); }
        else if(ttsState === 'paused') msState('paused');
      });
      audioEl.addEventListener('loadedmetadata', function(){ if(ttsPendingSeek != null){ try{ audioEl.currentTime = ttsPendingSeek; }catch(e){} ttsPendingSeek = null; } ttsProgress(); });
      audioEl.addEventListener('timeupdate', ttsAudioSync);
      // continuous playback: roll into the next chapter when one finishes
      audioEl.addEventListener('ended', function(){
        ttsClearHL();
        var i = order.indexOf((document.querySelector('.chapter.active') || {}).id);
        if(ttsAutoAdvance && i >= 0 && i < order.length - 1){
          ttsAdvancing = true; show(order[i + 1]); ttsAdvancing = false;
          startReadAloud(0); return;
        }
        ttsWantPlay = false; ttsState = 'idle'; ttsMode = 'speech'; ttsIdx = -1; ttsUI();
      });
      audioEl.addEventListener('error', function(){ if(ttsMode === 'audio'){ ttsMode = 'speech'; toast('Recorded audio unavailable — using device voice'); startReadAloud(undefined, true); } });
      // coming back from a lock/background: resume exactly where we left off (one tap if iOS blocks auto-play)
      function ttsResumeIfWanted(){
        if(document.hidden || !ttsWantPlay || ttsMode !== 'audio' || !audioEl.paused) return;
        var p = audioEl.play();
        if(p && p.then){ p.then(function(){ ttsState = 'playing'; ttsUI(); }).catch(function(){ /* iOS needs a tap — Resume is already showing */ }); }
        else { ttsState = 'playing'; ttsUI(); }
      }
      document.addEventListener('visibilitychange', ttsResumeIfWanted);
      addEventListener('pageshow', ttsResumeIfWanted);
    }
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

// ===== last-page star rating (saved locally; the message link reaches the author) =====
(function(){
  var wrap = document.getElementById('storyStars');
  if(!wrap) return;
  var stars = [].slice.call(wrap.querySelectorAll('.star'));
  var thanks = document.getElementById('fbThanks');
  var KEY = 'fbtb:rating';
  function val(s){ return parseInt(s.getAttribute('data-v'), 10) || 0; }
  function paint(v){ stars.forEach(function(s){ var on = val(s) <= v; s.classList.toggle('on', on); s.setAttribute('aria-checked', val(s) === v ? 'true' : 'false'); }); }
  function rated(){ var v = 0; try{ v = parseInt(localStorage.getItem(KEY), 10) || 0; }catch(e){} return v; }
  function say(v){ if(!thanks) return; thanks.hidden = v <= 0; thanks.textContent = v >= 4 ? 'Thank you — so glad you enjoyed it!' : (v > 0 ? 'Thanks for the honest rating. Tell me more below ↓' : ''); }
  var start = rated(); paint(start); say(start);
  stars.forEach(function(s){
    s.addEventListener('mouseenter', function(){ paint(val(s)); });
    s.addEventListener('focus', function(){ paint(val(s)); });
    s.addEventListener('click', function(){ var v = val(s); try{ localStorage.setItem(KEY, v); }catch(e){} paint(v); say(v); });
  });
  wrap.addEventListener('mouseleave', function(){ paint(rated()); });
})();
