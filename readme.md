Description:
Originally designed to host a submission and voting based competition bracket
that allows discord server users to contribute in a democractic based process
that determines a winner submission

Stage 1:
You may configure premliminary qualification rounds that allows
many submissions and gives users a chance to pick the top names from each round

Stage 2:
Once enough submissions qualify (based on your bracket size) a visual bracket will generate
where a single elimination style voting will take place. Each round walks through the bracket
until only 1 submission remains

The server owner/admin is responsible for walking through each round by using the /confirm command

- Feel free to request features as desired, this project was built for a very specific vision



Setup Section:
1. Run `source .venv/bin/activate` - This creates a Python environment for the command line.
2. Run `./start.sh` to connect the bot to the Discord server.
3. Run `./stop.sh` to stop the bot from the Discord server.

Commands Section:
1. `/start` - Begins the voting process.
2. `/confirm` - Locks in the votes for the current round and moves forward. This command should be used to step through the entire bracket.
3. `/reset` - Should only be used in testing or emergencies. This command resets the bot's state and clears all votes.
4. `/give_vote {amount} {user|null}` - This command can give extra votes to everyone or a specified user. It should only be used during the preliminary stages, not during the bracket.
   - `{amount}`: The number of extra votes to give.
   - `{user|null}`: The user to give extra votes to. If this parameter is left blank, extra votes will be given to everyone.