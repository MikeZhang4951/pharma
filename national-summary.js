// Optional national normalization summary extension.
let normalizationLevels = [80, 90, 100, 110];
let selectedNationalMetrics = [
  'basePerPerson', 'headcount', 'budget', 'totalPayout', 'overUnder',
  'utilization', 'averagePayout', 'maxMinPayout', 'attainmentRange',
  'payoutRange', 'engagement', 'meaningful'
];
let hypotheticalTrxAttainment = 100;
let hypotheticalNrxAttainment = 100;

const NATIONAL_METRICS = {
  basePerPerson: {label:'Base / person', format:formatMoney},
  headcount: {label:'Headcount', format:value => value.toLocaleString()},
  budget: {label:'Base budget', format:formatMoney},
  totalPayout: {label:'Total payout', format:formatMoney},
  overUnder: {label:'Over / Under', format:value => `${value >= 0 ? '+' : ''}${formatMoney(value)}`, tone:value => value > 0 ? 'bad' : 'good'},
  utilization: {label:'Utilization', format:value => value.toFixed(1) + '%'},
  averagePayout: {label:'Avg payout', format:formatMoney},
  maxMinPayout: {label:'Max / Min', format:value => `${formatMoney(value.max)} / ${formatMoney(value.min)}`},
  attainmentRange: {label:'Attain range', format:value => `${value.min.toFixed(1)}% – ${value.max.toFixed(1)}%`},
  payoutRange: {label:'Payout% range', format:value => `${value.min.toFixed(1)}% – ${value.max.toFixed(1)}%`},
  engagement: {label:'Engagement (>0%)', format:value => `${value.count}/${value.total} (${value.percent.toFixed(1)}%)`},
  meaningful: {label:'Meaningful (>75%)', format:value => value.toFixed(1) + '%'}
};

function mountNationalSummary() {
  let root = document.getElementById('nationalSummaryRoot');
  const legacySection = document.querySelector('.national-section');

  // Conflict resolutions may keep the old hard-coded section instead of the
  // extension mount point. Convert that legacy markup into the mount point so
  // either merge choice initializes the current summary without duplicate IDs.
  if (!root && legacySection) {
    root = document.createElement('div');
    root.id = 'nationalSummaryRoot';
    legacySection.replaceWith(root);
  }
  if (!root) return false;
  if (legacySection && legacySection.parentNode && !root.contains(legacySection)) legacySection.remove();

  root.innerHTML = `
    <section class="panel national-section" aria-labelledby="nationalSummaryHeading">
      <div class="panel-header"><div><h2 id="nationalSummaryHeading">Normalized national pay summaries</h2><p>Compare national payout outcomes across configurable TRx and NRx attainment scenarios.</p></div></div>
      <div class="normalization-controls">
        <p class="normalization-copy"><strong>How normalization works:</strong> national attainment is total actual volume ÷ total goal volume. Territory attainment is normalized directly to each hypothetical national attainment before the payout curve is applied. No scale-factor metric is shown.</p>
        <div class="level-editor">
          <div class="field"><label for="normalizationLevel">Add column</label><div class="input-shell"><input type="number" id="normalizationLevel" value="120" min="0" max="300" step="1" onkeydown="if(event.key==='Enter') addNormalizationLevel()"><span class="suffix">%</span></div></div>
          <button class="btn" type="button" onclick="addNormalizationLevel()">+ Add column</button>
        </div>
      </div>
      <div class="level-chips" id="normalizationChips"></div>
      <div class="summary-config">
        <div class="config-group">
          <span class="config-group-label">Plan summary metrics</span>
          <div class="config-row"><select id="metricSelect" aria-label="Metric to add"></select><button class="btn" type="button" onclick="addNationalMetric()">+ Add metric</button></div>
          <div class="metric-chips" id="metricChips"></div>
        </div>
        <div class="config-group hypothetical-controls">
          <span class="config-group-label">Hypothetical combined national attainment</span>
          <p class="config-help">Type any TRx and NRx attainment values to update the combined national pay summary.</p>
          <div class="config-row">
            <div class="field"><label for="hypotheticalTrxAttainment">TRx attainment</label><div class="input-shell"><input id="hypotheticalTrxAttainment" type="number" min="0" max="300" step="0.1" value="100" oninput="updateHypotheticalAttainment('trx', this.value)"><span class="suffix">%</span></div></div>
            <div class="field"><label for="hypotheticalNrxAttainment">NRx attainment</label><div class="input-shell"><input id="hypotheticalNrxAttainment" type="number" min="0" max="300" step="0.1" value="100" oninput="updateHypotheticalAttainment('nrx', this.value)"><span class="suffix">%</span></div></div>
          </div>
        </div>
      </div>
      <div class="national-grid">
        <article class="national-card"><div class="national-card-header"><h3>TRx national pay summary</h3><p id="trxNationalContext"></p></div><div class="national-table-wrap" id="trxNationalSummary"></div></article>
        <article class="national-card"><div class="national-card-header"><h3>NRx national pay summary</h3><p id="nrxNationalContext"></p></div><div class="national-table-wrap" id="nrxNationalSummary"></div></article>
        <article class="national-card combined-card"><div class="national-card-header"><h3>Hypothetical combined national pay summary</h3><p id="combinedNationalContext"></p></div><div class="national-table-wrap" id="combinedNationalSummary"></div></article>
      </div>
    </section>`;
  return true;
}

