// Online mode: Supabase login, admin approval, shared data with live updates.
// Exposes window.Cloud. If config.js has no Supabase URL, Cloud.enabled is false
// and the app keeps working as before (Claude artifact or browser-only).
(function () {
  'use strict';
  var C = window.APP_CONFIG || {};
  var enabled = !!(C.supabaseUrl && C.supabaseKey && window.supabase && window.supabase.createClient);
  var sb = null, me = null, profile = null, pendingTimer = null, emailForCode = '';

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function here() { return location.origin + location.pathname; }
  function msg(text, bad) { var m = $('gmsg'); m.textContent = text || ''; m.className = bad ? 'bad' : 'mute'; }
  function errText(e) { return (e && (e.message || e.error_description)) || String(e || ''); }

  // ---------------------------------------------------------------- screens
  function showPane(name) {
    $('gate').hidden = false;
    $('app').hidden = true;
    ['gLogin', 'gCode', 'gPending', 'gLoading'].forEach(function (id) { $(id).hidden = id !== name; });
  }
  function showApp() {
    $('gate').hidden = true;
    $('app').hidden = false;
    document.documentElement.classList.add('ready');
  }

  function showLogin() {
    stopPending();
    $('gGoogle').hidden = C.loginWithGoogle === false;
    $('gEmailBox').hidden = C.loginWithEmail === false;
    $('gOr').hidden = C.loginWithGoogle === false || C.loginWithEmail === false;
    showPane('gLogin');
  }

  function showPending() {
    $('gPendEmail').textContent = (me && me.email) || '';
    showPane('gPending');
    stopPending();
    pendingTimer = setInterval(recheck, 20000);
  }
  function stopPending() { if (pendingTimer) { clearInterval(pendingTimer); pendingTimer = null; } }

  // ---------------------------------------------------------------- auth
  function wireLogin() {
    $('gGoogle').onclick = function () {
      msg('מעבירים להתחברות עם Google…');
      sb.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: here() } })
        .then(function (r) { if (r.error) msg('ההתחברות נכשלה: ' + errText(r.error), 1); });
    };
    $('gSend').onclick = function () {
      var email = $('gEmail').value.trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { msg('כתובת המייל לא תקינה.', 1); $('gEmail').focus(); return; }
      $('gSend').disabled = true; msg('שולחים קוד…');
      sb.auth.signInWithOtp({ email: email, options: { emailRedirectTo: here(), shouldCreateUser: true } })
        .then(function (r) {
          $('gSend').disabled = false;
          if (r.error) { msg('שליחת הקוד נכשלה: ' + errText(r.error), 1); return; }
          emailForCode = email;
          $('gCodeEmail').textContent = email;
          $('gCodeIn').value = '';
          msg('');
          showPane('gCode');
          $('gCodeIn').focus();
        });
    };
    $('gEmail').onkeydown = function (e) { if (e.key === 'Enter') $('gSend').click(); };
    $('gVerify').onclick = function () {
      var code = $('gCodeIn').value.replace(/\s/g, '');
      if (!/^\d{6,10}$/.test(code)) { msg('הקוד צריך להיות מספרים בלבד, כמו שהופיע במייל.', 1); return; }
      $('gVerify').disabled = true; msg('בודקים…');
      sb.auth.verifyOtp({ email: emailForCode, token: code, type: 'email' }).then(function (r) {
        $('gVerify').disabled = false;
        if (r.error) { msg('הקוד שגוי או שפג תוקפו. אפשר לבקש קוד חדש.', 1); return; }
        msg('');
      });
    };
    $('gCodeIn').onkeydown = function (e) { if (e.key === 'Enter') $('gVerify').click(); };
    $('gBack').onclick = function () { msg(''); showLogin(); };
    $('gRecheck').onclick = recheck;
    $('gOut').onclick = signOut;
    $('uOut').onclick = signOut;
  }

  function signOut() {
    stopPending();
    sb.auth.signOut().finally(function () { location.replace(here()); });
  }

  function loadProfile() {
    return sb.from('profiles').select('id,email,full_name,approved,is_admin').eq('id', me.id).maybeSingle()
      .then(function (r) { if (r.error) throw r.error; return r.data; });
  }

  var resolveStart = null, started = false;
  function check(session) {
    if (!session) { me = null; showLogin(); return; }
    me = session.user;
    loadProfile().then(function (p) {
      profile = p;
      if (!p || !p.approved) { showPending(); return; }
      stopPending();
      if (started) return;
      started = true;
      showPane('gLoading');
      makeDb().then(function (db) {
        setupUserBar();
        showApp();
        resolveStart(db);
      }, function (e) { showPane('gLogin'); msg('לא ניתן לטעון את הנתונים: ' + errText(e), 1); });
    }, function (e) { showPane('gLogin'); msg('שגיאה בבדיקת ההרשאה: ' + errText(e), 1); });
  }
  function recheck() { sb.auth.getSession().then(function (r) { check(r.data && r.data.session); }); }

  // ---------------------------------------------------------------- data adapter
  // Same shape as the Claude artifact database the app already uses:
  //   db.collection(c).get() / .onSnapshot(fn) / .doc(id).set(obj) / .doc(id).delete()
  //   db.doc('settings/main').set(obj) / .onSnapshot(fn)
  function makeDb() {
    var cache = {}, subs = {}, loaded = false;
    var chk = function (r) { if (r.error) throw r.error; return r; };

    function snap(c) {
      var m = cache[c] || {};
      var docs = Object.keys(m).map(function (id) { return { id: id, data: function () { return m[id]; } }; });
      return { empty: !docs.length, docs: docs };
    }
    function emit(c) { (subs[c] || []).forEach(function (f) { try { f(snap(c)); } catch (e) { console.error(e); } }); }

    function fetchAll() {
      var all = [], step = 1000;
      function page(from) {
        return sb.from('records').select('collection,id,data').order('collection').order('id')
          .range(from, from + step - 1).then(chk).then(function (r) {
            all = all.concat(r.data);
            return r.data.length < step ? all : page(from + step);
          });
      }
      return page(0).then(function (rows) {
        var nc = {};
        rows.forEach(function (row) { (nc[row.collection] = nc[row.collection] || {})[row.id] = row.data; });
        cache = nc; loaded = true;
        Object.keys(subs).forEach(emit);
      });
    }

    function upsert(c, id, data) {
      (cache[c] = cache[c] || {})[id] = data;   // optimistic, so other updates don't undo it on screen
      return sb.from('records').upsert({ collection: c, id: id, data: data }).then(chk);
    }
    function remove(c, id) {
      if (cache[c]) delete cache[c][id];
      return sb.from('records').delete().match({ collection: c, id: id }).then(chk);
    }

    function onChange(p) {
      if (p.eventType === 'DELETE') {
        var o = p.old || {};
        if (cache[o.collection]) delete cache[o.collection][o.id];
        emit(o.collection);
      } else {
        var n = p.new || {};
        (cache[n.collection] = cache[n.collection] || {})[n.id] = n.data;
        emit(n.collection);
      }
    }

    var reload = function () { fetchAll().catch(function (e) { console.error('reload failed', e); }); };
    sb.channel('records-live')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'records' }, onChange)
      .subscribe(function (status) { if (status === 'SUBSCRIBED' && loaded) reload(); });
    // Phones pause pages in the background; catch up when the page is visible again.
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') reload(); });

    function listen(c, f) { (subs[c] = subs[c] || []).push(f); if (loaded) f(snap(c)); }

    var db = {
      collection: function (c) {
        return {
          get: function () { return Promise.resolve(snap(c)); },
          onSnapshot: function (f) { listen(c, f); return function () {}; },
          doc: function (id) {
            return { set: function (d) { return upsert(c, id, d); }, delete: function () { return remove(c, id); } };
          }
        };
      },
      doc: function (path) {
        var parts = path.split('/'), c = parts[0], id = parts[1];
        return {
          set: function (d) { return upsert(c, id, d); },
          onSnapshot: function (f) {
            listen(c, function () { var m = cache[c] || {}; f({ exists: id in m, data: function () { return m[id]; } }); });
            return function () {};
          }
        };
      }
    };
    return fetchAll().then(function () { return db; });
  }

  // ---------------------------------------------------------------- user bar & admin
  function setupUserBar() {
    $('ubar').hidden = false;
    $('uName').textContent = profile.full_name ? profile.full_name + ' (' + (profile.email || '') + ')' : (profile.email || '');
    if (!profile.is_admin) {
      if ($('reset')) $('reset').hidden = true;
      return;
    }
    $('uAdmin').hidden = false;
    $('uAdmin').onclick = function () {
      var s = $('users'); s.hidden = !s.hidden;
      if (!s.hidden) { loadUsers(); s.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    };
    $('usRefresh').onclick = loadUsers;
    $('usList').addEventListener('click', function (e) {
      var act = e.target.getAttribute('data-u'), id = e.target.getAttribute('data-id');
      if (!act || !id) return;
      var change = { approve: { approved: true }, revoke: { approved: false }, mkadmin: { is_admin: true }, rmadmin: { is_admin: false } }[act];
      if (act === 'del') {
        if (!confirm('להסיר את המשתמש/ת מהרשימה? אם ינסו להתחבר שוב, יופיעו כממתינים לאישור.')) return;
        sb.from('profiles').delete().eq('id', id).then(function (r) { if (r.error) alert(errText(r.error)); loadUsers(); });
        return;
      }
      if (act === 'revoke' && !confirm('לבטל את הגישה של המשתמש/ת?')) return;
      sb.from('profiles').update(change).eq('id', id).then(function (r) { if (r.error) alert(errText(r.error)); loadUsers(); });
    });
    loadUsers();
  }

  function loadUsers() {
    sb.from('profiles').select('id,email,full_name,approved,is_admin,created_at').order('created_at').then(function (r) {
      if (r.error) { $('usList').innerHTML = '<p class="bad">' + esc(errText(r.error)) + '</p>'; return; }
      var pend = r.data.filter(function (u) { return !u.approved; }).length;
      $('uAdmin').textContent = 'ניהול משתמשים' + (pend ? ' (' + pend + ' ממתינים)' : '');
      $('usList').innerHTML = '<div class="wide"><table><tr><th>שם</th><th>מייל</th><th>נרשם/ה</th><th>מצב</th><th></th></tr>' +
        r.data.map(function (u) {
          var self = u.id === me.id, b = '';
          if (!self) {
            b += u.approved
              ? '<button class="g" data-u="revoke" data-id="' + u.id + '">ביטול גישה</button> '
              : '<button data-u="approve" data-id="' + u.id + '">אישור</button> ';
            if (u.approved) b += u.is_admin
              ? '<button class="g" data-u="rmadmin" data-id="' + u.id + '">הסרת ניהול</button> '
              : '<button class="g" data-u="mkadmin" data-id="' + u.id + '">הפיכה למנהל/ת</button> ';
            b += '<button class="g" data-u="del" data-id="' + u.id + '">הסרה</button>';
          }
          var st = !u.approved ? '<b class="bad">ממתין/ה לאישור</b>' : u.is_admin ? '<span class="good">מנהל/ת</span>' : 'מאושר/ת';
          return '<tr><td>' + esc(u.full_name || '') + (self ? ' <span class="tag">את/ה</span>' : '') + '</td><td>' + esc(u.email || '') +
            '</td><td>' + esc((u.created_at || '').slice(0, 10)) + '</td><td>' + st + '</td><td>' + b + '</td></tr>';
        }).join('') + '</table></div>';
    });
  }

  // ---------------------------------------------------------------- start
  function start() {
    return new Promise(function (resolve) {
      resolveStart = resolve;
      sb = window.supabase.createClient(C.supabaseUrl, C.supabaseKey, {
        auth: { flowType: 'pkce', persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
      });
      wireLogin();
      showPane('gLoading');
      var q = new URLSearchParams(location.search + '&' + location.hash.slice(1));
      var urlErr = q.get('error_description');
      sb.auth.onAuthStateChange(function (event, session) {
        // Don't call Supabase inside this callback directly (it can lock); defer it.
        if (event === 'INITIAL_SESSION' || event === 'SIGNED_IN') setTimeout(function () {
          if (location.search.indexOf('code=') >= 0 || location.hash.indexOf('access_token') >= 0) history.replaceState(null, '', here());
          check(session);
          if (urlErr && !session) msg('ההתחברות נכשלה: ' + urlErr, 1);
        }, 0);
        if (event === 'SIGNED_OUT') setTimeout(function () { location.replace(here()); }, 0);
      });
    });
  }

  window.Cloud = {
    enabled: enabled,
    start: start,
    isAdmin: function () { return !!(profile && profile.is_admin); }
  };
})();
