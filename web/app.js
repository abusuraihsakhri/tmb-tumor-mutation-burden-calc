(function (root) {
  "use strict";
  function calc(mutations, regionMb, synonymous) {
    if (!Number.isSafeInteger(mutations) || mutations < 0) throw new Error("Mutation count must be a non-negative integer.");
    if (!Number.isFinite(regionMb) || regionMb <= 0) throw new Error("Callable territory must be finite and greater than zero.");
    if (!Number.isSafeInteger(synonymous) || synonymous < 0 || synonymous > mutations) throw new Error("Synonymous count must be between 0 and total mutations.");
    var raw = mutations / regionMb;
    if (!Number.isFinite(raw)) throw new Error("Calculated TMB is not finite.");
    var category = raw < 5 ? "Low" : raw < 10 ? "Intermediate" : raw < 16 ? "High" : "Very high";
    return {tmb: Math.round((raw + Number.EPSILON) * 100) / 100, raw: raw,
      category: category, cutoff: raw >= 10, nonSynonymous: mutations - synonymous};
  }
  function parseCsv(text) {
    var rows = [], row = [], cell = "", quoted = false, afterQuote = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (quoted) {
        if (ch === '"') {
          if (text[i + 1] === '"') {cell += '"'; i++;} else {quoted = false; afterQuote = true;}
        } else {cell += ch;}
      } else if (afterQuote) {
        if (ch === ',') {row.push(cell); cell = ""; afterQuote = false;}
        else if (ch === '\n' || ch === '\r') {
          row.push(cell); rows.push(row); row = []; cell = ""; afterQuote = false;
          if (ch === '\r' && text[i + 1] === '\n') i++;
        } else if (ch !== ' ' && ch !== '\t') throw new Error("Malformed CSV after closing quote.");
      } else if (ch === '"' && cell === "") {quoted = true;}
      else if (ch === '"') {throw new Error("Malformed CSV quote.");}
      else if (ch === ',') {row.push(cell); cell = "";}
      else if (ch === '\n' || ch === '\r') {
        row.push(cell); rows.push(row); row = []; cell = "";
        if (ch === '\r' && text[i + 1] === '\n') i++;
      } else {cell += ch;}
    }
    if (quoted) throw new Error("Unterminated CSV quoted field.");
    if (afterQuote || cell !== "" || row.length) {row.push(cell); rows.push(row);}
    return rows.filter(function (r) {return !(r.length === 1 && r[0] === "");});
  }
  function integer(value, label) {
    if (!/^\d+$/.test(String(value).trim())) throw new Error(label + " must be a non-negative integer.");
    var n = Number(value);
    if (!Number.isSafeInteger(n)) throw new Error(label + " is outside the supported integer range.");
    return n;
  }
  function positive(value, label) {
    if (String(value).trim() === "") throw new Error(label + " is required.");
    var n = Number(value);
    if (!Number.isFinite(n) || n <= 0) throw new Error(label + " must be a finite positive number.");
    return n;
  }
  function escapeCell(value, untrusted) {
    var s = String(value == null ? "" : value);
    if (untrusted && /^\s*[=+\-@]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  }
  function processCsv(text) {
    var rows = parseCsv(text.replace(/^\uFEFF/, ""));
    if (!rows.length) throw new Error("CSV is empty.");
    var headers = rows[0].map(function (s) {return s.trim();});
    if (new Set(headers).size !== headers.length) throw new Error("Duplicate CSV headers.");
    var mIdx = headers.indexOf("total_mutations"), rIdx = headers.indexOf("coding_region_size_mb"),
      sIdx = headers.indexOf("synonymous_count");
    if (mIdx < 0 || rIdx < 0) throw new Error("Required CSV columns are missing.");
    if (rows.length > 10001) throw new Error("Maximum 10,000 records per file.");
    var extra = ["tmb", "tmb_category", "meets_numeric_fda_tmb_cutoff"];
    var keep = extra.filter(function (key) {return !headers.includes(key);});
    var output = [headers.concat(keep).map(function (c) {return escapeCell(c, false);}).join(",")];
    for (var i = 1; i < rows.length; i++) {
      if (rows[i].length !== headers.length) throw new Error("CSV row " + (i + 1) + " has the wrong number of columns.");
      try {
        var result = calc(integer(rows[i][mIdx], "Mutations"), positive(rows[i][rIdx], "Callable Mb"),
          sIdx < 0 || rows[i][sIdx].trim() === "" ? 0 : integer(rows[i][sIdx], "Synonymous count"));
        var values = rows[i].slice();
        var computed = {tmb:result.tmb, tmb_category:result.category, meets_numeric_fda_tmb_cutoff:result.cutoff};
        headers.forEach(function (key, idx) {if (Object.prototype.hasOwnProperty.call(computed, key)) values[idx] = String(computed[key]);});
        keep.forEach(function (key) {values.push(String(computed[key]));});
        output.push(values.map(function (v, idx) {return escapeCell(v, idx < headers.length && !Object.prototype.hasOwnProperty.call(computed, headers[idx]));}).join(","));
      } catch (e) {throw new Error("CSV row " + (i + 1) + ": " + e.message);}
    }
    return {count: rows.length - 1, csv: output.join("\r\n") + "\r\n"};
  }
  if (typeof module !== "undefined" && module.exports) module.exports = {calc:calc, parseCsv:parseCsv, processCsv:processCsv};
  if (typeof document === "undefined") return;
  var form = document.getElementById("calc-form");
  var download = document.getElementById("download");
  var lastCsv = "";
  function show() {
    var err = document.getElementById("error");
    err.textContent = "";
    try {
      var result = calc(integer(document.getElementById("mutations").value, "Mutations"),
        positive(document.getElementById("region").value, "Callable Mb"),
        integer(document.getElementById("synonymous").value, "Synonymous count"));
      document.getElementById("tmb-value").textContent = result.tmb.toFixed(2);
      document.getElementById("category").textContent = result.category + " (illustrative category)";
      document.getElementById("cutoff").textContent = result.cutoff ? "Meets numeric cutoff" : "Below numeric cutoff";
      document.getElementById("nonsyn").textContent = String(result.nonSynonymous);
    } catch (e) {
      err.textContent = e.message;
      document.getElementById("tmb-value").textContent = "—";
      document.getElementById("category").textContent = "Invalid input";
      document.getElementById("cutoff").textContent = "—";
      document.getElementById("nonsyn").textContent = "—";
    }
  }
  form.addEventListener("submit", function (e) {e.preventDefault(); show();});
  show();
  document.getElementById("csv-input").addEventListener("change", async function (e) {
    download.disabled = true; lastCsv = "";
    var file = e.target.files[0], status = document.getElementById("batch-status");
    if (!file) {status.textContent = "No file selected."; return;}
    try {
      if (file.size > 2 * 1024 * 1024) throw new Error("File exceeds the 2 MB limit.");
      var result = processCsv(await file.text());
      lastCsv = result.csv;
      status.textContent = "Processed " + result.count + " record(s) locally. Results ready.";
      download.disabled = false;
    } catch (err) {status.textContent = "Unable to process file: " + err.message;}
  });
  download.addEventListener("click", function () {
    if (!lastCsv) return;
    var url = URL.createObjectURL(new Blob([lastCsv], {type:"text/csv;charset=utf-8"}));
    var a = document.createElement("a");
    a.href = url; a.download = "tmb_results.csv";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () {URL.revokeObjectURL(url);}, 1000);
  });
})(typeof globalThis !== "undefined" ? globalThis : this);