function formatMoney(value) {
  const sign = value < 0 ? '-' : '';
  return sign + '$' + Math.abs(Math.round(value)).toLocaleString();
}

function addNormalizationLevel() {
  const input = document.getElementById('normalizationLevel');
  const level = Number(input.value);
  if (!Number.isFinite(level) || level < 0 || level > MAX_X) return;
  const rounded = Math.round(level * 10) / 10;
  if (!normalizationLevels.includes(rounded)) normalizationLevels.push(rounded);
  normalizationLevels.sort((a, b) => a - b);
  input.value = '';
  renderAll();
}

function removeNormalizationLevel(level) {
  normalizationLevels = normalizationLevels.filter(value => value !== level);
  renderAll();
}

function addNationalMetric() {
  const select = document.getElementById('metricSelect');
  if (select.value && !selectedNationalMetrics.includes(select.value)) selectedNationalMetrics.push(select.value);
  renderAll();
}

function removeNationalMetric(metric) {
  selectedNationalMetrics = selectedNationalMetrics.filter(value => value !== metric);
  renderAll();
}

function updateHypotheticalAttainment(component, value) {
  if (value === '') return;
  const attainment = Number(value);
  if (!Number.isFinite(attainment)) return;
  const bounded = Math.min(MAX_X, Math.max(0, attainment));
  if (component === 'trx') hypotheticalTrxAttainment = bounded;
  else hypotheticalNrxAttainment = bounded;
  renderAll();
}

function getNationalMetrics(qData, component, targetLevel, basePay, weight) {
  const goalKey = component + 'Goal';
  const actualKey = component + 'Actual';
  const totalGoal = qData.reduce((sum, row) => sum + (Number(row[goalKey]) || 0), 0);
  const totalActual = qData.reduce((sum, row) => sum + (Number(row[actualKey]) || 0), 0);
  const currentAttainment = totalGoal ? totalActual / totalGoal * 100 : 0;
  const curve = component === 'trx' ? trxPct : nrxPct;
  const normalizedAttainments = qData.map(row => {
    const territoryAttainment = Number(row[goalKey]) ? Number(row[actualKey]) / Number(row[goalKey]) * 100 : 0;
    return currentAttainment ? territoryAttainment / currentAttainment * targetLevel : 0;
  });
  const payoutPcts = normalizedAttainments.map(curve);
  const payouts = payoutPcts.map(payoutPct => basePay * weight * payoutPct / 100);
  const totalPayout = payouts.reduce((sum, payout) => sum + payout, 0);
  const budget = basePay * weight * qData.length;
  const engaged = payoutPcts.filter(value => value > 0).length;
  return {
    targetLevel, currentAttainment, totalGoal, totalActual,
    basePerPerson:basePay * weight, headcount:qData.length, budget, totalPayout,
    overUnder:totalPayout - budget, utilization:budget ? totalPayout / budget * 100 : 0,
    averagePayout:qData.length ? totalPayout / qData.length : 0,
    maxMinPayout:rangeOf(payouts), attainmentRange:rangeOf(normalizedAttainments), payoutRange:rangeOf(payoutPcts),
    engagement:{count:engaged, total:qData.length, percent:qData.length ? engaged / qData.length * 100 : 0},
    meaningful:qData.length ? payoutPcts.filter(value => value > 75).length / qData.length * 100 : 0,
    payouts, payoutPcts, normalizedAttainments
  };
}

