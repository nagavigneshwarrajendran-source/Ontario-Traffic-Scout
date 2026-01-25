Ontario Traffic Scout: Build Your Own Local Monitor
Hey! I’m a Computer Science Engineer living in Kitchener, and like everyone else here, I spend way too much time staring at brake lights on Highways 7, 8, and 85.

I built this project because I was tired of opening slow websites just to see if the 401 was a mess. Instead, I wanted the road images sent directly to my phone. But instead of just giving you a bot, I wanted to show you how to build your own—for whatever city you live in.

What this actually does
This isn't just a simple script. It’s a framework that uses a Geofence (basically a digital box) to scan through 900+ cameras across Ontario and pick out only the ones in your neighborhood.

Real-Time: It pulls the latest frames directly from the Ontario 511 API.

Universal: I built it for KWC, but you can swap in Toronto, London, or Ottawa coordinates in about 10 seconds.

Interactive: You type "map" in Telegram, and the bot shows you a menu. You pick a number, and you get a live photo.

Why I'm sharing this
I'm currently working toward an AI/ML career and clearing an educational loan. I believe the best way to grow is to build tools that solve real local problems and then help others understand how they work.

How to get it running
Clone it: Grab the code from this repo.

Get a Token: Talk to @BotFather on Telegram to get your secret API key.

Set Your Box: Update the REGION coordinates in the script to match your area.

Run it: Start the script and check your phone!

Let's Connect
If you find this helpful or want to talk about AI, ML, or even Quantum Computing, check out my portfolio at nagavigneshwar.ca.

Happy coding, and stay safe on the roads!
