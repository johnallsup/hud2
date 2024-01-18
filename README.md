# hud2
Simple hud overlay in PySide6

This is a simple app that I can send text to via UDP
which is then displayed over the top of whatever's on screen.
Just scratching an itch, nothing remotely professional or well-engineered.
Best use is as random snippets for PySide6 rather than anything serious.

# hud.py
This is the main core of the code

# drivers
`hud1.py` runs once instance; `hud2.py` runs four.
In the case of the four instances, settings like font size
are individual to each.

# Future work
Enable word wrap. There is working code for basic word wrap in subt.

## Word Wrap
We need to do something like hyphenation if a single word does not fit
on a line. And perhaps if a line is too short after word wrapping.
For example, if a line becomes less than 65% long after wrapping,
search the word for a hypenation point. At first, just put as many
chars on the end of the line as will fit, including a -, and then
stick the rest on the following line.