function rangeOf(values) {
  return {max:values.length ? Math.max(...values) : 0, min:values.length ? Math.min(...values) : 0};
}

function combineNationalMetrics(trxMetrics, nrxMetrics, basePay, trxWeight, nrxWeight) {
  const payouts = trxMetrics.payouts.map((payout, index) => payout + nrxMetrics.payouts[index]);
  const payoutPcts = trxMetrics.payoutPcts.map((pct, index) => pct * trxWeight + nrxMetrics.payoutPcts[index] * nrxWeight);
  const normalizedAttainments = trxMetrics.normalizedAttainments.map((attainment, index) => attainment * trxWeight + nrxMetrics.normalizedAttainments[index] * nrxWeight);
  const budget = basePay * payouts.length;
  const totalPayout = payouts.reduce((sum, payout) => sum + payout, 0);
  const engaged = payoutPcts.filter(value => value > 0).length;
  return {
    basePerPerson:basePay, headcount:payouts.length, budget, totalPayout,
    overUnder:totalPayout - budget, utilization:budget ? totalPayout / budget * 100 : 0,
    averagePayout:payouts.length ? totalPayout / payouts.length : 0,
    maxMinPayout:rangeOf(payouts), attainmentRange:rangeOf(normalizedAttainments), payoutRange:rangeOf(payoutPcts),
    engagement:{count:engaged, total:payouts.length, percent:payouts.length ? engaged / payouts.length * 100 : 0},
    meaningful:payouts.length ? payoutPcts.filter(value => value > 75).length / payouts.length * 100 : 0
  };
}

function metricCell(metricKey, metrics) {
  const definition = NATIONAL_METRICS[metricKey];
  const value = metrics[metricKey];
  const tone = definition.tone ? definition.tone(value) : '';
  return `<td class="${tone}">${definition.format(value)}</td>`;
}

function renderComponentNationalTable(metrics) {
  if (!metrics.length) return '<div class="empty-levels">Add an attainment column to model payout.</div>';
  if (!selectedNationalMetrics.length) return '<div class="empty-levels">Add a plan summary metric to display results.</div>';
  return `<table class="national-table"><thead><tr><th>Plan summary metric</th>${metrics.map(metric => `<th>${metric.targetLevel.toFixed(1)}%</th>`).join('')}</tr></thead><tbody>${selectedNationalMetrics.map(metricKey => `<tr><td class="metric-label">${NATIONAL_METRICS[metricKey].label}</td>${metrics.map(metric => metricCell(metricKey, metric)).join('')}</tr>`).join('')}</tbody></table>`;
}

function renderMetricControls() {
  document.getElementById('metricChips').innerHTML = selectedNationalMetrics.map(metric => `<span class="level-chip">${NATIONAL_METRICS[metric].label}<button type="button" aria-label="Remove ${NATIONAL_METRICS[metric].label}" onclick="removeNationalMetric('${metric}')">×</button></span>`).join('');
  const available = Object.keys(NATIONAL_METRICS).filter(metric => !selectedNationalMetrics.includes(metric));
  const select = document.getElementById('metricSelect');
  select.innerHTML = available.length ? available.map(metric => `<option value="${metric}">${NATIONAL_METRICS[metric].label}</option>`).join('') : '<option value="">All metrics added</option>';
  select.disabled = !available.length;
}

