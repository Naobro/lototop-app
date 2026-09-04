/* ============================================================
   LotoStats
   ロト系（ロト7/ロト6/ミニロト）共通の集計ロジック。
   draws は { 回号, 日付, 本数字:[...], ボーナス数字:[...] } の配列を想定し、
   回号の昇順（古い→新しい）で渡すこと。
   ============================================================ */
const LotoStats = (function () {
  function getMainNumbers(draw, mainKey) {
    return draw[mainKey] || [];
  }

  function sortByRound(draws) {
    return [...draws].sort((a, b) => (a.回号 ?? 0) - (b.回号 ?? 0));
  }

  // 汎用CSVパーサー（tousen.pyが出力するCSVはフィールド内にカンマ・引用符を含まないため、
  // 単純なsplitで十分。1行目をヘッダーとして、各行を { 列名: 値 } のオブジェクトにする）。
  function parseCsv(text) {
    const lines = text.replace(/\r\n/g, '\n').split('\n').filter((line) => line.trim() !== '');
    if (lines.length === 0) return [];
    const headers = lines[0].split(',').map((h) => h.trim());
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split(',');
      const row = {};
      headers.forEach((h, idx) => {
        row[h] = cells[idx] !== undefined ? cells[idx].trim() : '';
      });
      rows.push(row);
    }
    return rows;
  }

  // parseCsv()の結果を、このプロジェクト共通のdraws形式
  // { 回号, 日付, 本数字:[...], (ボーナス数字:[...]) } に変換する。
  // roundCol/dateColは列名、mainColsは本数字の列名配列（順序が桁の並びになる）、
  // bonusColsはボーナス数字の列名配列（ナンバーズ系は空配列でよい）。
  function csvRowsToDraws(rows, { roundCol = '回号', dateCol = '抽せん日', mainCols, bonusCols = [] }) {
    return rows
      .map((row) => {
        const round = parseInt(row[roundCol], 10);
        const mainNumbers = mainCols.map((c) => parseInt(row[c], 10));
        if (!Number.isFinite(round) || mainNumbers.some((n) => !Number.isFinite(n))) return null;
        const draw = { 回号: round, 日付: row[dateCol] || '', 本数字: mainNumbers };
        if (bonusCols.length) {
          draw.ボーナス数字 = bonusCols.map((c) => parseInt(row[c], 10)).filter((n) => Number.isFinite(n));
        }
        return draw;
      })
      .filter((d) => d !== null);
  }

  // GitHub上のCSV（tousen.pyが更新するもの）を直接取得し、draws形式で返す。
  // これにより、tousen.pyでの保存・GitHub反映が、サイト側の再読み込みだけで
  // 自動的に反映される（別途JSONへの同期作業が不要になる）。
  async function loadDrawsFromCsv(url, csvOptions) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`CSVの読み込みに失敗しました（HTTP ${res.status}）`);
    const text = await res.text();
    const rows = parseCsv(text);
    const draws = csvRowsToDraws(rows, csvOptions);
    return sortByRound(draws);
  }

  // 数字ごとの出現回数・出現率（1〜maxNumber全て）
  function calcFrequency(draws, { maxNumber, mainKey }) {
    const counts = new Array(maxNumber + 1).fill(0);
    draws.forEach((d) => {
      getMainNumbers(d, mainKey).forEach((n) => {
        if (n >= 1 && n <= maxNumber) counts[n] += 1;
      });
    });
    const total = draws.length;
    const result = [];
    for (let n = 1; n <= maxNumber; n++) {
      result.push({
        number: n,
        count: counts[n],
        rate: total > 0 ? Math.round((counts[n] / total) * 1000) / 10 : 0,
      });
    }
    return result;
  }

  // 各数字の「最新回から何回前に出たか」（0=今回出た, nullは出現なし）
  function calcCurrentIntervals(draws, { maxNumber, mainKey }) {
    const result = {};
    for (let n = 1; n <= maxNumber; n++) result[n] = null;
    for (let i = draws.length - 1; i >= 0; i--) {
      const sinceLatest = draws.length - 1 - i;
      getMainNumbers(draws[i], mainKey).forEach((n) => {
        if (n >= 1 && n <= maxNumber && result[n] === null) {
          result[n] = sinceLatest;
        }
      });
    }
    const arr = [];
    for (let n = 1; n <= maxNumber; n++) arr.push({ number: n, interval: result[n] });
    return arr;
  }

  // 直近n回の抽せんと、その範囲内での出現頻度
  function calcRecentTrend(draws, n, { maxNumber, mainKey }) {
    const recent = draws.slice(-n);
    return {
      draws: recent,
      frequency: calcFrequency(recent, { maxNumber, mainKey }),
    };
  }

  function pct(part, total) {
    return total > 0 ? Math.round((part / total) * 1000) / 10 : 0;
  }

  // 数字を位グループに分類する。boundaries は昇順の境界値配列
  // （例: ロト7/ロト6=[1,10,20,30], ミニロト=[1,10,20]）。
  // num以上の最大の境界値をラベルとして返すため、最後の境界は
  // 自動的にmaxNumberまで延長される（ゲームごとに個別対応不要）。
  const DEFAULT_POSITION_BOUNDARIES = [1, 10, 20, 30];

  function bucketLabel(num, boundaries = DEFAULT_POSITION_BOUNDARIES) {
    let label = boundaries[0];
    for (const b of boundaries) {
      if (num >= b) label = b;
    }
    return String(label);
  }

  function positionLabelsFor(boundaries = DEFAULT_POSITION_BOUNDARIES) {
    return boundaries.map((b) => `${b}の位`);
  }

  // 出現回数に応じた階層分類の既定ルール（全ゲーム共通の前提）。
  // label・minCount は設定値であり、判定ロジック側は特定の記号に依存しない。
  // 出現回数が多い順に並べること（先頭ほど基準が高い）。
  const DEFAULT_TIER_RULES = [
    { label: 'S', minCount: 5 },
    { label: 'A', minCount: 3 },
    { label: 'B', minCount: 0 },
  ];

  // 出現回数からtierRulesに沿って階層ラベルを1つ決定する共通ロジック。
  // S/A/B等の具体的な呼び方には依存しない。
  function classifyByTier(count, tierRules) {
    for (const tier of tierRules) {
      if (count >= tier.minCount) return tier.label;
    }
    return tierRules[tierRules.length - 1].label;
  }

  // ラベル配列(例:['S','S','A',...])を、tierRulesの順に「S6A1」のように要約する。
  // 0個の階層は省略する。特定の記号(S/A/B等)には依存しない汎用ロジック。
  function summarizeTierLabels(labels, tierRules) {
    return tierRules
      .map((t) => {
        const count = labels.filter((l) => l === t.label).length;
        return count > 0 ? `${t.label}${count}` : '';
      })
      .join('');
  }

  // 本数字の配列から「偶数X 奇数Y」の要約文字列を作る
  function summarizeEvenOdd(numbers) {
    const evenCount = numbers.filter((num) => num % 2 === 0).length;
    const oddCount = numbers.length - evenCount;
    return `偶数${evenCount} 奇数${oddCount}`;
  }

  // 直近n回の本数字を集計し、数字ごとの出現回数マップを返す
  function countRecentNumbers(draws, mainKey, n) {
    const recent = draws.slice(-n);
    const countMap = {};
    recent.forEach((d) => {
      getMainNumbers(d, mainKey).forEach((num) => {
        countMap[num] = (countMap[num] || 0) + 1;
      });
    });
    return { recent, countMap };
  }

  // 階層分類（直近n回）：tierRulesの基準に沿って、直近n回に出現した回数で
  // 各数字を階層付けする。基準・呼び方(S/A/B等)が変わってもこの関数自体は
  // 変更不要（tierRulesを差し替えるだけでよい）。
  function calcTierAnalysis(draws, { mainKey, tierRules = DEFAULT_TIER_RULES }, n = 24) {
    const { recent, countMap } = countRecentNumbers(draws, mainKey, n);

    const tierMap = {};
    Object.entries(countMap).forEach(([numStr, count]) => {
      tierMap[Number(numStr)] = classifyByTier(count, tierRules);
    });

    const rows = [];
    const tierTotals = {};
    tierRules.forEach((t) => {
      tierTotals[t.label] = 0;
    });
    let pullTotal = 0;
    let contTotal = 0;

    recent.forEach((d, i) => {
      const nums = [...getMainNumbers(d, mainKey)].sort((a, b) => a - b);
      const labels = nums.map((num) => {
        const label = tierMap[num] ?? tierRules[tierRules.length - 1].label;
        tierTotals[label] += 1;
        return label;
      });

      const hasConsecutive = nums.some((num, idx) => idx > 0 && num - nums[idx - 1] === 1);
      if (hasConsecutive) contTotal += 1;

      let pullText = '-';
      if (i > 0) {
        const prevNums = getMainNumbers(recent[i - 1], mainKey);
        const pullCount = nums.filter((num) => prevNums.includes(num)).length;
        pullText = pullCount > 0 ? `${pullCount}個` : 'なし';
        if (pullCount > 0) pullTotal += 1;
      }

      rows.push({
        回号: d.回号,
        日付: d.日付,
        numbers: nums,
        labels,
        sabSummary: summarizeTierLabels(labels, tierRules),
        evenOddSummary: summarizeEvenOdd(nums),
        pullText,
        hasConsecutive,
      });
    });

    const totalLabels = Object.values(tierTotals).reduce((sum, v) => sum + v, 0);

    return {
      n: recent.length,
      rows,
      tierLabels: tierRules.map((t) => t.label),
      tierRules,
      summary: {
        tierPercents: tierRules.map((t) => ({
          label: t.label,
          percent: pct(tierTotals[t.label], totalLabels),
        })),
        pullRate: pct(pullTotal, recent.length - 1),
        consecutiveRate: pct(contTotal, recent.length),
      },
    };
  }

  // 出現回数の多い順3位以内→rank-top3、4〜10位→rank-top10、
  // 出現回数の少ない方から10位以内→rank-worst10、それ以外→rank-normal
  // 同数の場合は数字が小さい方を優先する。
  function calcNumberRanks(freq) {
    const byTopOrder = [...freq].sort((a, b) => b.count - a.count || a.number - b.number);
    const byWorstOrder = [...freq].sort((a, b) => a.count - b.count || a.number - b.number);

    const top3 = new Set(byTopOrder.slice(0, 3).map((f) => f.number));
    const top10 = new Set(byTopOrder.slice(3, 10).map((f) => f.number));
    const worst10 = new Set(byWorstOrder.slice(0, 10).map((f) => f.number));

    return freq.map((f) => {
      let rankClass = 'rank-normal';
      if (top3.has(f.number)) rankClass = 'rank-top3';
      else if (top10.has(f.number)) rankClass = 'rank-top10';
      else if (worst10.has(f.number)) rankClass = 'rank-worst10';
      return { ...f, rankClass };
    });
  }

  // draws（sortByRound済み）から収録されている回号の範囲を取得
  function getRoundRange(draws) {
    if (draws.length === 0) return null;
    return { min: draws[0].回号, max: draws[draws.length - 1].回号 };
  }

  // ② S数字・A数字の位別分類：直近n回の出現回数から階層分類し、
  // 最下位階層（tierRulesの末尾＝「それ以外」を意味する基準）を除いた
  // 上位階層のみ、位グループ別に一覧化する。各数字が最新回に含まれるかも付与する。
  function calcTierPositionGroups(
    draws,
    { mainKey, tierRules = DEFAULT_TIER_RULES, maxNumber, positionBoundaries = DEFAULT_POSITION_BOUNDARIES },
    n = 24
  ) {
    const { countMap } = countRecentNumbers(draws, mainKey, n);
    const tiersToShow = tierRules.slice(0, -1);
    const posLabels = positionLabelsFor(positionBoundaries);

    const latest = draws.length ? draws[draws.length - 1] : null;
    const latestNumbers = new Set(latest ? getMainNumbers(latest, mainKey) : []);

    const groups = posLabels.map((label) => {
      const tiers = {};
      tiersToShow.forEach((t) => {
        tiers[t.label] = [];
      });
      return { label, tiers };
    });

    for (let num = 1; num <= maxNumber; num++) {
      const count = countMap[num];
      if (!count) continue;
      const tierLabel = classifyByTier(count, tierRules);
      const tierIndex = tiersToShow.findIndex((t) => t.label === tierLabel);
      if (tierIndex === -1) continue; // 最下位階層は表示対象外
      const posIndex = posLabels.indexOf(`${bucketLabel(num, positionBoundaries)}の位`);
      groups[posIndex].tiers[tierLabel].push({ number: num, isLatest: latestNumbers.has(num) });
    }

    return { groups, tierLabels: tiersToShow.map((t) => t.label) };
  }

  // ③ 各位の出現回数TOP5：直近n回の本数字を位グループごとに集計し、上位topN件を返す
  function calcPositionTop5(
    draws,
    { mainKey, maxNumber, positionBoundaries = DEFAULT_POSITION_BOUNDARIES },
    n = 24,
    topN = 5
  ) {
    const { countMap } = countRecentNumbers(draws, mainKey, n);
    const posLabels = positionLabelsFor(positionBoundaries);

    const groups = posLabels.map((label) => ({ label, top: [] }));
    for (let num = 1; num <= maxNumber; num++) {
      const count = countMap[num];
      if (!count) continue;
      const posIndex = posLabels.indexOf(`${bucketLabel(num, positionBoundaries)}の位`);
      groups[posIndex].top.push({ number: num, count });
    }
    groups.forEach((g) => {
      g.top.sort((a, b) => b.count - a.count || a.number - b.number);
      g.top = g.top.slice(0, topN);
    });
    return groups;
  }

  // ④ 各数字（第1〜第n数字別）の出現回数TOP5：直近n回の本数字を昇順に並べ、
  // 位置（第1数字, 第2数字, ...）ごとに集計し、上位topN件を返す
  function calcDigitPositionTop5(draws, { mainKey, mainCount }, n = 24, topN = 5) {
    const recent = draws.slice(-n);
    const positions = [];
    for (let i = 0; i < mainCount; i++) {
      const countMap = {};
      recent.forEach((d) => {
        const nums = [...getMainNumbers(d, mainKey)].sort((a, b) => a - b);
        const val = nums[i];
        if (val === undefined) return;
        countMap[val] = (countMap[val] || 0) + 1;
      });
      const top = Object.entries(countMap)
        .map(([numStr, count]) => ({ number: Number(numStr), count }))
        .sort((a, b) => b.count - a.count || a.number - b.number)
        .slice(0, topN);
      positions.push({ label: `第${i + 1}数字`, top });
    }
    return positions;
  }

  // エリア分析：直近n回について、位置（第1数字〜第mainCount数字）ごとに
  // 1〜maxNumberの各数字が何回その位置に出現したかを集計する。
  // positionFreq[i].counts[num] = 出現回数（0はまだ埋まっていないマス）
  function calcPositionFrequency(draws, { mainKey, mainCount, maxNumber }, n = 24) {
    const recent = draws.slice(-n);
    const positionFreq = [];
    for (let i = 0; i < mainCount; i++) {
      const counts = new Array(maxNumber + 1).fill(0);
      recent.forEach((d) => {
        const nums = [...getMainNumbers(d, mainKey)].sort((a, b) => a - b);
        const val = nums[i];
        if (val !== undefined) counts[val] += 1;
      });
      // エリア（min〜max）：この位置に実際に出現した数字の最小値・最大値。
      // データから動的に算出する（固定値にしない）。
      let min = null;
      let max = null;
      for (let num = 1; num <= maxNumber; num++) {
        if (counts[num] > 0) {
          if (min === null) min = num;
          max = num;
        }
      }
      positionFreq.push({ position: i + 1, counts, min, max });
    }
    return { n: recent.length, maxNumber, positionFreq };
  }

  // 連続数字ペア（隣り合う数字の組）の出現ランキング（直近n回）
  function calcConsecutivePairs(draws, { mainKey }, n = 24) {
    const recent = draws.slice(-n);
    const pairCounts = {};
    recent.forEach((d) => {
      const nums = [...getMainNumbers(d, mainKey)].sort((a, b) => a - b);
      for (let i = 0; i < nums.length - 1; i++) {
        if (nums[i + 1] - nums[i] === 1) {
          const key = `${nums[i]}-${nums[i + 1]}`;
          pairCounts[key] = (pairCounts[key] || 0) + 1;
        }
      }
    });
    return Object.entries(pairCounts)
      .map(([pair, count]) => ({ pair, count }))
      .sort((a, b) => b.count - a.count);
  }

  // パターン分析（直近n回）：数字を位グループでグループ化した構成パターンの出現頻度
  function calcPatternAnalysis(draws, { mainKey, positionBoundaries = DEFAULT_POSITION_BOUNDARIES }, n = 24) {
    const recent = draws.slice(-n);
    const patternCounts = {};
    recent.forEach((d) => {
      const nums = [...getMainNumbers(d, mainKey)].sort((a, b) => a - b);
      const pattern = nums.map((num) => bucketLabel(num, positionBoundaries)).join('-');
      patternCounts[pattern] = (patternCounts[pattern] || 0) + 1;
    });
    return Object.entries(patternCounts)
      .map(([pattern, count]) => ({ pattern, count }))
      .sort((a, b) => b.count - a.count);
  }

  // 直近n回の出現回数から、tierRulesの各階層に属する数字を{number,count}のリストに分ける。
  function calcTierPools(draws, { mainKey, tierRules = DEFAULT_TIER_RULES }, n = 24) {
    const { countMap } = countRecentNumbers(draws, mainKey, n);
    const pools = {};
    tierRules.forEach((t) => {
      pools[t.label] = [];
    });
    Object.entries(countMap).forEach(([numStr, count]) => {
      const num = Number(numStr);
      const label = classifyByTier(count, tierRules);
      pools[label].push({ number: num, count });
    });
    return pools;
  }

  // 各数字が「各位の出現回数TOP5」の中で何位に入っているかを加点方式でスコア化する
  // （1位=5点〜5位=1点、複数の位のTOP5に入っていれば合算）。
  // S数字・A数字の候補が選定枠より多いときのタイブレークに使う。
  function calcPositionScore(digitTop5) {
    const score = {};
    digitTop5.forEach((pos) => {
      pos.top.forEach((item, idx) => {
        score[item.number] = (score[item.number] || 0) + (5 - idx);
      });
    });
    return score;
  }

  // 間隔バランス度（山型スコア、0〜1）：直近n回の中で「最後に出現してから何回目か」を
  // 理論上の平均間隔と比較する。出た直後（間隔が短すぎる＝連続気味）は低評価、
  // 程よい間隔でピーク、長期未出現は頭打ちにして過大評価しない。
  // 「出現回数が多い数字＝また出る」という単純な発想を避け、出現パターンの
  // バランスで優先順位を付けるための指標（S/A分類自体は出現回数のまま変更しない）。
  function calcGapBalanceScore(draws, { mainKey, maxNumber, mainCount }, n = 24) {
    const recent = draws.slice(-n);
    const windowLen = recent.length;
    const expectedGap = maxNumber / mainCount;

    const lastSeenIndex = {}; // number -> 0(直近)〜windowLen-1
    for (let i = windowLen - 1; i >= 0; i--) {
      const sinceLatest = windowLen - 1 - i;
      getMainNumbers(recent[i], mainKey).forEach((num) => {
        if (lastSeenIndex[num] === undefined) lastSeenIndex[num] = sinceLatest;
      });
    }

    const score = {};
    for (let num = 1; num <= maxNumber; num++) {
      const gap = lastSeenIndex[num] !== undefined ? lastSeenIndex[num] : windowLen;
      const ratio = expectedGap > 0 ? gap / expectedGap : 0;
      let s;
      if (ratio < 0.5) {
        s = (ratio / 0.5) * 0.4;
      } else if (ratio <= 1.8) {
        s = 0.4 + 0.6 * (1 - Math.abs(ratio - 1.15) / 0.65);
      } else if (ratio <= 3.5) {
        s = 1.0 - (0.3 * (ratio - 1.8)) / 1.7;
      } else {
        s = 0.55;
      }
      score[num] = Math.max(0, Math.min(1, s));
    }
    return score;
  }

  // 3分割バランス度（0〜1）：直近n回を3等分（直近セグメント・中間セグメント・古いセグメント）
  // し、出現が特定の1セグメントに偏っている数字（例：直近セグメントだけに集中＝頭打ちの
  // 可能性）を相対的に低く評価する。3セグメントに均等に出現している数字ほど高スコア。
  // calcGapBalanceScoreは「最後に出た1回」だけを見るのに対し、こちらは出現回数の
  // 時系列での分布そのものを見るための指標。
  function calcSegmentBalanceScore(draws, { mainKey, maxNumber }, n = 24) {
    const recent = draws.slice(-n);
    const segLen = Math.floor(recent.length / 3);
    const segments =
      segLen > 0
        ? [
            recent.slice(recent.length - segLen), // 直近セグメント
            recent.slice(recent.length - segLen * 2, recent.length - segLen), // 中間セグメント
            recent.slice(recent.length - segLen * 3, recent.length - segLen * 2), // 古いセグメント
          ]
        : [recent, [], []];

    const score = {};
    for (let num = 1; num <= maxNumber; num++) {
      const segCounts = segments.map((seg) => seg.filter((d) => getMainNumbers(d, mainKey).includes(num)).length);
      const total = segCounts.reduce((a, b) => a + b, 0);
      if (total === 0) {
        score[num] = 0.5; // 未出現はどちらとも言えないため中立
        continue;
      }
      const idealShare = 1 / 3;
      const maxShare = Math.max(...segCounts) / total;
      const penalty = Math.max(0, (maxShare - idealShare) / (1 - idealShare));
      score[num] = Math.max(0, Math.min(1, 1 - penalty));
    }
    return score;
  }

  // nCr（組み合わせの数）。厳選数字による当選確率の改善度を示すために使用。
  function combinations(n, r) {
    if (r < 0 || r > n) return 0;
    let result = 1;
    for (let i = 0; i < r; i++) {
      result = (result * (n - i)) / (i + 1);
    }
    return Math.round(result);
  }

  // 厳選数字（1軍・2軍）・削除数字の選定。
  // 引っ張り数字（直近1回の当せん番号）は、ひっぱり率が直近n回で7割前後と高く、
  // 「直近すぎるから除外」は統計的に不合理なため、階層やスコアに関わらず必ず
  // 厳選数字に含める（実際に買うかどうかは読者の判断に委ねる）。
  // 残りの枠はS数字とA・B数字を、実際の候補数の比率でselectedCountに按分する
  // （SだけでもA・BだけでもなくSAの割合で按分、という考え方）。A数字とB数字は
  // 階層の壁で区切らず横断的に競わせ、出現回数が少なくても間隔的に「そろそろ
  // 来そう」なB数字が割って入る余地を持たせる。
  // 候補が枠より多い場合のタイブレークは「出現回数」を使わず、「間隔バランス度
  // （最後に出てから何回目か）」＋「3分割バランス度（直近8回・中8回・古8回の
  // 出現の偏り。特定セグメントに偏っている＝頭打ちの可能性を減点）」の合算スコア
  // →「位別ランキングスコア」→「数字が小さい方」の順。出現回数は既にS/A/B分類
  // そのものに使っているため、タイブレークにも使うと「直近よく出ている数字を
  // 選ぶ」だけになってしまい、抽せんが毎回独立しているという前提と矛盾するため
  // 採用しない。
  function calcSelectedNumbers(draws, config, n = 24) {
    const { mainKey, maxNumber, selectedCount, tierRules = DEFAULT_TIER_RULES } = config;
    const pools = calcTierPools(draws, { mainKey, tierRules }, n);
    const topLabel = tierRules[0].label; // 例: S
    const secondaryLabels = tierRules.slice(1).map((t) => t.label); // 例: [A, B]
    const secondaryLabel = secondaryLabels[0] || topLabel; // tierPicksのキー・表示上の「2軍」ラベル

    const digitTop5 = calcDigitPositionTop5(draws, config, n, 5);
    const positionScore = calcPositionScore(digitTop5);
    const gapBalance = calcGapBalanceScore(draws, config, n);
    const segmentBalance = calcSegmentBalanceScore(draws, config, n);

    function combinedScore(num) {
      return (gapBalance[num] || 0) + (segmentBalance[num] || 0);
    }

    function sortCandidates(list) {
      return [...list].sort(
        (a, b) =>
          combinedScore(b.number) - combinedScore(a.number) ||
          (positionScore[b.number] || 0) - (positionScore[a.number] || 0) ||
          a.number - b.number
      );
    }

    const numberToTier = {};
    Object.entries(pools).forEach(([label, list]) => {
      list.forEach((c) => {
        numberToTier[c.number] = label;
      });
    });

    const selectedSet = new Set();

    // 引っ張り数字を無条件で確保する
    const latestDraw = draws[draws.length - 1];
    if (latestDraw) {
      getMainNumbers(latestDraw, mainKey).forEach((num) => {
        if (selectedSet.size < selectedCount) selectedSet.add(num);
      });
    }

    const sPoolRemaining = (pools[topLabel] || []).filter((c) => !selectedSet.has(c.number));
    const secondaryPoolRemaining = secondaryLabels
      .flatMap((label) => pools[label] || [])
      .filter((c) => !selectedSet.has(c.number));

    const totalRemainingCandidates = sPoolRemaining.length + secondaryPoolRemaining.length;
    let remaining = Math.max(selectedCount - selectedSet.size, 0);

    const sSlot =
      totalRemainingCandidates > 0
        ? Math.min(Math.round((selectedCount * sPoolRemaining.length) / totalRemainingCandidates), remaining)
        : 0;
    sortCandidates(sPoolRemaining)
      .slice(0, sSlot)
      .forEach((c) => selectedSet.add(c.number));
    remaining = Math.max(selectedCount - selectedSet.size, 0);

    sortCandidates(secondaryPoolRemaining)
      .slice(0, remaining)
      .forEach((c) => selectedSet.add(c.number));

    const tierPicks = { [topLabel]: [], [secondaryLabel]: [] };
    selectedSet.forEach((num) => {
      const bucket = numberToTier[num] === topLabel ? topLabel : secondaryLabel;
      tierPicks[bucket].push(num);
    });

    const cut = [];
    for (let num = 1; num <= maxNumber; num++) {
      if (!selectedSet.has(num)) cut.push(num);
    }

    const oddsBase = combinations(maxNumber, config.mainCount);
    const oddsSelected = combinations(selectedSet.size, config.mainCount);
    const oddsImprovement = oddsSelected > 0 ? Math.round((oddsBase / oddsSelected) * 10) / 10 : null;

    return {
      tierLabels: [topLabel, secondaryLabel], // ['S','A'] -> 1軍/2軍の順
      tierPicks, // { S:[...], A:[...] }
      selected: [...selectedSet].sort((a, b) => a - b),
      cut,
      selectedCount: selectedSet.size,
      maxNumber,
      mainCount: config.mainCount,
      oddsBase,
      oddsSelected,
      oddsImprovement,
    };
  }

  // 厳選数字（1軍・2軍）を位グループ別に、数字の小さい順でまとめる。
  // 厳選数字は1軍/2軍という独自の括りであり、S数字/A数字の分類とは表示上区別する
  // （内部の選定計算にはS/A階層を使うが、この関数の出力にはS/Aのラベルを含めない）。
  function groupSelectionByPosition(selection, positionBoundaries = DEFAULT_POSITION_BOUNDARIES) {
    const posLabels = positionLabelsFor(positionBoundaries);
    const groups = posLabels.map((label) => ({ label, items: [] }));
    selection.tierLabels.forEach((tierLabel, tierIndex) => {
      (selection.tierPicks[tierLabel] || []).forEach((num) => {
        const posIndex = posLabels.indexOf(`${bucketLabel(num, positionBoundaries)}の位`);
        groups[posIndex].items.push({ number: num, tierIndex });
      });
    });
    groups.forEach((g) => g.items.sort((a, b) => a.number - b.number));
    return groups;
  }

  // 当選検証：最新回を除いたデータで厳選数字を再計算し、
  // 実際の最新回の当選番号が全て厳選数字に含まれていたかを検証する。
  function calcSelectionVerification(draws, config, n = 24) {
    if (draws.length < 2) return null;
    const priorDraws = draws.slice(0, -1);
    const latest = draws[draws.length - 1];
    const selection = calcSelectedNumbers(priorDraws, config, n);
    const latestNumbers = [...getMainNumbers(latest, config.mainKey)].sort((a, b) => a - b);
    const latestBonusNumbers = [...(latest[config.bonusKey] || [])].sort((a, b) => a - b);
    const selectedSet = new Set(selection.selected);
    const coveredNumbers = latestNumbers.filter((num) => selectedSet.has(num));
    const missedNumbers = latestNumbers.filter((num) => !selectedSet.has(num));
    const coveredBonusNumbers = latestBonusNumbers.filter((num) => selectedSet.has(num));
    const missedBonusNumbers = latestBonusNumbers.filter((num) => !selectedSet.has(num));
    const allCovered = missedNumbers.length === 0;
    // 2等相当：本数字が(mainCount-1)個一致し、かつボーナス数字を少なくとも1個含む場合、
    // 選び方次第で2等相当（1個少ないがボーナス的中）が狙えた可能性がある。
    const secondPrizePossible =
      !allCovered && coveredNumbers.length === config.mainCount - 1 && coveredBonusNumbers.length > 0;
    return {
      round: latest.回号,
      date: latest.日付,
      latestNumbers,
      latestBonusNumbers,
      selectedCount: selection.selectedCount,
      coveredNumbers,
      missedNumbers,
      coveredBonusNumbers,
      missedBonusNumbers,
      allCovered,
      secondPrizePossible,
    };
  }

  return {
    DEFAULT_TIER_RULES,
    DEFAULT_POSITION_BOUNDARIES,
    sortByRound,
    parseCsv,
    csvRowsToDraws,
    loadDrawsFromCsv,
    calcFrequency,
    calcCurrentIntervals,
    calcRecentTrend,
    calcTierAnalysis,
    calcNumberRanks,
    getRoundRange,
    calcTierPositionGroups,
    calcPositionTop5,
    calcDigitPositionTop5,
    calcPositionFrequency,
    calcConsecutivePairs,
    calcPatternAnalysis,
    calcGapBalanceScore,
    calcSelectedNumbers,
    groupSelectionByPosition,
    calcSelectionVerification,
  };
})();
