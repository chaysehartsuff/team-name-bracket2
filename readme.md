# Project Setup and Commands

## Setup Section
1. **Install Python and Virtual Environment Package:**
   * On Ubuntu/Debian:
     ```bash
     sudo apt update
     sudo apt install python3 python3-venv python3-pip
     ```
   * On Fedora:
     ```bash
     sudo dnf install python3 python3-pip
     ```
2. **Create the Virtual Environment:**
   Navigate to your project directory and run:
   ```bash
   python3 -m venv .venv
   ```
3. **Activate the Virtual Environment:**
   ```bash
   source .venv/bin/activate
   ```
   *(This creates and activates a Python environment for the command line.)*
4. **Install Dependencies:**
   With your virtual environment active, install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the Bot:**
   Run `./start.sh` to connect the bot to the Discord server. *(Ensure your `start.sh` correctly invokes the `.venv` Python interpreter).*
6. **Stop the Bot:**
   Run `./stop.sh` to stop the bot from the Discord server.

## Commands Section
1. `/start` - Begins the voting process.
2. `/confirm` - Locks in the votes for the current round and moves forward. This command should be used to step through the entire bracket.
3. `/reset` - Should only be used in testing or emergencies. This command resets the bot's state and clears all votes.
4. `/give_vote {amount} {user|null}` - This command can give extra votes to everyone or a specified user. It should only be used during the preliminary stages, not during the bracket.
   - `{amount}`: The number of extra votes to give.
   - `{user|null}`: The user to give extra votes to. If this parameter is left blank, extra votes will be given to everyone.