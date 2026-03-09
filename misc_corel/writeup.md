# The Trilogy of Death Vol 1: Corel

**Author:** @davezero (Davide Maiorca)
**CTF:** Srdnlen CTF 2026 Quals
**Category:** Misc
**Difficulty:** Easy
**Solves:** 79

## Description

> The Trilogy of Death - Chapter I - Corel
\
[Attachments](https://unicadrsi-my.sharepoint.com/:f:/g/personal/davide_maiorca_unica_it1/IgCQXVtk_QPdTJyDMzAxt5PAAUi_B-Ql762Rxt2VmOIAmQ8?e=wz1yXe)
\
"He was born in a forgotten kingdom."
\
In an era when the penguin still dreamed of conquering the desktop, a kingdom rose - beautiful, ambitious, and doomed. It promised a new world, dressed in the robes of a giant that never truly understood it. The Armourer was there when it was built, and there when it crumbled. He made his first forge in its ruins, hiding his earliest secrets inside a dead world that nobody thought to search anymore. Most people never even knew the kingdom existed. That was always the point.
\
Note by DaveZero: This was supposed to be easy mode, but I may be wrong...
\
The Trilogy of Death follows the digital ghost of a legendary hacker known only as The Armourer - a figure who lived and died by obsolete machines, leaving fragments of his secrets scattered across three machines. Are you able to unveil their secrets?
\
The Trilogy of Death is composed of three forensics challenges of increasing difficulty. The three challenges are completely independent and can be solved separately (i.e., you can solve chapter 3 without solving the other two). 
\
I hope you will enjoy the lore and the ideas behind the challenges, which will deeply challenge your forensics knowledge and skills!

## Solution

You got a qcow file. The image was constructed by installing Corel Linux, an ancient Linux-based OS, on QEMU.

The original intended solution was:

1. Running the qcow file with Qemu, loading Corel Linux
2. Exploring the folder structure and finding a WordPerfect macro file, fc.wcm (wordperfect was used a lot in the Corel suite at the time) in the /var/log folder. A good way to find it quickly would be to order the files by modification date.
3. Executing the macro: the macro features an encrypted string and prints a message: The Key is in what is left.
4. Ironically, the players used an uninteded solution, that is a Known Plantext attack against the key (my bad: i used a key that was too short, should have used OTP Instead)
5. The intended solution and the meaning of the message was that the key was saved in the slack space of the fc.wcm file itself (you can easily retrieve it by checking the corresponding inode and associated blocks: the block that is the left is the one used).

That gives the flag:

`srdnlen{wh3n_c0r3l_w4s_4n_4lt3rn4t1v3}`