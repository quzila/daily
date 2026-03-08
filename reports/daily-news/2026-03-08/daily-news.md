# デイリーAI・半導体ニュース（2026-03-08）

## 今日のハイライト（3選）
> 1) 「Codex Security: now in research preview」が上位に入り、公式AI発の議論を通じて開発フロー最適化の重要性が改めて可視化された。
> 2) 「Introducing the Codex app」が上位に入り、公式AI発の議論を通じて開発フロー最適化の重要性が改めて可視化された。
> 3) 「GPT-5.4 is generally available in GitHub Copilot」が上位に入り、公式AI発の議論を通じて開発フロー最適化の重要性が改めて可視化された。

---

## AI ニュース

### 公式ソース

---
### 【カテゴリA: 公式ソース（AI）】Codex Security: now in research preview（公式AI, 2026-03-06）

**ひとことサマリー（1文）**: 公式AI の「Codex Security: now in research preview」では、OpenAIがアプリケーションセキュリティ向けのCodex Securityを研究プレビューで公開した。リポジトリから脅威モデルを作り、発見した脆弱性を検証しながら修正案まで返す流れを一体化している。ベータでは過去30日で120万超のコミットを走査し、792件のcriticalと10,561件のhighを検出したほか、あるケースではノイズを84%削減した。

**何が起きたか（What）**:  
公式AIの「Codex Security: now in research preview」は2026-03-06公開。OpenAIがアプリケーションセキュリティ向けのCodex Securityを研究プレビューで公開した。リポジトリから脅威モデルを作り、発見した脆弱性を検証しながら修正案まで返す流れを一体化している。ベータでは過去30日で120万超のコミットを走査し、792件のcriticalと10,561件のhighを検出したほか、あるケースではノイズを84%削減した。

**なぜ重要か（Why it matters）**:  
AIエージェントが実装速度を上げるほど、セキュリティレビューの誤検知と手戻りが新しいボトルネックになる。脅威モデルと自動検証を組み合わせて精度を上げる設計は、単純なルールベース診断より実務への組み込み余地が大きい。

**自分への影響（So what）**:  
自分の開発では、コード生成の前後でセキュリティ確認を別工程にせず、コンテキスト付きのスキャンと修正提案をCIに近い位置へ置く設計を試す価値がある。レビュー時は検出件数より、誤検知削減と修正パッチの妥当性を評価軸にする。

