// Observe focus changes inside Dash React-Select dropdowns and announce the focused option.
(function(){
  const LIVE_REGION_ID = 'dropdown-live-region';
  const ANNOUNCE_DELAY = 30; // ms

  function getLive(){ return document.getElementById(LIVE_REGION_ID); }
  function announce(text){
    if(!text) return;
    const live = getLive();
    if(!live) return;
    // Clear first to ensure SR re-reads identical text
    live.textContent = '';
    setTimeout(()=>{ live.textContent = text; }, 5);
  }

  function extractLabelFromOption(optionEl){
    if(!optionEl) return '';
    let label = optionEl.getAttribute('aria-label') || optionEl.textContent || '';
    return (label || '').trim();
  }

  function currentFocusedOption(){
    // Dash (react-select) focused option may have one of these classes
    const sel = document.querySelector('.Select-option.is-focused, .VirtualizedSelectFocusedOption');
    if(sel) return sel;
    // Fallback: role=option with aria-selected=true (some variants)
    const aria = document.querySelector('[role="option"][aria-selected="true"]');
    return aria || null;
  }

  function scheduleAnnounce(){
    setTimeout(()=>{
      const opt = currentFocusedOption();
      const label = extractLabelFromOption(opt);
      if(label) announce(label);
    }, ANNOUNCE_DELAY);
  }

  function onFocusIn(e){
    const el = e.target;
    if(!el) return;
    if(el.getAttribute && el.getAttribute('role') === 'option'){
      announce(extractLabelFromOption(el));
    }
  }

  function onKeyDown(e){
    if(e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'PageDown' || e.key === 'PageUp' || e.key === 'Home' || e.key === 'End'){
      // Only if a dropdown menu is open
      const menuOpen = document.querySelector('.Select-menu-outer, .Select-menu') || document.querySelector('[class*="menu"] [role="listbox"]');
      if(menuOpen){
        scheduleAnnounce();
      }
    }
  }

  // Observe mutations to catch aria-activedescendant changes (extra safety)
  const observer = new MutationObserver((muts)=>{
    for(const m of muts){
      if(m.type === 'attributes' && m.attributeName === 'aria-activedescendant'){
        scheduleAnnounce();
      }
    }
  });
  // Attach observer lazily when dropdown gains focus
  document.addEventListener('focusin', (e)=>{
    const container = e.target.closest && e.target.closest('.Select, [role="combobox"]');
    if(container && container.getAttribute && !container._a11yObserved){
      observer.observe(container, { attributes: true, subtree: true, attributeFilter: ['aria-activedescendant'] });
      container._a11yObserved = true;
    }
    onFocusIn(e);
  }, true);

  document.addEventListener('keydown', onKeyDown, true);
})();
