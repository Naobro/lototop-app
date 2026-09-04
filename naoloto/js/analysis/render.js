/* ============================================================
   LotoRender
   LotoStats の集計結果を、分析ページのHTMLへ描画する共通処理。
   ============================================================ */
const LotoRender = (function () {
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
  function renderLatestDraw(container, draw, { bonusKey, dataFileName }) {
    container.innerHTML = '';
    if (!draw) {
      emptyState(container, `まだデータがありません。${dataFileName} に当選番号を追加してください。`);
      return;
    }
    const card = el('div', 'latest-card');
    card.appendChild(el('div', 'round', `第${draw.回号}回`));
    card.appendChild(el('div', 'date', draw.日付));

    card.appendChild(el('div', 'ball-label', '本数字'));
    const mainRow = el('div', 'ball-row');
    draw.本数字.forEach((n) => mainRow.appendChild(el('div', 'ball', String(n))));
    card.appendChild(mainRow);

    const bonus = draw[bonusKey];
    if (bonus && bonus.length) {
      card.appendChild(el('div', 'ball-label', 'ボーナス数字'));
      const bonusRow = el('div', 'ball-row');
      bonus.forEach((n) => bonusRow.appendChild(el('div', 'ball bonus', String(n))));
      card.appendChild(bonusRow);
    }
    container.appendChild(card);
  }

  // ③④ 各数字の出現回数・出現率
  function renderFrequencyTable(container, freq) {
    container.innerHTML = '';
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>数字</th><th>出現回数</th><th>出現率</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    [...freq]
      .sort((a, b) => b.count - a.count || a.number - b.number)
      .forEach((f) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td class="num-cell">${f.number}</td><td>${f.count}回</td><td>${f.rate}%</td>`;
        tbody.appendChild(tr);
      });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ⑤ 現在の出現間隔
  function renderIntervalTable(container, intervalArr) {
    container.innerHTML = '';
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>数字</th><th>最後の出現から</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    [...intervalArr]
      .sort((a, b) => {
        const av = a.interval === null ? -1 : a.interval;
        const bv = b.interval === null ? -1 : b.interval;
        return bv - av;
      })
      .forEach((it) => {
        const tr = document.createElement('tr');
        const label = it.interval === null ? '未出現' : it.interval === 0 ? '今回出現' : `${it.interval}回前`;
        tr.innerHTML = `<td class="num-cell">${it.number}</td><td>${label}</td>`;
        tbody.appendChild(tr);
      });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ⑦ 出現状況を見やすくした表（出現回数ランキングに基づく配色グリッド）
  // rankedFreq は LotoStats.calcNumberRanks() の戻り値
  // （各要素に rank-top3 / rank-top10 / rank-worst10 / rank-normal のいずれかを持つ）
  function renderNumberGrid(container, rankedFreq) {
    container.innerHTML = '';
    const grid = el('div', 'number-grid');
    rankedFreq.forEach((f) => {
      const cell = el('div', `number-cell ${f.rankClass}`);
      cell.appendChild(el('div', 'num', String(f.number)));
      cell.appendChild(el('div', 'cnt', `${f.count}回`));
      grid.appendChild(cell);
    });
    container.appendChild(grid);
  }

  // ⑧ 次回予想を考えるための参考情報
  // recentFreq は直近n回（recentN）基準、intervalArr のみ収録データ（保有データ）基準（経過回数を正確に把握するための例外）
  function renderReferenceInfo(container, { intervalArr, recentFreq, recentN, roundRange, gameName }) {
    container.innerHTML = '';
    const cards = el('div', 'info-cards');

    function topByCount(list, n) {
      return [...list].sort((a, b) => b.count - a.count).slice(0, n);
    }

    const topRecent = topByCount(recentFreq, 5);
    const cardRecent = el('div', 'info-card');
    cardRecent.appendChild(el('h4', null, `直近${recentN}回でよく出ている数字 TOP5`));
    cardRecent.appendChild(el('div', 'nums', topRecent.map((x) => `${x.number}（${x.count}回）`).join(' ／ ')));
    cards.appendChild(cardRecent);

    const longInterval = [...intervalArr]
      .filter((x) => x.interval !== null)
      .sort((a, b) => b.interval - a.interval)
      .slice(0, 5);
    const cardInterval = el('div', 'info-card');
    cardInterval.appendChild(el('h4', null, 'しばらく出ていない数字 TOP5'));
    cardInterval.appendChild(el('div', 'nums', longInterval.map((x) => `${x.number}（${x.interval}回前）`).join(' ／ ')));
    if (roundRange) {
      const note = el(
        'div',
        null,
        `（収録データ内（第${roundRange.min}回〜第${roundRange.max}回）での経過回数）`
      );
      note.style.fontSize = '0.75rem';
      note.style.color = 'var(--text-sub)';
      note.style.fontWeight = 'normal';
      note.style.marginTop = '6px';
      cardInterval.appendChild(note);
    }
    cards.appendChild(cardInterval);

    container.appendChild(cards);

    const disclaimer = el(
      'div',
      'disclaimer-box',
      `これらは過去データの集計に基づく参考情報であり、次回の当選数字を予測・保証するものではありません。${gameName}の抽せんは毎回独立しており、過去の出現状況が次回の出やすさに影響することはありません。数字選びを楽しむための材料としてご活用ください。`
    );
    container.appendChild(disclaimer);
  }

  // 階層分類ごとの出現回数の範囲を説明する文言（強調タグ付き）を生成する。
  // 「<strong>S数字</strong>」「<strong>5回以上</strong>出現した数字」のように、
  // tierRules（閾値の設定値）から自動的に文章を組み立てるため、
  // 基準や呼び方が変わっても書き換え不要。
  function describeTierHtml(tierRules, index) {
    const tier = tierRules[index];
    const label = `「<strong>${tier.label}数字</strong>」`;
    if (index === tierRules.length - 1) {
      return `${label}それ以外`;
    }
    if (index === 0) {
      return `${label}<strong>${tier.minCount}回以上</strong>出現した数字`;
    }
    const range = `${tier.minCount}〜${tierRules[index - 1].minCount - 1}回`;
    return `${label}<strong>${range}</strong>出現した数字`;
  }

  // 階層分類（直近n回）：説明文＋比率カード＋回ごとの構成テーブル
  function renderTierTable(container, tierAnalysis) {
    container.innerHTML = '';

    const { tierRules, n } = tierAnalysis;
    const lines = [`直近${n}回の中で、`];
    tierRules.forEach((tier, i) => {
      lines.push(describeTierHtml(tierRules, i));
    });
    lines.push('として分類しています。');

    const lead = document.createElement('p');
    lead.className = 'page-lead';
    lead.style.marginBottom = '16px';
    lead.innerHTML = lines.join('<br>');
    container.appendChild(lead);

    const cards = el('div', 'info-cards-row');
    tierAnalysis.summary.tierPercents.forEach(({ label, percent }) => {
      const card = el('div', 'info-card');
      card.appendChild(el('h4', null, `${label}数字の割合`));
      card.appendChild(el('div', 'nums', `${percent}%`));
      cards.appendChild(card);
    });
    container.appendChild(cards);

    const tierColumnLabel = `${tierAnalysis.tierLabels.join('/')}構成`;
    const tierSummaryLabel = `${tierAnalysis.tierLabels.join('/')}集計`;
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr>
      <th>回号</th><th>抽せん日</th><th>数字構成</th><th>${tierColumnLabel}</th><th>${tierSummaryLabel}</th><th>ひっぱり</th><th>連続</th><th>偶奇</th>
    </tr></thead>`;
    const tbody = document.createElement('tbody');
    [...tierAnalysis.rows].reverse().forEach((row) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>第${row.回号}回</td><td>${row.日付}</td>
        <td>${row.numbers.join(', ')}</td>
        <td>${row.labels.join(', ')}</td>
        <td>${row.sabSummary}</td>
        <td>${row.pullText}</td>
        <td>${row.hasConsecutive ? 'あり' : 'なし'}</td>
        <td>${row.evenOddSummary}</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ひっぱり率・連続数字率のサマリー
  function renderPullConsecutiveSummary(container, summary, n) {
    container.innerHTML = '';

    const lead = document.createElement('p');
    lead.className = 'page-lead';
    lead.style.marginBottom = '16px';
    lead.innerHTML =
      'ひっぱりとは「前回当選数字と今回当選数字に共通する数字があること」<br>連続数字とは「隣り合う数字（例：12と13）が同時に出ていること」を指します。';
    container.appendChild(lead);

    const cards = el('div', 'info-cards');

    const cardPull = el('div', 'info-card');
    cardPull.appendChild(el('h4', null, `ひっぱり率（直近${n}回）`));
    cardPull.appendChild(el('div', 'nums', `${summary.pullRate}%`));
    cards.appendChild(cardPull);

    const cardCont = el('div', 'info-card');
    cardCont.appendChild(el('h4', null, `連続数字の出現率（直近${n}回）`));
    cardCont.appendChild(el('div', 'nums', `${summary.consecutiveRate}%`));
    cards.appendChild(cardCont);

    container.appendChild(cards);

    const note = el(
      'div',
      'disclaimer-box',
      'ひっぱり・連続数字の有無は毎回の抽せん結果を振り返った記録であり、次回に同じ傾向が続くことを示すものではありません。'
    );
    container.appendChild(note);
  }

  // ② S数字・A数字の位別分類：位グループ×階層で数字を一覧表示する。
  // 最新回の当選数字と一致するものは赤い太文字で強調する。
  function renderTierPositionGroupsTable(container, { groups, tierLabels }, n) {
    container.innerHTML = '';

    const lead = el(
      'p',
      'page-lead',
      `直近${n}回の出現状況をもとに分類した${tierLabels.join('・')}数字を、位グループ別に一覧表示しています。赤い太字は最新回の当選数字と一致することを表します。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table position-sab-table';
    const headCells = tierLabels.map((label) => `<th>${label}数字</th>`).join('');
    table.innerHTML = `<thead><tr><th>位</th>${headCells}</tr></thead>`;
    const tbody = document.createElement('tbody');
    groups.forEach((g) => {
      const tr = document.createElement('tr');
      const cells = tierLabels
        .map((label) => {
          const items = g.tiers[label] || [];
          const text = items.length
            ? items
                .map((it) =>
                  it.isLatest ? `<strong class="highlight-latest">${it.number}</strong>` : String(it.number)
                )
                .join(', ')
            : '—';
          return `<td>${text}</td>`;
        })
        .join('');
      tr.innerHTML = `<td>${g.label}</td>${cells}`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ③ 各位の出現回数TOP5
  function renderPositionTop5Table(container, positionGroups, n) {
    container.innerHTML = '';

    const lead = el('p', 'page-lead', `直近${n}回の当選数字を位グループごとに集計した、出現回数の多い上位5数字です。`);
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const maxRows = Math.max(...positionGroups.map((g) => g.top.length), 0);
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = positionGroups.map((g) => `<th>${g.label}</th>`).join('');
    table.innerHTML = `<thead><tr><th>順位</th>${headCells}</tr></thead>`;
    const tbody = document.createElement('tbody');
    for (let rank = 0; rank < maxRows; rank++) {
      const tr = document.createElement('tr');
      const cells = positionGroups
        .map((g) => {
          const item = g.top[rank];
          return `<td>${item ? `${item.number}（${item.count}回）` : ''}</td>`;
        })
        .join('');
      tr.innerHTML = `<td>${rank + 1}位</td>${cells}`;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // ④ 各数字（第1〜第n数字別）の出現回数TOP5
  function renderDigitPositionTop5Table(container, digitPositions, n) {
    container.innerHTML = '';

    const lead = el(
      'p',
      'page-lead',
      `当選数字を小さい順に並べたときの位置（第1数字〜第${digitPositions.length}数字）ごとに、直近${n}回で出現回数の多い上位5数字を集計しています。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const maxRows = Math.max(...digitPositions.map((p) => p.top.length), 0);
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    const headCells = digitPositions.map((p) => `<th>${p.label}</th>`).join('');
    table.innerHTML = `<thead><tr><th>順位</th>${headCells}</tr></thead>`;
    const tbody = document.createElement('tbody');
    for (let rank = 0; rank < maxRows; rank++) {
      const tr = document.createElement('tr');
      const cells = digitPositions
        .map((p) => {
          const item = p.top[rank];
          return `<td>${item ? `${item.number}（${item.count}回）` : ''}</td>`;
        })
        .join('');
      tr.innerHTML = `<td>${rank + 1}位</td>${cells}`;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // エリア分析：位置（第1〜第n数字）× 数字(1〜maxNumber) のヒートマップ表。
  // 「エリア」＝その位置に実際に出現した数字の最小値〜最大値（動的に算出）。
  // 背景色はエリア内かどうかだけで決定し、数値表示は出現回数(>0)で別途決定する。
  function renderPositionHeatmap(container, { maxNumber, positionFreq }) {
    container.innerHTML = '';

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table position-heatmap-table';

    const headCells = [];
    for (let num = 1; num <= maxNumber; num++) headCells.push(`<th>${num}</th>`);
    table.innerHTML = `<thead><tr><th>位置</th><th>エリア</th>${headCells.join('')}</tr></thead>`;

    const tbody = document.createElement('tbody');
    positionFreq.forEach((row) => {
      const tr = document.createElement('tr');
      const rowClass = `position-row-${row.position}`;
      const areaText = row.min !== null ? `${row.min}〜${row.max}` : '-';
      const cells = [];
      for (let num = 1; num <= maxNumber; num++) {
        const inArea = row.min !== null && num >= row.min && num <= row.max;
        if (inArea) {
          const count = row.counts[num] || 0;
          cells.push(`<td class="${rowClass}">${count > 0 ? count : ''}</td>`);
        } else {
          cells.push('<td class="area-out"></td>');
        }
      }
      tr.innerHTML = `<th class="${rowClass}">第${row.position}数字</th><td class="${rowClass}">${areaText}</td>${cells.join('')}`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // 厳選数字（1軍・2軍）・削除数字
  // selection: LotoStats.calcSelectedNumbers() の戻り値
  // positionGroups: LotoStats.groupSelectionByPosition(selection, positionBoundaries) の戻り値
  // 厳選数字は「1軍・2軍」という独自の括りであり、S数字・A数字の分類とは表示上区別する。
  // 1軍は青文字、2軍は通常の文字色で、位グループごとに1つの並びとして表示する。
  function renderSelectedNumbers(container, selection, positionGroups, n) {
    container.innerHTML = '';
    const { cut, selectedCount, maxNumber, oddsBase, oddsSelected, oddsImprovement } = selection;

    const lead = document.createElement('p');
    lead.className = 'page-lead';
    lead.style.marginBottom = '16px';
    lead.innerHTML = `直近${n}回の出現傾向に応じて、${maxNumber}個の中から厳選数字${selectedCount}個を選んでいます。厳選数字の中でも優先度が高い数字を<strong class="tier1-num">1軍</strong>（太字）、それに次ぐ数字を2軍としています。単に直近の出現回数が多い数字を選んでいるわけではなく、出現の間隔バランスや位別ランキングも考慮しています。`;
    container.appendChild(lead);

    if (oddsImprovement !== null) {
      const oddsRow = el('div', 'info-cards-row');
      const oddsCard = el('div', 'info-card');
      oddsCard.appendChild(el('h4', null, '1等の当せん確率（参考）'));
      oddsCard.appendChild(
        el('div', 'nums', `1/${oddsBase.toLocaleString()} → 1/${oddsSelected.toLocaleString()}（約${oddsImprovement}倍）`)
      );
      oddsRow.appendChild(oddsCard);
      container.appendChild(oddsRow);
    }

    // note等へのコピー時にtable構造が崩れる（セルの区切りが失われ1行に連結される）
    // ことがあるため、position-sab-tableではなくdivベースの一覧で表示する。
    const list = el('div', 'copy-list');
    positionGroups.forEach((g) => {
      const row = el('div', 'copy-list-row');
      const text = g.items.length
        ? g.items
            .map((it) =>
              it.tierIndex === 0
                ? `<strong class="tier1-num" style="color:#1a56c4;font-weight:bold;">${it.number}</strong>`
                : String(it.number)
            )
            .join(', ')
        : '—';
      row.innerHTML = `<strong>${g.label}：</strong>${text}`;
      list.appendChild(row);
    });
    container.appendChild(list);

    const tierCards = el('div', 'info-cards');
    const cutCard = el('div', 'info-card');
    cutCard.appendChild(el('h4', null, `削除数字（${cut.length}個）`));
    cutCard.appendChild(el('div', 'nums', [...cut].sort((a, b) => a - b).join(', ') || 'なし'));
    tierCards.appendChild(cutCard);
    container.appendChild(tierCards);

    const disclaimer = el(
      'div',
      'disclaimer-box',
      'これらは過去データの傾向をもとに数字を絞り込んだ参考情報であり、当選を予測・保証するものではありません。厳選数字に次回の当選番号が含まれることを保証するものでもありません。'
    );
    container.appendChild(disclaimer);
  }

  // 予想パターン（直近n回の位パターンの出現回数、上位topN件）
  function renderPredictionPatterns(container, patterns, n, topN = 10) {
    container.innerHTML = '';

    const lead = el(
      'p',
      'page-lead',
      `直近${n}回で出現回数が多い上位${topN}パターンです。厳選数字（1軍・2軍）の中から数字を選ぶ際の、位構成の目安としてご利用ください。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    // note等へのコピー時にtable構造が崩れることがあるため、divベースの一覧で表示する。
    const top = patterns.slice(0, topN);
    const list = el('div', 'copy-list');
    top.forEach((p, idx) => {
      const row = el('div', 'copy-list-row', `${idx + 1}位　${p.pattern}　${p.count}回`);
      list.appendChild(row);
    });
    container.appendChild(list);
  }

  // 当選検証：最新回を除いたデータで厳選数字を再計算し、
  // 実際の最新回の当選番号が含まれていたかを表示する。
  function renderSelectionVerification(container, verification) {
    container.innerHTML = '';
    if (!verification) {
      emptyState(container, 'データが不足しているため検証できません。');
      return;
    }

    const lead = el(
      'p',
      'page-lead',
      `第${verification.round}回（${verification.date}）の抽せんについて、その回を除いたデータで厳選数字（${verification.selectedCount}個）を計算し、実際の当選番号・ボーナス数字が含まれていたかを検証しています。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    function withBonus(numbers, bonusNumbers) {
      const base = numbers.join(', ') || 'なし';
      return bonusNumbers.length ? `${base}（${bonusNumbers.join(', ')}）` : base;
    }

    const cards = el('div', 'info-cards-row');
    const cardCovered = el('div', 'info-card');
    cardCovered.appendChild(el('h4', null, '厳選数字に含まれていた本数字'));
    cardCovered.appendChild(el('div', 'nums', withBonus(verification.coveredNumbers, verification.coveredBonusNumbers)));
    cards.appendChild(cardCovered);

    const cardMissed = el('div', 'info-card');
    cardMissed.appendChild(el('h4', null, '厳選数字に含まれていなかった本数字'));
    cardMissed.appendChild(el('div', 'nums', withBonus(verification.missedNumbers, verification.missedBonusNumbers)));
    cards.appendChild(cardMissed);
    container.appendChild(cards);

    let verdictText;
    if (verification.allCovered) {
      verdictText = `第${verification.round}回は、当選番号${verification.latestNumbers.length}個が全て厳選数字（${verification.selectedCount}個）に含まれていました（1等相当）。`;
    } else if (verification.secondPrizePossible) {
      verdictText = `第${verification.round}回は、1等相当は狙えませんでしたが、当選番号${
        verification.coveredNumbers.length
      }個とボーナス数字が厳選数字に含まれており、選び方次第では2等相当が狙えた可能性があります。`;
    } else {
      verdictText = `第${verification.round}回は、当選番号のうち${verification.missedNumbers.length}個が厳選数字（${verification.selectedCount}個）に含まれていませんでした。`;
    }
    const verdict = el('div', 'disclaimer-box', verdictText);
    container.appendChild(verdict);
  }

  // 連続数字ペアの出現ランキング
  function renderConsecutivePairsTable(container, pairs) {
    container.innerHTML = '';
    if (pairs.length === 0) {
      emptyState(container, '直近の集計範囲内では、連続する数字のペアは出現していません。');
      return;
    }
    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>連続ペア</th><th>出現回数</th></tr></thead>`;
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

  // 位グループの範囲説明文（例:「1の位（1〜9）／10の位（10〜19）／...」）を
  // positionBoundaries と maxNumber から動的に組み立てる。
  function buildPositionRangeDescription(positionBoundaries, maxNumber) {
    return positionBoundaries
      .map((b, i) => {
        const upper = i < positionBoundaries.length - 1 ? positionBoundaries[i + 1] - 1 : maxNumber;
        return `${b}の位（${b}〜${upper}）`;
      })
      .join('／');
  }

  // 直近n回のパターン分析（数字を位でグループ化した構成の出現頻度）
  function renderPatternTable(container, patterns, { mainCount, positionBoundaries, maxNumber }) {
    container.innerHTML = '';

    const rangeDesc = buildPositionRangeDescription(positionBoundaries, maxNumber);
    const lead = el(
      'p',
      'page-lead',
      `当選数字${mainCount}個を「${rangeDesc}」に分類し、その並び方のパターンごとに出現回数を集計しています。`
    );
    lead.style.marginBottom = '16px';
    container.appendChild(lead);

    const wrap = el('div', 'table-scroll');
    const table = document.createElement('table');
    table.className = 'analysis-table';
    table.innerHTML = `<thead><tr><th>パターン</th><th>出現回数</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    patterns.forEach((p) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${p.pattern}</td><td>${p.count}回</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);
  }

  // note投稿用：指定した複数セクション（見出し込みのsection要素のid）のテキストを
  // まとめてクリップボードにコピーするボタンを初期化する。
  function setupCopyButton(buttonId, statusId, sectionIds) {
    const button = document.getElementById(buttonId);
    const status = document.getElementById(statusId);
    if (!button) return;

    function showStatus(message) {
      if (!status) return;
      status.textContent = message;
      setTimeout(() => {
        status.textContent = '';
      }, 3000);
    }

    button.addEventListener('click', () => {
      const sections = sectionIds.map((id) => document.getElementById(id)).filter(Boolean);
      if (sections.length === 0) return;

      const html = sections.map((s) => s.innerHTML).join('<hr>');
      const text = sections
        .map((s) => s.innerText.trim())
        .filter(Boolean)
        .join('\n\n');

      function fallbackPlainCopy() {
        navigator.clipboard
          .writeText(text)
          .then(() => showStatus('✅ コピーしました（プレーンテキスト）'))
          .catch(() => showStatus('❌ コピーに失敗しました'));
      }

      // text/html も一緒にコピーすることで、noteなどリッチテキスト対応先に
      // 貼り付けたとき、太字や1軍の青文字などの装飾が保持される。
      // プレーンテキストのみ対応の貼り付け先では自動的にtext/plainが使われる。
      if (window.ClipboardItem) {
        const item = new ClipboardItem({
          'text/html': new Blob([html], { type: 'text/html' }),
          'text/plain': new Blob([text], { type: 'text/plain' }),
        });
        navigator.clipboard
          .write([item])
          .then(() => showStatus('✅ コピーしました（装飾つき）'))
          .catch(fallbackPlainCopy);
      } else {
        fallbackPlainCopy();
      }
    });
  }

  return {
    emptyState,
    renderLatestDraw,
    renderFrequencyTable,
    renderIntervalTable,
    renderNumberGrid,
    renderReferenceInfo,
    renderTierTable,
    renderPullConsecutiveSummary,
    renderTierPositionGroupsTable,
    renderPositionTop5Table,
    renderDigitPositionTop5Table,
    renderPositionHeatmap,
    renderConsecutivePairsTable,
    renderPatternTable,
    renderSelectedNumbers,
    renderPredictionPatterns,
    renderSelectionVerification,
    setupCopyButton,
  };
})();
