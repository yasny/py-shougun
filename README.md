# py-shougun

`py-shougun` takes Java thread dumps created by `jstack` and creates a static HTML site to help with analysis.

This program is inspired by [侍 (samurai)](https://github.com/yusuke/samurai/) which it a great tool but can grind to a halt with a large number of thread dumps.
`py-shougun` was tested and seems to work just fine with thread dump files over 80MB, containing over 70,000 separate stack dumps.
