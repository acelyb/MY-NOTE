# github 配置

可以。考虑到你之前有 Ubuntu 20.04/22.04 和 CentOS 7 的开发环境，我给你一套偏“生产环境”的做法：不执行陌生的一键脚本、不把私钥放到 GitHub、不把 Token 写进 shell history，并且尽量使用 GitHub 官方仓库。

下面分成两条路线：

Ubuntu / Debian：推荐
CentOS 7 / RHEL 系：单独处理，因为 CentOS 7 已经比较老

GitHub CLI 官方目前提供签名的软件仓库，并公布了仓库签名密钥指纹；官方 Debian/Ubuntu 安装方式使用 signed-by 绑定 keyring，而 RPM 系也提供官方仓库。

一、先确认你的 Linux

先执行：

cat /etc/os-release
uname -m

例如：

Ubuntu 22.04
x86_64

或者：

CentOS Linux 7
x86_64

下面我直接把两套命令都给你。

二、Ubuntu / Debian：推荐方案
1. 安装 Git
sudo apt update
sudo apt install -y git openssh-client ca-certificates curl gnupg

检查：

git --version
ssh -V
三、安装 GitHub CLI

这里不要用：

curl xxx | bash

而是使用 GitHub CLI 官方仓库，并让 APT 用专门的 keyring 验证软件包。

GitHub CLI 官方当前公布的 Linux 仓库签名密钥指纹为：

2C6106201985B60E6C7AC87323F3D4EA75716059
7F38BBB59D064DBCB3D84D725612B36462313325

官方还提供 keyring 的 SHA256 校验值。

先建立 keyring 目录
sudo mkdir -p -m 755 /etc/apt/keyrings
下载官方 keyring
curl -fsSL \
  https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  -o /tmp/githubcli-archive-keyring.gpg
检查 SHA256
sha256sum /tmp/githubcli-archive-keyring.gpg

官方当前 SHA256：

6084d5d7bd8e288441e0e94fc6275570895da18e6751f70f057485dc2d1a811b

两者应该完全一致。

然后：

sudo cp /tmp/githubcli-archive-keyring.gpg \
  /etc/apt/keyrings/githubcli-archive-keyring.gpg

sudo chmod 644 /etc/apt/keyrings/githubcli-archive-keyring.gpg
添加官方仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

然后：

sudo apt update
sudo apt install -y gh

检查：

gh version

这就是 GitHub CLI 官方推荐的 Debian/Ubuntu 路线。

四、生成 SSH Key

这一部分很重要。

不要把 GitHub 密码、Personal Access Token 直接塞进 Git remote URL。

推荐：

Git
 ↓
SSH
 ↓
Ed25519 private key
 ↓
GitHub

GitHub 官方目前推荐新 SSH key 使用 Ed25519；对于不支持 Ed25519 的老系统才考虑 RSA 4096。

1. 先看看有没有现有 SSH key
ls -la ~/.ssh

以及：

