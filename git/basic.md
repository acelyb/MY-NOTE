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
