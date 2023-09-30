# dndCombatSim
A python simulator for a D&amp;D combat. Used by a DM to check how difficult a combat is for your players.

The main file is dndCombatSim.py. If you wish to run the program, just run from command line which will execute main().

> {repo}/dndCombatSim.py

The output to the console will give the most important information. If you want more details on what happened, read battle###.log where ### is YYYYMMDDHHmmSS of when the script was ran.

If you wish to have a direct approach to running the simulator. You can run in python. Example below.

> {repo}/python.exe
>
>\>>> import dndCombatSim as dcs
>
>\>>> battle = dcs.battleStage()

To change the characters in the combat, you edit characters.json. Read the json_format.txt to know how to create your own characters.