ls ~/.ssh/*.pub 2>/dev/null

可能看到：

id_ed25519
id_ed25519.pub

或者：

id_rsa
id_rsa.pub

如果已经有一把正在使用的 SSH key，不建议直接覆盖。

最好给 GitHub 单独建一把：

ssh-keygen -t ed25519 \
  -C "你的GitHub邮箱" \
  -f ~/.ssh/id_ed25519_github

例如：

ssh-keygen -t ed25519 \
  -C "xxx@example.com" \
  -f ~/.ssh/id_ed25519_github

它会让你输入：

Enter passphrase

建议设置 passphrase。

这样即使机器上的私钥文件被偷走，也增加了一层保护。GitHub 官方文档也建议为 SSH key 设置 passphrase。

最终：

~/.ssh/id_ed25519_github
~/.ssh/id_ed25519_github.pub

其中：

id_ed25519_github

是私钥

id_ed25519_github.pub

是公钥

五、保护 SSH 私钥

执行：

chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519_github
chmod 644 ~/.ssh/id_ed25519_github.pub

检查：

ls -l ~/.ssh/id_ed25519_github*

应该类似：

-rw------- id_ed25519_github
-rw-r--r-- id_ed25519_github.pub
千万不要：
chmod 777 ~/.ssh

也不要：

chmod 644 ~/.ssh/id_ed25519_github

私钥应该尽可能严格限制权限。

六、启动 ssh-agent

GitHub 官方给出的 Linux 流程也是使用 ssh-agent 管理带 passphrase 的 SSH key。

当前 shell：

eval "$(ssh-agent -s)"

然后：

ssh-add ~/.ssh/id_ed25519_github

输入刚才设置的 passphrase。

检查：

ssh-add -l

应该可以看到类似：

256 SHA256:xxxxx ... id_ed25519_github (ED25519)
七、配置 SSH 使用 GitHub 这把 key

这是我非常推荐做的一步。

创建：

vim ~/.ssh/config

写：

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes

然后：

chmod 600 ~/.ssh/config

为什么加：

IdentitiesOnly yes

因为你机器上可能有很多 SSH key。

例如：

id_rsa
id_ed25519
id_ed25519_github
id_ed25519_company
id_ed25519_server

不加的话，SSH 可能尝试很多 key。

加上之后：

github.com
     ↓
id_ed25519_github

关系非常明确。

对于你这种开发环境比较复杂、可能同时连公司服务器/GitHub/GitLab 的情况，这个配置尤其值得做。

八、测试 GitHub SSH

执行：

ssh -T git@github.com

第一次通常会看到：

The authenticity of host 'github.com' can't be established.

这时候不要机械地输入 yes。

先确认 GitHub 的 SSH host key。GitHub 官方维护了对应的 fingerprints。当前 GitHub 文档给出的 ED25519 host key fingerprint 是：

SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPmsSzlH2mH3b8=

确认无误后再输入：

yes

之后应该看到类似：

Hi YOUR_USERNAME! You've successfully authenticated, but GitHub does not provide shell access.

这就说明：

Linux
 ↓
SSH
 ↓
你的私钥
 ↓
GitHub

已经打通。

九、把公钥添加到 GitHub

先查看：

cat ~/.ssh/id_ed25519_github.pub

你会得到：

ssh-ed25519 AAAA... xxx@example.com

只复制 .pub 的内容。

不要复制：

~/.ssh/id_ed25519_github

那个是私钥。

进入 GitHub：

Settings
→ SSH and GPG keys
→ New SSH key

类型选择：

Authentication Key

然后粘贴：

id_ed25519_github.pub

GitHub 官方支持把 SSH public key 添加到账户，也可以使用 gh ssh-key add 来完成。

十、设置 Git 用户信息

这和 GitHub 登录是两个概念。

执行：

git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"

检查：

git config --global --list

例如：

user.name=Robert Luo
user.email=xxx@example.com
十一、设置 GitHub CLI

现在运行：

gh auth login

选择：

GitHub.com

然后：

What is your preferred protocol for Git operations?

选择：

SSH

GitHub CLI 官方支持在 gh auth login 时直接指定：

gh auth login --git-protocol ssh

并支持浏览器 OAuth 登录。

所以你可以直接：

gh auth login --git-protocol ssh --web

然后按照提示在浏览器完成授权。

最后：

gh auth status

检查。

十二、一个更完整的验证流程

建议最终依次执行：

git --version
gh version
ssh -T git@github.com
gh auth status

然后：

git config --global --get user.name
git config --global --get user.email

全部正常以后，再测试：

git clone git@github.com:用户名/仓库名.git

例如：

git clone git@github.com:torvalds/linux.git
十三、国内网络环境：最重要的几个坑

这里需要把**“认证问题”和“网络问题”**分开。

这是很多人排查 GitHub 时最容易混在一起的地方。

情况 A：SSH 连接超时

比如：

ssh: connect to host github.com port 22: Connection timed out

这通常不是 SSH key 有问题，而是：

你的机器
   ↓
网络
   ↓
github.com:22

被阻断或者不稳定。

情况 B：22 端口不通

GitHub 提供了 SSH over HTTPS 端口的方式，可以把 SSH 放到：

github.com:443

而不是：

github.com:22

你可以测试：

ssh -T -p 443 git@ssh.github.com

如果 443 能通，可以在：

vim ~/.ssh/config

加入：

Host github.com
    HostName ssh.github.com
    User git
    Port 443
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes

之后：

ssh -T git@github.com

实际上会走：

github.com
   ↓
ssh.github.com:443

这在企业网络、校园网、部分国内网络环境中往往比直接走 22 稳定。

十四、判断到底是 DNS、443 还是 22 的问题

遇到 GitHub 连不上，不要马上换各种镜像。

先：

getent hosts github.com

然后：

curl -I https://github.com

再：

nc -vz github.com 22

再：

nc -vz ssh.github.com 443

大致可以这样判断：

DNS失败
   ↓
DNS问题

github.com:443失败
   ↓
HTTPS网络问题

github.com:22失败
ssh.github.com:443成功
   ↓
SSH 22 端口问题

SSH 443成功
   ↓
优先使用 SSH over 443
十五、不要随便使用 GitHub 镜像作为正式 remote

国内网络不稳定时，你可能会看到各种：

github.xxx.com
gitclone.xxx.com
ghproxy.xxx.com

这类代理/镜像对于下载公开代码有时候很方便。

但是对于：

git push
私有仓库
SSH authentication
GitHub token

我不建议把正式 remote 指向陌生第三方。

尤其不要：

git clone https://某个陌生代理/github.com/xxx/xxx.git

然后把账号、Token 或 SSH 凭据交给它。

对于你自己的代码，最好始终：

Git remote
      ↓
github.com

网络问题通过：

SSH 443
代理
VPN
企业出口

解决，而不是把身份认证交给第三方。

十六、如果你所在的机器不能直接访问 GitHub

这时候建议把问题分成两个层次：

下载公开代码

可以考虑：

HTTPS + 网络代理
push / private repo

建议：

SSH
+
正规代理/VPN

尤其不要把 Personal Access Token 写成：

git clone https://TOKEN@github.com/xxx/xxx.git

因为 Token 很容易进入：

shell history
日志
进程参数
CI 日志
十七、CentOS 7 的情况

你之前的环境里出现过 CentOS 7，这个需要特别提醒：

CentOS 7 已于 2024-06-30 EOL，因此很多新的软件已经不再针对 CentOS 7 提供完善支持。

如果你的机器就是 CentOS 7，我不建议为了装最新 GitHub CLI 而乱加第三方仓库。

先：

cat /etc/centos-release

然后：

git --version
ssh -V

Git 通常可以：

sudo yum install -y git openssh-clients

但是 gh 在这种老环境上，最好根据你机器的：

uname -m
openssl version
glibc

来决定是官方 RPM 还是官方 release binary。

GitHub CLI 官方确实提供 CentOS/RHEL 的 RPM 仓库，但不同老系统的兼容性需要单独判断。

十八、我最推荐你的最终配置

如果这是你的个人 Linux 开发机，最终我建议保持：

Git
│
├── git clone
├── git pull
└── git push
        │
        ▼
      SSH
        │
        ▼
id_ed25519_github
        │
        ▼
    GitHub

以及：

gh
│
├── gh repo
├── gh pr
├── gh issue
└── gh release
        │
        ▼
    GitHub OAuth

配置文件：

~/.ssh/
├── config                    600
├── id_ed25519_github         600   ← 私钥
└── id_ed25519_github.pub     644   ← 公钥

~/.ssh/config：

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes

如果国内/企业网络下 22 端口不稳定，再改成：

Host github.com
    HostName ssh.github.com
    User git
    Port 443
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
最后给你一份可以直接照着执行的 Ubuntu 22.04 版本
# 1. 基础工具
sudo apt update
sudo apt install -y git openssh-client ca-certificates curl gnupg

# 2. 安装 GitHub CLI 官方仓库
sudo mkdir -p -m 755 /etc/apt/keyrings

curl -fsSL \
  https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  -o /tmp/githubcli-archive-keyring.gpg

echo "6084d5d7bd8e288441e0e94fc6275570895da18e6751f70f057485dc2d1a811b  /tmp/githubcli-archive-keyring.gpg" \
  | sha256sum -c -

sudo cp /tmp/githubcli-archive-keyring.gpg \
  /etc/apt/keyrings/githubcli-archive-keyring.gpg

sudo chmod 644 /etc/apt/keyrings/githubcli-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

sudo apt update
sudo apt install -y gh

# 3. 创建 SSH key
mkdir -p ~/.ssh
chmod 700 ~/.ssh

ssh-keygen -t ed25519 \
  -C "你的GitHub邮箱" \
  -f ~/.ssh/id_ed25519_github

chmod 600 ~/.ssh/id_ed25519_github
chmod 644 ~/.ssh/id_ed25519_github.pub

# 4. 启动 ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_github

# 5. 配置 GitHub SSH
cat > ~/.ssh/config <<'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config

# 6. 配置 Git
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"

# 7. 查看公钥
cat ~/.ssh/id_ed25519_github.pub

# 8. 测试 SSH
ssh -T git@github.com

# 9. GitHub CLI 登录
gh auth login --git-protocol ssh --web

# 10. 检查
git --version
gh version
gh auth status
ssh-add -l

唯一需要你手动做的步骤是把：

cat ~/.ssh/id_ed25519_github.pub

输出的公钥复制到 GitHub 的 Settings → SSH and GPG keys。GitHub 官方也支持用 gh ssh-key add 自动添加公钥，但前提是 gh 已经完成认证。

对于你这种可能同时使用 Ubuntu/CentOS、公司内网、GitHub/GitLab、多 SSH key 的开发环境，我更建议进一步把 “GitHub SSH + 国内代理 + Git 代理 + GitLab SSH” 一起配置好，这样以后切换不同代码仓库基本不需要再折腾。


这个报错其实很明确：网络连接已经成功，GitHub 服务器的身份也确认成功了，但 GitHub 没有接受你本机提供的 SSH 公钥。

而且你这里有一个好消息：你看到的 GitHub ED25519 指纹

SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU

与 GitHub 官方当前公布的指纹完全一致。所以刚才 yes 这一步是正确的，不是中间人攻击或主机指纹问题。

现在只需要排查 SSH 用户认证。

先看最可能的问题

按照我们前面的配置，你应该生成了：

~/.ssh/id_ed25519_github
~/.ssh/id_ed25519_github.pub

首先执行：

ls -l ~/.ssh/id_ed25519_github*

然后：

cat ~/.ssh/id_ed25519_github.pub

你应该看到类似：

ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... 你的邮箱
关键问题

你有没有把这个 .pub 公钥添加到 GitHub？

GitHub 官方要求：生成 SSH key 后，必须把公钥添加到对应 GitHub 账号，否则 SSH 会得到：

Permission denied (publickey)

进入 GitHub：

GitHub
→ Settings
→ SSH and GPG keys
→ New SSH key

把：

cat ~/.ssh/id_ed25519_github.pub

输出的整行内容复制进去。

注意只上传：

id_ed25519_github.pub

绝对不要上传：

id_ed25519_github

后者是你的私钥。

如果你已经添加了公钥

那我建议我们直接检查 SSH 到底有没有使用这把 key。

执行：

ssh -vT git@github.com

这个命令会输出很多信息，但我们重点看几个地方。

你应该看到类似：

Offering public key: /home/xxx/.ssh/id_ed25519_github

以及：

Server accepts key: ...

正常情况最后：

Hi YOUR_USERNAME! You've successfully authenticated, but GitHub does not provide shell access.
如果没有看到 Offering public key

那基本就是你的 ~/.ssh/config 没有生效。

把：

cat ~/.ssh/config

发给我看看。

你的配置应该类似：

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes

然后检查：

chmod 700 ~/.ssh
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519_github
chmod 644 ~/.ssh/id_ed25519_github.pub

再测试：

ssh -T git@github.com
还有一个很常见的问题：ssh-agent

如果你之前执行过：

ssh-add ~/.ssh/id_ed25519_github

检查：

ssh-add -l

正常应该看到类似：

256 SHA256:xxxxxxxxxxxxxxxx /home/xxx/.ssh/id_ed25519_github (ED25519)

如果看到：

The agent has no identities.

那么重新：

eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_github

然后：

ssh-add -l

再：

ssh -T git@github.com
我特别建议你做一个“绕过配置文件”的测试

这样可以一次判断到底是 GitHub 没有你的公钥，还是 SSH 配置错了。

直接运行：

ssh -i ~/.ssh/id_ed25519_github \
    -o IdentitiesOnly=yes \
    -T git@github.com
如果这样成功

出现：

Hi YOUR_USERNAME! You've successfully authenticated, but GitHub does not provide shell access.

那么说明：

SSH key 本身       ✅
GitHub 公钥        ✅
网络               ✅
问题就在 ~/.ssh/config
如果还是：
Permission denied (publickey)

那么基本就只剩：

1. 公钥没有添加到 GitHub
2. 添加到了错误的 GitHub 账号
3. 本地私钥和你上传的公钥不是一对
再检查一个非常关键的东西：公私钥是不是一对

执行：

ssh-keygen -y -f ~/.ssh/id_ed25519_github

它会根据你的私钥重新计算公钥。

输出应该和：

cat ~/.ssh/id_ed25519_github.pub

得到的内容一致。

可以直接：

diff \
  <(ssh-keygen -y -f ~/.ssh/id_ed25519_github) \
  <(cut -d' ' -f1,2 ~/.ssh/id_ed25519_github.pub)

如果没有输出，说明公私钥匹配。

还有一种情况：你添加的是 Deploy Key

如果你在某个 GitHub 仓库里面添加的是：

Repository
→ Settings
→ Deploy keys

那它和：

GitHub Account
→ Settings
→ SSH and GPG keys

不是一回事。

你现在执行：

ssh -T git@github.com

测试的是账号身份认证，所以最简单的方式是把公钥添加到：

个人 GitHub 账号
→ Settings
→ SSH and GPG keys
我建议你现在只执行这 5 条

这样我们不用猜：

echo "=== key ==="
ls -l ~/.ssh/id_ed25519_github*

echo "=== ssh config ==="
cat ~/.ssh/config

echo "=== agent ==="
ssh-add -l

echo "=== direct test ==="
ssh -i ~/.ssh/id_ed25519_github -o IdentitiesOnly=yes -T git@github.com

echo "=== debug ==="
ssh -vT git@github.com 2>&1 | grep -E "identity|Offering|accept|Authentications|Permission"

把这几条的输出贴给我即可。不要贴 id_ed25519_github 私钥内容，也不要贴任何 GitHub Token。

从你现在的报错看，我判断大概率不是网络问题，而是“GitHub 账号里还没添加这把公钥”或者“SSH 实际没有使用 id_ed25519_github”。GitHub 官方对 Permission denied (publickey) 的排查也是沿着这两个方向进行的。

这里就按提示操作即可。你现在进入的是 GitHub CLI 自动把 SSH 公钥添加到 GitHub 账号 的流程。

当前提示：

? Upload your SSH public key to your GitHub account?
  /home/cambricon/.ssh/id_ed25519_github.pub
? Title for your SSH key: (GitHub CLI)
1. Upload your SSH public key...

直接按 Enter。

它已经检测到了你之前生成的：

/home/cambricon/.ssh/id_ed25519_github.pub

注意这里是 .pub，也就是公钥，可以上传。

2. Title for your SSH key

这里可以直接按 Enter，使用：

GitHub CLI

也可以改成更容易识别的名字，例如：

Cambricon Ubuntu 22.04

我更推荐：

Cambricon Linux

因为以后你可能还有其他机器：

MacBook
Office PC
Cambricon Linux
Cloud Server

这样在 GitHub：

Settings
→ SSH and GPG keys

里一眼就知道这把 key 属于哪台机器。

所以你现在可以输入：

Cambricon Linux

然后回车。

3. 后面会发生什么

接下来 gh 会让你通过浏览器登录 GitHub，并授权 GitHub CLI。

正常流程大概是：

? Upload your SSH public key to your GitHub account?
  Yes

? Title for your SSH key:
  Cambricon Linux

! First copy your one-time code: XXXXXXXX
Press Enter to open github.com in your browser...

你按 Enter 后浏览器会打开 GitHub。

完成授权以后，回到终端。

4. 登录完成后检查

执行：

gh auth status

正常会类似：

github.com
  ✓ Logged in to github.com account YOUR_USERNAME
  ✓ Git operations for github.com configured to use ssh
  ✓ Token: *******************

然后再次：

ssh -T git@github.com

正常应该得到：

Hi YOUR_USERNAME! You've successfully authenticated, but GitHub does not provide shell access.

这时候就全部打通了。

5. 你现在这个情况其实比刚才更方便

刚才你的：

ssh -T git@github.com

报：

Permission denied (publickey)

原因很可能就是你生成了公钥，但还没有把它添加到 GitHub 账号。

现在 gh auth login 已经发现：

/home/cambricon/.ssh/id_ed25519_github.pub

并主动问你：

Upload your SSH public key to your GitHub account?

所以你直接同意上传即可，不需要自己去 GitHub 网页复制公钥。

你现在可以直接这样操作
? Upload your SSH public key to your GitHub account?
> Yes        ← 回车

? Title for your SSH key:
> Cambricon Linux        ← 输入这个，然后回车

然后按照浏览器里的 GitHub 登录/授权流程走。

完成后把终端最后几行输出贴给我，我可以继续帮你检查 gh、SSH、Git clone/push 是否全部配置正确。
