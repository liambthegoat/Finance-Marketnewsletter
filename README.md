# Finance-Marketnewsletter
This newsletter displays index stocks, currency exchange rates, and a sample of the S&amp;P 500.
The first thing you want to do is to download the 3 other files other than licence and this one
you want to go into newsletter.py and complete the setup with a gmail and app password along with the api key
then you want to run these 4 commands in terminal
mkdir -p ~/market_newsletter
cp ~/Downloads/newsletter.py ~/Downloads/run_newsletter.sh ~/Downloads/com.marketdaily.newsletter.plist ~/market_newsletter/
chmod +x ~/market_newsletter/run_newsletter.sh
cp ~/market_newsletter/com.marketdaily.newsletter.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.marketdaily.newsletter.plist
and then you are done and it will run on launch
happy newsletters guys
remember to save your changes by hitting command+s
