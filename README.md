Script for automatically verifying tutorial commands contained within a markdown file.  Useful for
double checking things like tutorials.

Try running `python3 markdown_bash_checker.py -h` to get the usage and instructions on how to format
markdown files.

Here is an example markdown file that shows how to set environment variables, execute a command, and
check the command's output:

<pre>
# This is a markdown header.

This is some markdown text.

This sets an environment variable:
```bash-env
export FOO=foo
```

This echoes the variable to the screen:
```bash-exec
echo $FOO
```

This is the output that you should then expect to see:
```bash-output
foo
```
</pre>
