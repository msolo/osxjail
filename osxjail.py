#!/usr/bin/env python2.7

import argparse
import errno
import os
import shutil
import stat
import subprocess
import sys

default_manifest = 'jail.manifest'
implicit_chroot_files = [
  '/dev/null',
  '/dev/zero',
  '/dev/urandom',
  '/usr/lib/dyld', # everyone needs a linker in their life
  ]

def main():
  ap = argparse.ArgumentParser()

  sp = ap.add_subparsers()

  cp = sp.add_parser('run')
  cp.add_argument('--manifest', default=default_manifest)
  cp.add_argument('--hardlink', action='store_true')
  cp.add_argument('jaildir')
  cp.add_argument('chroot_args', nargs='*')
  cp.set_defaults(func=cmd_run)

  cp = sp.add_parser('freeze')
  cp.add_argument('--manifest', default=default_manifest)
  cp.add_argument('files', nargs='+')
  cp.set_defaults(func=cmd_freeze)

  args = ap.parse_args()
  args.func(args)
  
def cmd_run(args):
  if os.getuid() != 0 or not os.environ.get('SUDO_USER'):
    sys.exit('mkjail must be run via sudo')

  jaildir = os.path.realpath(args.jaildir)
  if 'jail' not in jaildir:
    sys.exit('jail path should contain the word "jail" in it')
    
  file_manifest = [x.strip() for x in open(args.manifest) if x.strip()]
  dir_manifest = list(sorted(set(os.path.dirname(x) for x in file_manifest if os.path.dirname(x) != '/')))

  print 'creating', jaildir, '...'
  
  for dname in dir_manifest:
    dst = os.path.join(jaildir, dname.lstrip('/'))
    try:
      os.makedirs(dst)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise

  print 'copying', len(file_manifest), 'files...'
  # copying is sort of annoying. it would be interesting to hardlink and chflag each hardlink
  # simmutable to keep chroot cheap and safe.
  for fname in file_manifest:
    dst = os.path.join(jaildir, fname.lstrip('/'))
    try:
      fstat = os.stat(fname)
    except OSError as e:
      print 'missing entry', fname
      continue
    if stat.S_ISCHR(fstat.st_mode):
      major, minor = os.major(fstat.st_dev), os.minor(fstat.st_dev)
      dev = os.makedev(major, minor)
      print 'mknod', dst, major, minor, dev
      if os.path.exists(dst):
        os.remove(dst)
      os.mknod(dst, 0600|stat.S_IFCHR, dev)
    elif stat.S_ISDIR(fstat.st_mode):
      print 'bad entry', fname
      pass # already created
    else:
      shutil.copy(fname, dst)
  print 'entering jail', jaildir, '...'
  chroot_cmd = ['chroot', '-u', os.environ['SUDO_USER'], jaildir]
  if args.chroot_args:
    chroot_cmd += args.chroot_args
  os.execv('/usr/sbin/chroot', chroot_cmd)

def cmd_freeze(args):
  deps = find_deps(args.files)
  with open(args.manifest, 'w') as f:
    f.write('\n'.join(deps))
    f.write('\n')

# Find all dependency paths for a binary.
def _find_deps(fnames):
  out = subprocess.check_output(['otool', '-L',] + fnames)
  dep_paths = set()
  for line in out.splitlines():
    if ':' in line:
      continue
    try:
      dep_paths.add(line.strip().split()[0])
    except:
      print 'bad line', line
  return list(dep_paths)

def find_deps(fnames):
  dep_paths = set(implicit_chroot_files)
  check_paths = fnames
  while check_paths:
    paths = _find_deps(check_paths)
    dep_paths.update(check_paths)
    check_paths = list(set(paths) - dep_paths)
  return list(sorted(dep_paths))

if __name__ == '__main__':
  main()
