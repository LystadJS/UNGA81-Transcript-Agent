/* Browser-only preferences; no transcript data or credentials in localStorage. */
(function () {
  'use strict';
  const key = 'un-readout-topics-v1';
  const install = function () {
    if (!window.Shiny) return;
    Shiny.addCustomMessageHandler('setBusy', function (message) {
      const busy = !!message.busy;
      const generate = document.getElementById('generate');
      if (generate) { generate.disabled = busy; generate.textContent = busy ? 'Preparing readout…' : 'Generate readout'; }
      const cancel = document.getElementById('cancel');
      if (cancel) cancel.style.display = busy ? 'block' : 'none';
    });
    Shiny.addCustomMessageHandler('savePreferences', function (data) {
      try {
        localStorage.setItem(key, JSON.stringify(data));
        Shiny.setInputValue('preference_status', {ok:true, message:'Topics saved in this browser.'}, {priority:'event'});
      } catch (_) {
        Shiny.setInputValue('preference_status', {ok:false, message:'Browser storage is unavailable. Your current topics are unchanged.'}, {priority:'event'});
      }
    });
    Shiny.addCustomMessageHandler('restorePreferences', function () {
      try {
        const text = localStorage.getItem(key);
        if (!text || text.length > 100000) throw new Error('No valid saved topics');
        Shiny.setInputValue('saved_preferences', JSON.parse(text), {priority:'event'});
      } catch (_) {
        Shiny.setInputValue('preference_status', {ok:false, message:'No valid saved topic set was found in this browser.'}, {priority:'event'});
      }
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install);
  else install();
}());
