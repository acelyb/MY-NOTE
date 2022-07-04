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
