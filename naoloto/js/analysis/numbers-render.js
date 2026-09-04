/* ============================================================
   NumbersRender
   NumbersStats の集計結果を、分析ページのHTMLへ描画する共通処理。
   ============================================================ */
const NumbersRender = (function () {
  function el(tag, className, text) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function emptyState(container, message) {
    container.innerHTML = '';
    container.appendChild(el('div', 'empty-state', message));
  }

  // ① 最新の当選番号
  function renderLatestDraw(container, draw, { mainKey, dataFileName }) {
    container.innerHTML = '';
    if (!draw) {
      emptyState(container, `まだデータがありません。${dataFileName} に当選番号を追加してください。`);
      return;
    }
    const card = el('div', 'latest-card');
    card.appendChild(el('div', 'round', `第${draw.回号}回`));
    card.appendChild(el('div', 'date', draw.日付));
    card.appendChild(el('div', 'ball-label', '当選番号'));
    const row = el('div', 'ball-row');
    draw[mainKey].forEach((d) => row.appendChild(el('div', 'ball', String(d))));
    card.appendChild(row);
    container.appendChild(card);
  }

  // 過去の当選番号一覧（新しい順）
  function renderHistoryTable(container, draws, { mainKey, digitCount }) {
    container.innerHTML = '';
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = [];
    for (let i = 1; i <= digitCount; i++) headCells.push(`<th>第${i}数字</th>`);
    table.innerHTML = `<thead><tr><th>回号</th><th>抽せん日</th>${headCells.join('')}</tr></thead>`;
    const tbody = document.createElement('tbody');
    [...draws].reverse().forEach((d) => {
      const tr = document.createElement('tr');
      const cells = d[mainKey].map((v) => `<td class="num-cell">${v}</td>`).join('');
      tr.innerHTML = `<td>第${d.回号}回</td><td>${d.日付}</td>${cells}`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 数字選びの参考情報：桁ごとのよく出ている数字・しばらく出ていない数字
  function renderReferenceInfo(container, { digitTop5, digitIntervals, n }) {
    container.innerHTML = '';
    const cards = el('div', 'info-cards');

    digitTop5.forEach((pos) => {
      const card = el('div', 'info-card');
      card.appendChild(el('h4', null, `第${pos.position}数字でよく出ている数字（直近${n}回 TOP5）`));
      card.appendChild(el('div', 'nums', pos.top.map((x) => `${x.digit}（${x.count}回）`).join(' ／ ')));
      cards.appendChild(card);
    });

    digitIntervals.forEach((pos) => {
      const longWaiting = [...pos.intervals]
        .filter((x) => x.interval !== null)
        .sort((a, b) => b.interval - a.interval)
        .slice(0, 3);
      const card = el('div', 'info-card');
      card.appendChild(el('h4', null, `第${pos.position}数字のしばらく出ていない数字`));
      card.appendChild(el('div', 'nums', longWaiting.map((x) => `${x.digit}（${x.interval}回前）`).join(' ／ ')));
      cards.appendChild(card);
    });
    container.appendChild(cards);

    const disclaimer = el(
      'div',
      'disclaimer-box',
      'これらは過去データの集計に基づく参考情報であり、次回の当選数字を予測・保証するものではありません。ナンバーズの抽せんは毎回独立しており、過去の出現状況が次回の出やすさに影響することはありません。'
    );
    container.appendChild(disclaimer);
  }

  // 各桁の出現回数・出現率（直近n回）
  function renderDigitFrequencyTable(container, digitFrequency, n) {
    container.innerHTML = '';
    const lead = el('p', 'page-lead', `直近${n}回について、各桁（位置）ごとに0〜9それぞれの出現回数・出現率を集計しています。`);
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = digitFrequency.positions.map((p) => `<th colspan="2">第${p.position}数字</th>`).join('');
    const subCells = digitFrequency.positions.map(() => `<th>回数</th><th>率</th>`).join('');
    table.innerHTML = `<thead><tr><th rowspan="2">数字</th>${headCells}</tr><tr>${subCells}</tr></thead>`;
    const tbody = document.createElement('tbody');
    for (let digit = 0; digit <= 9; digit++) {
      const tr = document.createElement('tr');
      const cells = digitFrequency.positions
        .map((p) => {
          const f = p.frequency.find((x) => x.digit === digit);
          return `<td>${f.count}回</td><td>${f.rate}%</td>`;
        })
        .join('');
      tr.innerHTML = `<td class="num-cell">${digit}</td>${cells}`;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 各桁の現在の出現間隔
  function renderDigitIntervalTable(container, digitIntervals) {
    container.innerHTML = '';
    const lead = el('p', 'page-lead', '最新回から数えて、各桁にその数字が何回前に出現したかを表しています。');
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = digitIntervals.map((p) => `<th>第${p.position}数字</th>`).join('');
    table.innerHTML = `<thead><tr><th>数字</th>${headCells}</tr></thead>`;
    const tbody = document.createElement('tbody');
    for (let digit = 0; digit <= 9; digit++) {
      const tr = document.createElement('tr');
      const cells = digitIntervals
        .map((p) => {
          const it = p.intervals.find((x) => x.digit === digit);
          const label = it.interval === null ? '未出現' : it.interval === 0 ? '今回出現' : `${it.interval}回前`;
          return `<td>${label}</td>`;
        })
        .join('');
      tr.innerHTML = `<td class="num-cell">${digit}</td>${cells}`;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 各桁の出現回数TOP5
  function renderDigitTop5Table(container, digitTop5, n) {
    container.innerHTML = '';
    const lead = el('p', 'page-lead', `直近${n}回で、各桁ごとに出現回数の多い上位5数字です。`);
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const maxRows = Math.max(...digitTop5.map((p) => p.top.length), 0);
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = digitTop5.map((p) => `<th>第${p.position}数字</th>`).join('');
    table.innerHTML = `<thead><tr><th>順位</th>${headCells}</tr></thead>`;
    const tbody = document.createElement('tbody');
    for (let rank = 0; rank < maxRows; rank++) {
      const tr = document.createElement('tr');
      const cells = digitTop5
        .map((p) => {
          const item = p.top[rank];
          return `<td>${item ? `${item.digit}（${item.count}回）` : ''}</td>`;
        })
        .join('');
      tr.innerHTML = `<td>${rank + 1}位</td>${cells}`;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 奇数偶数分析
  function renderParitySummary(container, parity) {
    container.innerHTML = '';
    const lead = el(
      'p',
      'page-lead',
      `直近${parity.n}回について、当選番号の合計値（各桁の和）が偶数か奇数か、および桁ごとの偶数率を集計しています。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const cards = el('div', 'info-cards-row');
    const cardEven = el('div', 'info-card');
    cardEven.appendChild(el('h4', null, '合計値が偶数の割合'));
    cardEven.appendChild(el('div', 'nums', `${parity.evenSumRate}%`));
    cards.appendChild(cardEven);

    const cardOdd = el('div', 'info-card');
    cardOdd.appendChild(el('h4', null, '合計値が奇数の割合'));
    cardOdd.appendChild(el('div', 'nums', `${parity.oddSumRate}%`));
    cards.appendChild(cardOdd);
    container.appendChild(cards);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>桁</th><th>偶数の割合</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    parity.perDigitEvenRate.forEach((p) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>第${p.position}数字</td><td>${p.evenRate}%</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 数字合計の分布
  function renderSumDistribution(container, distribution) {
    container.innerHTML = '';
    const lead = el('p', 'page-lead', `直近${distribution.n}回について、当選番号の合計値（各桁の和）がどのレンジに何回入ったかを集計しています。`);
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>合計値レンジ</th><th>回数</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    distribution.bins.forEach((b) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${b.label}</td><td>${b.count}回</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 直近n回の当選番号一覧（SAB分類付き、新しい順）
  function renderTierAnnotatedHistoryTable(container, history) {
    container.innerHTML = '';
    const lead = el(
      'p',
      'page-lead',
      `直近${history.n}回の当選番号です。SAB分類はロトのページと同じ定義（S=直近${history.n}回で5回以上出現／A=3〜4回／それ以外=B）で、数字（値）ごとに判定しています。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const digitCount = history.rows.length ? history.rows[0].digits.length : 0;
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = [];
    for (let i = 1; i <= digitCount; i++) headCells.push(`<th>第${i}数字</th>`);
    table.innerHTML = `<thead><tr><th>回号</th><th>抽せん日</th>${headCells.join('')}<th>SAB分類</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    [...history.rows].reverse().forEach((row) => {
      const tr = document.createElement('tr');
      const digitCells = row.digits.map((v) => `<td class="num-cell">${v}</td>`).join('');
      tr.innerHTML = `<td>第${row.回号}回</td><td>${row.日付}</td>${digitCells}<td>${row.labels.join(', ')}</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ひっぱり回数
  function renderPullCount(container, pull) {
    container.innerHTML = '';
    const lead = el(
      'p',
      'page-lead',
      'ひっぱりとは「前回の当選番号と同じ数字（値）を1つ以上含んでいること」を指します。'
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const cards = el('div', 'info-cards-row');
    const card = el('div', 'info-card');
    card.appendChild(el('h4', null, `ひっぱり回数（直近${pull.n}回）`));
    card.appendChild(el('div', 'nums', `${pull.pullCount}回（${pull.pullRate}%）`));
    cards.appendChild(card);
    container.appendChild(cards);
  }

  // シングル・ダブル・トリプル（・ボックス）回数
  function renderRepeatPatternSummary(container, summary) {
    container.innerHTML = '';
    const lead = el(
      'p',
      'page-lead',
      `直近${summary.n}回の当選番号を、数字の重複具合で分類しています（シングル＝全桁とも異なる数字／ダブル＝同じ数字が2つ／トリプル＝同じ数字が3つ）。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>タイプ</th><th>回数</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    summary.items.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${item.label}</td><td>${item.count}回</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 数字の範囲ごとの分布
  function renderRangeDistribution(container, distribution) {
    container.innerHTML = '';
    const lead = el('p', 'page-lead', `直近${distribution.n}回の数字（全桁合算）を、値の範囲ごとに集計しています。`);
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>範囲</th><th>出現回数</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    distribution.ranges.forEach((r) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.label}</td><td>${r.count}回</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ペア出現ランキング
  function renderDigitPairRanking(container, pairs, n) {
    container.innerHTML = '';
    const lead = el(
      'p',
      'page-lead',
      `直近${n}回で、同じ回に含まれていた数字の2つ組（同じ値同士のペアも含む）の出現回数上位です。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>ペア</th><th>出現回数</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    pairs.forEach((p) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="num-cell">${p.pair}</td><td>${p.count}回</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 合計値の出現回数（値ごと）
  function renderSumFrequency(container, sumFreq, n) {
    container.innerHTML = '';
    const lead = el('p', 'page-lead', `直近${n}回について、当選番号の合計値（各桁の和）ごとの出現回数です。`);
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>合計値</th><th>出現回数</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    sumFreq.forEach((s) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td class="num-cell">${s.sum}</td><td>${s.count}回</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  return {
    emptyState,
    renderLatestDraw,
    renderHistoryTable,
    renderReferenceInfo,
    renderDigitFrequencyTable,
    renderDigitIntervalTable,
    renderDigitTop5Table,
    renderParitySummary,
    renderSumDistribution,
    renderTierAnnotatedHistoryTable,
    renderPullCount,
    renderRepeatPatternSummary,
    renderRangeDistribution,
    renderDigitPairRanking,
    renderSumFrequency,
  };
})();
