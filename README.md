# vector
Vector is an AI assistant that helps me track open tasks and schedule focus time into my calendar to get things done. Feel free to copy this and use it however you like!

# How to run
The way that Vector communicates with me is through Signal. Running this requires a docker container running in the background on my machine. I got that part of the project from [here](https://github.com/bbernhard/signal-cli-rest-api).

Since I'm on Windows the steps are:
- Open Docker Desktop
- run `docker run -d --name signal-api -p 7388:8080 -v ${HOME}\.signal_cli:/home/.local/share/signal-cli bbernhard/signal-cli-rest-api` (I like to run it from port 7388 and I have my .signal_cli data stored under my home directory)
- run python main.py in this project and leave it running in the background all day
- while running, logs are captured in `logs.txt` in the project directory

# First time Signal setup
Here's what I did (I ran all these curl commands in Linux on WSL on my Windows machine since powershell is annoying):
- got a phone number from Google Voice
- got docker container up and running, check that it's working by running `curl http://localhost:7388/v1/about` 
- register your new number`curl -X POST -H "Content-Type: application/json" -d '{"use_voice": false}' http://localhost:7388/v1/register/+1{NEW_NUMBER}`
    - In my case, I got an error and had to generate a captcha here: https://signalcaptchas.org/registration/generate.html
    - Then copied the "Open Signal" link and used token in the register endpoint: `curl -X POST -H "Content-Type: application/json" -d '{"use_voice": false, "captcha": "{LONG_TOKEN_HERE}"}' http://localhost:7388/v1/register/+1{NUMBER}`
- Then I got the text on my Google Voice account with a 6 digit code! Run `curl -X POST -H "Content-Type: application/json" http://localhost:7388/v1/register/+1{NUMBER}/verify/{CODE}` to verify
- At this point, I was able to send myself a message and verified that it worked! `curl -X POST -H "Content-Type: application/json" -d '{"message": "Hello from Vector!", "number": "+1{NUMBER}", "recipients": ["+1{MY_NUMBER}"]}' http://localhost:7388/v2/send`
- I also wanted to set my profile name and have a cool profile picture: `curl -X PUT -H "Content-Type: application/json" -d '{"name": "Vector", "base64_avatar": "{SUPER_LONG_BASE64_PNG}"}' http://localhost:7388/v1/profiles/+1{NUMBER}`
This link is super useful for seeing everything you can do with this API: https://bbernhard.github.io/signal-cli-rest-api/#/