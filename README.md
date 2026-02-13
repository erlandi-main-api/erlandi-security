# erlandi-security 
bot ini sedangan dalam pengembangan masih tahan beta salam hangat erlandi.eu org
# linux install
mkdir -p erlandi-security/data
cd erlandi-security

touch bot.py requirements.txt .gitignore .env.example
touch data/fban.txt

# local
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export BOT_TOKEN="ISI_TOKEN_KAMU"
python bot.py
