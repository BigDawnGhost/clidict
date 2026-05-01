# clidict

终端词典，根据语言自动路由，本项目纯vibe coding，欢迎改进。
<img width="1280" height="720" alt="图片" src="https://github.com/user-attachments/assets/2d3bbd85-57dd-4308-b2a2-c3bb623b82ec" />

- **英语** → [Cambridge Dictionary](https://dictionary.cambridge.org)（英汉双语）
- **俄语** → [千亿词霸](https://w.qianyix.com)（俄汉双语）

识别方式基于字符：西里尔字母走千亿词霸，其余走剑桥。
<img width="1280" height="720" alt="图片" src="https://github.com/user-attachments/assets/db603c07-1505-4ae1-8674-66b0ecb5bc59" />


## 安装

```sh
uv tool install git+https://github.com/BigDawnGhost/clidict
```

## 用法

```sh
clidict hello
clidict phrasal verb
clidict привет
```

剑桥词条展示 CEFR 等级、语法标注、英美发音、中文释义和例句。俄语词条包含重音标注、专业含义及词形变化表。

### 查询流程

3 个 HTTP 请求并行发出：剑桥（中英）、剑桥（纯英）、Bing。优先级：

1. 剑桥中英版（最快路径）
2. 剑桥纯英版
3. [Bing 词典](https://cn.bing.com/dict)（兜底）

当剑桥没有收录时（如 `genshin`），自动切换到 Bing。

## 补全

**Fish：**

```sh
cp completions/clidict.fish ~/.config/fish/completions/
```
<img width="1280" height="720" alt="图片" src="https://github.com/user-attachments/assets/86be2962-8b3a-455a-9959-f8fedaeaad60" />

**Bash：**

```sh
echo 'source /path/to/completions/clidict.bash' >> ~/.bashrc
```

补全词表来自内置词典（american-english + british-english），`pip install` 和独立二进制均可用。候选词按长度升序排列。

## 打包独立二进制

需要 [PyInstaller](https://pyinstaller.org)：

```sh
uv run pyinstaller clidict.spec
# 输出在 dist/clidict
```

## 开发

```sh
uv sync
uv run pytest
```
