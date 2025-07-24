# Onresize
[![NPM version](https://img.shields.io/npm/v/resizelistener.svg?style=flat-square)](https://www.npmjs.com/package/resizelistener)
[![Dependency Status](https://img.shields.io/david/chemzqm/onresize.svg?style=flat-square)](https://david-dm.org/chemzqm/onresize)
[![Build Status](https://img.shields.io/travis/chemzqm/onresize/master.svg?style=flat-square)](http://travis-ci.org/chemzqm/onresize)

Attach resize event listener(s) to element without polling.

The technique is originally from: http://www.backalleycoder.com/2013/03/18/cross-browser-event-based-element-resize-detection/

**Notice** element would be set position to `relative` if it's position is
`static`

### Install

    npm i resizelistener

## API

### Onresize(element, listener)

Call listener function when ever element resizes, return a function could be
called to unbind this listener.

## LICENSE

  Copyright 2016 chemzqm@gmail.com

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the "Software"),
  to deal in the Software without restriction, including without limitation
  the rights to use, copy, modify, merge, publish, distribute, sublicense,
  and/or sell copies of the Software, and to permit persons to whom the
  Software is furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included
  in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

