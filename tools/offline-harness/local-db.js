/* local-db.js - offline stand-in for @supabase/supabase-js.
 * Implements only the query-builder surface app.js actually uses.
 * Data lives in localStorage, seeded from seed.js on first run.
 * app.js is UNMODIFIED - it still calls supabase.createClient(url, key).
 */
(function () {
  'use strict';

  var LS_KEY = 'pantry_offline_db_v1';

  // Foreign keys needed to resolve PostgREST embedded selects.
  var REL = {
    meal_plan: {
      recipes: { kind: 'one', fk: 'recipe_id', target: 'recipes' }
    },
    recipe_ingredients: {
      recipes: { kind: 'one', fk: 'recipe_id', target: 'recipes' },
      stock_items: { kind: 'one', fk: 'stock_item_id', target: 'stock_items' }
    },
    recipes: {
      recipe_ingredients: { kind: 'many', fk: 'recipe_id', target: 'recipe_ingredients' }
    }
  };

  var db = null;

  function clone(v) { return JSON.parse(JSON.stringify(v)); }

  function load() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* fall through to seed */ }
    return clone(window.__SEED__ || {});
  }

  function save() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(db)); }
    catch (e) { console.warn('local-db: save failed', e); }
  }

  function ensure() { if (!db) db = load(); return db; }

  function rows(t) { var d = ensure(); if (!d[t]) d[t] = []; return d[t]; }

  function uuid() {
    if (crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  // --- select-string parsing -------------------------------------------
  // Splits on top-level commas only, so "a, rel(x, y), b" parses correctly.
  function splitTop(s) {
    var out = [], depth = 0, cur = '';
    for (var i = 0; i < s.length; i++) {
      var c = s[i];
      if (c === '(') depth++;
      if (c === ')') depth--;
      if (c === ',' && depth === 0) { out.push(cur); cur = ''; }
      else cur += c;
    }
    if (cur.trim()) out.push(cur);
    return out.map(function (x) { return x.trim(); }).filter(Boolean);
  }

  function parseSelect(sel) {
    var cols = [], embeds = [], star = false;
    splitTop(sel || '*').forEach(function (part) {
      var m = part.match(/^(?:([\w]+)\s*:\s*)?([\w]+)\s*\((.*)\)$/s);
      if (m) {
        embeds.push({ alias: m[1] || m[2], table: m[2], sel: m[3] });
      } else if (part === '*') {
        star = true;
      } else {
        cols.push(part.replace(/^[\w]+\s*:\s*/, ''));
      }
    });
    return { star: star, cols: cols, embeds: embeds };
  }

  function project(row, spec) {
    if (spec.star) return clone(row);
    var out = {};
    spec.cols.forEach(function (c) { out[c] = row[c] === undefined ? null : clone(row[c]); });
    return out;
  }

  function embed(table, row, out, spec) {
    spec.embeds.forEach(function (e) {
      var rel = (REL[table] || {})[e.table];
      if (!rel) { out[e.alias] = null; return; }
      var sub = parseSelect(e.sel);
      if (rel.kind === 'one') {
        var hit = rows(rel.target).find(function (r) { return r.id === row[rel.fk]; });
        out[e.alias] = hit ? finish(rel.target, hit, sub) : null;
      } else {
        out[e.alias] = rows(rel.target)
          .filter(function (r) { return r[rel.fk] === row.id; })
          .map(function (r) { return finish(rel.target, r, sub); });
      }
    });
  }

  function finish(table, row, spec) {
    var out = project(row, spec);
    embed(table, row, out, spec);
    return out;
  }

  function applyFilters(list, filters) {
    return list.filter(function (r) {
      return filters.every(function (f) {
        if (f.op === 'eq') return r[f.col] === f.val;
        if (f.op === 'in') return f.val.indexOf(r[f.col]) !== -1;
        return true;
      });
    });
  }

  function sortRows(list, ord) {
    if (!ord) return list;
    var dir = ord.asc === false ? -1 : 1;
    return list.slice().sort(function (a, b) {
      var x = a[ord.col], y = b[ord.col];
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      if (typeof x === 'string') return x.localeCompare(y) * dir;
      return (x < y ? -1 : x > y ? 1 : 0) * dir;
    });
  }

  // --- query builder ----------------------------------------------------
  function Query(table) {
    this.table = table;
    this.action = 'select';
    this.spec = parseSelect('*');
    this.filters = [];
    this.ord = null;
    this.payload = null;
    this.onConflict = null;
    this.wantSingle = false;
    this.headOnly = false;
    this.wantCount = false;
    this.returning = false;
  }

  Query.prototype.select = function (sel, opts) {
    opts = opts || {};
    if (this.action === 'select') {
      this.spec = parseSelect(sel);
    } else {
      this.returning = true;              // e.g. .insert(x).select('id')
      this.spec = parseSelect(sel);
    }
    if (opts.count) this.wantCount = true;
    if (opts.head) this.headOnly = true;
    return this;
  };

  Query.prototype.eq = function (col, val) {
    this.filters.push({ op: 'eq', col: col, val: val }); return this;
  };
  Query.prototype.in = function (col, val) {
    this.filters.push({ op: 'in', col: col, val: val || [] }); return this;
  };
  Query.prototype.order = function (col, opts) {
    this.ord = { col: col, asc: !(opts && opts.ascending === false) }; return this;
  };
  Query.prototype.limit = function (n) { this.lim = n; return this; };
  Query.prototype.single = function () { this.wantSingle = true; return this; };
  Query.prototype.maybeSingle = function () { this.wantSingle = 'maybe'; return this; };

  Query.prototype.insert = function (p) { this.action = 'insert'; this.payload = p; return this; };
  Query.prototype.update = function (p) { this.action = 'update'; this.payload = p; return this; };
  Query.prototype.delete = function () { this.action = 'delete'; return this; };
  Query.prototype.upsert = function (p, o) {
    this.action = 'upsert'; this.payload = p;
    this.onConflict = o && o.onConflict ? o.onConflict.split(',').map(function (s) { return s.trim(); }) : ['id'];
    return this;
  };

  function stamp(rec) {
    var now = new Date().toISOString();
    if (rec.id === undefined) rec.id = uuid();
    if (rec.created_at === undefined) rec.created_at = now;
    if (rec.updated_at === undefined) rec.updated_at = now;
    return rec;
  }

  Query.prototype.run = function () {
    var self = this, tbl = rows(this.table), result = null, count = null;

    if (this.action === 'select') {
      var list = sortRows(applyFilters(tbl, this.filters), this.ord);
      count = list.length;
      if (this.lim) list = list.slice(0, this.lim);
      result = this.headOnly ? null : list.map(function (r) { return finish(self.table, r, self.spec); });

    } else if (this.action === 'insert') {
      var recs = (Array.isArray(this.payload) ? this.payload : [this.payload]).map(function (p) {
        return stamp(clone(p));
      });
      recs.forEach(function (r) { tbl.push(r); });
      save();
      result = recs.map(function (r) { return finish(self.table, r, self.spec); });

    } else if (this.action === 'update') {
      var hits = applyFilters(tbl, this.filters);
      hits.forEach(function (r) { Object.assign(r, clone(self.payload)); });
      save();
      result = hits.map(function (r) { return finish(self.table, r, self.spec); });

    } else if (this.action === 'upsert') {
      var recs2 = Array.isArray(this.payload) ? this.payload : [this.payload];
      result = recs2.map(function (p) {
        var hit = tbl.find(function (r) {
          return self.onConflict.every(function (k) { return r[k] === p[k]; });
        });
        if (hit) { Object.assign(hit, clone(p)); return finish(self.table, hit, self.spec); }
        var rec = stamp(clone(p)); tbl.push(rec);
        return finish(self.table, rec, self.spec);
      });
      save();

    } else if (this.action === 'delete') {
      var doomed = applyFilters(tbl, this.filters);
      db[this.table] = tbl.filter(function (r) { return doomed.indexOf(r) === -1; });
      save();
      result = doomed.map(function (r) { return finish(self.table, r, self.spec); });
    }

    if (this.wantSingle) {
      var one = (result || [])[0];
      if (!one && this.wantSingle !== 'maybe') {
        return { data: null, error: { message: 'No rows found' }, count: count, status: 406 };
      }
      return { data: one || null, error: null, count: count, status: 200 };
    }
    if (this.action !== 'select' && !this.returning) result = null;
    return { data: result, error: null, count: count, status: 200 };
  };

  // Thenable: `await sb.from(...)...` resolves like a PostgREST response.
  Query.prototype.then = function (res, rej) {
    var out;
    try { out = this.run(); }
    catch (e) { out = { data: null, error: { message: e.message }, count: null, status: 500 }; }
    return Promise.resolve(out).then(res, rej);
  };
  Query.prototype.catch = function (f) { return this.then(null, f); };

  // --- public API -------------------------------------------------------
  var client = {
    from: function (table) { return new Query(table); },
    // convenience helpers for the offline build (not part of supabase-js)
    __reset: function () { localStorage.removeItem(LS_KEY); db = null; ensure(); },
    __export: function () { return clone(ensure()); },
    __import: function (obj) { db = clone(obj); save(); }
  };

  window.supabase = { createClient: function () { return client; } };
  window.localDb = client;

  ensure();
  console.log('local-db: offline mode, tables ->',
    Object.keys(db).map(function (k) { return k + ':' + db[k].length; }).join(', '));
})();
