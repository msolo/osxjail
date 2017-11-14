# osxjail
A quick and dirty chroot script.

# Demo

## Freeze a manfiest for a few useful binaries

```
> ./osxjail.py freeze --manifest ./jail.manifest /bin/sh /bin/echo
```

## Run a simple program inside the jail
```
> sudo ./osxjail.py run --manifest ./jail.manifest ~/src/jail/jail-demo /bin/echo "I'm calling you from jail"

creating /Users/msolo/src/jail/jail-demo ...
copying 45 files...
mknod /Users/msolo/src/jail/jail-demo/dev/null 34 6178000 576603344
mknod /Users/msolo/src/jail/jail-demo/dev/urandom 34 6178000 576603344
mknod /Users/msolo/src/jail/jail-demo/dev/zero 34 6178000 576603344
entering jail /Users/msolo/src/jail/jail-demo ...
I'm calling you from jail
```
