import streamlit as st
from PIL import Image

st.set_page_config(page_title="宝くじAI予想", layout="wide")

# ✅ ヘッダー画像
st.image("https://raw.githubusercontent.com/Naobro/lototop-app/main/header.png", use_container_width=True)

# タイトル・説明
st.markdown("## 🎯 NAOKIの宝くじAI予想")
st.markdown("データ分析＋AIで宝くじ予想")

# サイトの目的（NAOKIの思いを反映）
st.markdown("### 🎯 当サイトの目的（開設の想い）")
st.markdown("""
このサイトは、**4年間・毎日宝くじを買い続けてきた男「NAOKI」**の集大成として誕生しました。

これまでに、
- **ロト7で3等（80万円）**
- **ナンバーズ4でストレート2回的中**

などの実績を積み上げ、**半年以上かけて構築したAI×統計の宝くじ予想サイト**です。  
直近24回の出現傾向、ABC分類、連続数字、そして自作のファクターを組み合わせ、（今後50回など拡張予定）
少しでも当選確率を上げるための「選択の材料」を提供しています。

---

st.markdown("""
🔥 **ロト1等当選 → FIRE を本気で目指す方へ**

私は、  
<span style='color:#e63946; font-weight:bold; font-size:20px;'>
選択式宝くじは「99% 分析・統計、1% 運」
</span>  
だと考えています。
""", unsafe_allow_html=True)


**A/B数字の傾向を軸に選ぶ**ことが多く、  
「ただ買う」のではなく、「根拠を持って買う」ことが最短ルートです。

---

このサイトが、  
📈 **あなたの“買うべき数字”を決める一つの材料**になれば嬉しいです。
""")

# 高額当選実績
st.markdown("### 💰 高額当選実績")
st.markdown("""
- **2022年4月8日** ロト7 3等　➡️ **801,300円**  
- **2024年10月4日** ナンバーズ4 0784 セットストレート　➡️ **558,000円**
- **2025年4月23日** ナンバーズ4 7059 セットストレート　➡️ **583,400円**
""")

# 各ページリンク
st.markdown("### 🔗 各予想ページへ")
st.markdown("""
📄 **コンテンツ内容**
- 当選番号
- 直近24回の当選番号
- 出現傾向・パターン分析
- 各位の出現回数TOP5
- 各数字の出現回数TOP5
- ABC分類
- 基本予想
- セレクト予想
            
""")

# ✅ 会員専用ページへのリンク（マルチページ用）
st.markdown("### 🔐 会員専用ページ（月額予想サブスク）")
st.page_link("pages/member.py", label="🔐 会員ページはこちら", icon="🔐")

# 今だけ無料案内とLINE誘導
st.markdown("### 🟢 今だけ無料！LINEでパスワードをGET")
st.markdown("""
このページに来てくれたあなたには、**今だけ無料で限定予想を公開中！**

以下のLINEから登録するだけで、今月のパスワードが届きます。
""")

# ✅ LINE登録ボタン（スマホ対応）
st.markdown("""
<a href="https://lin.ee/uCn26Ig">
  <img src="https://scdn.line-apps.com/n/line_add_friends/btn/ja.png" alt="友だち追加" height="36" border="0">
</a>
""", unsafe_allow_html=True)

# ✅ QRコード画像をGitHubから表示
st.image("https://raw.githubusercontent.com/Naobro/lototop-app/main/L_gainfriends_2dbarcodes_GW.png", caption="QRコードからも登録できます", width=180)
# 限定ページリンク
st.markdown("""
🔐 [➡ 限定予想ページはこちら（パスワード入力）](https://naoloto-win.streamlit.app/member)
""")


st.markdown("### 💡 今後　サブスク & 単発予想販売（予定）")
st.markdown("""
- ✅ 単発予想：200円 / 回（Noteにて販売予定）  
- ✅ 月額サブスク：プラン　500円 
""")

# SNSリンク
st.markdown("### 📣 最新情報はこちらから")
st.markdown("""
- 🐦 [X（旧Twitter）ギャンブル全般呟いてます](https://x.com/naobillionaire?s=21&t=KpcTrZ6ZAmmyanT1g9425Q)  
- 📘 [Noteはこちら](https://note.com/naobillion)
""")

# 注意事項
st.markdown("---")
st.markdown("### 📝 ご利用にあたっての注意事項")
st.markdown("""
- 本予想は **100%の当選を保証するものではありません**。  
- 宝くじの購入は **すべて自己責任**でお願いします。  
- 情報を利用したことによる **損害の賠償責任は一切負いません**。  
- 的中する場合もあれば外れる場合もあります。**参考程度**にご活用ください。
""")

# 確率改善表
st.markdown("### 📊 削除法による確率イメージ（参考）")
st.markdown("""
実際に削除法を使った場合、**当せん確率がどれほど改善されるか？**  
以下にロト各種での比較イメージを載せています。
""")
st.markdown("""
| 宝くじ種別 | 通常の1等当せん確率 | 数字削除後の選択 | 絞込み後の通り数 | 改善後の確率（目安） |
|:-----------|:----------------------|:------------------|:------------------|:-------------------|
| ロト6       | 約1/6,096,454         | 43→20個から6個選 | 約38,760通り      | 約1/38,760         |
| ロト7       | 約1/10,295,472        | 37→20個から7個選 | 約77,520通り      | 約1/77,520         |
| ミニロト     | 約1/169,911           | 31→15個から5個選 | 約3,003通り       | 約1/3,003          |
""")