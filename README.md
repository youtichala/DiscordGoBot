# DiscordGoBot
DC內下棋小程式

# 說明
由於本軟體是從原始機器人拆下來的下棋部分，可能會存在少許方法沒刪除乾淨 </br>
使用 Python 3.9.2-3，除此之外還包含 : </br>
<ol>
<li>pip install requests</li>
<li>pip install Pillow</li>
<li>pip install git+https://github.com/Rapptz/discord.py</li>
</ol>
</br>
圍棋AI : <strong>leela-zero-0.17</strong> (https://github.com/leela-zero/leela-zero)</br>
神經網路載點 : https://zero.sjeng.org/ (舊版本) 以及 https://zero.sjeng.org/best-network (最新神經網路)</br>
並搭配這篇文章 : https://www.reddit.com/r/cbaduk/comments/aj8avc/adjusted_strength_ratings_for_leela_zero/ 的說明降低2階設定棋力</br>
</br>
點空計算腳本參考 : https://github.com/online-go/score-estimator 並將其重新撰寫成Python版</br>

由於本AI非使用純CPU版本，因此運行此DCBot的電腦必須具備獨立顯示卡才能正常使用

# 額外設定 - 登錄檔
必須要額外在根目錄加上註冊用檔案 : <strong>bot_token.py</strong></br>
</br>
檔案內部包含兩個變數 :</br>
<ol>
<li><strong>key</strong> : [Discord金鑰]</li>
<li><strong>Owner</strong> : [擁有者DC編號]</li>
</ol>