function renderNationalSummaries(qData, basePay, trxWeight, nrxWeight) {
  document.getElementById('normalizationChips').innerHTML = normalizationLevels.map(level => `<span class="level-chip">${level.toFixed(1)}%<button type="button" aria-label="Remove ${level.toFixed(1)}% attainment column" onclick="removeNormalizationLevel(${level})">×</button></span>`).join('');
  renderMetricControls();

  const trxInput = document.getElementById('hypotheticalTrxAttainment');
  const nrxInput = document.getElementById('hypotheticalNrxAttainment');
  if (document.activeElement !== trxInput) trxInput.value = hypotheticalTrxAttainment;
  if (document.activeElement !== nrxInput) nrxInput.value = hypotheticalNrxAttainment;

  const trxMetrics = normalizationLevels.map(level => getNationalMetrics(qData, 'trx', level, basePay, trxWeight));
  const nrxMetrics = normalizationLevels.map(level => getNationalMetrics(qData, 'nrx', level, basePay, nrxWeight));
  const trxCurrent = getNationalMetrics(qData, 'trx', 0, basePay, trxWeight);
  const nrxCurrent = getNationalMetrics(qData, 'nrx', 0, basePay, nrxWeight);
  document.getElementById('trxNationalContext').textContent = `Current national attainment: ${trxCurrent.currentAttainment.toFixed(1)}% (${trxCurrent.totalActual.toLocaleString()} actual / ${trxCurrent.totalGoal.toLocaleString()} goal). Attainment scenarios are shown in columns.`;
  document.getElementById('nrxNationalContext').textContent = `Current national attainment: ${nrxCurrent.currentAttainment.toFixed(1)}% (${nrxCurrent.totalActual.toLocaleString()} actual / ${nrxCurrent.totalGoal.toLocaleString()} goal). Attainment scenarios are shown in columns.`;
  document.getElementById('trxNationalSummary').innerHTML = renderComponentNationalTable(trxMetrics);
  document.getElementById('nrxNationalSummary').innerHTML = renderComponentNationalTable(nrxMetrics);

  const combined = document.getElementById('combinedNationalSummary');
  if (!selectedNationalMetrics.length) {
    combined.innerHTML = '<div class="empty-levels">Add a plan summary metric to display results.</div>';
    return;
  }
  const selectedTrx = getNationalMetrics(qData, 'trx', hypotheticalTrxAttainment, basePay, trxWeight);
  const selectedNrx = getNationalMetrics(qData, 'nrx', hypotheticalNrxAttainment, basePay, nrxWeight);
  const combinedMetrics = combineNationalMetrics(selectedTrx, selectedNrx, basePay, trxWeight, nrxWeight);
  document.getElementById('combinedNationalContext').textContent = `Typed scenario: TRx ${hypotheticalTrxAttainment.toFixed(1)}% + NRx ${hypotheticalNrxAttainment.toFixed(1)}%, using the plan weights of ${(trxWeight * 100).toFixed(0)}% / ${(nrxWeight * 100).toFixed(0)}%.`;
  combined.innerHTML = `<table class="national-table combined-national-table"><thead><tr><th>Plan summary metric</th><th>TRx ${hypotheticalTrxAttainment.toFixed(1)}%</th><th>NRx ${hypotheticalNrxAttainment.toFixed(1)}%</th><th>Combined</th></tr></thead><tbody>${selectedNationalMetrics.map(metricKey => `<tr><td class="metric-label">${NATIONAL_METRICS[metricKey].label}</td>${metricCell(metricKey, selectedTrx)}${metricCell(metricKey, selectedNrx)}${metricCell(metricKey, combinedMetrics)}</tr>`).join('')}</tbody></table>`;
}

mountNationalSummary();
if (typeof quarterlyData !== 'undefined' && quarterlyData.length && typeof renderAll === 'function') renderAll();
