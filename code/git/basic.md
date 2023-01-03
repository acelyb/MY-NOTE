# git 常用指令

# git 实操

## 重命名远程分支

在 github 上修改远程分支的名字后，本地需要做如下操作

```shell
git branch -m main master
git fetch origin
git branch -u origin/master master
git remote set-head origin -a
```

## 二分法 git bisect

`git bisect start`命令启动查错，它的格式如下

```shell
$ git bisect start [终点] [起点]
```

例：

```shell
$ git bisect start HEAD 4d83cf
```

如果正确，使用 `git bisect good` 命令

如果错误，使用 `git bisect bad` 命令

接下来，不断重复这个过程，直到成功找到出问题的那一次提交为止。这时，Git 会给出如下的提示

```shell
xxxxx is the first bad commit
```

既然找到那个有问题的提交，就可以检查代码，确定具体是什么错误

然后，使用 `git bisect reset` 命令，退出查错，回到最近一次的代码提交

## git commit

### --amend

对之前的 `commit` 提交进行修改。这里的之前指最近的commit，而且没有push到远程

修改提交的内容分为2种情况：

1. 提交了代码之后,又有新的改动，不想创建两个commit
2. 发现一个地方改错了，下次提交时不想保留上一次的记录

这时就可以使用`git commit --amend`命令把新的内容添加到之前的commit里面,这个命令没有添加新的提交，而是用新提交取代了原始提交

可以使用 `git commit --amend -m "提交描述"` 修改comment

## git rebase

### -i

`git rebase -i` 命令可以压缩合并多次提交

格式：`git rebase -i [startpoint] [endpoint]`

```git
git rebase -i HEAD~4
```

合并最新4次提交

在查看git的log后，可以使用如下命令

```git
// 合并从当前head到15f745b(commit id)
git rebase -i 15f745b
或:
// 合并最近的两次提交
git rebase -i HEAD~2
```

执行这个命令后会跳到一个vi编辑器

里面的提示有：

* pick：保留该commit（缩写:p）
* reword：保留该commit，但我需要修改该commit的注释（缩写:r）
* edit：保留该commit, 但我要停下来修改该提交(不仅仅修改注释)（缩写:e）
* squash：将该commit和前一个commit合并（缩写:s）
* fixup：将该commit和前一个commit合并，但我不要保留该提交的注释信息（缩写:f）
* exec：执行shell命令（缩写:x）
* drop：我要丢弃该commit（缩写:d）

修改后保存退出即可
