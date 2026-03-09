I had an idea: what if we could treat some files as time series? Imagine if when you wrote to a file at a certain offset, that offset was maintained even when you wrote to another file. We'd have a perfect time log of when you wrote what to the files...

I made a dummy implementation of this; take a look.

This is a remote challenge, you can connect to the service with: `nc common-offset.challs.srdnlen.it 1089`