- リンク: [https://openai.com/index/codex-security-now-in-research-preview/](https://openai.com/index/codex-security-now-in-research-preview/)
- 確信度: 高
---

---
### 【カテゴリA: 公式ソース（AI）】Introducing the Codex app（公式AI, 2026-02-02）

**ひとことサマリー（1文）**: 公式AI の「Introducing the Codex app」では、OpenAIがCodexアプリを公開し、複数エージェントを並列で動かしながらスレッド単位で差分確認やコメント、worktree運用までできるデスクトップ体験を前面に出した。skillsとautomationsを同じUIから扱え、CLIやIDE拡張の設定も引き継げる。

**何が起きたか（What）**:  
公式AIの「Introducing the Codex app」は2026-02-02公開。OpenAIがCodexアプリを公開し、複数エージェントを並列で動かしながらスレッド単位で差分確認やコメント、worktree運用までできるデスクトップ体験を前面に出した。skillsとautomationsを同じUIから扱え、CLIやIDE拡張の設定も引き継げる。

**なぜ重要か（Why it matters）**:  
コーディング支援の競争軸が単発補完から、複数エージェントの監督と長時間タスクの運用へ移っている。agentを増やしてもローカルgit状態を汚さずに管理できる点は、個人開発だけでなくチーム導入の障壁を下げる。

**自分への影響（So what）**:  
自分の運用では、単一チャットで詰め込むより、作業単位でagentを分離して並列化する方が再現性とレビュー効率を上げやすい。daily automationやskill化まで一体で設計すると、日次の調査やCI確認を継続運用しやすくなる。

- リンク: [https://openai.com/index/introducing-the-codex-app/](https://openai.com/index/introducing-the-codex-app/)
- 確信度: 高
---

---
### 【カテゴリA: 公式ソース（AI）】GPT-5.4 is generally available in GitHub Copilot（公式AI, 2026-03-05）

**ひとことサマリー（1文）**: 公式AI の「GPT-5.4 is generally available in GitHub Copilot」では、GitHubがCopilotでGPT-5.4を一般提供に切り替えた。GitHubの案内では、実運用のagentic codingやソフトウェア開発タスクで従来より高い性能を示したモデルとして位置づけている。

**何が起きたか（What）**:  
公式AIの「GPT-5.4 is generally available in GitHub Copilot」は2026-03-05公開。GitHubがCopilotでGPT-5.4を一般提供に切り替えた。GitHubの案内では、実運用のagentic codingやソフトウェア開発タスクで従来より高い性能を示したモデルとして位置づけている。

**なぜ重要か（Why it matters）**:  
IDE内の補完だけでなく、レビューやエージェント実行まで含めた開発フロー全体でモデル差が効く段階に入っている。Copilot側で新モデルが標準化されると、既存チームの評価基準やプロンプト資産も見直しが必要になる。

**自分への影響（So what）**:  
自分の開発では、モデル更新日にベンチマークを回すだけでなく、PRコメント生成や複数ファイル変更の安定度も比較したい。採用判断は速度より、長いタスクでの破綻率とレビュー負荷の減り方で見るべきだ。

- リンク: [https://github.blog/changelog/2026-03-05-gpt-5-4-is-generally-available-in-github-copilot/](https://github.blog/changelog/2026-03-05-gpt-5-4-is-generally-available-in-github-copilot/)
- 確信度: 高
---

### Zenn ピックアップ

---
### 【カテゴリC: 日本語コミュニティ（Zenn）】Claude と Gemini でコードレビューを比較した結果と使い分け（Zenn, 2026-03-08）

**ひとことサマリー（1文）**: Zenn の「Claude と Gemini でコードレビューを比較した結果と使い分け」では、同じコードをClaudeとGeminiにレビューさせ、指摘の傾向と向いている用途を比較した記事。著者は両者の得意分野がはっきり分かれ、レビューの目的に応じて使い分けた方が実務では機能すると整理している。

**何が起きたか（What）**:  
Zennの「Claude と Gemini でコードレビューを比較した結果と使い分け」は2026-03-08公開。同じコードをClaudeとGeminiにレビューさせ、指摘の傾向と向いている用途を比較した記事。著者は両者の得意分野がはっきり分かれ、レビューの目的に応じて使い分けた方が実務では機能すると整理している。

**なぜ重要か（Why it matters）**:  
AIコードレビューの品質差はモデル名だけでは見えにくく、実例比較がないと現場に載せづらい。レビュー用途を一つのモデルに固定せず、欠陥検出と説明のしやすさを分けて考える視点は運用設計に直結する。

**自分への影響（So what）**:  
自分の運用でも、モデルを一本化する前に同一diffで比較し、レビュー観点ごとに役割分担させる検証を入れたい。特にPRレビューでは、精度だけでなく根拠の分かりやすさも採用条件にする。

- リンク: [https://zenn.dev/ga14tools/articles/ai-code-review-claude-gemini](https://zenn.dev/ga14tools/articles/ai-code-review-claude-gemini)
- 確信度: 高
---

---
### 【カテゴリC: 日本語コミュニティ（Zenn）】AIコーディングの原則（Zenn, 2026-03-08）

**ひとことサマリー（1文）**: Zenn の「AIコーディングの原則」では、AIコーディングが広がる一方で、低品質なAI生成物がチーム全体のレビュー負荷を増やすという前提から、著者がチーム運用向けの原則をまとめた。個人では吸収できるノイズも、組織では増幅されるため、人間の責任範囲や品質基準を明確に置くべきだと論じている。

**何が起きたか（What）**:  
Zennの「AIコーディングの原則」は2026-03-08公開。AIコーディングが広がる一方で、低品質なAI生成物がチーム全体のレビュー負荷を増やすという前提から、著者がチーム運用向けの原則をまとめた。個人では吸収できるノイズも、組織では増幅されるため、人間の責任範囲や品質基準を明確に置くべきだと論じている。

**なぜ重要か（Why it matters）**:  
2026年のAIコーディングは導入可否より、どう統制するかが論点になっている。生成速度よりも、スロップをチームでどう抑えるかを原則レベルで言語化した記事は、実務導入の失敗を減らしやすい。

**自分への影響（So what）**:  
自分の開発では、便利なプロンプト集を増やす前に、誰が最終責任を持つかとレビュー基準を文章化した方がよい。AI利用ルールをコード品質と切り離さず、PR運用に落とし込む必要がある。

- リンク: [https://zenn.dev/takekazuomi/articles/ai-coding-principles](https://zenn.dev/takekazuomi/articles/ai-coding-principles)
- 確信度: 高
---

---
### 【カテゴリC: 日本語コミュニティ（Zenn）】Amazon Bedrock AgentCore Policyが正式リリース——AIエージェントに「コード外ガードレール」を適用する（Zenn, 2026-03-08）

**ひとことサマリー（1文）**: Zenn の「Amazon Bedrock AgentCore Policyが正式リリース——AIエージェントに「コード外ガードレール」を適…」では、Amazon Bedrock AgentCore PolicyのGAを受けて、エージェントへコード外のガードレールを与える考え方と適用範囲を整理した記事。実装ロジックとは別に、エージェントの許容行動をポリシーとして制御する発想を説明している。

**何が起きたか（What）**:  
Zennの「Amazon Bedrock AgentCore Policyが正式リリース——AIエージェントに「コード外ガードレール」を適…」は2026-03-08公開。Amazon Bedrock AgentCore PolicyのGAを受けて、エージェントへコード外のガードレールを与える考え方と適用範囲を整理した記事。実装ロジックとは別に、エージェントの許容行動をポリシーとして制御する発想を説明している。

**なぜ重要か（Why it matters）**:  
AIエージェントはツール実行まで踏み込むため、コードレビューだけでは防げない事故が増える。ポリシーレイヤーで制約を定義する考え方は、agent運用が本番系へ近づくほど重要になる。

**自分への影響（So what）**:  
自分の自動化でも、権限や実行条件をプロンプトだけに埋め込まず、別レイヤーで明示的に制御する設計を試したい。特にファイル編集や外部アクセスの可否は、運用ルールとして切り出した方が安全だ。

- リンク: [https://zenn.dev/taketaka1986/articles/2026-03-07-bedrock-agentcore-policy-ga](https://zenn.dev/taketaka1986/articles/2026-03-07-bedrock-agentcore-policy-ga)
- 確信度: 高
---

### note ピックアップ

---
### 【カテゴリD: 日本語コミュニティ（note）】生成AIニュース Geminiと漫画でニュース3連発！〜布団でClaude Codeと生成AIの食費と女子高生副村長〜（note, 2026-02-27）

**ひとことサマリー（1文）**: note の「生成AIニュース Geminiと漫画でニュース3連発！〜布団でClaude Codeと生成AIの食費と女子高生副村長〜」では、Claude Codeのスマホ操作対応や生成AI関連の話題を、複数ニュースをつなぎながら分かりやすく整理した記事。ツール単体の新機能紹介にとどまらず、移動中や布団の中からでもAIコーディングを回すような利用シーンまで落としている。

**何が起きたか（What）**:  
noteの「生成AIニュース Geminiと漫画でニュース3連発！〜布団でClaude Codeと生成AIの食費と女子高生副村長〜」は2026-02-27公開。Claude Codeのスマホ操作対応や生成AI関連の話題を、複数ニュースをつなぎながら分かりやすく整理した記事。ツール単体の新機能紹介にとどまらず、移動中や布団の中からでもAIコーディングを回すような利用シーンまで落としている。

**なぜ重要か（Why it matters）**:  
一般ユーザー向けの解説でも、AIコーディングがデスクトップ前提から外れ始めていることが見て取れる。使い方の裾野が広がると、機能差より日常の導線にどう入り込むかが競争軸になる。

**自分への影響（So what）**:  
自分の運用でも、机の前でしか回せないワークフローは見直したい。外出時の確認や軽い指示出しをどう組み込むかを考えると、agent運用の設計が変わる。

- リンク: [https://note.com/chatgpt_ysd/n/ne4b2902dcffd](https://note.com/chatgpt_ysd/n/ne4b2902dcffd)
- 確信度: 中
---

### Reddit / HN ピックアップ

---
### 【カテゴリE: Reddit（AI）】Anthropic just made Claude Code run without you. Scheduled tasks are live. This is a bi…（Reddit, 2026-03-07）

**ひとことサマリー（1文）**: Reddit の「Anthropic just made Claude Code run without you. Scheduled task…」では、r/ClaudeAIで、Claude Codeのscheduled tasks対応が大きく注目された。投稿本文では、daily commit review、dependency audit、error log scan、PR reviewのような定期作業を、対話なしで夜間に回せる点が強調されている。

**何が起きたか（What）**:  
Redditの「Anthropic just made Claude Code run without you. Scheduled task…」は2026-03-07公開。r/ClaudeAIで、Claude Codeのscheduled tasks対応が大きく注目された。投稿本文では、daily commit review、dependency audit、error log scan、PR reviewのような定期作業を、対話なしで夜間に回せる点が強調されている。

**なぜ重要か（Why it matters）**:  
コミュニティが反応しているのは新しいUIではなく、agentが定期実行へ踏み込んだことだ。AIコーディングが都度対話型から自動運転型へ移ると、監督方法と権限設計の重要度が一段上がる。

**自分への影響（So what）**:  
自分の使い方でも、毎回手で投げている作業をautomation化できるかを見直したい。価値があるのは派手なデモより、毎日同じ確認作業を安全に回せるかどうかだ。

- リンク: [https://www.reddit.com/r/ClaudeAI/comments/1rna5mb/anthropic_just_made_claude_code_run_without_you/](https://www.reddit.com/r/ClaudeAI/comments/1rna5mb/anthropic_just_made_claude_code_run_without_you/)
- 確信度: 高
---

---

## 半導体ニュース

### 公式ソース

---
### 【カテゴリB: 公式ソース（半導体）】NVIDIA CEO Jensen Huang and Global Technology Leaders to Showcase Age of AI at GTC 2026（公式半導体, 2026-03-03）

**ひとことサマリー（1文）**: 公式半導体 の「NVIDIA CEO Jensen Huang and Global Technology Leaders to Showca…」では、NVIDIAがGTC 2026の概要を公表し、3月16日から19日に3万人超が集まり、AIファクトリー、チップ、インフラ、モデル、アプリケーションまでAIスタック全体の更新を扱うと告知した。基調講演ではJensen Huang氏が加速計算からphysical AIまで今年の方向性を示すとしている。

**何が起きたか（What）**:  
公式半導体の「NVIDIA CEO Jensen Huang and Global Technology Leaders to Showca…」は2026-03-03公開。NVIDIAがGTC 2026の概要を公表し、3月16日から19日に3万人超が集まり、AIファクトリー、チップ、インフラ、モデル、アプリケーションまでAIスタック全体の更新を扱うと告知した。基調講演ではJensen Huang氏が加速計算からphysical AIまで今年の方向性を示すとしている。

**なぜ重要か（Why it matters）**:  
NVIDIAは単体GPUの発表だけでなく、AI向け設備投資全体の温度感を決める存在になっている。GTCの焦点がチップ単体ではなくAIファクトリー全体に移っていることは、需要がデータセンター設計と電力・光学まで広がっていることを示す。

**自分への影響（So what）**:  
自分の調達やウォッチでは、今後はGPU SKUだけでなく、周辺のネットワークや電力設計を含めて見る必要がある。GTC後は個別製品名より、どのレイヤーに投資が集中するかで次の半導体ニュースを整理したい。

- リンク: [https://nvidianews.nvidia.com/news/nvidia-ceo-jensen-huang-and-global-technology-leaders-to-showcase-age-of-ai-at-gtc-2026](https://nvidianews.nvidia.com/news/nvidia-ceo-jensen-huang-and-global-technology-leaders-to-showcase-age-of-ai-at-gtc-2026)
- 確信度: 高
---

---
### 【カテゴリB: 公式ソース（半導体）】AMD and Nutanix Announce Strategic Partnership to Advance an Open and Scalable Platform…（公式半導体, 2026-02-25）

**ひとことサマリー（1文）**: 公式半導体 の「AMD and Nutanix Announce Strategic Partnership to Advance an Op…」では、AMDとNutanixが、enterprise AI向けのオープンなフルスタック基盤を共同開発する複数年提携を発表した。AMDはNutanix株に1.5億ドルを出資し、さらに最大1億ドルを共同開発とGo-to-Marketへ拠出する。EPYC CPU、Instinct GPU、ROCm、Nutanix Cloud Platformを組み合わせたagentic AI基盤を2026年後半から市場投入する計画だ。

**何が起きたか（What）**:  
公式半導体の「AMD and Nutanix Announce Strategic Partnership to Advance an Op…」は2026-02-25公開。AMDとNutanixが、enterprise AI向けのオープンなフルスタック基盤を共同開発する複数年提携を発表した。AMDはNutanix株に1.5億ドルを出資し、さらに最大1億ドルを共同開発とGo-to-Marketへ拠出する。EPYC CPU、Instinct GPU、ROCm、Nutanix Cloud Platformを組み合わせたagentic AI基盤を2026年後半から市場投入する計画だ。

**なぜ重要か（Why it matters）**:  
エンタープライズAI基盤の勝負が、単一GPU性能からCPU・GPU・ソフトウェア・運用基盤の束ね方へ移っている。オープン構成でNVIDIA一極依存を崩したい顧客にとって、AMD陣営の具体的な投資額と投入時期が見えた点は大きい。

**自分への影響（So what）**:  
自分の観点では、企業向けAI導入はモデル性能だけでなく、どのスタックが長期運用しやすいかで選ぶ局面に入っている。今後はROCm互換性やKubernetes運用のしやすさも、GPU比較と同じ重みで見るべきだ。

- リンク: [https://www.amd.com/en/newsroom/press-releases/2026-2-25-amd-and-nutanix-announce-strategic-partnership-to.html](https://www.amd.com/en/newsroom/press-releases/2026-2-25-amd-and-nutanix-announce-strategic-partnership-to.html)
- 確信度: 高
---

---
### 【カテゴリB: 公式ソース（半導体）】AI + Mobile Networks: Intel Showcases What’s Next at MWC 2026（公式半導体, 2026-02-10）

**ひとことサマリー（1文）**: 公式半導体 の「AI + Mobile Networks: Intel Showcases What’s Next at MWC 2026」では、IntelはMWC 2026で、ライブモバイルネットワーク上でAI推論を動かす展示を行い、既存5Gインフラを全面刷新せずにコア、RAN、エッジへAIを広げる方針を示した。記事ではAI推論をネットワークの近くで動かし、トラフィック最適化や混雑緩和、信号品質改善をリアルタイムで行う構想を説明している。

**何が起きたか（What）**:  
公式半導体の「AI + Mobile Networks: Intel Showcases What’s Next at MWC 2026」は2026-02-10公開。IntelはMWC 2026で、ライブモバイルネットワーク上でAI推論を動かす展示を行い、既存5Gインフラを全面刷新せずにコア、RAN、エッジへAIを広げる方針を示した。記事ではAI推論をネットワークの近くで動かし、トラフィック最適化や混雑緩和、信号品質改善をリアルタイムで行う構想を説明している。

**なぜ重要か（Why it matters）**:  
AI推論の主戦場がデータセンターだけでなく通信網のエッジに広がると、求められる半導体はGPU単体からCPU・アクセラレータ・ネットワーク最適化向け製品へ分散する。通信事業者のROIを前面に出した点も、AI投資が実証段階から商用効率の議論へ移っていることを示す。

**自分への影響（So what）**:  
自分のウォッチでは、今後の半導体ニュースをデータセンター専用の話として切り分けない方が良い。ローカル推論やエッジAIに近い文脈として、通信や産業インフラでどのチップが採用されるかも追う価値がある。

- リンク: [https://newsroom.intel.com/5g-wireless/ai-mobile-networks-intel-showcases-whats-next-at-mwc-2026](https://newsroom.intel.com/5g-wireless/ai-mobile-networks-intel-showcases-whats-next-at-mwc-2026)
- 確信度: 高
---

### コミュニティ（Reddit / HN / その他）

---
### 【カテゴリE/F: コミュニティ（半導体）】【コアメンバー】NVIDIA説明会 4つの注目発言（note, 2026-02-26）

**ひとことサマリー（1文）**: note の「【コアメンバー】NVIDIA説明会 4つの注目発言」では、NVIDIA決算説明会で出た発言のうち、AI需要の実態を見るうえで重要なポイントを4つに絞って整理した記事。NVIDIA自身がAIエージェントを活用していることや、需要の広がりを投資家向けに読み解いている。

**何が起きたか（What）**:  
noteの「【コアメンバー】NVIDIA説明会 4つの注目発言」は2026-02-26公開。NVIDIA決算説明会で出た発言のうち、AI需要の実態を見るうえで重要なポイントを4つに絞って整理した記事。NVIDIA自身がAIエージェントを活用していることや、需要の広がりを投資家向けに読み解いている。

**なぜ重要か（Why it matters）**:  
半導体の需給を見る際に、決算短信だけでは経営陣の温度感や需要の質が見えにくい。説明会発言を追うことで、AI投資が一過性か継続的かを読む材料が増える。

**自分への影響（So what）**:  
自分が半導体ニュースを見るときも、製品発表だけでなく決算説明会の発言を合わせて追うべきだ。GPU価格や供給見通しを考えるうえで、経営陣が何を強調しているかは実用的な判断材料になる。

- リンク: [https://note.com/goto_finance/n/n25e8d4d5d4fb](https://note.com/goto_finance/n/n25e8d4d5d4fb)
- 確信度: 中
---

---
### 【カテゴリE/F: コミュニティ（半導体）】Nvidia dominates gaming GPU market with 95 percent share as sales of AMD Radeon graphic…（Reddit, 2026-03-07）

**ひとことサマリー（1文）**: Reddit の「Nvidia dominates gaming GPU market with 95 percent share as sal…」では、r/Amdで、Jon Peddie ResearchをもとにしたTom's Hardwareの記事が上位に入った。2025年第4四半期の単体GPU市場でNVIDIAが95%、AMDが5%まで低下したという内容で、前年同期比では市場全体が伸びてもシェア差がさらに開いたと整理されている。

**何が起きたか（What）**:  
Redditの「Nvidia dominates gaming GPU market with 95 percent share as sal…」は2026-03-07公開。r/Amdで、Jon Peddie ResearchをもとにしたTom's Hardwareの記事が上位に入った。2025年第4四半期の単体GPU市場でNVIDIAが95%、AMDが5%まで低下したという内容で、前年同期比では市場全体が伸びてもシェア差がさらに開いたと整理されている。

**なぜ重要か（Why it matters）**:  
ローカルAIや開発機のGPU調達は、性能だけでなく市場支配率と価格形成に強く影響される。AMDの存在感低下が続くなら、NVIDIA偏重による価格高止まりや選択肢不足が長引く可能性が高い。

**自分への影響（So what）**:  
自分のGPU調達でも、NVIDIA偏重を前提に代替構成を早めに考える必要がある。価格や在庫が崩れにくい市場なら、購入タイミングとクラウド代替の比較を先にやっておくべきだ。

- リンク: [https://www.tomshardware.com/pc-components/gpus/nvidia-dominates-discrete-gpu-market-as-sales-of-amd-radeon-graphics-cards-hit-historical-low](https://www.tomshardware.com/pc-components/gpus/nvidia-dominates-discrete-gpu-market-as-sales-of-amd-radeon-graphics-cards-hit-historical-low)
- 確信度: 高
---

## その他の候補記事（選外）

### カテゴリA（公式AI）
- OpenAI Robotics head resigns after deal with Pentagon（当日の主要トピック優先のため選外）  
  https://www.reuters.com/business/openai-robotics-head-resigns-after-deal-with-pentagon-2026-03-07/

### カテゴリB（公式半導体）
- 該当候補なし（当日採用を優先）

### カテゴリC（Zenn）
- Claude Code に向いているプログラミング言語（当日の主要トピック優先のため選外）  
  https://zenn.dev/mametter/articles/3e8580ec034201
- 個人的 AI情報の追い方（当日の主要トピック優先のため選外）  
  https://zenn.dev/knowledgework/articles/my-ai-catchup

### カテゴリD（note）
- 生成AIのひな祭り AI用語をChatGPT、Gemini、Claudeが漫画で解説（当日の主要トピック優先のため選外）  
  https://note.com/chatgpt_ysd/n/n79ea031eefa2
- 一次情報が生成AIを動かす。Gemini・ChatGPT・Copilotの回答から紐解く「自己紹介の人」と「noteアルゴリズム研究家」の認知の違い（当日の主要トピック優先のため選外）  
  https://note.com/hidehito_n/n/nb5372747fe24

### カテゴリE（Reddit）
- AMD GAIA 0.16 introduces C++17 agent framework for building AI PC agents in pure C++（当日の主要トピック優先のため選外）  
  https://www.phoronix.com/news/AMD-GAIA-0.16
- BREAKING: OpenAI just drppped GPT-5.4（当日の主要トピック優先のため選外）  
  https://i.redd.it/xpbjs93fq9ng1.png

### カテゴリF（Hacker News）
- SWE-CI: Evaluating Agent Capabilities in Maintaining Codebases via Continuous Integration（当日の主要トピック優先のため選外）  
  https://arxiv.org/abs/2603.03823
- New Research Reassesses the Value of Agents.md Files for AI Coding（当日の主要トピック優先のため選外）  
  https://www.infoq.com/news/2026/03/agents-context-file-value-review/


## ソース一覧
- 公式AI（Codex Security: now in research preview）, 公開日: 2026-03-06, アクセス日: 2026-03-08, 種別: 公式AI  
  https://openai.com/index/codex-security-now-in-research-preview/
- 公式AI（Introducing the Codex app）, 公開日: 2026-02-02, アクセス日: 2026-03-08, 種別: 公式AI  
  https://openai.com/index/introducing-the-codex-app/
- 公式AI（GPT-5.4 is generally available in GitHub Copilot）, 公開日: 2026-03-05, アクセス日: 2026-03-08, 種別: 公式AI  
  https://github.blog/changelog/2026-03-05-gpt-5-4-is-generally-available-in-github-copilot/
- Zenn（Claude と Gemini でコードレビューを比較した結果と使い分け）, 公開日: 2026-03-08, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://zenn.dev/ga14tools/articles/ai-code-review-claude-gemini
- Zenn（AIコーディングの原則）, 公開日: 2026-03-08, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://zenn.dev/takekazuomi/articles/ai-coding-principles
- Zenn（Amazon Bedrock AgentCore Policyが正式リリース——AIエージェントに「コード外ガードレール」…）, 公開日: 2026-03-08, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://zenn.dev/taketaka1986/articles/2026-03-07-bedrock-agentcore-policy-ga
- note（生成AIニュース Geminiと漫画でニュース3連発！〜布団でClaude Codeと生成AIの食費と女子高生副村長〜）, 公開日: 2026-02-27, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://note.com/chatgpt_ysd/n/ne4b2902dcffd
- Reddit（Anthropic just made Claude Code run without you. Scheduled ta…）, 公開日: 2026-03-07, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://www.reddit.com/r/ClaudeAI/comments/1rna5mb/anthropic_just_made_claude_code_run_without_you/
- 公式半導体（NVIDIA CEO Jensen Huang and Global Technology Leaders to Show…）, 公開日: 2026-03-03, アクセス日: 2026-03-08, 種別: 公式半導体  
  https://nvidianews.nvidia.com/news/nvidia-ceo-jensen-huang-and-global-technology-leaders-to-showcase-age-of-ai-at-gtc-2026
- 公式半導体（AMD and Nutanix Announce Strategic Partnership to Advance an…）, 公開日: 2026-02-25, アクセス日: 2026-03-08, 種別: 公式半導体  
  https://www.amd.com/en/newsroom/press-releases/2026-2-25-amd-and-nutanix-announce-strategic-partnership-to.html
- 公式半導体（AI + Mobile Networks: Intel Showcases What’s Next at MWC 2026）, 公開日: 2026-02-10, アクセス日: 2026-03-08, 種別: 公式半導体  
  https://newsroom.intel.com/5g-wireless/ai-mobile-networks-intel-showcases-whats-next-at-mwc-2026
- note（【コアメンバー】NVIDIA説明会 4つの注目発言）, 公開日: 2026-02-26, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://note.com/goto_finance/n/n25e8d4d5d4fb
- Reddit（Nvidia dominates gaming GPU market with 95 percent share as s…）, 公開日: 2026-03-07, アクセス日: 2026-03-08, 種別: コミュニティ  
  https://www.tomshardware.com/pc-components/gpus/nvidia-dominates-discrete-gpu-market-as-sales-of-amd-radeon-graphics-cards-hit-historical-low

## 対象範囲
- 対象日: 2026-03-08
- タイムゾーン: Asia/Tokyo
- 対象期間: 2026-03-08の48時間前〜現在（不足カテゴリは7日→14日へ拡張）
