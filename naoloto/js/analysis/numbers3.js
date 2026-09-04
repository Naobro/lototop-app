/* ============================================================
   ナンバーズ3 分析ページ 初期化処理
   GitHub上のCSV（tousen.pyが更新するdata/numbers3_24.csv）を直接読み込み、
   NumbersStats で集計し、NumbersRender で描画する。
   tousen.pyで保存・GitHub反映すると、次回読み込み時に自動的に反映される。
   ============================================================ */
(async function () {
  const CONFIG = {
    gameName: 'ナンバーズ3',
    mainKey: '本数字',
    digitCount: 3,
    dataUrl: 'https://raw.githubusercontent.com/Naobro/lototop-app/main/data/numbers3_24.csv',
    dataFileName: 'tousen.py（ナンバーズ3）',
    csvOptions: {
      mainCols: ['第1数字', '第2数字', '第3数字'],
      bonusCols: [],
    },
    tierN: 24,
    tierRules: LotoStats.DEFAULT_TIER_RULES,
  };

  const ids = [
    'latest-draw',
    'tier-history-table',
    'reference-info',
    'digit-frequency-table',
    'digit-interval-table',
    'digit-top5-table',
    'parity-summary',
    'sum-distribution',
    'sum-frequency-table',
    'repeat-pattern-summary',
    'pull-count',
    'range-distribution',
    'digit-pair-ranking',
    'prediction-numbers',
    'verification',
  ];

  function getEl(id) {
    return document.getElementById(id);
  }

  function showEmptyEverywhere(message) {
    ids.forEach((id) => {
      const c = getEl(id);
      if (c) NumbersRender.emptyState(c, message);
    });
  }

  try {
    const draws = await LotoStats.loadDrawsFromCsv(CONFIG.dataUrl, CONFIG.csvOptions);
    const latest = draws.length ? draws[draws.length - 1] : null;

    NumbersRender.renderLatestDraw(getEl('latest-draw'), latest, CONFIG);

    if (draws.length === 0) {
      showEmptyEverywhere(`データがありません。${CONFIG.dataFileName} で当選番号を追加してください。`);
      return;
    }

    const tierHistory = NumbersStats.calcTierAnnotatedHistory(draws, CONFIG, CONFIG.tierN, CONFIG.tierRules);
    NumbersRender.renderTierAnnotatedHistoryTable(getEl('tier-history-table'), tierHistory);

    const digitFrequency = NumbersStats.calcDigitFrequency(draws, CONFIG, CONFIG.tierN);
    NumbersRender.renderDigitFrequencyTable(getEl('digit-frequency-table'), digitFrequency, CONFIG.tierN);

    const digitIntervals = NumbersStats.calcDigitIntervals(draws, CONFIG);
    NumbersRender.renderDigitIntervalTable(getEl('digit-interval-table'), digitIntervals);

    const digitTop5 = NumbersStats.calcDigitTop5(draws, CONFIG, CONFIG.tierN, 5);
    NumbersRender.renderDigitTop5Table(getEl('digit-top5-table'), digitTop5, CONFIG.tierN);

    NumbersRender.renderReferenceInfo(getEl('reference-info'), { digitTop5, digitIntervals, n: CONFIG.tierN });

    const parity = NumbersStats.calcParitySummary(draws, CONFIG, CONFIG.tierN);
    NumbersRender.renderParitySummary(getEl('parity-summary'), parity);

    const sumDistribution = NumbersStats.calcSumDistribution(draws, CONFIG, CONFIG.tierN, 4);
    NumbersRender.renderSumDistribution(getEl('sum-distribution'), sumDistribution);

    const sumFrequency = NumbersStats.calcSumFrequency(draws, CONFIG, CONFIG.tierN);
    NumbersRender.renderSumFrequency(getEl('sum-frequency-table'), sumFrequency, CONFIG.tierN);

    const repeatPattern = NumbersStats.calcRepeatPatternSummary(draws, CONFIG, CONFIG.tierN);
    NumbersRender.renderRepeatPatternSummary(getEl('repeat-pattern-summary'), repeatPattern);

    const pull = NumbersStats.calcPullCount(draws, CONFIG, CONFIG.tierN);
    NumbersRender.renderPullCount(getEl('pull-count'), pull);

    const rangeDistribution = NumbersStats.calcRangeDistribution(draws, CONFIG, CONFIG.tierN);
    NumbersRender.renderRangeDistribution(getEl('range-distribution'), rangeDistribution);

    const digitPairRanking = NumbersStats.calcDigitPairRanking(draws, CONFIG, CONFIG.tierN, 15);
    NumbersRender.renderDigitPairRanking(getEl('digit-pair-ranking'), digitPairRanking, CONFIG.tierN);

    NumbersRender.renderPredictionNumbers(getEl('prediction-numbers'), digitTop5, CONFIG.tierN);

    const verification = NumbersStats.calcVerification(draws, CONFIG, CONFIG.tierN, 5);
    NumbersRender.renderVerification(getEl('verification'), verification, CONFIG.digitCount);

    LotoRender.setupCopyButton('copy-prediction-btn', 'copy-prediction-status', [
      'prediction-numbers-section',
      'reference-info-section',
    ]);
    LotoRender.setupCopyButton('copy-verification-btn', 'copy-verification-status', ['verification-section']);
  } catch (err) {
    console.error(err);
    showEmptyEverywhere(`読み込みエラー: ${err.message}`);
  }
})();
