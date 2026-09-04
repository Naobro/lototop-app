/* ============================================================
   NumbersStats
   ナンバーズ3・ナンバーズ4共通の集計ロジック。
   draws は { 回号, 日付, 本数字:[...] } の配列を想定し、回号の昇順で渡すこと。
   本数字は「桁の位置が固定・重複あり」（例: 1,1,7 も有効）という点で
   ロト系（数字プールから複数個選ぶ・重複なし）とは根本的に異なるため、
   桁を並べ替えたりプール化したりしない。
   ============================================================ */
const NumbersStats = (function () {
  function getDigits(draw, mainKey) {
    return draw[mainKey] || [];
  }

  function pct(part, total) {
    return total > 0 ? Math.round((part / total) * 1000) / 10 : 0;
  }

  // 各桁（位置）ごとに、直近n回で各数字(0〜9)が何回出現したかを集計する
  function calcDigitFrequency(draws, { mainKey, digitCount }, n = 24) {
    const recent = draws.slice(-n);
    const positions = [];
    for (let pos = 0; pos < digitCount; pos++) {
      const counts = new Array(10).fill(0);
      recent.forEach((d) => {
        const v = getDigits(d, mainKey)[pos];
        if (v !== undefined) counts[v] += 1;
      });
      const frequency = [];
      for (let digit = 0; digit <= 9; digit++) {
        frequency.push({ digit, count: counts[digit], rate: pct(counts[digit], recent.length) });
      }
      positions.push({ position: pos + 1, frequency });
    }
    return { n: recent.length, positions };
  }

  // 各桁の現在の出現間隔（最新回から何回前に、その桁にその数字が出たか。0=今回、nullは未出現）
  function calcDigitIntervals(draws, { mainKey, digitCount }) {
    const positions = [];
    for (let pos = 0; pos < digitCount; pos++) {
      const lastSeen = {};
      for (let d = 0; d <= 9; d++) lastSeen[d] = null;
      for (let i = draws.length - 1; i >= 0; i--) {
        const sinceLatest = draws.length - 1 - i;
        const v = getDigits(draws[i], mainKey)[pos];
        if (v !== undefined && lastSeen[v] === null) lastSeen[v] = sinceLatest;
      }
      const intervals = [];
      for (let d = 0; d <= 9; d++) intervals.push({ digit: d, interval: lastSeen[d] });
      positions.push({ position: pos + 1, intervals });
    }
    return positions;
  }

  // 各桁の出現回数TOP5（直近n回）
  function calcDigitTop5(draws, config, n = 24, topN = 5) {
    const freq = calcDigitFrequency(draws, config, n);
    return freq.positions.map((p) => ({
      position: p.position,
      top: [...p.frequency].sort((a, b) => b.count - a.count || a.digit - b.digit).slice(0, topN),
    }));
  }

  // 各桁・各数字の出現間隔バランススコア（ロトのcalcGapBalanceScoreと同じ考え方の曲線）。
  // 桁は0〜9の10通りから1つ選ばれるため、期待間隔は10回とする。
  // 戻り値: 位置ごとのスコアmap配列 [ {0:score,...,9:score}, ... ]
  function calcDigitGapBalanceScore(draws, { mainKey, digitCount }, n = 24) {
    const recent = draws.slice(-n);
    const windowLen = recent.length;
    const expectedGap = 10;

    const positions = [];
    for (let pos = 0; pos < digitCount; pos++) {
      const lastSeenIndex = {};
      for (let i = windowLen - 1; i >= 0; i--) {
        const sinceLatest = windowLen - 1 - i;
        const v = getDigits(recent[i], mainKey)[pos];
        if (v !== undefined && lastSeenIndex[v] === undefined) lastSeenIndex[v] = sinceLatest;
      }
      const score = {};
      for (let digit = 0; digit <= 9; digit++) {
        const gap = lastSeenIndex[digit] !== undefined ? lastSeenIndex[digit] : windowLen;
        const ratio = gap / expectedGap;
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
        score[digit] = Math.max(0, Math.min(1, s));
      }
      positions.push(score);
    }
    return positions;
  }

  // 予想数字（各桁TOP5）：単純な出現回数順ではなく、SAB階層（出現回数ベース）を優先して
  // 候補を絞り込み、同階層内では出現間隔バランスの良い数字を優先する
  // （ロトの厳選数字選定と同じ考え方。単に直近の出現回数が多い数字を並べるだけだと、
  // 出現が直近に偏っている数字ばかりを選ぶことになり矛盾するため）。
  // S数字はSCAP個までに制限し、S一色にならないようにする（S:A比率が3:2、2:3、
  // あるいはB数字も混じって2:2:1・3:1:1などになるのが自然になるように）。
  // 残りの枠はA数字・B数字を階層の壁で区切らず横断的に競わせる。
  // calcDigitTop5（純粋な出現回数ランキング、統計表示用）とは用途が異なる。
  function calcDigitPrediction(draws, config, n = 24, topN = 5) {
    const { tierRules } = config;
    const SCAP = 3;
    const freq = calcDigitFrequency(draws, config, n);
    const tierMaps = calcDigitTierMap(draws, config, n, tierRules);
    const gapScores = calcDigitGapBalanceScore(draws, config, n);
    const topLabel = tierRules[0].label; // 例: S
    const secondaryLabels = tierRules.slice(1).map((t) => t.label); // 例: [A, B]

    return freq.positions.map((p, pos) => {
      const tierMap = tierMaps[pos];
      const gapScore = gapScores[pos];

      function sortCandidates(list) {
        return [...list].sort((a, b) => (gapScore[b.digit] || 0) - (gapScore[a.digit] || 0) || a.digit - b.digit);
      }

      const pools = {};
      tierRules.forEach((t) => {
        pools[t.label] = [];
      });
      p.frequency.forEach((f) => {
        pools[tierMap[f.digit]].push(f);
      });

      const sPicked = sortCandidates(pools[topLabel] || []).slice(0, Math.min(SCAP, topN));

      const remaining = topN - sPicked.length;
      const secondaryPool = secondaryLabels.flatMap((label) => pools[label] || []);
      const secondaryPicked = sortCandidates(secondaryPool).slice(0, remaining);

      return { position: p.position, top: [...sPicked, ...secondaryPicked] };
    });
  }

  // 数字合計（各桁の合計値）の分布（直近n回、binCount等分レンジ）
  function calcSumDistribution(draws, { mainKey, digitCount }, n = 24, binCount = 4) {
    const recent = draws.slice(-n);
    const maxSum = digitCount * 9;
    const sums = recent.map((d) => getDigits(d, mainKey).reduce((a, b) => a + b, 0));
    const edges = [];
    for (let i = 0; i <= binCount; i++) edges.push(Math.round((maxSum * i) / binCount));
    const bins = [];
    for (let i = 0; i < binCount; i++) {
      const lo = i === 0 ? edges[i] : edges[i] + 1;
      const hi = edges[i + 1];
      const count = sums.filter((s) => s >= lo && s <= hi).length;
      bins.push({ label: `${lo}〜${hi}`, count });
    }
    return { n: recent.length, bins };
  }

  // 偶数・奇数分析：数字合計の偶奇比率、および桁ごとの偶数率（直近n回）
  function calcParitySummary(draws, { mainKey, digitCount }, n = 24) {
    const recent = draws.slice(-n);
    const perDigitEven = new Array(digitCount).fill(0);
    recent.forEach((d) => {
      getDigits(d, mainKey).forEach((v, i) => {
        if (v % 2 === 0) perDigitEven[i] += 1;
      });
    });
    return {
      n: recent.length,
      perDigitEvenRate: perDigitEven.map((c, i) => ({ position: i + 1, evenRate: pct(c, recent.length) })),
    };
  }

  // 出現回数からtierRulesに沿って階層ラベルを1つ決定する（ロト系と同じ考え方）
  function classifyDigitTier(count, tierRules) {
    for (const tier of tierRules) {
      if (count >= tier.minCount) return tier.label;
    }
    return tierRules[tierRules.length - 1].label;
  }

  // 直近n回について、桁の位置ごとに数字0〜9それぞれの出現回数を集計し、SAB階層を決定する。
  // 位置をまたいで合算すると出現数が過大になりS/Bの差が付かないため、必ず桁ごとに独立集計する
  // （ロトのS/A/B分類と同じ閾値。tierRulesはLotoStats.DEFAULT_TIER_RULES等を渡す）。
  // 戻り値: 位置ごとのtierMap配列（positionTierMaps[position][digit] = 'S'|'A'|'B'）
  function calcDigitTierMap(draws, { mainKey, digitCount }, n = 24, tierRules) {
    const recent = draws.slice(-n);
    const positionTierMaps = [];
    for (let pos = 0; pos < digitCount; pos++) {
      const counts = new Array(10).fill(0);
      recent.forEach((d) => {
        const v = getDigits(d, mainKey)[pos];
        if (v !== undefined) counts[v] += 1;
      });
      const tierMap = {};
      for (let digit = 0; digit <= 9; digit++) {
        tierMap[digit] = classifyDigitTier(counts[digit], tierRules);
      }
      positionTierMaps.push(tierMap);
    }
    return positionTierMaps;
  }

  // 直近n回の当選番号一覧に、桁ごとのSAB分類を付与する（桁の位置ごとに独立判定）
  function calcTierAnnotatedHistory(draws, { mainKey, digitCount }, n = 24, tierRules) {
    const recent = draws.slice(-n);
    const positionTierMaps = calcDigitTierMap(draws, { mainKey, digitCount }, n, tierRules);
    const rows = recent.map((d) => {
      const digits = getDigits(d, mainKey);
      return {
        回号: d.回号,
        日付: d.日付,
        digits,
        labels: digits.map((v, pos) => positionTierMaps[pos][v]),
      };
    });
    return { n: recent.length, rows };
  }

  // ひっぱり回数：直近n回のうち、前回と同じ数字（値）を1つ以上含む回の数
  function calcPullCount(draws, { mainKey }, n = 24) {
    const recent = draws.slice(-n);
    let pullCount = 0;
    for (let i = 1; i < recent.length; i++) {
      const cur = new Set(getDigits(recent[i], mainKey));
      const prev = new Set(getDigits(recent[i - 1], mainKey));
      const shared = [...cur].some((v) => prev.has(v));
      if (shared) pullCount += 1;
    }
    return { n: recent.length, pullCount, pullRate: pct(pullCount, recent.length - 1) };
  }

  // シングル・ダブル・トリプル（・ボックス=全桁同数字）の回数。
  // 各回の数字の中で最も多く重複した回数をもとに分類する。
  function calcRepeatPatternSummary(draws, { mainKey, digitCount }, n = 24) {
    const recent = draws.slice(-n);
    const counts = { single: 0, double: 0, triple: 0, quad: 0 };
    recent.forEach((d) => {
      const freq = {};
      getDigits(d, mainKey).forEach((v) => {
        freq[v] = (freq[v] || 0) + 1;
      });
      const maxRepeat = Math.max(...Object.values(freq));
      if (maxRepeat === 1) counts.single += 1;
      else if (maxRepeat === 2) counts.double += 1;
      else if (maxRepeat === 3) counts.triple += 1;
      else if (maxRepeat >= 4) counts.quad += 1;
    });
    const items = [
      { label: 'シングル', count: counts.single },
      { label: 'ダブル', count: counts.double },
      { label: 'トリプル', count: counts.triple },
    ];
    if (digitCount >= 4) items.push({ label: 'ボックス（4つ同数字）', count: counts.quad });
    return { n: recent.length, items };
  }

  // 数字の範囲ごとの分布：A(0-2)/B(3-5)/C(6-9)（全桁合算、直近n回）
  function calcRangeDistribution(draws, { mainKey }, n = 24) {
    const recent = draws.slice(-n);
    const ranges = [
      { label: 'A（0〜2）', lo: 0, hi: 2 },
      { label: 'B（3〜5）', lo: 3, hi: 5 },
      { label: 'C（6〜9）', lo: 6, hi: 9 },
    ];
    const counts = ranges.map(() => 0);
    recent.forEach((d) => {
      getDigits(d, mainKey).forEach((v) => {
        const idx = ranges.findIndex((r) => v >= r.lo && v <= r.hi);
        if (idx !== -1) counts[idx] += 1;
      });
    });
    return { n: recent.length, ranges: ranges.map((r, i) => ({ label: r.label, count: counts[i] })) };
  }

  // ペア出現：同じ回に含まれる数字（値）の2つ組の出現回数ランキング（同じ値同士のペアも含む）
  function calcDigitPairRanking(draws, { mainKey }, n = 24, topN = 15) {
    const recent = draws.slice(-n);
    const pairCounts = {};
    recent.forEach((d) => {
      const digits = getDigits(d, mainKey);
      for (let i = 0; i < digits.length; i++) {
        for (let j = i + 1; j < digits.length; j++) {
          const a = Math.min(digits[i], digits[j]);
          const b = Math.max(digits[i], digits[j]);
          const key = `${a}, ${b}`;
          pairCounts[key] = (pairCounts[key] || 0) + 1;
        }
      }
    });
    return Object.entries(pairCounts)
      .map(([pair, count]) => ({ pair, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, topN);
  }

  // 合計値の出現回数（レンジではなく、実際に出現した値ごとの回数）
  function calcSumFrequency(draws, { mainKey, digitCount }, n = 24) {
    const recent = draws.slice(-n);
    const maxSum = digitCount * 9;
    const counts = new Array(maxSum + 1).fill(0);
    recent.forEach((d) => {
      const sum = getDigits(d, mainKey).reduce((a, b) => a + b, 0);
      counts[sum] += 1;
    });
    const result = [];
    for (let s = 0; s <= maxSum; s++) {
      if (counts[s] > 0) result.push({ sum: s, count: counts[s] });
    }
    return result.sort((a, b) => b.count - a.count || a.sum - b.sum);
  }

  // 配列のすべての順列を返す（桁数が3〜4程度なので全探索で十分）
  function permutations(arr) {
    if (arr.length <= 1) return [arr];
    const result = [];
    arr.forEach((item, i) => {
      const rest = arr.slice(0, i).concat(arr.slice(i + 1));
      permutations(rest).forEach((p) => result.push([item, ...p]));
    });
    return result;
  }

  // 当選検証：最新回を除いたデータで各桁の予想数字（TOP5）を計算し、
  // 実際の最新回の当選番号がストレート・ボックス（・ミニ）で的中可能だったかを検証する。
  function calcVerification(draws, config, n = 24, topN = 5) {
    if (draws.length < 2) return null;
    const { mainKey, digitCount } = config;
    const priorDraws = draws.slice(0, -1);
    const latest = draws[draws.length - 1];

    const digitPrediction = calcDigitPrediction(priorDraws, config, n, topN);
    const candidateSets = digitPrediction.map((p) => new Set(p.top.map((x) => x.digit)));
    const actualDigits = getDigits(latest, mainKey);

    const straightHit = actualDigits.every((v, i) => candidateSets[i].has(v));

    let boxHit = false;
    for (const perm of permutations(actualDigits)) {
      if (perm.every((v, i) => candidateSets[i].has(v))) {
        boxHit = true;
        break;
      }
    }

    let miniHit = null;
    if (digitCount === 3) {
      // ミニ＝下2桁（第2数字・第3数字）がストレートで一致
      miniHit = candidateSets[1].has(actualDigits[1]) && candidateSets[2].has(actualDigits[2]);
    }

    return {
      round: latest.回号,
      date: latest.日付,
      actualDigits,
      candidateSets: candidateSets.map((s) => [...s].sort((a, b) => a - b)),
      straightHit,
      boxHit,
      miniHit,
    };
  }

  return {
    calcDigitFrequency,
    calcDigitIntervals,
    calcDigitTop5,
    calcDigitPrediction,
    calcSumDistribution,
    calcParitySummary,
    calcTierAnnotatedHistory,
    calcPullCount,
    calcRepeatPatternSummary,
    calcRangeDistribution,
    calcDigitPairRanking,
    calcSumFrequency,
    calcVerification,
  };
})();
