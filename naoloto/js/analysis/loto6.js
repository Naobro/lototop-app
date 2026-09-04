/* ============================================================
   ロト6 分析ページ 初期化処理
   data/loto6.json を読み込み、LotoStats で集計し、LotoRender で描画する。
   ロト7版（loto7.js）と同一の構成。ゲーム固有の設定はCONFIGのみで管理する。
   ============================================================ */
(async function () {
  const CONFIG = {
    gameName: 'ロト6',
    maxNumber: 43,
    mainKey: '本数字',
    bonusKey: 'ボーナス数字',
    mainCount: 6,
    positionBoundaries: [1, 10, 20, 30],
    dataUrl: '../../data/loto6.json',
    dataFileName: 'data/loto6.json',
    tierN: 24,
    tierRules: LotoStats.DEFAULT_TIER_RULES,
    selectedCount: 30,
  };

  const ids = [
    'latest-draw',
    'frequency-table',
    'interval-table',
    'number-grid',
    'reference-info',
    'abc-table',
    'pull-consecutive-summary',
    'consecutive-pairs-table',
    'pattern-table',
    'tier-position-groups',
    'position-top5',
    'digit-position-top5',
    'position-heatmap',
    'selected-numbers',
    'prediction-patterns',
    'selection-verification',
  ];

  function getEl(id) {
    return document.getElementById(id);
  }

  async function loadDraws(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`データの読み込みに失敗しました（HTTP ${res.status}）`);
    const raw = await res.json();
    return LotoStats.sortByRound(raw);
  }

  function showEmptyEverywhere(message) {
    ids.forEach((id) => {
      const c = getEl(id);
      if (c) LotoRender.emptyState(c, message);
    });
  }

  try {
    const draws = await loadDraws(CONFIG.dataUrl);
    const latest = draws.length ? draws[draws.length - 1] : null;

    LotoRender.renderLatestDraw(getEl('latest-draw'), latest, CONFIG);

    if (draws.length === 0) {
      showEmptyEverywhere(`データがありません。${CONFIG.dataFileName} に当選番号を追加してください。`);
      return;
    }

    // getRoundRange は「しばらく出ていない数字TOP5」の注記（収録データの範囲表示）で使用する。
    const range = LotoStats.getRoundRange(draws);

    // 出現率・出現回数グリッドは直近tierN回を基準に統一する。
    // 出現間隔（intervalArr）のみ、経過回数を正確に把握するため収録データ（保有データ）を使う例外。
    const recent = LotoStats.calcRecentTrend(draws, CONFIG.tierN, CONFIG);
    const freq = recent.frequency;
    LotoRender.renderFrequencyTable(getEl('frequency-table'), freq);

    const intervalArr = LotoStats.calcCurrentIntervals(draws, CONFIG);
    LotoRender.renderIntervalTable(getEl('interval-table'), intervalArr);

    const rankedFreq = LotoStats.calcNumberRanks(freq);
    LotoRender.renderNumberGrid(getEl('number-grid'), rankedFreq);

    LotoRender.renderReferenceInfo(getEl('reference-info'), {
      intervalArr,
      recentFreq: freq,
      recentN: CONFIG.tierN,
      roundRange: range,
      gameName: CONFIG.gameName,
    });

    const tierAnalysis = LotoStats.calcTierAnalysis(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderTierTable(getEl('abc-table'), tierAnalysis);
    LotoRender.renderPullConsecutiveSummary(getEl('pull-consecutive-summary'), tierAnalysis.summary, tierAnalysis.n);

    const tierPositionGroups = LotoStats.calcTierPositionGroups(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderTierPositionGroupsTable(getEl('tier-position-groups'), tierPositionGroups, CONFIG.tierN);

    const positionTop5 = LotoStats.calcPositionTop5(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderPositionTop5Table(getEl('position-top5'), positionTop5, CONFIG.tierN);

    const digitPositionTop5 = LotoStats.calcDigitPositionTop5(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderDigitPositionTop5Table(getEl('digit-position-top5'), digitPositionTop5, CONFIG.tierN);

    const positionFrequency = LotoStats.calcPositionFrequency(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderPositionHeatmap(getEl('position-heatmap'), positionFrequency);

    const consecutivePairs = LotoStats.calcConsecutivePairs(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderConsecutivePairsTable(getEl('consecutive-pairs-table'), consecutivePairs);

    const patternAnalysis = LotoStats.calcPatternAnalysis(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderPatternTable(getEl('pattern-table'), patternAnalysis, CONFIG);

    const selection = LotoStats.calcSelectedNumbers(draws, CONFIG, CONFIG.tierN);
    const selectionByPosition = LotoStats.groupSelectionByPosition(selection, CONFIG.positionBoundaries);
    LotoRender.renderSelectedNumbers(getEl('selected-numbers'), selection, selectionByPosition, CONFIG.tierN);

    LotoRender.renderPredictionPatterns(getEl('prediction-patterns'), patternAnalysis, CONFIG.tierN, 10);

    const verification = LotoStats.calcSelectionVerification(draws, CONFIG, CONFIG.tierN);
    LotoRender.renderSelectionVerification(getEl('selection-verification'), verification);

    LotoRender.setupCopyButton('copy-prediction-btn', 'copy-prediction-status', [
      'selected-numbers-section',
      'prediction-patterns-section',
    ]);
    LotoRender.setupCopyButton('copy-verification-btn', 'copy-verification-status', ['selection-verification-section']);
  } catch (err) {
    console.error(err);
    showEmptyEverywhere(`読み込みエラー: ${err.message}`);
  }
})();
