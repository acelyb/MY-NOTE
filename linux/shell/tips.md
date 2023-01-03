# Shell tips

## difference between bash vs source

```shell
A
> ./myscript

B
> source myscript
```

Both sourcing and executing the script will run the commands in the script line by line, as if you typed those commands by hand line by line.

The differences are:

* When you execute the script you are opening a new shell, type the commands in the new shell, copy the output back to your current shell, then close the new shell. Any changes to environment will take effect only in the new shell and will be lost once the new shell is closed.
* When you source the script you are typing the commands in your current shell. Any changes to the environment will take effect and stay in your current shell.

the "environment" are things like the current working directory and environment variables. also shell settings (among others history and completion features). there are more but those are the most visible.

Use source if you want the script to change the environment in your currently running shell. use execute otherwise.

# 参考链接

1. [What is the difference between executing a Bash script vs sourcing it?](https://superuser.com/questions/176783/what-is-the-difference-between-executing-a-bash-script-vs-sourcing-it)
