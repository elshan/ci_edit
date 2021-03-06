# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import io
import inspect
import os
import sys
import time
import traceback


screenLog = [u"--- screen log ---"]
fullLog = [u"--- begin log ---"]
enabledChannels = {
  u'meta': True,
  #'mouse': True,
  u'startup': True,
}
shouldWritePrintLog = False
startTime = time.time()

def getLines():
  global screenLog
  return screenLog

def parseLines(frame, channel, *args):
  if not len(args):
    args = [u""]
  msg = str(args[0])
  if 1:
    msg = u"%s %s %s %s: %s"%(channel, os.path.split(frame[1])[1],
        frame[2], frame[3], msg)
  prior = msg
  for i in args[1:]:
    if not len(prior) or prior[-1] != u'\n':
      msg += u' '
    prior = repr(i)  #unicode(i)
    msg += prior
  return msg.split("\n")

def channelEnable(channel, isEnabled):
  global enabledChannels, fullLog, shouldWritePrintLog
  fullLog += [u"%10s %10s: %s %r" % (u'logging', u'channelEnable', channel,
      isEnabled)]
  if isEnabled:
    enabledChannels[channel] = isEnabled
    shouldWritePrintLog = True
  else:
    enabledChannels.pop(channel, None)

def channel(channel, *args):
  global enabledChannels, fullLog, screenLog
  if channel in enabledChannels:
    lines = parseLines(inspect.stack()[2], channel, *args)
    screenLog += lines
    fullLog += lines

def caller(*args):
  global fullLog, screenLog
  caller = inspect.stack()[2]
  msg = (u"%s %s %s" % (
      os.path.split(caller[1])[1], caller[2], caller[3]),) + args
  lines = parseLines(inspect.stack()[1], u"caller", *msg)
  screenLog += lines
  fullLog += lines

def exception(e):
  error(e)
  errorType, value, tracebackInfo = sys.exc_info()
  out = traceback.format_exception(errorType, value, tracebackInfo)
  for i in out:
    error(i[:-1])

def check_failed(prefix, a, op, b):
  stack(u'failed %s %r %s %r' % (prefix, a, op, b))
  raise Exception('fatal error')

def check_ge(a, b):
  if a >= b:
    return
  check_failed(u'check_ge', a, u'>=', b)

def check_gt(a, b):
  if a > b:
    return
  check_failed(u'check_lt', a, u'<', b)

def check_le(a, b):
  if a <= b:
    return
  check_failed(u'check_le', a, u'<=', b)

def check_lt(a, b):
  if a < b:
    return
  check_failed(u'check_lt', a, u'<', b)


def stack(*args):
  global fullLog, screenLog
  stack = inspect.stack()[1:]
  stack.reverse()
  for i,frame in enumerate(stack):
    line = [u"stack %2d %14s %4s %s" % (i, os.path.split(frame[1])[1],
        frame[2], frame[3])]
    screenLog += line
    fullLog += line
  if len(args):
    screenLog.append(u"stack    " + repr(args[0]))
    fullLog.append(u"stack    " + repr(args[0]))

def info(*args):
  channel(u'info', *args)

def meta(*args):
  """Log information related to logging."""
  channel(u'meta', *args)

def mouse(*args):
  channel(u'mouse', *args)

def parser(*args):
  channel(u'parser', *args)

def startup(*args):
  channel(u'startup', *args)

def quick(*args):
  global fullLog, screenLog
  msg = str(args[0])
  prior = msg
  for i in args[1:]:
    if not len(prior) or prior[-1] != u'\n':
      msg += u' '
    prior = i  # unicode(i)
    msg += prior
  lines = msg.split(u"\n")
  screenLog += lines
  fullLog += lines

def debug(*args):
  global enabledChannels, fullLog, screenLog
  if u'debug' in enabledChannels:
    lines = parseLines(inspect.stack()[1], u'debug_@@@', *args)
    screenLog += lines
    fullLog += lines

def detail(*args):
  global enabledChannels, fullLog
  if u'detail' in enabledChannels:
    lines = parseLines(inspect.stack()[1], u'detail', *args)
    fullLog += lines

def error(*args):
  global fullLog
  lines = parseLines(inspect.stack()[1], u'error', *args)
  fullLog += lines

def when(*args):
  args = (time.time() - startTime,) + args
  channel(u'info', *args)

def wrapper(function, shouldWrite=True):
  global shouldWritePrintLog
  shouldWritePrintLog = shouldWrite
  r = -1
  try:
    try:
      r = function()
    except BaseException:
      shouldWritePrintLog = True
      errorType, value, tracebackInfo = sys.exc_info()
      out = traceback.format_exception(errorType, value, tracebackInfo)
      for i in out:
        error(i[:-1])
  finally:
    flush()
  return r

def writeToFile(path):
  fullPath = os.path.expanduser(os.path.expandvars(path))
  with io.open(fullPath, 'w+') as out:
    out.write(u"\n".join(fullLog)+u"\n")

def flush():
  global fullLog
  if shouldWritePrintLog:
    sys.stdout.write(u"\n".join(fullLog) + u"\n")
