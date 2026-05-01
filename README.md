# clidict

终端词典，根据语言自动路由：

- **英语** → [Cambridge Dictionary](https://dictionary.cambridge.org)（英汉双语）
- **俄语** → [千亿词霸](https://w.qianyix.com)（俄汉双语）

识别方式基于字符：西里尔字母走千亿词霸，其余走剑桥。

## 安装

```sh
uv tool install git+https://github.com/BigDawnGhost/clidict
```

## 用法

```sh
camdict hello
camdict phrasal verb
camdict привет
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
cp completions/camdict.fish ~/.config/fish/completions/
```

**Bash：**

```sh
echo 'source /path/to/completions/camdict.bash' >> ~/.bashrc
```

补全词表来自内置词典（american-english + british-english），`pip install` 和独立二进制均可用。候选词按长度升序排列。

## 打包独立二进制

需要 [PyInstaller](https://pyinstaller.org)：

```sh
uv run pyinstaller camdict.spec
# 输出在 dist/camdict
```

## 开发

```sh
uv sync
uv run pytest
```
