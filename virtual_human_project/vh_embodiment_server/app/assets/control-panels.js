export function setupControlPanels() {
  const $ = selector => document.querySelector(selector);
  function tabs(selector, prefix, initial, onChange = () => {}) {
    const buttons = [...document.querySelectorAll(selector)];
    function select(button, focus = false) {
      for (const item of buttons) {
        const active = item === button;
        item.setAttribute('aria-selected', String(active)); item.tabIndex = active ? 0 : -1;
        document.getElementById(item.getAttribute('aria-controls')).hidden = !active;
      }
      onChange(button.dataset[prefix]);
      if (focus) button.focus();
    }
    buttons.forEach((button, index) => {
      button.addEventListener('click', () => select(button));
      button.addEventListener('keydown', event => {
        let next;
        if (['ArrowDown','ArrowRight'].includes(event.key)) next = (index + 1) % buttons.length;
        if (['ArrowUp','ArrowLeft'].includes(event.key)) next = (index + buttons.length - 1) % buttons.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = buttons.length - 1;
        if (next !== undefined) { event.preventDefault(); select(buttons[next], true); }
      });
    });
    select(buttons.find(button => button.dataset[prefix] === initial));
  }
  tabs('[data-settings-tab]', 'settingsTab', 'character', name => {
    if (name === 'microphone') $('#settings').dispatchEvent(new Event('enter-microphone'));
    if (name !== 'microphone') $('#settings').dispatchEvent(new Event('leave-microphone'));
  });
  const closePlayground = () => {
    $('#playground').hidden = true; document.body.classList.remove('api-mode');
    $('#openPlayground').setAttribute('aria-expanded','false');
    $('#openPlayground').focus();
  };
  const openPlayground = () => {
    $('#settings').close();
    $('#playground').hidden = false; document.body.classList.add('api-mode');
    $('#openPlayground').setAttribute('aria-expanded','true');
    $('#closePlayground').focus();
  };
  $('#openPlayground').addEventListener('click', () => $('#playground').hidden ? openPlayground() : closePlayground());
  $('#settingsToPlayground').addEventListener('click', openPlayground);
  $('#closePlayground').addEventListener('click', closePlayground);
  $('#playground').addEventListener('keydown', event => { if (event.key === 'Escape') { event.preventDefault();closePlayground(); } });
  $('#openSettings').addEventListener('click', () => { if (!$('#playground').hidden) closePlayground(); $('#settings').showModal(); });
  $('#closeSettings').addEventListener('click', () => $('#settings').close());
  $('#settings').addEventListener('click', event => {
    const rect = $('#settings').getBoundingClientRect();
    if (event.target === $('#settings') && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) $('#settings').close();
  });
}
