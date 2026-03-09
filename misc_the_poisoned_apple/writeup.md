# The Trilogy of Death Vol 3: The Poisoned Apple

**Author:** @davezero (Davide Maiorca)
**CTF:** Srdnlen CTF 2026 Quals
**Category:** Misc
**Difficulty:** Medium
**Solves:** 80

## Description

> The Trilogy of Death - Chapter III - The Poisoned Apple
\
"He is gone. His last machine still holds its breath."
His last machine is here. Still running. Still breathing — barely. The Armourer is dead, but the truth of what he was building across three lifetimes is waiting. He left a final note:
\
"One taste of the poisoned apple, and the victim's eyes will close forever, in the Sleeping Death."
\
500.000 keys to decrypt the attached bin file (you can find it inside the dmg as well). One of them is special. If you understand which one (and why), you will be able to decrypt the file. Note that each decryption attempt will consume roughly 90 seconds on a single core.
\
DaveZero's note: This is a brutal challenge that will test your resistance and forensics skills. This is NOT a crypto challenge NOR a stego challenge. It requires A LOT of technical knowledge to be solved (unless you manage to find an unintended solution). Please note that, for this one, I will deliberately ignore any tickets that do not contain any reasonable advancements on the challenge.
\
The Trilogy of Death follows the digital ghost of a legendary hacker known only as The Armourer — a figure who lived and died by obsolete machines, leaving fragments of his secrets scattered across three machines. Are you able to unveil their secrets?
\
The Trilogy of Death is composed of three forensics challenges of increasing difficulty. The three challenges are completely independent and can be solved separately (i.e., you can solve chapter 3 without solving the other two). 
\
I hope you will enjoy the lore and the ideas behind the challenges, which will deeply challenge your forensics knowledge and skills!

## Solution

This challenge went horribly wrong. I spent a long time learning the APFS specifications (link here: https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf)

The APFS file system is CRAZY and has a lot of super interesting characteristics: CoW (copy-on-write), checkpoint support (but only under certain conditions), etc.

So I created a dmg image with 500.000 keys. One key was intentionally modified, and I used strong cryptography that would require roughly 90 seconds to decipher the key (to avoid brute force).

The original idea is the following:

- Each inode corresponding to a directory/file  is characterized by one or multiple physical extents (if modified)
- The idea was to parse each APFS block to determine whether the block was part of a B-Tree (the structure that contains the files and folders). A B-Tree node is very complex, but essentially we are interested in objects corresponding to file extents (ID value of objects Dir_rec → 0x9 and file extent → 0x8)
- Each extent maps files to a physical block number and is characterized by a transaction number (xid)
- The idea was to find that there was one inode with two file extents (two transaction nodes). The newer extent contained the real key, the older extent the previous key. The original idea was making you write a manual apfs parser (a non-trivial task even with slopping..this is why I boasted about the challenge difficulty : ) ).
- Retrieve manually the correct inode, corresponding to file key_449231.txt, retrieve the physical block and the two keys, try the older one, profit :).

Unfortunately, I didn’t consider that the file system contains a file called .fseventsd, which essentially contains transaction logs. Another interesting unintended was checking the files’ modification date (the one with the key was actually different - silly me that I didn’t corrupt the timestamps :-).

Fake key was: `b1a64c6e89971c26ce98d5984ec0499756306813c692ebb26cc039ad4c9b3319`

Original key: `39f520679fd68654500f9cd44e8caed2bc897a3227dc297c4520336de2a59dd7`

The deciphered flag is: `srdnlen{b3h0ld_th3_d34dl1_APFS!}`

I wanted to write a much deeper technical writeup, but I am storing it for another challenge or blog post (there is a lot of work, and next time I’d like to force you to navigate the file format manually :P ).
